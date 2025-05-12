import json
import logging
import os
import parser
import shutil
import subprocess
import defusedxml.ElementTree as ET
import zipfile
from functools import partial, wraps

from osgeo import gdal
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.forms.models import formset_factory
from django.template import Template, Context
from dominate import tags as html_tags
from osgeo.gdalconst import GA_ReadOnly
from rdflib import BNode, RDF, Literal

from hs_core.forms import CoverageTemporalForm, CoverageSpatialForm
from hs_core.hs_rdf import HSTERMS, rdf_terms
from hs_core.hydroshare import utils
from hs_core.models import ResourceFile, AbstractMetaDataElement
from hs_core.signals import post_add_raster_aggregation
from hs_file_types import raster_meta_extract
from .base import AbstractFileMetaData, AbstractLogicalFile, FileTypeContext


# additional metadata for raster aggregation type to store the original box type coverage
# since the core metadata coverage stores the converted WGS84 geographic coordinate
# system projection coverage, see issue #210 on github for details
@rdf_terms(HSTERMS.spatialReference)
class OriginalCoverageRaster(AbstractMetaDataElement):
    term = 'OriginalCoverage'

    """
    _value field stores a json string as shown below for box coverage type
     _value = "{'northlimit':northenmost coordinate value,
                'eastlimit':easternmost coordinate value,
                'southlimit':southernmost coordinate value,
                'westlimit':westernmost coordinate value,
                'units:units applying to 4 limits (north, east, south & east),
                'projection': name of the projection (optional),
                'projection_string: OGC WKT string of the projection (optional),
                'datum: projection datum name (optional),
                }"
    """
    _value = models.CharField(max_length=10000, null=True)

    class Meta:
        # OriginalCoverage element is not repeatable
        unique_together = ("content_type", "object_id")

    @property
    def value(self):
        return json.loads(self._value)

    @classmethod
    def create(cls, **kwargs):
        """
        The '_value' subelement needs special processing. (Check if the 'value' includes the
        required info and convert 'value' dict as Json string to be the '_value' subelement value.)
        The base class create() can't do it.

        :param kwargs: the 'value' in kwargs should be a dictionary

        """

        value_arg_dict = None
        if 'value' in kwargs:
            value_arg_dict = kwargs['value']
        elif '_value' in kwargs:
            value_arg_dict = json.loads(kwargs['_value'])

        if value_arg_dict:
            # check that all the required sub-elements exist
            for value_item in ['units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit']:
                if value_item not in value_arg_dict:
                    raise ValidationError("For coverage of type 'box' values for {} is missing. {}"
                                          .format(value_item, value_arg_dict))

            value_dict = {k: v for k, v in list(value_arg_dict.items())
                          if k in ('units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit',
                                   'projection', 'projection_string', 'datum')}

            value_json = json.dumps(value_dict)
            if 'value' in kwargs:
                del kwargs['value']
            kwargs['_value'] = value_json
            return super(OriginalCoverageRaster, cls).create(**kwargs)
        else:
            raise ValidationError('Coverage value is missing.')

    @classmethod
    def update(cls, element_id, **kwargs):
        """
        The '_value' subelement needs special processing.
        (Convert the 'value' dict as Json string to be the "_value" subelement value.)
        The base class update() can't do it.

        :param kwargs: the 'value' in kwargs should be a dictionary
        """

        cov = OriginalCoverageRaster.objects.get(id=element_id)

        if 'value' in kwargs:
            value_dict = cov.value

            for item_name in ('units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit',
                              'projection', 'projection_string', 'datum'):
                if item_name in kwargs['value']:
                    value_dict[item_name] = kwargs['value'][item_name]

            value_json = json.dumps(value_dict)
            del kwargs['value']
            kwargs['_value'] = value_json
            super(OriginalCoverageRaster, cls).update(element_id, **kwargs)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Coverage element can't be deleted.")

    hsterms = ['spatialReference', 'box', ]
    rdf = ['value']

    def rdf_triples(self, subject, graph):
        original_coverage = BNode()
        graph.add((subject, self.get_class_term(), original_coverage))
        graph.add((original_coverage, RDF.type, HSTERMS.box))
        value_string = "; ".join(["=".join([key, str(val)]) for key, val in self.value.items()])
        graph.add((original_coverage, RDF.value, Literal(value_string)))

    @classmethod
    def ingest_rdf(cls, graph, subject, content_object):
        for _, _, cov in graph.triples((subject, cls.get_class_term(), None)):
            value_str = graph.value(subject=cov, predicate=RDF.value)
            if value_str:
                value_dict = {}
                for key_value in value_str.split(";"):
                    key_value = key_value.strip()
                    k, v = key_value.split("=")
                    if k in ['start', 'end']:
                        v = parser.parse(v).strftime("%Y/%m/%d")
                    value_dict[k] = v
                OriginalCoverageRaster.create(value=value_dict, content_object=content_object)

    @classmethod
    def get_html_form(cls, resource, element=None, allow_edit=True, file_type=False):
        """Generates html form code for an instance of this metadata element so
        that this element can be edited"""

        from ..forms import OriginalCoverageSpatialForm

        ori_coverage_data_dict = {}
        if element is not None:
            ori_coverage_data_dict['projection'] = element.value.get('projection', None)
            ori_coverage_data_dict['datum'] = element.value.get('datum', None)
            ori_coverage_data_dict['projection_string'] = element.value.get('projection_string',
                                                                            None)
            ori_coverage_data_dict['units'] = element.value['units']
            ori_coverage_data_dict['northlimit'] = element.value['northlimit']
            ori_coverage_data_dict['eastlimit'] = element.value['eastlimit']
            ori_coverage_data_dict['southlimit'] = element.value['southlimit']
            ori_coverage_data_dict['westlimit'] = element.value['westlimit']

        originalcov_form = OriginalCoverageSpatialForm(
            initial=ori_coverage_data_dict, allow_edit=allow_edit,
            res_short_id=resource.short_id if resource else None,
            element_id=element.id if element else None, file_type=file_type)

        return originalcov_form

    def get_html(self, pretty=True):
        """Generates html code for displaying data for this metadata element"""

        root_div = html_tags.div(cls="content-block")

        def get_th(heading_name):
            return html_tags.th(heading_name, cls="text-muted")

        with root_div:
            html_tags.legend('Spatial Reference')
            html_tags.div('Coordinate Reference System', cls='text-muted has-space-top')
            html_tags.div(self.value.get('projection', ''))
            html_tags.div('Coordinate Reference System Unit', cls='text-muted has-space-top')
            html_tags.div(self.value['units'])
            html_tags.div('Datum', cls='text-muted has-space-top')
            html_tags.div(self.value.get('datum', ''))
            html_tags.div('Coordinate String', cls='text-muted has-space-top')
            html_tags.div(self.value.get('projection_string', ''), style="word-break: break-all;")
            html_tags.h4('Extent', cls='space-top')
            with html_tags.table(cls='custom-table'):
                with html_tags.tbody():
                    with html_tags.tr():
                        get_th('North')
                        html_tags.td(self.value['northlimit'])
                    with html_tags.tr():
                        get_th('West')
                        html_tags.td(self.value['westlimit'])
                    with html_tags.tr():
                        get_th('South')
                        html_tags.td(self.value['southlimit'])
                    with html_tags.tr():
                        get_th('East')
                        html_tags.td(self.value['eastlimit'])

        return root_div.render(pretty=pretty)


