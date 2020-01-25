from django.contrib.postgres.fields import JSONField
from django.core.exceptions import PermissionDenied
from django.db import models

from base_model_program_instance import AbstractModelLogicalFile
from generic import GenericFileMetaDataMixin
from model_program import ModelProgramLogicalFile


class ModelInstanceFileMetaData(GenericFileMetaDataMixin):
    has_model_output = models.BooleanField(default=False)
    executed_by = models.ForeignKey(ModelProgramLogicalFile, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="model_instances")
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

    def set_link_to_model_program(self, user, model_prog_aggr):
        """Creates a link to the specified model program aggregation *model_prog_aggr* using the
        executed_by metadata field.

        :param  user: user who is associating this (self) model instance aggregation to a model program aggregation
        :param  model_prog_aggr: an instance of ModelProgramLogicalFile to be associated with
        :raises PermissionDenied exception if the user does not have edit permission for the resource to which this
        model instance aggregation belongs or doesn't have view permission for the resource that contains the model
        program aggregation.
        """

        # check if user has edit permission for the resources
        mi_res = self.resource
        mp_res = model_prog_aggr.resource
        authorized = user.uaccess.can_change_resource(mi_res)
        if not authorized:
            raise PermissionDenied("You don't have permission to edit resource(ID:{})".format(mi_res.short_id))
        if mi_res.short_id != mp_res.short_id:
            authorized = user.uaccess.can_view_resource(mp_res)
            if not authorized:
                raise PermissionDenied("You don't have permission to view resource(ID:{})".format(mp_res.short_id))

        self.metadata.executed_by = model_prog_aggr
        self.metadata.save()
