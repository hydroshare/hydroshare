import logging

from django.core.management.base import BaseCommand

from hs_core.hydroshare import current_site_url, set_dirty_bag_flag
from hs_core.models import CoreMetaData, Coverage

from hs_app_netCDF.models import NetcdfResource
from hs_file_types.models import NetCDFLogicalFile
from ..utils import migrate_core_meta_elements


class Command(BaseCommand):
    help = "Convert all multidimensional resources to composite resource"

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        resource_counter = 0
        to_resource_type = 'CompositeResource'
        msg = "THERE ARE CURRENTLY {} MULTIDIMENSIONAL RESOURCES PRIOR TO CONVERSION.".format(
            NetcdfResource.objects.all().count())
        logger.info(msg)
        print(">> {}".format(msg))

        for nc_res in NetcdfResource.objects.all():
            # check resource exists on irods
            istorage = nc_res.get_irods_storage()
            if not istorage.exists(nc_res.root_path):
                err_msg = "NetCDF resource not found in irods (ID: {})".format(nc_res.short_id)
                logger.error(err_msg)
                print("Error:>> {}".format(err_msg))
                # skip this netcdf resource for migration
                continue

            # get the nc file name which needs to be used to create a new folder
            nc_file = None
            txt_file = None
            if nc_res.files.count() == 2:
                for res_file in nc_res.files.all():
                    if res_file.extension.lower() == '.nc':
                        nc_file = res_file
                    elif res_file.file_name.lower().endswith('header_info.txt'):
                        txt_file = res_file

            create_nc_aggregation = nc_file is not None and txt_file is not None
            if create_nc_aggregation:
                # check resource files exist on irods
                file_missing = False
                for res_file in nc_res.files.all():
                    file_path = res_file.public_path
                    if not istorage.exists(file_path):
                        err_msg = "File path not found in irods:{}".format(file_path)
                        logger.error(err_msg)
                        err_msg = "Failed to convert netcdf resource (ID: {}). Resource file is " \
                                  "missing on irods".format(nc_res.short_id)
                        print("Error:>> {}".format(err_msg))
                        file_missing = True
                        break
                if file_missing:
                    # skip this corrupt netcdf resource for migration
                    continue

            # change the resource_type
            nc_metadata_obj = nc_res.metadata
            nc_res.resource_type = to_resource_type
            nc_res.content_model = to_resource_type.lower()
            nc_res.save()
            # get the converted resource object - CompositeResource
            comp_res = nc_res.get_content_model()

            # set CoreMetaData object for the composite resource
            core_meta_obj = CoreMetaData.objects.create()
            comp_res.content_object = core_meta_obj
            # migrate netcdf resource core metadata elements to composite resource
            migrate_core_meta_elements(nc_metadata_obj, comp_res)

            # update url attribute of the metadata 'type' element
            type_element = comp_res.metadata.type
            type_element.url = '{0}/terms/{1}'.format(current_site_url(), to_resource_type)
            type_element.save()
            if create_nc_aggregation:
                # create a NetCDF aggregation
                nc_aggr = None
                try:
                    nc_aggr = NetCDFLogicalFile.create(resource=comp_res)
                except Exception as ex:
                    err_msg = 'Failed to create NetCDF aggregation for resource (ID: {})'
                    err_msg = err_msg.format(nc_res.short_id)
                    err_msg = err_msg + '\n' + ex.message
                    logger.error(err_msg)
                    print("Error:>> {}".format(err_msg))

                if nc_aggr is not None:
                    # set aggregation dataset title
                    nc_aggr.dataset_name = comp_res.metadata.title.value
                    nc_aggr.save()
                    # make the res files part of the aggregation
                    for res_file in comp_res.files.all():
                        nc_aggr.add_resource_file(res_file)

                    # migrate netcdf specific metadata to aggregation
                    for variable in nc_metadata_obj.variables.all():
                        variable.content_object = nc_aggr.metadata
                        variable.save()

                    # create aggregation level coverage elements
                    for coverage in comp_res.metadata.coverages.all():
                        aggr_coverage = Coverage()
                        aggr_coverage.type = coverage.type
                        aggr_coverage._value = coverage._value
                        aggr_coverage.content_object = nc_aggr.metadata
                        aggr_coverage.save()

                    org_coverage = nc_metadata_obj.originalCoverage
                    if org_coverage:
                        org_coverage.content_object = nc_aggr.metadata
                        org_coverage.save()

                    # create aggregation level keywords
                    keywords = [sub.value for sub in comp_res.metadata.subjects.all()]
                    nc_aggr.metadata.keywords = keywords
                    # set aggregation metadata dirty status to that of the netcdf resource metadata
                    # dirty status - this would trigger netcdf file update for the new aggregation
                    # if metadata is dirty
                    nc_aggr.metadata.is_dirty = nc_metadata_obj.is_dirty
                    nc_aggr.metadata.save()
                    # create aggregation level xml files
                    nc_aggr.create_aggregation_xml_documents()
                    msg = 'One Multidimensional aggregation was created in resource (ID: {})'
                    msg = msg.format(comp_res.short_id)
                    logger.info(msg)

            # set resource to dirty so that resource level xml files (resource map and
            # metadata xml files) will be re-generated as part of next bag download
            comp_res.save()
            try:
                set_dirty_bag_flag(comp_res)
            except Exception as ex:
                err_msg = 'Failed to set bag flag dirty for the converted resource (ID: {})'
                err_msg = err_msg.format(nc_res.short_id)
                err_msg = err_msg + '\n' + ex.message
                logger.error(err_msg)
                print("Error:>> {}".format(err_msg))

            resource_counter += 1
            # delete the instance of NetCdfMetaData that was part of the original netcdf resource
            nc_metadata_obj.delete()
            msg = 'Multidimensional resource (ID: {}) was converted to Composite Resource type'
            msg = msg.format(comp_res.short_id)
            logger.info(msg)

        msg = "{} MULTIDIMENSIONAL RESOURCES WERE CONVERTED TO COMPOSITE RESOURCE.".format(
            resource_counter)
        logger.info(msg)
        print(">> {}".format(msg))
        msg = "THERE ARE CURRENTLY {} MULTIDIMENSIONAL RESOURCES AFTER CONVERSION.".format(
            NetcdfResource.objects.all().count())
        logger.info(msg)
        if NetcdfResource.objects.all().count() > 0:
            msg = "NOT ALL MULTIDIMENSIONAL RESOURCES WERE CONVERTED TO COMPOSITE RESOURCE TYPE"
            logger.error(msg)
        print(">> {}".format(msg))