class BandInformation(AbstractMetaDataElement):
    term = 'BandInformation'
    # required fields
    # has to call the field name rather than bandName, which seems to be enforced by
    # the AbstractMetaDataElement;
    # otherwise, got an error indicating required "name" field does not exist
    name = models.CharField(max_length=500, null=True)
    variableName = models.TextField(max_length=100, null=True)
    variableUnit = models.CharField(max_length=50, null=True)

    # optional fields
    method = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    noDataValue = models.TextField(null=True, blank=True)
    maximumValue = models.TextField(null=True, blank=True)
    minimumValue = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.name

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("BandInformation element of the raster resource cannot be deleted.")

    def get_html(self, pretty=True):
        """Generates html code for displaying data for this metadata element"""

        root_div = html_tags.div()

        def get_th(heading_name):
            return html_tags.th(heading_name, cls="text-muted")

        with root_div:
            with html_tags.div(cls="custom-well"):
                html_tags.strong(self.name)
                with html_tags.table(cls='custom-table'):
                    with html_tags.tbody():
                        with html_tags.tr():
                            get_th('Variable Name')
                            html_tags.td(self.variableName)
                        with html_tags.tr():
                            get_th('Variable Unit')
                            html_tags.td(self.variableUnit)
                        if self.noDataValue:
                            with html_tags.tr():
                                get_th('No Data Value')
                                html_tags.td(self.noDataValue)
                        if self.maximumValue:
                            with html_tags.tr():
                                get_th('Maximum Value')
                                html_tags.td(self.maximumValue)
                        if self.minimumValue:
                            with html_tags.tr():
                                get_th('Minimum Value')
                                html_tags.td(self.minimumValue)
                        if self.method:
                            with html_tags.tr():
                                get_th('Method')
                                html_tags.td(self.method)
                        if self.comment:
                            with html_tags.tr():
                                get_th('Comment')
                                html_tags.td(self.comment)

        return root_div.render(pretty=pretty)


