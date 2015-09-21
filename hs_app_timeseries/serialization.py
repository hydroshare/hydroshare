
from hs_core.serialization import GenericResourceMeta


class TimeSeriesResourceMeta(GenericResourceMeta):
    """
    Lightweight class for representing metadata of TimeSeriesResource instances.
    """

    def __init__(self):
        super(TimeSeriesResourceMeta, self).__init__()

    def _read_resource_metadata(self):
        super(TimeSeriesResourceMeta, self)._read_resource_metadata()

    def write_metadata_to_resource(self, resource):
        super(TimeSeriesResourceMeta, self).write_metadata_to_resource(resource)
