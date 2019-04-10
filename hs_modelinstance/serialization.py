import os

import rdflib

from django.db import transaction

from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_core.serialization import GenericResourceMeta, HsDeserializationDependencyException
from hs_modelinstance.models import ExecutedBy


class ModelInstanceResourceMeta(GenericResourceMeta):

    def __init__(self):
        super(ModelInstanceResourceMeta, self).__init__()

        self.has_model_output = False
        self.executed_by_name = None   # Optional
        self.executed_by_uri = None  # Optional

    def __str__(self):
        msg = "ModelInstanceResourceMeta has_model_output: {has_model_output}, "
        msg += "executed_by_name: {executed_by_name}, executed_by_uri: {executed_by_uri}"
        msg = msg.format(has_model_output=self.has_model_output,
                         executed_by_name=self.executed_by_name,
                         executed_by_uri=self.executed_by_uri)
        return msg

    def __unicode__(self):
        return unicode(str(self))

    def _read_resource_metadata(self):
        super(ModelInstanceResourceMeta, self)._read_resource_metadata()

        print("--- ModelInstanceResource ---")

        hsterms = rdflib.namespace.Namespace('http://hydroshare.org/terms/')

        # Get ModelOutput
        for s, p, o in self._rmeta_graph.triples((None, hsterms.ModelOutput, None)):
            # Get has_model_output
            has_model_output_lit = self._rmeta_graph.value(o, hsterms.includesModelOutput)
            if has_model_output_lit is None:
                msg = "includesModelOutput for ModelOutput was not found for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.has_model_output = str(has_model_output_lit) == 'Yes'
        # Get ExecutedBy
        for s, p, o in self._rmeta_graph.triples((None, hsterms.ExecutedBy, None)):
            # Get modelProgramName
            executed_by_name_lit = self._rmeta_graph.value(o, hsterms.modelProgramName)
            if executed_by_name_lit is not None:
                self.executed_by_name = str(executed_by_name_lit)
            # Get modelProgramIdentifier
            executed_by_uri_lit = self._rmeta_graph.value(o, hsterms.modelProgramIdentifier)
            if executed_by_uri_lit is not None:
                self.executed_by_uri = str(executed_by_uri_lit)
            if (self.executed_by_name is not None) ^ (self.executed_by_uri is not None):
                msg = "Both modelProgramName and modelProgramIdentifier must be supplied if one is supplied."
                raise GenericResourceMeta.ResourceMetaException(msg)
        print("\t\t{0}".format(str(self)))

    @transaction.atomic
    def write_metadata_to_resource(self, resource):
        """
        Write metadata to resource

        :param resource: ModelInstanceResource instance
        """
        super(ModelInstanceResourceMeta, self).write_metadata_to_resource(resource)

        resource.metadata._model_output.update(includes_output=self.has_model_output)

        if self.executed_by_uri:
            uri_stripped = self.executed_by_uri.strip('/')
            short_id = os.path.basename(uri_stripped)
            if short_id == '':
                msg = "ExecutedBy URL {0} does not contain a model program resource ID, "
                msg += "for resource {1}"
                msg = msg.format(self.executed_by_uri, self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            # Make sure the resource specified by ExecutedBy exists
            try:
                executed_by_resource = get_resource_by_shortkey(short_id,
                                                                or_404=False)
            except BaseResource.DoesNotExist:
                msg = "ExecutedBy resource {0} does not exist.".format(short_id)
                raise HsDeserializationDependencyException(short_id, msg)
            executed_by = resource.metadata.executed_by
            if not executed_by:
                # Create
                ExecutedBy.create(content_object=resource.metadata,
                                  model_name=short_id)
            else:
                # Update
                ExecutedBy.update(executed_by.element_id,
                                  model_name=short_id)
