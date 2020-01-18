from django.contrib.postgres.fields import JSONField
from django.db import models

from base_model_program_instance import AbstractModelLogicalFile
from generic import GenericFileMetaDataMixin
from model_program import ModelProgramLogicalFile


class ModelInstanceFileMetaData(GenericFileMetaDataMixin):
    has_model_output = models.BooleanField(default=False)
    executed_by = models.ForeignKey(ModelProgramLogicalFile, null=True, blank=True, related_name="model_instances")
    # additional metadata in json format based on metadata schema of the related (executed_by)
    # model program aggregation
    metadata_json = JSONField(default=dict)


class ModelInstanceLogicalFile(AbstractModelLogicalFile):
    """ One file or more than one file in a specific folder can be part of this aggregation """

    # attribute to store type of model instance (SWAT, UEB etc)
    model_instance_type = models.CharField(max_length=255, default="Unknown Model Instance")
    metadata = models.OneToOneField(ModelInstanceFileMetaData, related_name="logical_file")
    data_type = "Model Instance"

    @classmethod
    def create(cls, resource):
        # this custom method MUST be used to create an instance of this class
        mi_metadata = ModelInstanceFileMetaData.objects.create(keywords=[])
        # Note we are not creating the logical file record in DB at this point
        # the caller must save this to DB
        return cls(metadata=mi_metadata, resource=resource)

    @staticmethod
    def get_aggregation_display_name():
        return 'Model Instance Content: One or more files with specific metadata'

    @staticmethod
    def get_aggregation_type_name():
        return "ModelInstanceAggregation"

    # used in discovery faceting to aggregate native and composite content types
    def get_discovery_content_type(self):
        """Return a human-readable content type for discovery.
        This must agree between Composite Types and native types).
        """
        return self.model_instance_type
