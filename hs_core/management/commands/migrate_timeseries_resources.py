import logging

from django.core.management.base import BaseCommand

from hs_app_timeseries.models import TimeSeriesResource
from hs_core.hydroshare import current_site_url, set_dirty_bag_flag
from hs_core.models import CoreMetaData, Coverage
from hs_file_types.models import TimeSeriesLogicalFile
from ..utils import migrate_core_meta_elements


class Command(BaseCommand):
    help = "Convert all timeseries resources to composite resource"

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        resource_counter = 0
        to_resource_type = 'CompositeResource'
        msg = "THERE ARE CURRENTLY {} TIMESERIES RESOURCES PRIOR TO CONVERSION.".format(
            TimeSeriesResource.objects.all().count())
        logger.info(msg)
        print(">> {}".format(msg))

        for ts_res in TimeSeriesResource.objects.all():
            # check resource exists on irods
            istorage = ts_res.get_irods_storage()
            if not istorage.exists(ts_res.root_path):
                err_msg = "Timeseries resource not found in irods (ID: {})".format(ts_res.short_id)
                logger.error(err_msg)
                print("Error:>> {}".format(err_msg))
                # skip this timeseries resource for migration
                continue

            sqlite_file = None
            res_file_count = ts_res.files.count()
            if res_file_count == 1 or res_file_count == 2:
                for res_file in ts_res.files.all():
                    if res_file.extension.lower() == '.sqlite':
                        sqlite_file = res_file

            create_ts_aggregation = sqlite_file is not None
            if create_ts_aggregation:
                # check resource files exist on irods
                file_missing = False
                for res_file in ts_res.files.all():
                    file_path = res_file.public_path
                    if not istorage.exists(file_path):
                        err_msg = "File path not found in irods:{}".format(file_path)
                        logger.error(err_msg)
                        err_msg = "Failed to convert timeseries resource (ID: {}). " \
                                  "Resource file is missing on irods".format(ts_res.short_id)
                        print("Error:>> {}".format(err_msg))
                        file_missing = True
                        break
                if file_missing:
                    # skip this corrupt timeseries resource for migration
                    continue

            # change the resource_type
            ts_metadata_obj = ts_res.metadata
            ts_res.resource_type = to_resource_type
            ts_res.content_model = to_resource_type.lower()
            ts_res.save()
            # get the converted resource object - CompositeResource
            comp_res = ts_res.get_content_model()

            # set CoreMetaData object for the composite resource
            core_meta_obj = CoreMetaData.objects.create()
            comp_res.content_object = core_meta_obj

            # migrate timeseries resource core metadata elements to composite resource
            migrate_core_meta_elements(ts_metadata_obj, comp_res)

            # update url attribute of the metadata 'type' element
            type_element = comp_res.metadata.type
            type_element.url = '{0}/terms/{1}'.format(current_site_url(), to_resource_type)
            type_element.save()
            if create_ts_aggregation:
                # create a Timeseries aggregation
                ts_aggr = None
                try:
                    ts_aggr = TimeSeriesLogicalFile.create(resource=comp_res)
                except Exception as ex:
                    err_msg = 'Failed to create Timeseries aggregation for resource (ID: {})'
                    err_msg = err_msg.format(ts_res.short_id)
                    err_msg = err_msg + '\n' + ex.message
                    logger.error(err_msg)
                    print("Error:>> {}".format(err_msg))

                if ts_aggr is not None:
                    # set aggregation dataset title
                    ts_aggr.dataset_name = comp_res.metadata.title.value
                    ts_aggr.save()
                    # make the res files part of the aggregation
                    for res_file in comp_res.files.all():
                        ts_aggr.add_resource_file(res_file)

                    # migrate timeseries specific metadata to aggregation
                    for site in ts_metadata_obj.sites:
                        site.content_object = ts_aggr.metadata
                        site.save()
                    for variable in ts_metadata_obj.variables:
                        variable.content_object = ts_aggr.metadata
                        variable.save()
                    for method in ts_metadata_obj.methods:
                        method.content_object = ts_aggr.metadata
                        method.save()
                    for proc_level in ts_metadata_obj.processing_levels:
                        proc_level.content_object = ts_aggr.metadata
                        proc_level.save()
                    for ts_result in ts_metadata_obj.time_series_results:
                        ts_result.content_object = ts_aggr.metadata
                        ts_result.save()

                    # create aggregation level coverage elements
                    for coverage in comp_res.metadata.coverages.all():
                        aggr_coverage = Coverage()
                        aggr_coverage.type = coverage.type
                        aggr_coverage._value = coverage._value
                        aggr_coverage.content_object = ts_aggr.metadata
                        aggr_coverage.save()

                    utc_offset = ts_metadata_obj.utc_offset
                    if utc_offset:
                        utc_offset.content_object = ts_aggr.metadata
                        utc_offset.save()

                    ts_aggr.metadata.value_counts = ts_metadata_obj.value_counts
                    ts_aggr.metadata.save()

                    # create aggregation level keywords
                    keywords = [sub.value for sub in comp_res.metadata.subjects.all()]
                    ts_aggr.metadata.keywords = keywords
                    # set aggregation metadata dirty status to that of the timeseries resource
                    # metadata dirty status - this would trigger netcdf file update for the
                    # new aggregation if metadata is dirty
                    ts_aggr.metadata.is_dirty = ts_metadata_obj.is_dirty
                    ts_aggr.metadata.save()
                    # create aggregation level xml files
                    ts_aggr.create_aggregation_xml_documents()
                    msg = 'One Timeseries aggregation was created in resource (ID: {})'
                    msg = msg.format(comp_res.short_id)
                    logger.info(msg)

            comp_res.save()
            # set resource to dirty so that resource level xml files (resource map and
            # metadata xml files) will be re-generated as part of next bag download
            try:
                set_dirty_bag_flag(comp_res)
            except Exception as ex:
                err_msg = 'Failed to set bag flag dirty for the converted resource (ID: {})'
                err_msg = err_msg.format(ts_res.short_id)
                err_msg = err_msg + '\n' + ex.message
                logger.error(err_msg)
                print("Error:>> {}".format(err_msg))

            resource_counter += 1
            # delete the instance of TimeSeriesMetaData that was part of the original
            # timeseries resource
            ts_metadata_obj.delete()
            msg = 'Timeseries resource (ID: {}) was converted to Composite Resource type'
            msg = msg.format(comp_res.short_id)
            logger.info(msg)

        msg = "{} TIMESERIES RESOURCES WERE CONVERTED TO COMPOSITE RESOURCE.".format(
            resource_counter)
        logger.info(msg)
        print(">> {}".format(msg))
        msg = "THERE ARE CURRENTLY {} TIMESERIES RESOURCES AFTER CONVERSION.".format(
            TimeSeriesResource.objects.all().count())
        logger.info(msg)
        if TimeSeriesResource.objects.all().count() > 0:
            msg = "NOT ALL TIMESERIES RESOURCES WERE CONVERTED TO COMPOSITE RESOURCE TYPE"
            logger.error(msg)
        print(">> {}".format(msg))