class CellInformation(AbstractMetaDataElement):
    term = 'CellInformation'
    # required fields
    name = models.CharField(max_length=500, null=True)
    rows = models.IntegerField(null=True)
    columns = models.IntegerField(null=True)
    cellSizeXValue = models.FloatField(null=True)
    cellSizeYValue = models.FloatField(null=True)
    cellDataType = models.CharField(max_length=50, null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        # CellInformation element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("CellInformation element of a raster resource cannot be removed")

    def get_html_form(self, resource):
        """Generates html form code for this metadata element so that this element can be edited"""

        from ..forms import CellInfoForm
        cellinfo_form = CellInfoForm(instance=self,
                                     res_short_id=resource.short_id if resource else None,
                                     element_id=self.id if self else None)
        return cellinfo_form

    def get_html(self, pretty=True):
        """Generates html code for displaying data for this metadata element"""

        root_div = html_tags.div(cls="content-block")

        def get_th(heading_name):
            return html_tags.th(heading_name, cls="text-muted")

        with root_div:
            html_tags.legend('Cell Information')
            with html_tags.table(cls='custom-table'):
                with html_tags.tbody():
                    with html_tags.tr():
                        get_th('Rows')
                        html_tags.td(self.rows)
                    with html_tags.tr():
                        get_th('Columns')
                        html_tags.td(self.columns)
                    with html_tags.tr():
                        get_th('Cell Size X Value')
                        html_tags.td(self.cellSizeXValue)
                    with html_tags.tr():
                        get_th('Cell Size Y Value')
                        html_tags.td(self.cellSizeYValue)
                    with html_tags.tr():
                        get_th('Cell Data Type')
                        html_tags.td(self.cellDataType)

        return root_div.render(pretty=pretty)


class GeoRasterMetaDataMixin(models.Model):
    """This class must be the first class in the multi-inheritance list of classes"""

    # required non-repeatable cell information metadata elements
    _cell_information = GenericRelation(CellInformation)
    _band_information = GenericRelation(BandInformation)
    _ori_coverage = GenericRelation(OriginalCoverageRaster)

    class Meta:
        abstract = True

    @property
    def cellInformation(self):
        return self._cell_information.all().first()

    @property
    def bandInformations(self):
        return self._band_information.all()

    @property
    def originalCoverage(self):
        return self._ori_coverage.all().first()

    def has_all_required_elements(self):
        if not super(GeoRasterMetaDataMixin, self).has_all_required_elements():
            return False
        if not self.cellInformation:
            return False
        if self.bandInformations.count() == 0:
            return False
        if not self.coverages.all().filter(type='box').first():
            return False
        return True

    def get_required_missing_elements(self):
        missing_required_elements = super(GeoRasterMetaDataMixin,
                                          self).get_required_missing_elements()
        if not self.coverages.all().filter(type='box').first():
            missing_required_elements.append('Spatial Coverage')
        if not self.cellInformation:
            missing_required_elements.append('Cell Information')
        if not self.bandInformations:
            missing_required_elements.append('Band Information')

        return missing_required_elements

    def delete_all_elements(self):
        super(GeoRasterMetaDataMixin, self).delete_all_elements()
        if self.cellInformation:
            self.cellInformation.delete()
        if self.originalCoverage:
            self.originalCoverage.delete()
        self.bandInformations.delete()

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(GeoRasterMetaDataMixin, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('CellInformation')
        elements.append('BandInformation')
        elements.append('OriginalCoverageRaster')
        return elements


class GeoRasterFileMetaData(GeoRasterMetaDataMixin, AbstractFileMetaData):
    # the metadata element models used for this file type are from the raster resource type app
    # use the 'model_app_label' attribute with ContentType, do dynamically find the right element
    # model class from element name (string)
    model_app_label = 'hs_file_types'

    @classmethod
    def get_metadata_model_classes(cls):
        metadata_model_classes = super(GeoRasterFileMetaData, cls).get_metadata_model_classes()
        metadata_model_classes['originalcoverageraster'] = OriginalCoverageRaster
        metadata_model_classes['bandinformation'] = BandInformation
        metadata_model_classes['cellinformation'] = CellInformation
        return metadata_model_classes

    def get_metadata_elements(self):
        elements = super(GeoRasterFileMetaData, self).get_metadata_elements()
        elements += [self.cellInformation, self.originalCoverage]
        elements += list(self.bandInformations.all())
        return elements

    def _get_metadata_element_model_type(self, element_model_name):
        if element_model_name.lower() == 'originalcoverage':
            element_model_name = 'originalcoverageraster'
        return super()._get_metadata_element_model_type(element_model_name)

    def to_json(self):
        json_dict = super().to_json()
        json_dict['additionalType'] = self.logical_file.get_aggregation_type_name()
        cellinfo = self.cellInformation
        if cellinfo:
            cellinfo_meta = {}
            if cellinfo.name:
                cellinfo_meta['hsterms:name'] = cellinfo.name
            if cellinfo.rows:
                cellinfo_meta['hsterms:rows'] = cellinfo.rows
            if cellinfo.columns:
                cellinfo_meta['hsterms:columns'] = cellinfo.columns
            if cellinfo.cellSizeXValue:
                cellinfo_meta['hsterms:cellSizeXValue'] = cellinfo.cellSizeXValue
            if cellinfo.cellSizeYValue:
                cellinfo_meta['hsterms:cellSizeYValue'] = cellinfo.cellSizeYValue
            if cellinfo.cellDataType:
                cellinfo_meta['hsterms:cellDataType'] = cellinfo.cellDataType

            if cellinfo_meta:
                json_dict.update({"hsterms:cellInformation": cellinfo_meta})

        bandinfo_meta_list = []
        for bandinfo in self.bandInformations:
            bandinfo_meta = {}
            if bandinfo.name:
                bandinfo_meta['hsterms:name'] = bandinfo.name
            if bandinfo.variableName:
                bandinfo_meta['hsterms:variableName'] = bandinfo.variableName
            if bandinfo.variableUnit:
                bandinfo_meta['hsterms:variableUnit'] = bandinfo.variableUnit
            if bandinfo.noDataValue:
                bandinfo_meta['hsterms:noDataValue'] = bandinfo.noDataValue
            if bandinfo.maximumValue:
                bandinfo_meta['hsterms:maximumValue'] = bandinfo.maximumValue
            if bandinfo.minimumValue:
                bandinfo_meta['hsterms:minimumValue'] = bandinfo.minimumValue
            if bandinfo.method:
                bandinfo_meta['hsterms:method'] = bandinfo.method
            if bandinfo.comment:
                bandinfo_meta['hsterms:comment'] = bandinfo.comment
            if bandinfo_meta:
                bandinfo_meta_list.append(bandinfo_meta)

        if bandinfo_meta_list:
            json_dict.update({"hsterms:bandInformation": bandinfo_meta_list})

        originalCoverage = self.originalCoverage
        if originalCoverage:
            orig_coverage_meta = {
                "hsterms:northLimit": originalCoverage.value["northlimit"],
                "hsterms:eastLimit": originalCoverage.value["eastlimit"],
                "hsterms:southLimit": originalCoverage.value["southlimit"],
                "hsterms:westLimit": originalCoverage.value["westlimit"],
                "hsterms:units": originalCoverage.value["units"],
            }
            if 'projection' in originalCoverage.value and originalCoverage.value['projection']:
                orig_coverage_meta['hsterms:projection'] = originalCoverage.value['projection']
                orig_coverage_meta['hsterms:projectionString'] = originalCoverage.value['projection_string']
                orig_coverage_meta['hsterms:datum'] = originalCoverage.value['datum']
            json_dict.update({"hsterms:originalCoverage": orig_coverage_meta})
        return json_dict

    def get_html(self, **kwargs):
        """overrides the base class function to generate html needed to display metadata
        in view mode"""

        html_string = super(GeoRasterFileMetaData, self).get_html()
        spatial_coverage = self.spatial_coverage
        if spatial_coverage:
            html_string += spatial_coverage.get_html()
        originalCoverage = self.originalCoverage
        if originalCoverage:
            html_string += originalCoverage.get_html()

        html_string += self.cellInformation.get_html()
        temporal_coverage = self.temporal_coverage
        if temporal_coverage:
            html_string += temporal_coverage.get_html()
        band_legend = html_tags.legend("Band Information")
        html_string += band_legend.render()
        for band_info in self.bandInformations:
            html_string += band_info.get_html()

        template = Template(html_string)
        context = Context({})
        return template.render(context)

    def get_html_forms(self, dataset_name_form=True, temporal_coverage=True, **kwargs):
        """overrides the base class function to generate html needed for metadata editing"""

        root_div = html_tags.div("{% load crispy_forms_tags %}")
        with root_div:
            super(GeoRasterFileMetaData, self).get_html_forms()
            with html_tags.div(id="spatial-coverage-filetype"):
                with html_tags.form(id="id-spatial-coverage-file-type",
                                    cls='hs-coordinates-picker', data_coordinates_type="point",
                                    action="{{ coverage_form.action }}",
                                    method="post", enctype="multipart/form-data"):
                    html_tags.div("{% crispy coverage_form %}")
                    with html_tags.div(cls="row", style="margin-top:10px;"):
                        with html_tags.div(cls="col-md-offset-10 col-xs-offset-6 "
                                               "col-md-2 col-xs-6"):
                            html_tags.button("Save changes", type="button",
                                             cls="btn btn-primary pull-right",
                                             style="display: none;")

                html_tags.div("{% crispy orig_coverage_form %}", cls="content-block")

                html_tags.div("{% crispy cellinfo_form %}", cls='content-block')

                with html_tags.div(id="variables", cls="content-block"):
                    html_tags.div("{% for form in bandinfo_formset_forms %}")
                    with html_tags.form(id="{{ form.form_id }}", action="{{ form.action }}",
                                        method="post", enctype="multipart/form-data", cls='well'):
                        html_tags.div("{% crispy form %}")
                        with html_tags.div(cls="row", style="margin-top:10px;"):
                            with html_tags.div(cls="col-md-offset-10 col-xs-offset-6 "
                                                   "col-md-2 col-xs-6"):
                                html_tags.button("Save changes", type="button",
                                                 cls="btn btn-primary pull-right btn-form-submit",
                                                 style="display: none;")
                    html_tags.div("{% endfor %}")

        template = Template(root_div.render())
        context_dict = dict()

        context_dict["orig_coverage_form"] = self.get_original_coverage_form()
        context_dict["cellinfo_form"] = self.get_cellinfo_form()
        temp_cov_form = self.get_temporal_coverage_form()

        update_action = "/hsapi/_internal/GeoRasterLogicalFile/{0}/{1}/{2}/update-file-metadata/"
        create_action = "/hsapi/_internal/GeoRasterLogicalFile/{0}/{1}/add-file-metadata/"
        spatial_cov_form = self.get_spatial_coverage_form(allow_edit=True)
        spatial_coverage = self.spatial_coverage
        if spatial_coverage:
            form_action = update_action.format(self.logical_file.id, "coverage",
                                               spatial_coverage.id)
        else:
            form_action = create_action.format(self.logical_file.id, "coverage")

        spatial_cov_form.action = form_action

        temporal_coverage = self.temporal_coverage
        if temporal_coverage:
            form_action = update_action.format(self.logical_file.id, "coverage",
                                               temporal_coverage.id)
            temp_cov_form.action = form_action
        else:
            form_action = create_action.format(self.logical_file.id, "coverage")
            temp_cov_form.action = form_action

        context_dict["coverage_form"] = spatial_cov_form
        context_dict["temp_form"] = temp_cov_form
        context_dict["bandinfo_formset_forms"] = self.get_bandinfo_formset().forms
        context = Context(context_dict)
        rendered_html = template.render(context)
        return rendered_html

    def get_cellinfo_form(self):
        return self.cellInformation.get_html_form(resource=None)

    def get_original_coverage_form(self):
        return OriginalCoverageRaster.get_html_form(resource=None, element=self.originalCoverage,
                                                    file_type=True, allow_edit=False)

    def get_bandinfo_formset(self):
        from ..forms import BandInfoForm, BaseBandInfoFormSet

        BandInfoFormSetEdit = formset_factory(
            wraps(BandInfoForm)(partial(BandInfoForm, allow_edit=True)),
            formset=BaseBandInfoFormSet, extra=0)
        bandinfo_formset = BandInfoFormSetEdit(
            initial=list(self.bandInformations.values()), prefix='BandInformation')

        for frm in bandinfo_formset.forms:
            if len(frm.initial) > 0:
                frm.action = "/hsapi/_internal/%s/%s/bandinformation/%s/update-file-metadata/" % (
                    "GeoRasterLogicalFile", self.logical_file.id, frm.initial['id'])
                frm.number = frm.initial['id']

        return bandinfo_formset

    @classmethod
    def validate_element_data(cls, request, element_name):
        """overriding the base class method"""

        from ..forms import BandInfoValidationForm

        if element_name.lower() not in [el_name.lower() for el_name
                                        in cls.get_supported_element_names()]:
            err_msg = "{} is nor a supported metadata element for Geo Raster file type"
            err_msg = err_msg.format(element_name)
            return {'is_valid': False, 'element_data_dict': None, "errors": err_msg}
        element_name = element_name.lower()
        if element_name == 'bandinformation':
            form_data = {}
            for field_name in BandInfoValidationForm().fields:
                matching_key = [key for key in request.POST if '-' + field_name in key][0]
                form_data[field_name] = request.POST[matching_key]
            element_form = BandInfoValidationForm(form_data)
        elif element_name == 'coverage' and 'start' not in request.POST:
            element_form = CoverageSpatialForm(data=request.POST)
        else:
            # element_name must be coverage
            # here we are assuming temporal coverage
            element_form = CoverageTemporalForm(data=request.POST)

        if element_form.is_valid():
            return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
        else:
            return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}

    def get_preview_data_url(self, resource, folder_path):
        """Get a GeoServer layer preview link."""

        if self.spatial_coverage:
            preview_data_url = utils.build_preview_data_url(
                resource=resource,
                folder_path=folder_path,
                spatial_coverage=self.spatial_coverage.value
            )
        else:
            preview_data_url = None

        return preview_data_url


class GeoRasterLogicalFile(AbstractLogicalFile):
    metadata = models.OneToOneField(GeoRasterFileMetaData, on_delete=models.CASCADE, related_name="logical_file")
    data_type = "GeographicRaster"

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        """only .zip and .tif file can be set to this logical file group"""
        return [".zip", ".tif", ".tiff"]

    def get_metadata_json(self):
        """Return the metadata in JSON format - uses schema.org terms where possible and the rest
        terms are based on hsterms."""

        return self.metadata.to_json()

    @property
    def metadata_json_file_path(self):
        """Returns the storage path of the aggregation metadata json file"""

        from hs_file_types.enums import AggregationMetaFilePath

        primary_file = self.get_primary_resource_file(self.files.all())
        meta_file_path = primary_file.storage_path + AggregationMetaFilePath.METADATA_JSON_FILE_ENDSWITH
        return meta_file_path

    @classmethod
    def get_main_file_type(cls):
        """The main file type for this aggregation"""
        return ".vrt"

    @classmethod
    def get_allowed_storage_file_types(cls):
        """file types allowed in this logical file group are: .tif and .vrt"""
        return [".tiff", ".tif", ".vrt"]

    @staticmethod
    def get_aggregation_display_name():
        return 'Geographic Raster Content: A geographic grid represented by a virtual raster ' \
               'tile (.vrt) file and one or more geotiff (.tif) files'

    @staticmethod
    def get_aggregation_term_label():
        return "Geographic Raster Aggregation"

    @staticmethod
    def get_aggregation_type_name():
        return "GeographicRasterAggregation"

    # used in discovery faceting to aggregate native and composite content types
    @staticmethod
    def get_discovery_content_type():
        """Return a human-readable content type for discovery.
        This must agree between Composite Types and native types.
        """
        return "Geographic Raster"

    @classmethod
    def create(cls, resource):
        """this custom method MUST be used to create an instance of this class"""
        raster_metadata = GeoRasterFileMetaData.objects.create(keywords=[], extra_metadata={})
        # Note we are not creating the logical file record in DB at this point
        # the caller must save this to DB
        return cls(metadata=raster_metadata, resource=resource)

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

    @classmethod
    def check_files_for_aggregation_type(cls, files):
        """Checks if the specified files can be used to set this aggregation type
        :param  files: a list of ResourceFile objects

        :return If the files meet the requirements of this aggregation type, then returns this
        aggregation class name, otherwise empty string.
        """
        if not files:
            # no files
            return ""

        for fl in files:
            if fl.extension.lower() not in cls.get_allowed_storage_file_types():
                return ""

        # check that there can be only one vrt file
        vrt_files = [f for f in files if f.extension.lower() == ".vrt"]
        if len(vrt_files) > 1:
            return ""

        # check if there are multiple tif files, then there has to be one vrt file
        tif_files = [f for f in files if f.extension.lower() == ".tif" or f.extension.lower()
                     == ".tiff"]
        if len(tif_files) > 1:
            if len(vrt_files) != 1:
                return ""
        elif not tif_files:
            # there has to be at least one tif file
            return ""

        return cls.__name__

    @classmethod
    def set_file_type(cls, resource, user, file_id=None, folder_path=''):
        """ Creates a GeoRasterLogicalFile (aggregation) from a tif or a zip resource file """

        log = logging.getLogger()
        with FileTypeContext(aggr_cls=cls, user=user, resource=resource, file_id=file_id,
                             folder_path=folder_path,
                             post_aggr_signal=post_add_raster_aggregation,
                             is_temp_file=True) as ft_ctx:

            res_file = ft_ctx.res_file
            file_name = res_file.file_name
            # get file name without the extension - needed for naming the aggregation folder
            base_file_name = file_name[:-len(res_file.extension)]
            file_folder = res_file.file_folder
            upload_folder = file_folder
            temp_file = ft_ctx.temp_file
            temp_dir = ft_ctx.temp_dir

            raster_folder = folder_path if folder_path else file_folder
            # validate the file
            validation_results = raster_file_validation(raster_file=temp_file, resource=resource,
                                                        raster_folder=raster_folder)

            if not validation_results['error_info']:
                vrt_created = validation_results['vrt_created']
                msg = "Geographic raster aggregation. Error when creating aggregation. Error:{}"
                log.info("Geographic raster aggregation validation successful.")
                # extract metadata
                temp_vrt_file_path = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if
                                      '.vrt' == os.path.splitext(f)[1]].pop()
                metadata = extract_metadata(temp_vrt_file_path)
                log.info("Geographic raster metadata extraction was successful.")

                with transaction.atomic():
                    try:
                        res_files = validation_results['raster_resource_files']
                        files_to_upload = validation_results['new_resource_files_to_add']
                        # create a raster aggregation
                        logical_file = cls.create_aggregation(dataset_name=base_file_name,
                                                              resource=resource,
                                                              res_files=res_files,
                                                              new_files_to_upload=files_to_upload,
                                                              folder_path=upload_folder)

                        log.info("Geographic raster aggregation type - new files were added "
                                 "to the resource.")
                        logical_file.extra_data['vrt_created'] = str(vrt_created)
                        logical_file.save()
                        # use the extracted metadata to populate file metadata
                        for element in metadata:
                            # here k is the name of the element
                            # v is a dict of all element attributes/field names and field values
                            k, v = list(element.items())[0]
                            logical_file.metadata.create_element(k, **v)

                        log.info("Geographic raster aggregation type - metadata was saved to DB")
                        ft_ctx.logical_file = logical_file
                    except Exception as ex:
                        logical_file.remove_aggregation()
                        msg = msg.format(str(ex))
                        log.exception(msg)
                        raise ValidationError(msg)

                return logical_file
            else:
                err_msg = "Geographic raster aggregation type validation failed. {}".format(
                    ' '.join(validation_results['error_info']))
                log.error(err_msg)
                raise ValidationError(err_msg)

    def remove_aggregation(self):
        """Deletes the aggregation object (logical file) *self* and the associated metadata
        object. If the aggregation contains a system generated vrt file that resource file also will be
        deleted."""

        # need to delete the system generated vrt file
        vrt_created = self.extra_data.get('vrt_created', 'False')
        vrt_file = None
        if vrt_created == 'True':
            # the vrt file is a system generated file
            for res_file in self.files.all():
                if res_file.file_name.lower().endswith(".vrt"):
                    vrt_file = res_file
                    break
        super(GeoRasterLogicalFile, self).remove_aggregation()
        if vrt_file is not None:
            vrt_file.delete()

    @classmethod
    def get_primary_resource_file(cls, resource_files):
        """Gets a resource file that has extension .vrt (if exists) otherwise 'tif'
        from the list of files *resource_files* """

        res_files = [f for f in resource_files if f.extension.lower() == '.vrt']
        if not res_files:
            res_files = [f for f in resource_files if f.extension.lower() in ('.tif', 'tiff')]

        return res_files[0] if res_files else None

    def create_aggregation_xml_documents(self, create_map_xml=True):
        super(GeoRasterLogicalFile, self).create_aggregation_xml_documents(create_map_xml)
        self.metadata.is_dirty = False
        self.metadata.save()


