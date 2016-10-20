from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from hs_core.models import AbstractMetaDataElement
from django.contrib.postgres.fields import HStoreField

from hs_core.models import ResourceFile


class AbstractFileMetaData(models.Model):
    # base class for file metadata, shared among all supported HS file types

    # kye/value metadata
    extra_metadata = HStoreField(default={})

    class Meta:
        abstract = True

    def delete_all_elements(self):
        # subclass must implement
        raise NotImplementedError

    def get_html(self):
        # subclass must implement
        raise NotImplementedError

    @classmethod
    def get_supported_element_names(cls):
        raise NotImplementedError

    def create_element(self, element_model_name, **kwargs):
        model_type = self._get_metadata_element_model_type(element_model_name)
        kwargs['content_object'] = self
        element = model_type.model_class().create(**kwargs)
        return element

    def update_element(self, element_model_name, element_id, **kwargs):
        model_type = self._get_metadata_element_model_type(element_model_name)
        kwargs['content_object'] = self
        model_type.model_class().update(element_id, **kwargs)

    def delete_element(self, element_model_name, element_id):
        model_type = self._get_metadata_element_model_type(element_model_name)
        model_type.model_class().remove(element_id)

    def _get_metadata_element_model_type(self, element_model_name):
        element_model_name = element_model_name.lower()
        if not self._is_valid_element(element_model_name):
            raise ValidationError("Metadata element type:%s is not one of the "
                                  "supported metadata elements."
                                  % element_model_name)

        unsupported_element_error = "Metadata element type:%s is not supported." \
                                    % element_model_name
        try:
            model_type = ContentType.objects.get(app_label='hs_geo_raster_resource',
                                                 model=element_model_name)
        except ObjectDoesNotExist:
            try:
                model_type = ContentType.objects.get(app_label='hs_core',
                                                     model=element_model_name)
            except ObjectDoesNotExist:
                raise ValidationError(unsupported_element_error)

        if not issubclass(model_type.model_class(), AbstractMetaDataElement):
            raise ValidationError(unsupported_element_error)

        return model_type

    def _is_valid_element(self, element_name):
        allowed_elements = [el.lower() for el in self.get_supported_element_names()]
        return element_name.lower() in allowed_elements


class AbstractLogicalFile(models.Model):
    # total size of all files in the logical group
    size = models.IntegerField(default=0)
    # mime type of the dominant file in the group
    mime_type = models.CharField(max_length=1000, default='')
    # files associated with this logical file group
    files = GenericRelation(ResourceFile, content_type_field='logical_file_content_type',
                            object_id_field='logical_file_object_id')
    # the dataset name will allow us to identify a logical file group on user interface
    dataset_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        abstract = True

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        # can upload any file types - subclass needs to override this
        return [".*"]

    @classmethod
    def get_allowed_storage_file_types(cls):
        # can store any file types - subclass needs to override this
        return [".*"]

    @classmethod
    def type_name(cls):
        return cls.__name__

    @property
    def has_metadata(self):
        return hasattr(self, 'metadata')

    def logical_delete(self, user):
        # deletes the logical file as well as all resource files associated with the logical file
        from hs_core.hydroshare.resource import delete_resource_file
        self.delete_metadata()
        # delete all resource files associated with this instance of logical file
        for f in self.files.all():
            delete_resource_file(f.resource.short_id, f.id, user,
                                 delete_logical_file=False)

        super(AbstractLogicalFile, self).delete()

    def delete_metadata(self):
        if self.has_metadata:
            self.metadata.delete_all_elements()
            self.metadata.delete()


