from functools import partial, wraps

from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.forms.models import formset_factory
from django.template import Template, Context

from dominate.tags import div, legend, form, button

from hs_core.models import Coverage
from hs_core.forms import CoverageTemporalForm

from hs_geo_raster_resource.models import CellInformation, BandInformation, OriginalCoverage, \
    GeoRasterMetaDataMixin
from hs_geo_raster_resource.forms import BandInfoForm, BaseBandInfoFormSet, BandInfoValidationForm

from base import AbstractFileMetaData, AbstractLogicalFile


class GeoRasterFileMetaData(AbstractFileMetaData, GeoRasterMetaDataMixin):
    _cell_information = GenericRelation(CellInformation)
    _band_information = GenericRelation(BandInformation)
    _ori_coverage = GenericRelation(OriginalCoverage)

    @classmethod
    def get_supported_element_names(cls):
        # TODO: check if this method has been unit tested
        elements = super(GeoRasterFileMetaData, cls).get_supported_element_names()
        elements.append('CellInformation')
        elements.append('BandInformation')
        elements.append('OriginalCoverage')
        return elements

    def delete_all_elements(self):
        super(GeoRasterFileMetaData, self).delete_all_elements()
        if self.cellInformation:
            self.cellInformation.delete()
        if self.originalCoverage:
            self.originalCoverage.delete()

        self.bandInformations.all().delete()

    def has_all_required_elements(self):
        # TODO: check if this method has been unit tested
        if not super(GeoRasterFileMetaData, self).has_all_required_elements():
            return False
        if self.coverages.count() == 0:
            return False
        if not self.cellInformation:
            return False
        if not self.originalCoverage:
            return False
        if self.bandInformations.count() == 0:
            return False

        return True

    def get_html(self):
        """
        generates template based html for all metadata associated with raster logical file
        that can be dynamically injected to existing html document for metadata viewing or can be
        included as part of the html document using this
        single line: {{ logical_file.metadata.get_html }}
        """

        html_string = super(GeoRasterFileMetaData, self).get_html()
        html_string += self.spatial_coverage.get_html()
        html_string += self.originalCoverage.get_html()
        html_string += self.cellInformation.get_html()
        if self.temporal_coverage:
            html_string += self.temporal_coverage.get_html()
        band_legend = legend("Band Information", cls="pull-left", style="margin-left:10px;")
        html_string += band_legend.render()
        for band_info in self.bandInformations:
            html_string += band_info.get_html()

        template = Template(html_string)
        context = Context({})
        return template.render(context)

    def get_html_forms(self, datatset_name_form=True):
        """
        generates html form code for all metadata associated with raster file type
        that can by dynamically injected to existing html document using jquery or loaded
        into an html document by including this single line:
        {{ logical_file.metadata.get_html_forms }}
        """
        root_div = div("{% load crispy_forms_tags %}")
        with root_div:
            super(GeoRasterFileMetaData, self).get_html_forms()
            with div(cls="well", id="variables"):
                with div(cls="col-lg-6 col-xs-12"):
                    with form(id="id-coverage_temporal-file-type", action="{{ temp_form.action }}",
                              method="post", enctype="multipart/form-data"):
                        div("{% crispy temp_form %}")
                        with div(cls="row", style="margin-top:10px;"):
                            with div(cls="col-md-offset-10 col-xs-offset-6 "
                                         "col-md-2 col-xs-6"):
                                button("Save changes", type="button",
                                       cls="btn btn-primary pull-right",
                                       style="display: none;",
                                       onclick="metadata_update_ajax_submit("
                                               "'id-coverage_temporal-file-type'); return false;")
            with div(cls="col-lg-6 col-xs-12"):
                div("{% crispy coverage_form %}")
            with div(cls="col-lg-6 col-xs-12"):
                div("{% crispy orig_coverage_form %}")
            with div(cls="col-lg-6 col-xs-12"):
                div("{% crispy cellinfo_form %}")

            with div(cls="pull-left col-sm-12"):
                with div(cls="well", id="variables"):
                    with div(cls="row"):
                        div("{% for form in bandinfo_formset_forms %}")
                        with div(cls="col-sm-6 col-xs-12"):
                            with form(id="{{ form.form_id }}", action="{{ form.action }}",
                                      method="post", enctype="multipart/form-data"):
                                div("{% crispy form %}")
                                with div(cls="row", style="margin-top:10px;"):
                                    with div(cls="col-md-offset-10 col-xs-offset-6 "
                                                 "col-md-2 col-xs-6"):
                                        button("Save changes", type="button",
                                               cls="btn btn-primary pull-right",
                                               style="display: none;",
                                               onclick="metadata_update_ajax_submit({{ "
                                                       "form.form_id_button }}); return false;")
                        div("{% endfor %}")

        template = Template(root_div.render())
        context_dict = dict()
        context_dict["coverage_form"] = self.get_spatial_coverage_form()
        context_dict["orig_coverage_form"] = self.get_original_coverage_form()
        context_dict["cellinfo_form"] = self.get_cellinfo_form()
        temp_cov_form = self.get_temporal_coverage_form()

        update_action = "/hsapi/_internal/GeoRasterLogicalFile/{0}/{1}/{2}/update-file-metadata/"
        create_action = "/hsapi/_internal/GeoRasterLogicalFile/{0}/{1}/add-file-metadata/"
        if self.temporal_coverage:
            temp_action = update_action.format(self.logical_file.id, "coverage",
                                               self.temporal_coverage.id)
            temp_cov_form.action = temp_action
        else:
            temp_action = create_action.format(self.logical_file.id, "coverage")
            temp_cov_form.action = temp_action

        context_dict["temp_form"] = temp_cov_form
        context_dict["bandinfo_formset_forms"] = self.get_bandinfo_formset().forms
        context = Context(context_dict)
        rendered_html = template.render(context)

        # file level form field ids need to changed so that they are different from
        # the ids used at the resource level for the same type of metadata elements
        rendered_html = rendered_html.replace("div_id_start", "div_id_start_filetype")
        rendered_html = rendered_html.replace("div_id_end", "div_id_end_filetype")
        rendered_html = rendered_html.replace("id_start", "id_start_filetype")
        rendered_html = rendered_html.replace("id_end", "id_end_filetype")
        for spatial_element_id in ('div_id_northlimit', 'div_id_southlimit', 'div_id_westlimit',
                                   'div_id_eastlimit'):
            rendered_html = rendered_html.replace(spatial_element_id,
                                                  spatial_element_id + "_filetype", 1)
        for spatial_element_id in ('div_id_type', 'div_id_north', 'div_id_east'):
            rendered_html = rendered_html.replace(spatial_element_id,
                                                  spatial_element_id + "_filetype", 1)
        return rendered_html

    def get_spatial_coverage_form(self):
        return Coverage.get_spatial_html_form(resource=None, element=self.spatial_coverage,
                                              allow_edit=False)

    def get_temporal_coverage_form(self):
        return Coverage.get_temporal_html_form(resource=None, element=self.temporal_coverage)

    def get_cellinfo_form(self):
        return self.cellInformation.get_html_form(resource=None)

    def get_original_coverage_form(self):
        return self.originalCoverage.get_html_form(resource=None)

    def get_bandinfo_formset(self):
        BandInfoFormSetEdit = formset_factory(
            wraps(BandInfoForm)(partial(BandInfoForm, allow_edit=True)),
            formset=BaseBandInfoFormSet, extra=0)
        bandinfo_formset = BandInfoFormSetEdit(
            initial=self.bandInformations.values(), prefix='BandInformation')

        for form in bandinfo_formset.forms:
            if len(form.initial) > 0:
                form.action = "/hsapi/_internal/%s/%s/bandinformation/%s/update-file-metadata/" % (
                    "GeoRasterLogicalFile", self.logical_file.id, form.initial['id'])
                form.number = form.initial['id']

        return bandinfo_formset

    @classmethod
    def validate_element_data(cls, request, element_name):
        # overidding the base class method

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

        else:
            # element_name must be coverage
            # here we are assuming temporal coverage
            element_form = CoverageTemporalForm(data=request.POST)

        if element_form.is_valid():
            return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
        else:
            return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}

    def add_to_xml_container(self, container):
        container_to_add_to = super(GeoRasterFileMetaData, self).add_to_xml_container(container)
        if self.originalCoverage:
            self.originalCoverage.add_to_xml_container(container_to_add_to)
        if self.cellInformation:
            self.cellInformation.add_to_xml_container(container_to_add_to)
        for bandinfo in self.bandInformations:
            bandinfo.add_to_xml_container(container_to_add_to)


class GeoRasterLogicalFile(AbstractLogicalFile):
    metadata = models.OneToOneField(GeoRasterFileMetaData, related_name="logical_file")
    data_type = "Geo Raster data"

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        # only .zip and .tif file can be set to this logical file group
        return [".zip", ".tif"]

    @classmethod
    def get_allowed_storage_file_types(cls):
        # TODO: check if there is a unit test for this method
        # file types allowed in this logical file group are: .tif and .vrt
        return [".tif", ".vrt"]

    @classmethod
    def create(cls):
        # this custom method MUST be used to create an instance of this class
        raster_metadata = GeoRasterFileMetaData.objects.create()
        return cls.objects.create(metadata=raster_metadata)

    @property
    def allow_resource_file_move(self):
        # resource files that are part of this logical file can't be moved
        return False

    @property
    def allow_resource_file_rename(self):
        # resource files that are part of this logical file can't be renamed
        return False
