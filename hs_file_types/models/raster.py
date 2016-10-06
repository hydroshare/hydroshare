from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

from hs_geo_raster_resource.models import CellInformation, BandInformation, OriginalCoverage, \
    GeoRasterMetaDataMixin
from base import AbstractFileMetaData, AbstractLogicalFile


class GeoRasterFileMetaData(AbstractFileMetaData, GeoRasterMetaDataMixin):
    # required non-repeatable cell information metadata elements
    _cell_information = GenericRelation(CellInformation)
    _band_information = GenericRelation(BandInformation)
    _ori_coverage = GenericRelation(OriginalCoverage)

class GeoRasterLogicalFile(AbstractLogicalFile):
    metadata = models.OneToOneField(GeoRasterFileMetaData)

    @property
    def get_allowed_uploaded_file_types(self):
        # can upload only .zip and .tif file types
        return [".zip", ".tif"]

    @property
    def get_allowed_storage_file_types(self):
        # file types allowed in the file group are: .tif and .vrt
        return [".tif", ".vrt"]