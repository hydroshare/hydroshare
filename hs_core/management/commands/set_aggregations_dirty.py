import os

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError

from hs_core.hydroshare import get_resource_by_shortkey, set_dirty_bag_flag
from hs_file_types.models import (
    GenericLogicalFile,
    FileSetLogicalFile,
    NetCDFLogicalFile,
    GeoRasterLogicalFile,
    GeoFeatureLogicalFile,
    TimeSeriesLogicalFile,
    RefTimeseriesLogicalFile,
    ModelProgramLogicalFile,
    ModelInstanceLogicalFile
)


class Command(BaseCommand):
    help = "Sets metadata dirty for all aggregations of a specific aggregation type, or all aggregations of a " \
           "given composite resource"

    def add_arguments(self, parser):

        # when resource id is specified all aggregations in that resource will be set metadata to dirty
        parser.add_argument('--resource_id', type=str,
                            help=('The existing id (short_id) of the resource. Required when aggr_type '
                                  'is not provided.'))
        # when aggr_type is specified, all aggregations of that type will be set to metadata dirty - this action
        # is across many resources
        parser.add_argument('--aggr_type', type=str,
                            help=('Name of the aggregation type for which metadata '
                                  'to be set dirty. Required when resource_id is not provided.'))

    def handle(self, *args, **options):
        valid_aggr_types = {GenericLogicalFile.type_name(): GenericLogicalFile,
                            FileSetLogicalFile.type_name(): FileSetLogicalFile,
                            NetCDFLogicalFile.type_name(): NetCDFLogicalFile,
                            GeoRasterLogicalFile.type_name(): GeoRasterLogicalFile,
                            GeoFeatureLogicalFile.type_name(): GeoFeatureLogicalFile,
                            TimeSeriesLogicalFile.type_name(): TimeSeriesLogicalFile,
                            RefTimeseriesLogicalFile.type_name(): RefTimeseriesLogicalFile,
                            ModelProgramLogicalFile.type_name(): ModelProgramLogicalFile,
                            ModelInstanceLogicalFile.type_name(): ModelInstanceLogicalFile
                            }
        res = None
        if options['resource_id']:
            res_id = options['resource_id']
            try:
                res = get_resource_by_shortkey(res_id, or_404=False)
            except ObjectDoesNotExist:
                raise CommandError(f"No Resource was found for id: {res_id}")
            if res.resource_type != "CompositeResource":
                raise CommandError(f"Specified resource (ID:{res_id}) is not a Composite Resource")

        if not options['aggr_type'] and res is None:
            raise CommandError('aggr_type argument is required when resource_id is not provided')
        if res is not None and options['aggr_type']:
            raise CommandError("aggr_type can't be used when resource_id is specified. Use only one of these "
                               "two arguments")

        if options['aggr_type']:
            aggr_type = options['aggr_type']
            if aggr_type not in valid_aggr_types:
                valid_aggr_types_str = ", ".join(valid_aggr_types.keys())
                err_msg = f"Invalid aggr_type:{aggr_type}\n Allowed aggregation types are:{valid_aggr_types_str}"
                raise CommandError(err_msg)

        if res is None:
            # all aggregations of the specified type will be set metadata as dirty - this action is
            # across many resources
            aggr_class = valid_aggr_types[aggr_type]
            aggr_count = aggr_class.objects.count()
            log_msg = f"{aggr_count} {aggr_type} aggregation(s) will be set metadata as dirty.\n"
            print(log_msg)
            aggr_count = 1
            for aggr in aggr_class.objects.all().iterator():
                aggr.metadata.is_dirty = True
                aggr.metadata.save()
                set_dirty_bag_flag(aggr.resource)
                aggr_path = os.path.join(aggr.resource.file_path, aggr.aggregation_name)
                log_msg = f"{aggr_count}. Metadata was set dirty for aggregation:{aggr_path}"
                print(log_msg)
                aggr_count += 1
        else:
            # all aggregations in the specified resource will be set metadata as dirty
            aggregations = [aggr for aggr in res.logical_files]
            aggr_count = len(aggregations)
            if aggr_count == 0:
                log_msg = f"There are no aggregations in this resource:{res_id}"
                print(log_msg)
                return
            log_msg = f"{aggr_count} aggregation(s) in resource:{res_id} will be set metadata as dirty.\n"
            print(log_msg)
            set_dirty_bag_flag(res)
            aggr_count = 1
            for aggr in aggregations:
                aggr.metadata.is_dirty = True
                aggr.metadata.save()
                aggr_path = os.path.join(aggr.resource.file_path, aggr.aggregation_name)
                log_msg = f"{aggr_count}. Metadata was set dirty for {aggr.type_name()} aggregation:{aggr_path}"
                print(log_msg)
                aggr_count += 1
