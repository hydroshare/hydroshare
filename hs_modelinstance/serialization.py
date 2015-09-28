import rdflib

from hs_core.serialization import GenericResourceMeta


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
            has_model_output_lit = self._rmeta_graph.value(o, hsterms.IncludesModelOutput)
            if has_model_output_lit is None:
                msg = "IncludesModelOutput for ModelOutput was not found for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.has_model_output = str(has_model_output_lit) == 'Yes'
        # Get ExecutedBy
        for s, p, o in self._rmeta_graph.triples((None, hsterms.ExecutedBy, None)):
            # Get ModelProgramName
            executed_by_name_lit = self._rmeta_graph.value(o, hsterms.ModelProgramName)
            if executed_by_name_lit is not None:
                self.executed_by_name = str(executed_by_name_lit)
            # Get ModelProgramURL
            executed_by_uri_lit = self._rmeta_graph.value(o, hsterms.ModelProgramURL)
            if executed_by_uri_lit is not None:
                self.executed_by_uri = str(executed_by_uri_lit)
            if (self.executed_by_name is not None) ^ (self.executed_by_uri is not None):
                msg = "Both ModelProgramName and ModelProgramURL must be supplied if one is supplied."
                raise GenericResourceMeta.ResourceMetaException(msg)
        print("\t\t{0}".format(str(self)))

    def write_metadata_to_resource(self, resource):
        """
        Write metadata to resource

        :param resource: RasterResource instance
        """
        super(ModelInstanceResourceMeta, self).write_metadata_to_resource(resource)

        resource.metadata.create_element('ModelOutput',
                                         includes_output=self.has_model_output)