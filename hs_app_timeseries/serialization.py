
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

    class Site(object):
        site_code = None
        site_name = None
        elevation_m = None
        elevation_datum = None
        site_type = None

        def __init__(self):
            pass

    class Variable(object):
        variable_code = None
        variable_name = None
        variable_type = None
        no_data_value = None
        variable_definition = None
        speciation = None

        def __init__(self):
            pass

    class Method(object):
        method_code = None
        method_name = None
        method_type = None
        method_description = None
        method_link = None

        def __init__(self):
            pass

    class ProcessingLevel(object):
        processing_level_code = None
        definition = None
        explanation = None

        def __init__(self):
            pass

    class TimeSeriesResult(object):
        units_type = None
        units_name = None
        units_abbreviation = None
        status = None
        sample_medium = None
        value_count = None
        aggregation_statistics = None

        def __init__(self):
            pass