def raster_file_validation(raster_file, resource, raster_folder=''):
    """ Validates if the relevant files are valid for raster aggregation or raster resource type

    :param  raster_file: a temp file (extension tif or zip) retrieved from S3 and stored on temp
    dir in django
    :param  raster_folder: (optional) folder in which raster file exists on S3.
    :param  resource: an instance of CompositeResource in which raster_file exits.

    :return A list of error messages and a list of file paths for all files that belong to raster
    """
    error_info = []
    new_resource_files_to_add = []
    raster_resource_files = []
    create_vrt = False
    validation_results = {'error_info': error_info,
                          'new_resource_files_to_add': new_resource_files_to_add,
                          'raster_resource_files': raster_resource_files,
                          'vrt_created': create_vrt}
    file_name_part, ext = os.path.splitext(os.path.basename(raster_file))
    ext = ext.lower()
    if ext == '.tif' or ext == '.tiff':
        res_files = ResourceFile.list_folder(resource=resource, folder=raster_folder,
                                             sub_folders=False)

        vrt_files_for_raster = get_vrt_files(raster_file, res_files)
        if len(vrt_files_for_raster) > 1:
            error_info.append("The raster {} is listed by more than one vrt file {}".format(raster_file,
                                                                                            vrt_files_for_raster))
            return validation_results

        if len(vrt_files_for_raster) == 1:
            vrt_file = vrt_files_for_raster[0]
            raster_resource_files.extend([vrt_file])
            temp_dir = os.path.dirname(raster_file)
            temp_vrt_file = utils.get_file_from_s3(resource=resource, file_path=vrt_file.storage_path,
                                                   temp_dir=temp_dir)
            listed_tif_files = list_tif_files(vrt_file)
            tif_files = [f for f in res_files if f.file_name in listed_tif_files]
            if len(tif_files) != len(listed_tif_files):
                error_info.append("The vrt file {} lists {} files, only found {}".format(vrt_file,
                                                                                         len(listed_tif_files),
                                                                                         len(tif_files)))
                return validation_results
        else:
            # create the .vrt file
            tif_files = [f for f in res_files if f.file_name == os.path.basename(raster_file)]
            try:
                vrt_file = create_vrt_file(raster_file)
                temp_vrt_file = vrt_file
                create_vrt = True
                validation_results['vrt_created'] = create_vrt
            except Exception as ex:
                error_info.append(str(ex))
            else:
                if os.path.isfile(vrt_file):
                    new_resource_files_to_add.append(vrt_file)

        raster_resource_files.extend(tif_files)

    elif ext == '.zip':
        try:
            extract_file_paths = _explode_raster_zip_file(raster_file)
        except Exception as ex:
            error_info.append(str(ex))
        else:
            if extract_file_paths:
                new_resource_files_to_add.extend(extract_file_paths)
    else:
        error_info.append("Invalid file mime type found.")

    if not error_info:
        if ext == ".zip":
            # in case of zip, there needs to be more than one file extracted out of the zip file
            if len(new_resource_files_to_add) < 2:
                error_info.append("Invalid zip file. Seems to contain only one file. "
                                  "Multiple tif files are expected.")
                return validation_results

            files_ext = [os.path.splitext(path)[1].lower() for path in new_resource_files_to_add]
            if files_ext.count('.vrt') > 1:
                error_info.append("Invalid zip file. Seems to contain multiple vrt files.")
                return validation_results
            elif files_ext.count('.vrt') == 0:
                error_info.append("Invalid zip file. No vrt file was found.")
                return validation_results
            elif files_ext.count('.tif') + files_ext.count('.tiff') < 1:
                error_info.append("Invalid zip file. No tif/tiff file was found.")
                return validation_results

            # check if there are files that are not raster related
            non_raster_files = [f_ext for f_ext in files_ext if f_ext
                                not in ('.tif', '.tiff', '.vrt')]
            if non_raster_files:
                error_info.append("Invalid zip file. Contains files that are not raster related.")
                return validation_results

            temp_vrt_file = new_resource_files_to_add[files_ext.index('.vrt')]

        # validate vrt file if we didn't create it
        if ext == '.zip' or not create_vrt:
            raster_dataset = gdal.Open(temp_vrt_file, GA_ReadOnly)
            if raster_dataset is None:
                error_info.append('Failed to open the vrt file.')
                return validation_results

            # check if the vrt file is valid
            try:
                raster_dataset.RasterXSize
                raster_dataset.RasterYSize
                raster_dataset.RasterCount
            except AttributeError:
                error_info.append('Raster size and band information are missing.')
                return validation_results

            # check if the raster file numbers and names are valid in vrt file
            with open(temp_vrt_file, 'r') as vrt_file:
                vrt_string = vrt_file.read()
                root = ET.fromstring(vrt_string)
                file_names_in_vrt = [file_name.text for file_name in root.iter('SourceFilename')]

            if ext == '.zip':
                file_names = [os.path.basename(path) for path in new_resource_files_to_add]
            else:
                file_names = [f.file_name for f in raster_resource_files]

            file_names = [f_name for f_name in file_names if not f_name.endswith('.vrt')]

            for vrt_ref_raster_name in file_names_in_vrt:
                if vrt_ref_raster_name in file_names \
                        or (os.path.split(vrt_ref_raster_name)[0] == '.'
                            and os.path.split(vrt_ref_raster_name)[1] in file_names):
                    continue
                else:
                    msg = "The file {tif} which is listed in the {vrt} file is missing."
                    msg = msg.format(tif=os.path.basename(vrt_ref_raster_name),
                                     vrt=os.path.basename(temp_vrt_file))
                    error_info.append(msg)
                    break

    return validation_results


