
from hs_core.serialization import GenericResourceMeta

class ModelInstanceResourceMeta(GenericResourceMeta):

    def __init__(self):
        super(ModelInstanceResourceMeta, self).__init__()

    def _read_resource_metadata(self):
        super(ModelInstanceResourceMeta, self)._read_resource_metadata()

    def write_metadata_to_resource(self, resource):
        """
        Write metadata to resource

        :param resource: RasterResource instance
        """
        super(ModelInstanceResourceMeta, self).write_metadata_to_resource(resource)
