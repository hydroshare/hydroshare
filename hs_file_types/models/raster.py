from functools import partial, wraps

from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.forms.models import formset_factory

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
        # in the template we can insert necessary html code for displaying all
        # file type metadata associated with a logical file using this
        # single line: {{ logical_file.metadata.get_html |safe }}
        html_string = ''
        for element in (self.originalCoverage, self.cellInformation, self.bandInformation):
            html_string += element.get_html() + "\n"
        return html_string

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