def list_tif_files(vrt_file):
    """
    lists tif files named in a vrt_file
    :param vrt_file: ResourceFile for of a vrt to list associated tif(f) files
    :return: List of string filenames read from vrt_file
    """
    resource = vrt_file.resource
    temp_vrt_file = utils.get_file_from_s3(resource=resource, file_path=vrt_file.storage_path)
    with open(temp_vrt_file, 'r') as opened_vrt_file:
        vrt_string = opened_vrt_file.read()
        root = ET.fromstring(vrt_string)
        file_names_in_vrt = [file_name.text for file_name in root.iter('SourceFilename')]
        return file_names_in_vrt


def get_vrt_files(raster_file, res_files):
    """
    Searches for vrt_files that lists the supplied raster_file
    :param raster_file: The raster file to find the associated vrt_file of
    :param res_files: list of ResourceFiles in the the folder of raster_file
    :return: A list of vrt ResourceFile(s) which lists the raster_file, empty List if not found.
    """
    vrt_files = [f for f in res_files if f.extension.lower() == ".vrt"]
    vrt_files_for_raster = []
    if vrt_files:
        for vrt_file in vrt_files:
            file_names_in_vrt = list_tif_files(vrt_file)
            for vrt_ref_raster_name in file_names_in_vrt:
                if raster_file.endswith(vrt_ref_raster_name):
                    vrt_files_for_raster.append(vrt_file)
    return vrt_files_for_raster


