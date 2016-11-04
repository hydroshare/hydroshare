from functools import partial, wraps

from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.forms.models import formset_factory
from django.template import Template, Context

from dominate.tags import *

from hs_core.models import Coverage

from hs_geo_raster_resource.models import CellInformation, BandInformation, OriginalCoverage, \
    GeoRasterMetaDataMixin
from hs_geo_raster_resource.forms import BandInfoForm, BaseBandInfoFormSet, BandInfoValidationForm

from base import AbstractFileMetaData, AbstractLogicalFile


class GeoRasterFileMetaData(AbstractFileMetaData, GeoRasterMetaDataMixin):
    _cell_information = GenericRelation(CellInformation)
    _band_information = GenericRelation(BandInformation)
    _ori_coverage = GenericRelation(OriginalCoverage)
    _coverages = GenericRelation(Coverage)

    @classmethod
    def get_supported_element_names(cls):
        elements = list()
        elements.append('CellInformation')
        elements.append('BandInformation')
        elements.append('OriginalCoverage')
        elements.append('Coverage')
        return elements

    @property
    def coverage(self):
        return self._coverages.all().first()

    def delete_all_elements(self):
        if self.coverage:
            self.coverage.delete()
        if self.cellInformation:
            self.cellInformation.delete()
        if self.originalCoverage:
            self.originalCoverage.delete()

        self.bandInformations.all().delete()

    def has_all_required_elements(self):
        if not self.coverage:
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

        html_string = self.coverage.get_html()
        html_string += self.originalCoverage.get_html()
        html_string += self.cellInformation.get_html()
        band_legend = legend("Band Information", cls="pull-left", style="margin-left:10px;")
        html_string += band_legend.render()
        for band_info in self.bandInformations:
            html_string += band_info.get_html()

        template = Template(html_string)
        context = Context({})
        return template.render(context)

    def get_html_forms(self):
        """
        generates html form code for all metadata associated with raster file type
        that can by dynamically injected to existing html document using jquery or loaded
        into an html document by including this single line:
        {{ logical_file.metadata.get_html_forms }}
        """
        root_div = div("{% load crispy_forms_tags %}")
        with root_div:
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
        context_dict["coverage_form"] = self.coverage.get_html_form(resource=None)
        context_dict["orig_coverage_form"] = self.originalCoverage.get_html_form(resource=None)
        context_dict["cellinfo_form"] = self.cellInformation.get_html_form(resource=None)
        context_dict["bandinfo_formset_forms"] = self.get_bandinfo_formset().forms
        context = Context(context_dict)
        return template.render(context)

    def get_coverage_form(self):
        return self.coverage.get_html_form(resource=None)

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
                "GeoRaster", self.logical_file.id, form.initial['id'])
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
            if element_form.is_valid():
                return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
            else:
                return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}


class GeoRasterLogicalFile(AbstractLogicalFile):
    metadata = models.OneToOneField(GeoRasterFileMetaData, related_name="logical_file")

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        # only .zip and .tif file can be set to this logical file group
        return [".zip", ".tif"]

    @classmethod
    def get_allowed_storage_file_types(cls):
        # file types allowed in this logical file group are: .tif and .vrt
        return [".tif", ".vrt"]

    @classmethod
    def create(cls):
        raster_metadata = GeoRasterFileMetaData.objects.create()
        return cls.objects.create(metadata=raster_metadata)


