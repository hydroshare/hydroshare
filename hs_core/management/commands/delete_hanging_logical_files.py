"""Removes hanging LogicalFiles in composite resources.   Hanging LogicalFiles do not have a
Resource nor reference any files.
"""

from django.core.management.base import BaseCommand

from hs_file_types.models.generic import GenericLogicalFile
from hs_file_types.models.geofeature import GeoFeatureLogicalFile
from hs_file_types.models.netcdf import NetCDFLogicalFile
from hs_file_types.models.raster import GeoRasterLogicalFile
from hs_file_types.models.reftimeseries import RefTimeseriesLogicalFile
from hs_file_types.models.timeseries import TimeSeriesLogicalFile


def delete_hanging_logical_files(logical_files):
    count = 0
    for file in logical_files:
        if not file.files.all() or not hasattr(file, 'resource'):
            file.delete()
            count = count + 1
    return count


class Command(BaseCommand):
    help = "Removes Logical Files without a resource and a file"

    def handle(self, *args, **options):
        count = delete_hanging_logical_files(GenericLogicalFile.objects.all())
        print(">> {} GenericLogicalFiles deleted".format(count))
        count = delete_hanging_logical_files(GeoFeatureLogicalFile.objects.all())
        print(">> {} GeoFeatureLogicalFile deleted".format(count))
        count = delete_hanging_logical_files(NetCDFLogicalFile.objects.all())
        print(">> {} NetCDFLogicalFile deleted".format(count))
        count = delete_hanging_logical_files(GeoRasterLogicalFile.objects.all())
        print(">> {} GeoRasterLogicalFile deleted".format(count))
        count = delete_hanging_logical_files(RefTimeseriesLogicalFile.objects.all())
        print(">> {} RefTimeseriesLogicalFile deleted".format(count))
        count = delete_hanging_logical_files(TimeSeriesLogicalFile.objects.all())
        print(">> {} TimeSeriesLogicalFile deleted".format(count))