def extract_metadata(temp_vrt_file_path):
    metadata = []
    res_md_dict = raster_meta_extract.get_raster_meta_dict(temp_vrt_file_path)
    wgs_cov_info = res_md_dict['spatial_coverage_info']['wgs84_coverage_info']
    # add core metadata coverage - box
    if wgs_cov_info:
        box = {'coverage': {'type': 'box', 'value': wgs_cov_info}}
        metadata.append(box)

    # Save extended meta spatial reference
    orig_cov_info = res_md_dict['spatial_coverage_info']['original_coverage_info']

    # Here the assumption is that if there is no value for the 'northlimit' then there is no value
    # for the bounding box
    if orig_cov_info['northlimit'] is not None:
        ori_cov = {'OriginalCoverageRaster': {'value': orig_cov_info}}
        metadata.append(ori_cov)

    # Save extended meta cell info
    res_md_dict['cell_info']['name'] = os.path.basename(temp_vrt_file_path)
    metadata.append({'CellInformation': res_md_dict['cell_info']})

    # Save extended meta band info
    for band_info in list(res_md_dict['band_info'].values()):
        metadata.append({'BandInformation': band_info})
    return metadata


def create_vrt_file(tif_file):
    """ tif_file exists in temp directory - retrieved from S3 """

    log = logging.getLogger()

    # create vrt file
    temp_dir = os.path.dirname(tif_file)
    tif_file_name = os.path.basename(tif_file)
    vrt_file_path = os.path.join(temp_dir, os.path.splitext(tif_file_name)[0] + '.vrt')

    with open(os.devnull, 'w') as fp:
        subprocess.Popen(['gdal_translate', '-of', 'VRT', tif_file, vrt_file_path],
                         stdout=fp,
                         stderr=fp).wait()  # need to wait

    # edit VRT contents
    try:
        tree = ET.parse(vrt_file_path)
        root = tree.getroot()
        for element in root.iter('SourceFilename'):
            element.text = tif_file_name
            element.attrib['relativeToVRT'] = '1'

        tree.write(vrt_file_path)

    except Exception as ex:
        log.exception("Failed to create/write to vrt file. Error:{}".format(str(ex)))
        raise Exception("Failed to create/write to vrt file")

    return vrt_file_path


def _explode_raster_zip_file(zip_file):
    """ zip_file exists in temp directory - retrieved from S3 """

    log = logging.getLogger()
    temp_dir = os.path.dirname(zip_file)
    try:
        zf = zipfile.ZipFile(zip_file, 'r')
        zf.extractall(temp_dir)
        zf.close()

        # get all the file abs names in temp_dir
        extract_file_paths = []
        for dirpath, _, filenames in os.walk(temp_dir):
            for name in filenames:
                file_path = os.path.abspath(os.path.join(dirpath, name))
                file_ext = os.path.splitext(os.path.basename(file_path))[1]
                file_ext = file_ext.lower()
                if file_ext in GeoRasterLogicalFile.get_allowed_storage_file_types():
                    shutil.move(file_path, os.path.join(temp_dir, name))
                    extract_file_paths.append(os.path.join(temp_dir, os.path.basename(file_path)))

    except Exception as ex:
        log.exception("Failed to unzip. Error:{}".format(str(ex)))
        raise ex

    return extract_file_paths
