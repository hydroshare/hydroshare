from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from hs_core.models import AbstractMetaDataElement
from django.contrib.postgres.fields import HStoreField

from hs_core.models import ResourceFile


class AbstractFileMetaData(models.Model):
    # base class for file metadata, shared among all supported HS file types
    size = models.IntegerField()
    # mime type of the dominant file in the group
    mime_type = models.CharField(max_length=1000)
    extra_metadata = HStoreField(default={})

    class Meta:
        abstract = True

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
                                  "supported in core metadata elements."
                                  % element_model_name)

        unsupported_element_error = "Metadata element type:%s is not supported." \
                                    % element_model_name
        try:
            model_type = ContentType.objects.get(app_label=self._meta.app_label,
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
    # the hydroshare file type to be used for a group of files
    hs_file_type = models.CharField(max_length=1000, default="Generic")
    # total size of all files in the logical group
    size = models.IntegerField()
    resource_files = GenericRelation(ResourceFile)

    class Meta:
        abstract = True

    @property
    def get_allowed_uploaded_file_types(self):
        # can upload any file types
        return [".*"]

    @property
    def get_allowed_storage_file_types(self):
        # can store any file types
        return [".*"]

    def delete(self, using=None):
        if hasattr(self, 'metadata'):
            self.metadata.delete_all_elements()
            self.metadata.delete()
        # delete all resource files associated with this instance of logical file
        for f in self.resource_files:
            f.delete()


class GenericLogicalFile(AbstractLogicalFile):
    pass
