import json
import logging
import os
import re
import shutil
from functools import partial, wraps

import netCDF4
import numpy as np
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.forms.models import formset_factory, BaseFormSet
from django.template import Template, Context
from dominate import tags as html_tags
from rdflib import RDF, BNode, Literal
from rdflib.namespace import DCTERMS

import hs_file_types.nc_functions.nc_dump as nc_dump
import hs_file_types.nc_functions.nc_meta as nc_meta
import hs_file_types.nc_functions.nc_utils as nc_utils
from hs_core.enums import RelationTypes
from hs_core.forms import CoverageTemporalForm, CoverageSpatialForm
from hs_core.hs_rdf import HSTERMS, rdf_terms
from hs_core.hydroshare import utils
from hs_core.models import Creator, Contributor, AbstractMetaDataElement
from hs_core.signals import post_add_netcdf_aggregation
from hs_file_types.models.base import AbstractFileMetaData, AbstractLogicalFile, FileTypeContext
from hs_file_types.enums import AggregationMetaFilePath


@rdf_terms(HSTERMS.spatialReference)
class OriginalCoverage(AbstractMetaDataElement):
    PRO_STR_TYPES = (
        ("", "---------"),
        ("WKT String", "WKT String"),
        ("Proj4 String", "Proj4 String"),
    )

    term = "OriginalCoverage"
    """
    _value field stores a json string. The content of the json as box coverage info
         _value = "{'northlimit':northenmost coordinate value,
                    'eastlimit':easternmost coordinate value,
                    'southlimit':southernmost coordinate value,
                    'westlimit':westernmost coordinate value,
                    'units:units applying to 4 limits (north, east, south & east),
                    'projection': name of the projection (optional)}"
    """
    _value = models.CharField(max_length=1024, null=True)
    projection_string_type = models.CharField(
        max_length=20, choices=PRO_STR_TYPES, null=True
    )
    projection_string_text = models.TextField(null=True, blank=True)
    datum = models.CharField(max_length=300, blank=True)

    class Meta:
        # OriginalCoverage element is not repeatable
        unique_together = ("content_type", "object_id")

    @property
    def value(self):
        return json.loads(self._value)

    @classmethod
    def ingest_rdf(cls, graph, subject, content_object):
        for _, _, cov in graph.triples((subject, cls.get_class_term(), None)):
            value = graph.value(subject=cov, predicate=RDF.value)
            value_dict = {}
            datum = ""
            projection_string_text = ""
            for key_value in value.split(";"):
                key_value = key_value.strip()
                k, v = key_value.split("=")
                if k == "datum":
                    datum = v
                elif k == "projection_string":
                    projection_string_text = v
                elif k == "projection_name":
                    value_dict["projection"] = v
                elif k == "projection_string_type":
                    projection_string_type = v
                else:
                    value_dict[k] = v
            OriginalCoverage.create(
                projection_string_type=projection_string_type,
                projection_string_text=projection_string_text,
                _value=json.dumps(value_dict),
                datum=datum,
                content_object=content_object,
            )

    def rdf_triples(self, subject, graph):
        coverage = BNode()
        graph.add((subject, self.get_class_term(), coverage))
        graph.add((coverage, RDF.type, DCTERMS.box))
        value_dict = {}
        for k, v in self.value.items():
            if k == "projection":
                value_dict["projection_name"] = v
            else:
                value_dict[k] = v
        value_dict["datum"] = self.datum
        value_dict["projection_string"] = self.projection_string_text
        value_dict["projection_string_type"] = self.projection_string_type
        value_string = "; ".join(
            ["=".join([key, str(val)]) for key, val in value_dict.items()]
        )
        graph.add((coverage, RDF.value, Literal(value_string)))

    @classmethod
    def create(cls, **kwargs):
        """
        The '_value' subelement needs special processing. (Check if the 'value' includes the
        required information and convert 'value' dict as Json string to be the '_value'
        subelement value.) The base class create() can't do it.

        :param kwargs: the 'value' in kwargs should be a dictionary
                       the '_value' in kwargs is a serialized json string
        """
        value_arg_dict = None
        if "value" in kwargs:
            value_arg_dict = kwargs["value"]
        elif "_value" in kwargs:
            value_arg_dict = json.loads(kwargs["_value"])

        if value_arg_dict:
            # check that all the required sub-elements exist and create new original coverage meta
            for value_item in [
                "units",
                "northlimit",
                "eastlimit",
                "southlimit",
                "westlimit",
            ]:
                if value_item not in value_arg_dict:
                    raise ValidationError(
                        "For original coverage meta, one or more bounding "
                        "box limits or 'units' is missing."
                    )

            value_dict = {
                k: v
                for k, v in list(value_arg_dict.items())
                if k
                in (
                    "units",
                    "northlimit",
                    "eastlimit",
                    "southlimit",
                    "westlimit",
                    "projection",
                )
            }

            cls._validate_bounding_box(value_dict)
            value_json = json.dumps(value_dict)
            if "value" in kwargs:
                del kwargs["value"]
            kwargs["_value"] = value_json
            return super(OriginalCoverage, cls).create(**kwargs)
        else:
            raise ValidationError("Coverage value is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        """Define custom update method for spatial reference (OriginalCoverage) model."""
        raise ValidationError("Spatial reference  can't be updated.")

    @classmethod
    def remove(cls, element_id):
        """Define custom remove method for spatial reference (OriginalCoverage) model."""
        raise ValidationError("Spatial reference can't be deleted.")

    @classmethod
    def _validate_bounding_box(cls, box_dict):
        for limit in ("northlimit", "eastlimit", "southlimit", "westlimit"):
            try:
                box_dict[limit] = float(box_dict[limit])
            except ValueError:
                raise ValidationError("Bounding box data is not numeric")

    @classmethod
    def get_html_form(cls, resource, element=None, allow_edit=True, file_type=False):
        """Generates html form code for this metadata element so that this element can be edited"""

        from ..forms import OriginalCoverageForm

        ori_coverage_data_dict = dict()
        if element is not None:
            ori_coverage_data_dict["projection"] = element.value.get("projection", None)
            ori_coverage_data_dict["datum"] = element.datum
            ori_coverage_data_dict[
                "projection_string_type"
            ] = element.projection_string_type
            ori_coverage_data_dict[
                "projection_string_text"
            ] = element.projection_string_text
            ori_coverage_data_dict["units"] = element.value["units"]
            ori_coverage_data_dict["northlimit"] = element.value["northlimit"]
            ori_coverage_data_dict["eastlimit"] = element.value["eastlimit"]
            ori_coverage_data_dict["southlimit"] = element.value["southlimit"]
            ori_coverage_data_dict["westlimit"] = element.value["westlimit"]

        originalcov_form = OriginalCoverageForm(
            initial=ori_coverage_data_dict,
            allow_edit=allow_edit,
            res_short_id=resource.short_id if resource else None,
            element_id=element.id if element else None,
            file_type=file_type,
        )

        return originalcov_form

    def get_html(self, pretty=True):
        """Generates html code for displaying data for this metadata element"""

        root_div = html_tags.div(cls="content-block")

        def get_th(heading_name):
            return html_tags.th(heading_name, cls="text-muted")

        with root_div:
            html_tags.legend("Spatial Reference")
            if self.value.get("projection", ""):
                html_tags.div("Coordinate Reference System", cls="text-muted")
                html_tags.div(self.value.get("projection", ""))
            if self.datum:
                html_tags.div("Datum", cls="text-muted has-space-top")
                html_tags.div(self.datum)
            if self.projection_string_type:
                html_tags.div("Coordinate String Type", cls="text-muted has-space-top")
                html_tags.div(self.projection_string_type)
            if self.projection_string_text:
                html_tags.div("Coordinate String Text", cls="text-muted has-space-top")
                html_tags.div(self.projection_string_text)

            html_tags.h4("Extent", cls="space-top")
            with html_tags.table(cls="custom-table"):
                with html_tags.tbody():
                    with html_tags.tr():
                        get_th("North")
                        html_tags.td(self.value["northlimit"])
                    with html_tags.tr():
                        get_th("West")
                        html_tags.td(self.value["westlimit"])
                    with html_tags.tr():
                        get_th("South")
                        html_tags.td(self.value["southlimit"])
                    with html_tags.tr():
                        get_th("East")
                        html_tags.td(self.value["eastlimit"])
                    with html_tags.tr():
                        get_th("Unit")
                        html_tags.td(self.value["units"])

        return root_div.render(pretty=pretty)


class Variable(AbstractMetaDataElement):
    # variable types are defined in OGC enhanced_data_model_extension_standard
    # left is the given value stored in database right is the value for the drop down list
    VARIABLE_TYPES = (
        ("Char", "Char"),  # 8-bit byte that contains uninterpreted character data
        ("Byte", "Byte"),  # integer(8bit)
        ("Short", "Short"),  # signed integer (16bit)
        ("Int", "Int"),  # signed integer (32bit)
        ("Float", "Float"),  # floating point (32bit)
        ("Double", "Double"),  # floating point(64bit)
        ("Int64", "Int64"),  # integer(64bit)
        ("Unsigned Byte", "Unsigned Byte"),
        ("Unsigned Short", "Unsigned Short"),
        ("Unsigned Int", "Unsigned Int"),
        ("Unsigned Int64", "Unsigned Int64"),
        ("String", "String"),  # variable length character string
        ("User Defined Type", "User Defined Type"),  # compound, vlen, opaque, enum
        ("Unknown", "Unknown"),
    )
    term = "Variable"
    # required variable attributes
    name = models.CharField(max_length=1000)
    unit = models.CharField(max_length=1000)
    type = models.CharField(max_length=1000, choices=VARIABLE_TYPES)
    shape = models.CharField(max_length=1000)
    # optional variable attributes
    descriptive_name = models.CharField(
        max_length=1000, null=True, blank=True, verbose_name="long name"
    )
    method = models.TextField(null=True, blank=True, verbose_name="comment")
    missing_value = models.CharField(max_length=1000, null=True, blank=True)

    def __unicode__(self):
        return self.name

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("The variable of the resource can't be deleted.")

    def get_html(self, pretty=True):
        """Generates html code for displaying data for this metadata element"""

        root_div = html_tags.div(cls="content-block")

        def get_th(heading_name):
            return html_tags.th(heading_name, cls="text-muted")

        with root_div:
            with html_tags.div(cls="custom-well"):
                html_tags.strong(self.name)
                with html_tags.table(cls="custom-table"):
                    with html_tags.tbody():
                        with html_tags.tr():
                            get_th("Unit")
                            html_tags.td(self.unit)
                        with html_tags.tr():
                            get_th("Type")
                            html_tags.td(self.type)
                        with html_tags.tr():
                            get_th("Shape")
                            html_tags.td(self.shape)
                        if self.descriptive_name:
                            with html_tags.tr():
                                get_th("Long Name")
                                html_tags.td(self.descriptive_name)
                        if self.missing_value:
                            with html_tags.tr():
                                get_th("Missing Value")
                                html_tags.td(self.missing_value)
                        if self.method:
                            with html_tags.tr():
                                get_th("Comment")
                                html_tags.td(self.method)

        return root_div.render(pretty=pretty)


class NetCDFMetaDataMixin(models.Model):
    """This class must be the first class in the multi-inheritance list of classes"""

    variables = GenericRelation(Variable)
    ori_coverage = GenericRelation(OriginalCoverage)

    class Meta:
        abstract = True

    @property
    def originalCoverage(self):
        return self.ori_coverage.all().first()

    def has_all_required_elements(self):
        # checks if all required metadata elements have been created
        if not super(NetCDFMetaDataMixin, self).has_all_required_elements():
            return False
        if not self.variables.all():
            return False
        return True

    def get_required_missing_elements(self):
        # get a list of missing required metadata element names
        missing_required_elements = super(
            NetCDFMetaDataMixin, self
        ).get_required_missing_elements()
        if not self.variables.all().first():
            missing_required_elements.append("Variable")

        return missing_required_elements

    def delete_all_elements(self):
        super(NetCDFMetaDataMixin, self).delete_all_elements()
        self.ori_coverage.all().delete()
        self.variables.all().delete()

    @classmethod
    def get_supported_element_names(cls):
        # get the class names of all supported metadata elements for this resource type
        # or file type
        elements = super(NetCDFMetaDataMixin, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append("Variable")
        elements.append("OriginalCoverage")
        return elements


class NetCDFFileMetaData(NetCDFMetaDataMixin, AbstractFileMetaData):
    # used in finding ContentType for the metadata model classes
    model_app_label = "hs_file_types"
    # flag to track when the .nc file of the aggregation needs to be updated.
    is_update_file = models.BooleanField(default=False)

    def update_element(self, element_model_name, element_id, **kwargs):
        if element_model_name.lower() == "coverage":
            model_type = self._get_metadata_element_model_type(element_model_name)
            element = model_type.model_class().objects.get(id=element_id)
            if element.type in ("box", "point"):
                logical_file = self.logical_file
                if logical_file.metadata.originalCoverage:
                    raise ValidationError(
                        "Spatial coverage can't be updated which has been computed "
                        "from spatial reference"
                    )

        super(NetCDFFileMetaData, self).update_element(
            element_model_name, element_id, **kwargs
        )

    def get_metadata_elements(self):
        elements = super(NetCDFFileMetaData, self).get_metadata_elements()
        elements += [self.originalCoverage]
        elements += list(self.variables.all())
        return elements

    @classmethod
    def get_metadata_model_classes(cls):
        metadata_model_classes = super(
            NetCDFFileMetaData, cls
        ).get_metadata_model_classes()
        metadata_model_classes["originalcoverage"] = OriginalCoverage
        metadata_model_classes["variable"] = Variable
        return metadata_model_classes

    @property
    def original_coverage(self):
        # There can be at most only one instance of type OriginalCoverage associated
        # with this metadata object
        return self.originalCoverage

    def to_json(self):
        """Returns metadata in JSON format using schema.org vocabulary where possible and the rest terms
          are based on hsterms."""

        json_dict = super().to_json()
        json_dict['additionalType'] = self.logical_file.get_aggregation_type_name()

        variables_meta = {"variableMeasured": []}
        for variable in self.variables.all():
            v_meta = {
                "hsterms:name": variable.name,
                "hsterms:type": variable.type,
                "hsterms:shape": variable.shape,
                "hsterms:unit": variable.unit
            }
            if variable.missing_value:
                v_meta["hsterms:missingValue"] = variable.missing_value
            if variable.descriptive_name:
                v_meta["hsterms:longName"] = variable.descriptive_name
            if variable.method:
                v_meta["hsterms:method"] = variable.method

            variables_meta["variableMeasured"].append(v_meta)
        if variables_meta["variableMeasured"]:
            json_dict.update(variables_meta)

        originalCoverage = self.originalCoverage
        if originalCoverage:
            orig_coverage_meta = {
                "hsterms:northLimit": originalCoverage.value["northlimit"],
                "hsterms:eastLimit": originalCoverage.value["eastlimit"],
                "hsterms:southLimit": originalCoverage.value["southlimit"],
                "hsterms:westLimit": originalCoverage.value["westlimit"],
                "hsterms:units": originalCoverage.value["units"],
            }
            if "projection" in originalCoverage.value and originalCoverage.value["projection"]:
                orig_coverage_meta.update({
                    "hsterms:projection": originalCoverage.value["projection"],
                    "hsterms:projectionString": originalCoverage.projection_string_text,
                    "hsterms:projectionStringType": originalCoverage.projection_string_type,
                    "hsterms:datum": originalCoverage.datum,
                })
        json_dict.update({"hsterms:originalCoverage": orig_coverage_meta})
        return json_dict

    def _get_opendap_html(self):
        opendap_div = html_tags.div(cls="content-block")
        res_id = self.logical_file.resource.short_id
        file_name = self.logical_file.aggregation_name
        opendap_url = f"{settings.THREDDS_SERVER_URL}dodsC/hydroshare/resources/{res_id}/data/contents/{file_name}.html"
        with opendap_div:
            html_tags.legend("OPeNDAP using DAP2")
            html_tags.em(
                "The netCDF data in this multidimensional content aggregation may be accessed at the link below "
                "using the OPeNDAP DAP2 protocol enabled on the HydroShare deployment of Unidata’s THREDDS data "
                "server. This enables direct and programmable access to this data through "
            )
            html_tags.a(
                " OPeNDAP client software",
                href="https://www.opendap.org/support/OPeNDAP-clients",
                target="_blank",
            )
            with html_tags.div(style="margin-top:10px;"):
                html_tags.a(opendap_url, href=opendap_url, target="_blank")

        return opendap_div.render()

    def get_html(self, **kwargs):
        """overrides the base class function"""

        html_string = super(NetCDFFileMetaData, self).get_html()
        if self.logical_file.resource.raccess.public:
            html_string += self._get_opendap_html()
        spatial_coverage = self.spatial_coverage
        if spatial_coverage:
            html_string += spatial_coverage.get_html()
        originalCoverage = self.originalCoverage
        if originalCoverage:
            html_string += originalCoverage.get_html()
        temporal_coverage = self.temporal_coverage
        if temporal_coverage:
            html_string += temporal_coverage.get_html()
        variable_legend = html_tags.legend("Variables")
        html_string += variable_legend.render()
        for variable in self.variables.all():
            html_string += variable.get_html()

        # ncdump text from the txt file
        html_string += self.get_ncdump_html().render()
        template = Template(html_string)
        context = Context({})
        return template.render(context)

    def get_html_forms(self, dataset_name_form=True, temporal_coverage=True, **kwargs):
        """overrides the base class function"""

        root_div = html_tags.div("{% load crispy_forms_tags %}")
        with root_div:
            if not self.originalCoverage:
                with html_tags.div(
                    cls="alert alert-warning alert-dismissible", role="alert"
                ):
                    with html_tags.div():
                        html_tags.p(
                            "NetCDF file is missing spatial coverage information:"
                        )
                        with html_tags.span(
                            "HydroShare uses GDAL to extract spatial coverage information from NetCDF files. "
                            "GDAL’s NetCDF driver follows the CF-1 Convention defined by UNIDATA. More information "
                            "about the GDAL NetCDF Driver is located"
                        ):
                            html_tags.a(
                                "here.",
                                target="_blank",
                                href="https://gdal.org/drivers/raster/netcdf.html#georeference",
                            )
                            with html_tags.span(
                                "You can verify a NetCDF file’s compliance with the CF-1 and other standards using"
                            ):
                                html_tags.a(
                                    "NASA’s Metadata Compliance checker.",
                                    target="_blank",
                                    href="https://podaac-tools.jpl.nasa.gov/mcc/",
                                )

            self.get_update_netcdf_file_html_form()
            super(NetCDFFileMetaData, self).get_html_forms()

            with html_tags.div():
                with html_tags.div(
                    cls="content-block", id="original-coverage-filetype"
                ):
                    with html_tags.form(
                        id="id-origcoverage-file-type",
                        action="{{ orig_coverage_form.action }}",
                        method="post",
                        enctype="multipart/form-data",
                    ):
                        html_tags.div("{% crispy orig_coverage_form %}")
                        with html_tags.div(cls="row", style="margin-top:10px;"):
                            with html_tags.div(
                                cls="col-md-offset-10 col-xs-offset-6 "
                                "col-md-2 col-xs-6"
                            ):
                                html_tags.button(
                                    "Save changes",
                                    type="button",
                                    cls="btn btn-primary pull-right",
                                    style="display: none;",
                                )

            with html_tags.div(cls="content-block", id="spatial-coverage-filetype"):
                with html_tags.form(
                    id="id-spatial-coverage-file-type",
                    cls="hs-coordinates-picker",
                    data_coordinates_type="box",
                    action="{{ spatial_coverage_form.action }}",
                    method="post",
                    enctype="multipart/form-data",
                ):
                    html_tags.div("{% crispy spatial_coverage_form %}")
                    with html_tags.div(cls="row", style="margin-top:10px;"):
                        with html_tags.div(
                            cls="col-md-offset-10 col-xs-offset-6 " "col-md-2 col-xs-6"
                        ):
                            html_tags.button(
                                "Save changes",
                                type="button",
                                cls="btn btn-primary pull-right",
                                style="display: none;",
                            )

            with html_tags.div():
                html_tags.legend("Variables")
                # id has to be variables to get the vertical scrollbar
                with html_tags.div(id="variables"):
                    with html_tags.div("{% for form in variable_formset_forms %}"):
                        with html_tags.form(
                            id="{{ form.form_id }}",
                            action="{{ form.action }}",
                            method="post",
                            enctype="multipart/form-data",
                            cls="well",
                        ):
                            html_tags.div("{% crispy form %}")
                            with html_tags.div(cls="row", style="margin-top:10px;"):
                                with html_tags.div(
                                    cls="col-md-offset-10 col-xs-offset-6 "
                                    "col-md-2 col-xs-6"
                                ):
                                    html_tags.button(
                                        "Save changes",
                                        type="button",
                                        cls="btn btn-primary pull-right",
                                        style="display: none;",
                                    )
                    html_tags.div("{% endfor %}")

            self.get_ncdump_html()

        template = Template(root_div.render())
        temp_cov_form = self.get_temporal_coverage_form()
        update_action = (
            "/hsapi/_internal/NetCDFLogicalFile/{0}/{1}/{2}/update-file-metadata/"
        )
        create_action = "/hsapi/_internal/NetCDFLogicalFile/{0}/{1}/add-file-metadata/"
        temporal_coverage = self.temporal_coverage
        if temporal_coverage:
            temp_action = update_action.format(
                self.logical_file.id, "coverage", temporal_coverage.id
            )
        else:
            temp_action = create_action.format(self.logical_file.id, "coverage")

        temp_cov_form.action = temp_action

        orig_cov_form = self.get_original_coverage_form()

        allow_coverage_edit = not self.originalCoverage
        spatial_cov_form = self.get_spatial_coverage_form(
            allow_edit=allow_coverage_edit
        )
        if allow_coverage_edit:
            spatial_coverage = self.spatial_coverage
            if spatial_coverage:
                temp_action = update_action.format(
                    self.logical_file.id, "coverage", spatial_coverage.id
                )
            else:
                temp_action = create_action.format(self.logical_file.id, "coverage")

        spatial_cov_form.action = temp_action
        context_dict = dict()
        context_dict["temp_form"] = temp_cov_form
        context_dict["orig_coverage_form"] = orig_cov_form
        context_dict["spatial_coverage_form"] = spatial_cov_form
        context_dict["variable_formset_forms"] = self.get_variable_formset().forms
        context = Context(context_dict)
        rendered_html = template.render(context)
        return rendered_html

    def get_update_netcdf_file_html_form(self):
        form_action = "/hsapi/_internal/{}/update-netcdf-file/".format(
            self.logical_file.id
        )
        style = "display:none;"
        self.refresh_from_db()
        if self.is_update_file:
            style = "margin-bottom:15px"
        root_div = html_tags.div(id="div-netcdf-file-update", cls="row", style=style)

        with root_div:
            with html_tags.div(cls="col-sm-12"):
                with html_tags.div(
                    cls="alert alert-warning alert-dismissible", role="alert"
                ):
                    html_tags.div(
                        "NetCDF file needs to be synced with metadata changes.",
                        cls="space-bottom",
                    )
                    html_tags._input(
                        id="metadata-dirty", type="hidden", value=self.is_update_file
                    )
                    with html_tags.form(
                        action=form_action, method="post", id="update-netcdf-file"
                    ):
                        html_tags.button(
                            "Update NetCDF File",
                            type="button",
                            cls="btn btn-primary",
                            id="id-update-netcdf-file",
                        )

        return root_div

    def get_original_coverage_form(self):
        return OriginalCoverage.get_html_form(
            resource=None, element=self.originalCoverage, file_type=True
        )

    def get_variable_formset(self):
        from ..forms import VariableForm

        VariableFormSetEdit = formset_factory(
            wraps(VariableForm)(partial(VariableForm, allow_edit=True)),
            formset=BaseFormSet,
            extra=0,
        )
        variable_formset = VariableFormSetEdit(
            initial=list(self.variables.all().values()), prefix="Variable"
        )

        for frm in variable_formset.forms:
            if len(frm.initial) > 0:
                frm.action = (
                    "/hsapi/_internal/%s/%s/variable/%s/update-file-metadata/"
                    % ("NetCDFLogicalFile", self.logical_file.id, frm.initial["id"])
                )
                frm.number = frm.initial["id"]

        return variable_formset

    def get_ncdump_html(self):
        """
        Generates html code to display the contents of the ncdump text file. The generated html
        is used for netcdf file type metadata view and edit modes.
        :return:
        """

        nc_dump_div = html_tags.div()
        nc_dump_res_file = None
        for f in self.logical_file.files.all():
            if f.extension == ".txt":
                nc_dump_res_file = f
                break
        if nc_dump_res_file is not None:
            nc_dump_div = html_tags.div(style="clear: both", cls="content-block")
            with nc_dump_div:
                html_tags.legend("NetCDF Header Information")
                html_tags.p(nc_dump_res_file.full_path[33:])
                header_info = nc_dump_res_file.resource_file.read()
                header_info = header_info.decode("utf-8")
                html_tags.textarea(
                    header_info,
                    readonly="",
                    rows="15",
                    cls="input-xlarge",
                    style="min-width: 100%; resize: vertical;",
                )

        return nc_dump_div

    @classmethod
    def validate_element_data(cls, request, element_name):
        """overriding the base class method"""
        from ..forms import VariableValidationForm, OriginalCoverageForm

        if element_name.lower() not in [
            el_name.lower() for el_name in cls.get_supported_element_names()
        ]:
            err_msg = "{} is nor a supported metadata element for NetCDF file type"
            err_msg = err_msg.format(element_name)
            return {"is_valid": False, "element_data_dict": None, "errors": err_msg}
        element_name = element_name.lower()
        if element_name == "variable":
            form_data = {}
            for field_name in VariableValidationForm().fields:
                try:
                    # when the request comes from the UI, the variable attributes have a prefix of
                    # '-'
                    matching_key = [
                        key for key in request.POST if "-" + field_name in key
                    ][0]
                except IndexError:
                    if field_name in request.POST:
                        matching_key = field_name
                    else:
                        continue
                form_data[field_name] = request.POST[matching_key]
            element_form = VariableValidationForm(form_data)
        elif element_name == "originalcoverage":
            element_form = OriginalCoverageForm(data=request.POST)
        elif element_name == "coverage" and "start" not in request.POST:
            element_form = CoverageSpatialForm(data=request.POST)
        else:
            # here we are assuming temporal coverage
            element_form = CoverageTemporalForm(data=request.POST)

        if element_form.is_valid():
            return {"is_valid": True, "element_data_dict": element_form.cleaned_data}
        else:
            return {
                "is_valid": False,
                "element_data_dict": None,
                "errors": element_form.errors,
            }


class NetCDFLogicalFile(AbstractLogicalFile):
    metadata = models.OneToOneField(
        NetCDFFileMetaData, on_delete=models.CASCADE, related_name="logical_file"
    )
    data_type = "Multidimensional"

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        """only .nc file can be set to this logical file group"""
        return [".nc"]

    @classmethod
    def get_main_file_type(cls):
        """The main file type for this aggregation"""
        return ".nc"

    @classmethod
    def get_allowed_storage_file_types(cls):
        """file types allowed in this logical file group are: .nc and .txt"""
        return [".nc", ".txt"]

    @staticmethod
    def get_aggregation_display_name():
        return (
            "Multidimensional Content: A multidimensional dataset represented by a NetCDF "
            "file (.nc) and text file giving its NetCDF header content"
        )

    @staticmethod
    def get_aggregation_term_label():
        return "Multidimensional Aggregation"

    @staticmethod
    def get_aggregation_type_name():
        return "MultidimensionalAggregation"

    # used in discovery faceting to aggregate native and composite content types
    @staticmethod
    def get_discovery_content_type():
        """Return a human-readable content type for discovery.
        This must agree between Composite Types and native types.
        """
        return "Multidimensional (NetCDF)"

    @classmethod
    def create(cls, resource):
        """this custom method MUST be used to create an instance of this class"""
        netcdf_metadata = NetCDFFileMetaData.objects.create(
            keywords=[], extra_metadata={}
        )
        # Note we are not creating the logical file record in DB at this point
        # the caller must save this to DB
        return cls(metadata=netcdf_metadata, resource=resource)

    @property
    def supports_resource_file_move(self):
        """resource files that are part of this logical file can't be moved"""
        return False

    @property
    def supports_resource_file_add(self):
        """doesn't allow a resource file to be added"""
        return False

    @property
    def supports_resource_file_rename(self):
        """resource files that are part of this logical file can't be renamed"""
        return False

    @property
    def supports_delete_folder_on_zip(self):
        """does not allow the original folder to be deleted upon zipping of that folder"""
        return False

    def update_netcdf_file(self, user):
        """
        writes metadata to the netcdf file associated with this instance of the logical file
        :return:
        """

        log = logging.getLogger()

        nc_res_file = ""
        txt_res_file = ""
        for f in self.files.all():
            if f.extension == ".nc":
                nc_res_file = f
                break

        for f in self.files.all():
            if f.extension == ".txt":
                txt_res_file = f
                break
        if not nc_res_file:
            msg = "No netcdf file exists for this logical file."
            log.exception(msg)
            raise ValidationError(msg)

        netcdf_file_update(self, nc_res_file, txt_res_file, user)

    @classmethod
    def check_files_for_aggregation_type(cls, files):
        """Checks if the specified files can be used to set this aggregation type
        :param  files: a list of ResourceFile objects

        :return If the files meet the requirements of this aggregation type, then returns this
        aggregation class name, otherwise empty string.
        """
        if len(files) != 1:
            # no files or more than 1 file
            return ""

        if files[0].extension not in cls.get_allowed_uploaded_file_types():
            return ""

        return cls.__name__

    @classmethod
    def set_file_type(cls, resource, user, file_id=None, folder_path=""):
        """Creates a NetCDFLogicalFile (aggregation) from a netcdf file (.nc) resource file"""

        log = logging.getLogger()
        with FileTypeContext(
            aggr_cls=cls,
            user=user,
            resource=resource,
            file_id=file_id,
            folder_path=folder_path,
            post_aggr_signal=post_add_netcdf_aggregation,
            is_temp_file=True,
        ) as ft_ctx:

            # base file name (no path included)
            res_file = ft_ctx.res_file
            file_name = res_file.file_name
            # file name without the extension - needed for naming the new aggregation folder
            nc_file_name = file_name[: -len(res_file.extension)]

            resource_metadata = []
            file_type_metadata = []

            # file validation and metadata extraction
            temp_file = ft_ctx.temp_file
            nc_dataset = nc_utils.get_nc_dataset(temp_file)
            if isinstance(nc_dataset, netCDF4.Dataset):
                msg = "NetCDF aggregation. Error when creating aggregation. Error:{}"
                # extract the metadata from netcdf file
                res_dublin_core_meta, res_type_specific_meta = nc_meta.get_nc_meta_dict(
                    temp_file
                )
                # populate resource_metadata and file_type_metadata lists with extracted metadata
                add_metadata_to_list(
                    resource_metadata,
                    res_dublin_core_meta,
                    res_type_specific_meta,
                    file_type_metadata,
                    resource,
                )

                # create the ncdump text file
                dump_file_name = nc_file_name + "_header_info.txt"
                folder_path = res_file.file_folder
                for file in resource.files.filter(file_folder=folder_path):
                    # look for and delete an existing header_file before creating it below.
                    fname = os.path.basename(file.resource_file.name)
                    if fname == dump_file_name:
                        file.delete()
                        break
                else:
                    # check if the dump file in S3 and then delete it
                    istorage = resource.get_s3_storage()
                    if folder_path:
                        dump_file_path = os.path.join(
                            resource.file_path, folder_path, dump_file_name
                        )
                    else:
                        dump_file_path = os.path.join(
                            resource.file_path, dump_file_name
                        )
                    if istorage.exists(dump_file_path):
                        istorage.delete(dump_file_path)

                dump_file = create_header_info_txt_file(temp_file, nc_file_name)
                dataset_title = res_dublin_core_meta.get("title", nc_file_name)
                logical_file = None
                with transaction.atomic():
                    try:
                        # create a netcdf logical file object
                        logical_file = cls.create_aggregation(
                            dataset_name=dataset_title,
                            resource=resource,
                            res_files=[res_file],
                            new_files_to_upload=[dump_file],
                            folder_path=folder_path,
                        )

                        log.info(
                            "NetCDF aggregation creation - a new file was added to the "
                            "resource."
                        )

                        # use the extracted metadata to populate resource metadata
                        for element in resource_metadata:
                            # here k is the name of the element
                            # v is a dict of all element attributes/field names and field values
                            k, v = list(element.items())[0]
                            if k == "title":
                                # update title element
                                title_element = resource.metadata.title
                                resource.metadata.update_element(
                                    "title", title_element.id, **v
                                )
                            else:
                                resource.metadata.create_element(k, **v)

                        log.info(
                            "NetCDF Aggregation creation - Resource metadata was saved to DB"
                        )

                        # use the extracted metadata to populate file metadata
                        for element in file_type_metadata:
                            # here k is the name of the element
                            # v is a dict of all element attributes/field names and field values
                            k, v = list(element.items())[0]
                            if k == "subject":
                                logical_file.metadata.keywords = v
                                logical_file.metadata.save()
                                # update resource level keywords
                                resource_keywords = [
                                    subject.value.lower()
                                    for subject in resource.metadata.subjects.all()
                                ]
                                for kw in logical_file.metadata.keywords:
                                    if kw.lower() not in resource_keywords:
                                        resource.metadata.create_element(
                                            "subject", value=kw
                                        )
                            else:
                                logical_file.metadata.create_element(k, **v)

                        log.info(
                            "NetCDF aggregation - metadata was saved in aggregation"
                        )
                        ft_ctx.logical_file = logical_file
                    except Exception as ex:
                        if logical_file is not None:
                            logical_file.remove_aggregation()
                        msg = msg.format(str(ex))
                        log.exception(msg)
                        raise ValidationError(msg)

                return logical_file
            else:
                err_msg = (
                    "Not a valid NetCDF file. NetCDF aggregation validation failed."
                )
                log.error(err_msg)
                raise ValidationError(err_msg)

    def remove_aggregation(self):
        """Deletes the aggregation object (logical file) *self* and the associated metadata
        object. If the aggregation contains a system generated txt file that resource file also will be
        deleted."""

        # need to delete the system generated ncdump txt file
        txt_file = None
        for res_file in self.files.all():
            if res_file.file_name.lower().endswith(".txt"):
                txt_file = res_file
                break
        super(NetCDFLogicalFile, self).remove_aggregation()
        if txt_file is not None:
            txt_file.delete()

    @classmethod
    def get_primary_resource_file(cls, resource_files):
        """Gets a resource file that has extension .nc from the list of files *resource_files*"""

        res_files = [f for f in resource_files if f.extension.lower() == ".nc"]
        return res_files[0] if res_files else None

    @property
    def metadata_json_file_path(self):
        """Returns the storage path of the aggregation metadata json file"""

        nc_file = self.get_primary_resource_file(self.files.all())
        meta_file_path = nc_file.storage_path + AggregationMetaFilePath.METADATA_JSON_FILE_ENDSWITH
        return meta_file_path

    def save_metadata_json_file(self):
        """Creates aggregation metadata json file and saves it to S3 """

        from hs_file_types.utils import save_metadata_json_file as utils_save_metadata_json_file

        metadata_json = self.metadata.to_json()
        to_file_name = self.metadata_json_file_path
        utils_save_metadata_json_file(self.resource.get_s3_storage(), metadata_json, to_file_name)


def add_metadata_to_list(
    res_meta_list,
    extracted_core_meta,
    extracted_specific_meta,
    file_meta_list=None,
    resource=None,
):
    """
    Helper function to populate metadata lists (*res_meta_list* and *file_meta_list*) with
    extracted metadata from the NetCDF file. These metadata lists are then used for creating
    metadata element objects by the caller.
    :param res_meta_list: a list to store data to create metadata elements at the resource level
    :param extracted_core_meta: a dict of extracted dublin core metadata
    :param extracted_specific_meta: a dict of extracted metadata that is NetCDF specific
    :param file_meta_list: a list to store data to create metadata elements at the file type level
    (must be None when this helper function is used for NetCDF resource and must not be None
    when used for NetCDF file type
    :param resource: an instance of BaseResource (must be None when this helper function is used
    for NteCDF resource and must not be None when used for NetCDF file type)
    :return:
    """

    # add title
    if resource is not None and file_meta_list is not None:
        # file type
        if resource.metadata.title.value.lower() == "untitled resource":
            add_title_metadata(res_meta_list, extracted_core_meta)
    else:
        # resource type
        add_title_metadata(res_meta_list, extracted_core_meta)

    # add abstract (Description element)
    if resource is not None and file_meta_list is not None:
        # file type
        if resource.metadata.description is None:
            add_abstract_metadata(res_meta_list, extracted_core_meta)
    else:
        # resource type
        add_abstract_metadata(res_meta_list, extracted_core_meta)

    # add keywords
    if file_meta_list is not None:
        # file type
        add_keywords_metadata(file_meta_list, extracted_core_meta)
    else:
        # resource type
        add_keywords_metadata(res_meta_list, extracted_core_meta, file_type=False)

    # add creators:
    if resource is not None:
        # file type
        add_creators_metadata(
            res_meta_list, extracted_core_meta, resource.metadata.creators.all()
        )
    else:
        # resource type
        add_creators_metadata(
            res_meta_list, extracted_core_meta, Creator.objects.none()
        )

    # add contributors:
    if resource is not None:
        # file type
        add_contributors_metadata(
            res_meta_list, extracted_core_meta, resource.metadata.contributors.all()
        )
    else:
        # resource type
        add_contributors_metadata(
            res_meta_list, extracted_core_meta, Contributor.objects.none()
        )

    # add relation of type 'source' (applies only to NetCDF resource type)
    if extracted_core_meta.get("source") and file_meta_list is None:
        relation = {
            "relation": {"type": "source", "value": extracted_core_meta["source"]}
        }
        res_meta_list.append(relation)

    # add relation of type 'references' (applies only to NetCDF resource type)
    if extracted_core_meta.get("references") and file_meta_list is None:
        relation = {
            "relation": {
                "type": "references",
                "value": extracted_core_meta["references"],
            }
        }
        res_meta_list.append(relation)

    # add rights (applies only to NetCDF resource type)
    if extracted_core_meta.get("rights") and file_meta_list is None:
        raw_info = extracted_core_meta.get("rights")
        b = re.search("(?P<url>https?://[^\s]+)", raw_info) # noqa
        url = b.group("url") if b else ""
        statement = raw_info.replace(url, "") if url else raw_info
        rights = {"rights": {"statement": statement, "url": url}}
        res_meta_list.append(rights)

    # add coverage - period
    if file_meta_list is not None:
        # file type
        add_temporal_coverage_metadata(file_meta_list, extracted_core_meta)
    else:
        # resource type
        add_temporal_coverage_metadata(res_meta_list, extracted_core_meta)

    # add coverage - box
    if file_meta_list is not None:
        # file type
        add_spatial_coverage_metadata(file_meta_list, extracted_core_meta)
    else:
        # resource type
        add_spatial_coverage_metadata(res_meta_list, extracted_core_meta)

    # add variables
    if file_meta_list is not None:
        # file type
        add_variable_metadata(file_meta_list, extracted_specific_meta)
    else:
        # resource type
        add_variable_metadata(res_meta_list, extracted_specific_meta)

    # add original spatial coverage
    if file_meta_list is not None:
        # file type
        add_original_coverage_metadata(file_meta_list, extracted_core_meta)
    else:
        # resource type
        add_original_coverage_metadata(res_meta_list, extracted_core_meta)


def add_original_coverage_metadata(metadata_list, extracted_metadata):
    """
    Adds data for the original coverage element to the *metadata_list*
    :param metadata_list: list to  which original coverage data needs to be added
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :return:
    """

    ori_cov = {}
    if extracted_metadata.get("original-box"):
        coverage_data = extracted_metadata["original-box"]
        projection_string_type = ""
        projection_string_text = ""
        datum = ""
        if extracted_metadata.get("projection-info"):
            projection_string_type = extracted_metadata["projection-info"]["type"]
            projection_string_text = extracted_metadata["projection-info"]["text"]
            datum = extracted_metadata["projection-info"]["datum"]

        ori_cov = {
            "originalcoverage": {
                "value": coverage_data,
                "projection_string_type": projection_string_type,
                "projection_string_text": projection_string_text,
                "datum": datum,
            }
        }
    if ori_cov:
        metadata_list.append(ori_cov)


def add_creators_metadata(metadata_list, extracted_metadata, existing_creators):
    """
    Adds data for creator(s) to the *metadata_list*
    :param metadata_list: list to  which creator(s) data needs to be added
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :param existing_creators: a QuerySet object for existing creators
    :return:
    """
    if extracted_metadata.get("creator_name"):
        name = extracted_metadata["creator_name"]
        # add creator only if there is no creator already with the same name
        if not existing_creators.filter(name=name).exists():
            email = extracted_metadata.get("creator_email", "")
            url = extracted_metadata.get("creator_url", "")
            creator = {"creator": {"name": name, "email": email, "homepage": url}}
            metadata_list.append(creator)


def add_contributors_metadata(metadata_list, extracted_metadata, existing_contributors):
    """
    Adds data for contributor(s) to the *metadata_list*
    :param metadata_list: list to  which contributor(s) data needs to be added
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :param existing_contributors: a QuerySet object for existing contributors
    :return:
    """
    if extracted_metadata.get("contributor_name"):
        name_list = extracted_metadata["contributor_name"].split(",")
        for name in name_list:
            # add contributor only if there is no contributor already with the
            # same name
            if not existing_contributors.filter(name=name).exists():
                contributor = {"contributor": {"name": name}}
                metadata_list.append(contributor)


def add_title_metadata(metadata_list, extracted_metadata):
    """
    Adds data for the title element to the *metadata_list*
    :param metadata_list: list to  which title data needs to be added
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :return:
    """
    if extracted_metadata.get("title"):
        res_title = {"title": {"value": extracted_metadata["title"]}}
        metadata_list.append(res_title)


def add_abstract_metadata(metadata_list, extracted_metadata):
    """
    Adds data for the abstract (Description) element to the *metadata_list*
    :param metadata_list: list to  which abstract data needs to be added
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :return:
    """

    if extracted_metadata.get("description"):
        description = {"description": {"abstract": extracted_metadata["description"]}}
        metadata_list.append(description)


def add_variable_metadata(metadata_list, extracted_metadata):
    """
    Adds variable(s) related data to the *metadata_list*
    :param metadata_list: list to  which variable data needs to be added
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :return:
    """
    for var_name, var_meta in list(extracted_metadata.items()):
        meta_info = {}
        for element, value in list(var_meta.items()):
            if value != "":
                meta_info[element] = value
        metadata_list.append({"variable": meta_info})


def add_spatial_coverage_metadata(metadata_list, extracted_metadata):
    """
    Adds data for one spatial coverage metadata element to the *metadata_list**
    :param metadata_list: list to which spatial coverage data needs to be added
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :return:
    """
    if extracted_metadata.get("box"):
        box = {"coverage": {"type": "box", "value": extracted_metadata["box"]}}
        metadata_list.append(box)


def add_temporal_coverage_metadata(metadata_list, extracted_metadata):
    """
    Adds data for one temporal metadata element to the *metadata_list*
    :param metadata_list: list to which temporal coverage data needs to be added
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :return:
    """
    if extracted_metadata.get("period"):
        period = {"coverage": {"type": "period", "value": extracted_metadata["period"]}}
        metadata_list.append(period)


def add_keywords_metadata(metadata_list, extracted_metadata, file_type=True):
    """
    Adds data for subject/keywords element to the *metadata_list*
    :param metadata_list: list to which keyword data needs to be added
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :param file_type: If True then this metadata extraction is for netCDF file type, otherwise
    metadata extraction is for NetCDF resource
    :return:
    """
    if extracted_metadata.get("subject"):
        keywords = extracted_metadata["subject"].split(",")
        if file_type:
            metadata_list.append({"subject": keywords})
        else:
            for keyword in keywords:
                metadata_list.append({"subject": {"value": keyword}})


def create_header_info_txt_file(nc_temp_file, nc_file_name):
    """
    Creates the header text file using the *nc_temp_file*
    :param nc_temp_file: the netcdf file copied from S3 to django
    for metadata extraction
    :return:
    """

    if nc_dump.get_nc_dump_string_by_ncdump(nc_temp_file):
        dump_str = nc_dump.get_nc_dump_string_by_ncdump(nc_temp_file)
    else:
        dump_str = nc_dump.get_nc_dump_string(nc_temp_file)

    # file name without the extension
    temp_dir = os.path.dirname(nc_temp_file)
    dump_file_name = nc_file_name + "_header_info.txt"
    dump_file = os.path.join(temp_dir, dump_file_name)
    if dump_str:
        # refine dump_str first line
        first_line = list("netcdf {0} ".format(nc_file_name))
        first_line_index = dump_str.index("{")
        dump_str_list = first_line + list(dump_str)[first_line_index:]
        dump_str = "".join(dump_str_list)
        with open(dump_file, "w") as dump_file_obj:
            dump_file_obj.write(dump_str)
            dump_file_obj.close()
    else:
        with open(dump_file, "w") as dump_file_obj:
            dump_file_obj.write("")
            dump_file_obj.close()

    return dump_file


def netcdf_file_update(instance, nc_res_file, txt_res_file, user):
    log = logging.getLogger()
    # check the instance type
    file_type = isinstance(instance, NetCDFLogicalFile)

    # get the file from S3 to temp dir
    resource = nc_res_file.resource
    temp_nc_file = utils.get_file_from_s3(
        resource=resource, file_path=nc_res_file.storage_path
    )
    nc_dataset = netCDF4.Dataset(temp_nc_file, "a")

    try:
        # update title
        title = instance.dataset_name if file_type else instance.metadata.title.value

        if title.lower() != "untitled resource":
            if hasattr(nc_dataset, "title"):
                delattr(nc_dataset, "title")
            nc_dataset.title = title

        # update keywords
        keywords = (
            instance.metadata.keywords
            if file_type
            else [item.value for item in instance.metadata.subjects.all()]
        )

        if hasattr(nc_dataset, "keywords"):
            delattr(nc_dataset, "keywords")

        if keywords:
            nc_dataset.keywords = ", ".join(keywords)

        # update key/value metadata
        extra_metadata_dict = (
            instance.metadata.extra_metadata if file_type else instance.extra_metadata
        )

        if hasattr(nc_dataset, "hs_extra_metadata"):
            delattr(nc_dataset, "hs_extra_metadata")

        if extra_metadata_dict:
            extra_metadata = []
            for k, v in list(extra_metadata_dict.items()):
                extra_metadata.append("{}:{}".format(k, v))
            nc_dataset.hs_extra_metadata = ", ".join(extra_metadata)

        # update temporal coverage
        temporal_coverage = (
            instance.metadata.temporal_coverage
            if file_type
            else instance.metadata.coverages.all().filter(type="period").first()
        )

        for attr_name in ["time_coverage_start", "time_coverage_end"]:
            if hasattr(nc_dataset, attr_name):
                delattr(nc_dataset, attr_name)

        if temporal_coverage:
            nc_dataset.time_coverage_start = temporal_coverage.value["start"]
            nc_dataset.time_coverage_end = temporal_coverage.value["end"]

        # update variables
        if instance.metadata.variables.all():
            dataset_variables = nc_dataset.variables
            for variable in instance.metadata.variables.all():
                if variable.name in list(dataset_variables.keys()):
                    dataset_variable = dataset_variables[variable.name]

                    # update units
                    if hasattr(dataset_variable, "units"):
                        delattr(dataset_variable, "units")
                    if variable.unit != "Unknown":
                        dataset_variable.setncattr("units", variable.unit)

                    # update long_name
                    if hasattr(dataset_variable, "long_name"):
                        delattr(dataset_variable, "long_name")
                    if variable.descriptive_name:
                        dataset_variable.setncattr(
                            "long_name", variable.descriptive_name
                        )

                    # update method
                    if hasattr(dataset_variable, "comment"):
                        delattr(dataset_variable, "comment")
                    if variable.method:
                        dataset_variable.setncattr("comment", variable.method)

                    # update missing value
                    if variable.missing_value:
                        if hasattr(dataset_variable, "missing_value"):
                            missing_value = dataset_variable.missing_value
                            delattr(dataset_variable, "missing_value")
                        else:
                            missing_value = ""
                        try:
                            dt = np.dtype(dataset_variable.datatype.name)
                            missing_value = np.fromstring(
                                variable.missing_value + " ", dtype=dt.type, sep=" "
                            )
                        except: # noqa
                            pass

                        if missing_value:
                            dataset_variable.setncattr("missing_value", missing_value)

        # Update metadata element that only apply to netCDF resource
        if not file_type:

            # update summary
            if hasattr(nc_dataset, "summary"):
                delattr(nc_dataset, "summary")
            if instance.metadata.description:
                nc_dataset.summary = instance.metadata.description.abstract

            # update contributor
            if hasattr(nc_dataset, "contributor_name"):
                delattr(nc_dataset, "contributor_name")

            contributor_list = instance.metadata.contributors.all()
            if contributor_list:
                res_contri_name = []
                for contributor in contributor_list:
                    res_contri_name.append(contributor.name)

                nc_dataset.contributor_name = ", ".join(res_contri_name)

            # update creator
            for attr_name in ["creator_name", "creator_email", "creator_url"]:
                if hasattr(nc_dataset, attr_name):
                    delattr(nc_dataset, attr_name)

            creator = instance.metadata.creators.all().filter(order=1).first()
            if creator:
                nc_dataset.creator_name = (
                    creator.name if creator.name else creator.organization
                )

                if creator.email:
                    nc_dataset.creator_email = creator.email
                if creator.relative_uri or creator.homepage:
                    nc_dataset.creator_url = (
                        creator.homepage
                        if creator.homepage
                        else "https://www.hydroshare.org" + creator.relative_uri
                    )

            # update license
            if hasattr(nc_dataset, "license"):
                delattr(nc_dataset, "license")
            if instance.metadata.rights:
                nc_dataset.license = "{0} {1}".format(
                    instance.metadata.rights.statement, instance.metadata.rights.url
                )

            # update reference
            if hasattr(nc_dataset, "references"):
                delattr(nc_dataset, "references")

            reference_list = instance.metadata.relations.all().filter(
                type=RelationTypes.references
            )
            if reference_list:
                res_meta_ref = []
                for reference in reference_list:
                    res_meta_ref.append(reference.value)
                nc_dataset.references = " \n".join(res_meta_ref)

            # update source
            if hasattr(nc_dataset, "source"):
                delattr(nc_dataset, "source")

            source_list = instance.metadata.relations.filter(
                type=RelationTypes.source
            ).all()
            if source_list:
                res_meta_source = []
                for source in source_list:
                    res_meta_source.append(source.value)
                nc_dataset.source = " \n".join(res_meta_source)

        # close nc dataset
        nc_dataset.close()

    except Exception as ex:
        log.exception(str(ex))
        if os.path.exists(temp_nc_file):
            shutil.rmtree(os.path.dirname(temp_nc_file))
        raise ex

    # create the ncdump text file
    nc_file_name = os.path.basename(temp_nc_file).split(".")[0]
    temp_text_file = create_header_info_txt_file(temp_nc_file, nc_file_name)

    # push the updated nc file and the txt file to S3
    utils.replace_resource_file_on_s3(temp_nc_file, nc_res_file, user)
    utils.replace_resource_file_on_s3(temp_text_file, txt_res_file, user)

    metadata = instance.metadata
    metadata.is_update_file = False
    metadata.save()

    # cleanup the temp dir
    if os.path.exists(temp_nc_file):
        shutil.rmtree(os.path.dirname(temp_nc_file))
