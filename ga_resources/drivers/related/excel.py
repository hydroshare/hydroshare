__author__ = 'th'
from . import Driver
from pandas import ExcelFile


class ExcelDriver(Driver):
    def get_dataset(self, *args, **kwargs):
        xls = ExcelFile(self.resource.resource_file.path)
        if 'sheet' in kwargs:
            return xls.parse(kwargs['sheet'])
        return xls.parse("Sheet1")

driver = ExcelDriver