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
from hs_file_types.models.model_instance import ModelInstanceLogicalFile
from hs_file_types.models.model_program import ModelProgramLogicalFile
from hs_file_types.models.fileset import FileSetLogicalFile
from hs_file_types.models.csv import CSVLogicalFile


def delete_hanging_logical_files(logical_files):
    count = 0
    for lf in logical_files:
        if not hasattr(lf, 'resource'):
            lf.delete()
            count = count + 1
        elif not lf.files.all():
            if lf.is_fileset:
                # we allow fileset to not have any files
                continue
            elif lf.is_model_instance and lf.folder:
                # we allow model instance based on folder to not have any files
                continue
            lf.delete()
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
        count = delete_hanging_logical_files(ModelInstanceLogicalFile.objects.all())
        print(">> {} ModelInstanceLogicalFile deleted".format(count))
        count = delete_hanging_logical_files(ModelProgramLogicalFile.objects.all())
        print(">> {} ModelProgramLogicalFile deleted".format(count))
        count = delete_hanging_logical_files(FileSetLogicalFile.objects.all())
        print(">> {} FileSetLogicalFile deleted".format(count))
        count = delete_hanging_logical_files(CSVLogicalFile.objects.all())
        print(">> {} CSVLogicalFile deleted".format(count))
