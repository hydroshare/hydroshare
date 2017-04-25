from django.db import models

from hs_geographic_feature_resource.models import GeographicFeatureMetaDataMixin, \
    OriginalCoverage, GeometryInformation, OriginalFileInfo, FieldInformation

from base import AbstractFileMetaData, AbstractLogicalFile


class GeoFeatureFileMetaData(GeographicFeatureMetaDataMixin, AbstractFileMetaData):
    # the metadata element models are from the geographic feature resource type app
    model_app_label = 'hs_geographic_feature_resource'

    def get_metadata_elements(self):
        elements = super(GeoFeatureFileMetaData, self).get_metadata_elements()
        elements += [self.originalcoverage, self.geometryinformation, self.originalfileinfo]
        elements += list(self.fieldinformations.all())
        return elements

    @classmethod
    def get_metadata_model_classes(cls):
        metadata_model_classes = super(GeoFeatureFileMetaData, cls).get_metadata_model_classes()
        metadata_model_classes['originalcoverage'] = OriginalCoverage
        metadata_model_classes['geometryinformation'] = GeometryInformation
        metadata_model_classes['originalfileinfo'] = OriginalFileInfo
        metadata_model_classes['fieldinformation'] = FieldInformation
        return metadata_model_classes


class GeoFeatureLogicalFile(AbstractLogicalFile):
    metadata = models.OneToOneField(GeoFeatureFileMetaData, related_name="logical_file")
    data_type = "Geo feature data"

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        """only .zip or .shp file can be set to this logical file group"""
        # See Shapefile format:
        # http://resources.arcgis.com/en/help/main/10.2/index.html#//005600000003000000
        return (".zip", ".shp", ".shx", ".dbf", ".prj",
                ".sbx", ".sbn", ".cpg", ".xml", ".fbn",
                ".fbx", ".ain", ".aih", ".atx", ".ixs",
                ".mxs")

    @classmethod
    def get_allowed_storage_file_types(cls):
        """file types allowed in this logical file group are the followings"""
        return [".shp", ".shx", ".dbf", ".prj",
                ".sbx", ".sbn", ".cpg", ".xml", ".fbn",
                ".fbx", ".ain", ".aih", ".atx", ".ixs",
                ".mxs"
                ]

    @classmethod
    def create(cls):
        """this custom method MUST be used to create an instance of this class"""
        feature_metadata = GeoFeatureFileMetaData.objects.create()
        return cls.objects.create(metadata=feature_metadata)

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
