__author__ = 'th'
from . import Driver
from pandas import DataFrame

class CSVDriver(Driver):
    def get_dataset(self, *args, **kwargs):
        return DataFrame.from_csv(self.resource.resource_file.path, index_col=None)

driver = CSVDriver