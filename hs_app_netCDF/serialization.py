
import rdflib

from hs_core.serialization import GenericResourceMeta


class NetcdfResourceMeta(GenericResourceMeta):
    """
    Lightweight class for representing metadata of NetcdfResource instances.
    """
    def __init__(self):
        super(NetcdfResourceMeta, self).__init__()

        self.variables = []
        self.spatial_reference = None

    def _read_resource_metadata(self):
        pass

    def write_metadata_to_resource(self, resource):
        """
        Write metadata to resource

        :param resource: NetcdfResource instance
        """
        pass
