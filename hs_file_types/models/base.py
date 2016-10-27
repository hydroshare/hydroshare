from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from hs_core.models import AbstractMetaDataElement
from django.contrib.postgres.fields import HStoreField

from hs_core.models import ResourceFile


class AbstractFileMetaData(models.Model):
    """ base class for HydroShare file type metadata """

    # kye/value metadata
    extra_metadata = HStoreField(default={})

    class Meta:
        abstract = True

    def delete_all_elements(self):
        # subclass must implement
        raise NotImplementedError

    def get_html(self):
        # subclass must implement
        # returns a string representing html code for display of metadata in view mode
        raise NotImplementedError

    @classmethod
    def get_supported_element_names(cls):
        # subclass must implement
        # returns a list of metadata element names supported by this metadata group
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

    @classmethod
    def validate_element_data(cls, request, element_name):
        raise NotImplementedError

class AbstractLogicalFile(models.Model):
    """ base class for HydroShare file types """

    # mime type of the dominant file in the group - not sure if we need this
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
        # any file can be part of this logical file group - subclass needs to override this
        return [".*"]

    @classmethod
    def get_allowed_storage_file_types(cls):
        # can store any file types in this logical file group - subclass needs to override this
        return [".*"]

    @classmethod
    def type_name(cls):
        return cls.__name__

    @property
    def has_metadata(self):
        return hasattr(self, 'metadata')

    @property
    def size(self):
        # get total size (in bytes) of all files in this file type
        return sum([f.size for f in self.files.all()])

    @property
    def resource(self):
        return self.files.all().first().resource

    def logical_delete(self, user):
        # deletes the logical file as well as all resource files associated with this logical file
        from hs_core.hydroshare.resource import delete_resource_file
        self.delete_metadata()
        # delete all resource files associated with this instance of logical file
        for f in self.files.all():
            delete_resource_file(f.resource.short_id, f.id, user,
                                 delete_logical_file=False)

        # delete logical file first then delete the associated metadata file object
        metadata = self.metadata
        super(AbstractLogicalFile, self).delete()
        metadata.delete()

    def delete_metadata(self):
        # delete all metadata associated with this file type
        if self.has_metadata:
            self.metadata.delete_all_elements()



