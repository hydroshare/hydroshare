from django.db import models
from django.contrib.postgres.fields import HStoreField
from django.core.exceptions import ValidationError

from base import AbstractFileMetaData, AbstractLogicalFile


class MetaDataManager(models.Manager):

    def __init__(self, element_type=None, *args, **kwargs):
        self.element_type = element_type
        super(MetaDataManager, self).__init__(*args, **kwargs)

    def create(self, *args, **kwargs):
        if self.element_type is None:
            kwargs.pop('element_type', None)
        return super(MetaDataManager, self).create(*args, **kwargs)

    def get_queryset(self):
        qs = super(MetaDataManager, self).get_queryset()
        if self.element_type:
            qs = qs.filter(element_type=self.element_type)
        return qs


class BaseMetaDataElement(models.Model):
    element_type = models.CharField(max_length=100, default="Generic")
    data = HStoreField(default={})
    metadata = models.ForeignKey(NetCDFFileMetaData)

    @classmethod
    def validate(cls, **kwargs):
        # here need to validate the dict. This needs to be used for
        # creating and updating
        data = kwargs.get('data', None)
        if data is None:
            raise ValidationError("Value for data attribute is missing")
        if not isinstance(data, dict):
            raise ValidationError("Value for data attribute must be in dict format")
        metadata = kwargs.get('metadata', None)
        if metadata is None or not isinstance(metadata, AbstractFileMetaData):
            raise ValidationError("Value for metadata attribute is missing")

    @classmethod
    def create(cls, **kwargs):
        return cls.objects.create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        element = BaseMetaDataElement.objects.get(id=element_id)
        element.data = kwargs['data']


class OriginalCoverage(BaseMetaDataElement):
    objects = MetaDataManager("OriginalCoverage")

    class Meta:
        verbose_name = "Original Coverage"
        proxy = True

    @classmethod
    def validate(cls, **kwargs):
        # here need to validate the dict. This needs to be used for
        # creating and updating
        super(OriginalCoverage, cls).validate(**kwargs)
        metadata = kwargs['metadata']
        element_type = kwargs['element_type']
        # Make sure we are not creating more than one element of this type
        if BaseMetaDataElement.objects.filter(metadata=metadata,
                                              element_type=element_type).exists():
            raise ValidationError("Original Coverage element already exists.")
        # TODO: validate the value for the data key
        data = kwargs['data']
        if 'north_limit' not in data:
            raise ValidationError("value for 'north_limit' is missing.")
        else:
            try:
                float(data['north_limit'])
            except TypeError:
                raise ValidationError("Value for 'north_limit' must be numeric.")

    @classmethod
    def create(cls, **kwargs):
        cls.validate(**kwargs)
        return super(OriginalCoverage, cls).create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        cls.validate(**kwargs)
        super(OriginalCoverage, cls).update(element_id, **kwargs)

    @property
    def north_limit(self):
        return self.data.get('north_limit', None)


class NetCDFFileMetaData(AbstractFileMetaData):
    __metadata_element_classes ={'originalcoverage': OriginalCoverage}

    def create_element(self, element_name, **kwargs):
        if element_name not in self.get_supported_element_names():
            raise ValidationError("'{}' is not a supported metadata element.".format(element_name))

        kwargs['element_type'] = element_name
        kwargs['metadata'] = self
        return self.__metadata_element_classes[element_name.lower()].create(**kwargs)

    def update_element(self, element_id, **kwargs):
        element = BaseMetaDataElement.objects.get(id=element_id)
        return self.__metadata_element_classes[element.element_type.lower()].update(element_id,
                                                                                    **kwargs)

    def original_coverage(self):
        OriginalCoverage.objects.filter(metadata=self).first()

    @classmethod
    def get_supported_element_names(cls):
        return ['OriginalCoverage']


class NetCDFLogicalFile(AbstractLogicalFile):
    metadata = models.OneToOneField(NetCDFFileMetaData, related_name="logical_file")
    data_type = "NetCDF data"

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        """only .nc file can be set to this logical file group"""
        return [".nc"]

    @classmethod
    def get_allowed_storage_file_types(cls):
        """file types allowed in this logical file group are: .nc and .txt"""
        return [".nc", ".txt"]

    @classmethod
    def create(cls):
        """this custom method MUST be used to create an instance of this class"""
        netcdf_metadata = NetCDFFileMetaData.objects.create()
        return cls.objects.create(metadata=netcdf_metadata)

    @property
    def supports_resource_file_move(self):
        """resource files that are part of this logical file can't be moved"""
        return False

    @property
    def supports_resource_file_rename(self):
        """resource files that are part of this logical file can't be renamed"""
        return False

    @property
    def supports_delete_folder_on_zip(self):
        """does not allow the original folder to be deleted upon zipping of that folder"""
        return False