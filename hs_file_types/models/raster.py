from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

from hs_core.models import Coverage

from hs_geo_raster_resource.models import CellInformation, BandInformation, OriginalCoverage, \
    GeoRasterMetaDataMixin
from base import AbstractFileMetaData, AbstractLogicalFile


class GeoRasterFileMetaData(AbstractFileMetaData, GeoRasterMetaDataMixin):
    # required non-repeatable cell information metadata elements
    _cell_information = GenericRelation(CellInformation)
    _band_information = GenericRelation(BandInformation)
    _ori_coverage = GenericRelation(OriginalCoverage)
    coverages = GenericRelation(Coverage)

    @classmethod
    def get_supported_element_names(cls):
        elements = []
        elements.append('CellInformation')
        elements.append('BandInformation')
        elements.append('OriginalCoverage')
        elements.append('Coverage')
        return elements

    def delete_all_elements(self):
        if self.cellInformation:
            self.cellInformation.delete()
        if self.originalCoverage:
            self.originalCoverage.delete()
        self.bandInformation.delete()
        self.coverages.all().delete()


class GeoRasterLogicalFile(AbstractLogicalFile):
    metadata = models.OneToOneField(GeoRasterFileMetaData, related_name="logical_file")

    @property
    def get_allowed_uploaded_file_types(self):
        # can upload only .zip and .tif file types
        return [".zip", ".tif"]

    @property
    def get_allowed_storage_file_types(self):
        # file types allowed in the file group are: .tif and .vrt
        return [".tif", ".vrt"]

    @classmethod
    def create(cls):
        raster_metadata = GeoRasterFileMetaData.objects.create()
        return cls.objects.create(metadata=raster_metadata)
