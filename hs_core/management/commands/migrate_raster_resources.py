import logging

from django.core.management.base import BaseCommand

from hs_core.hydroshare import current_site_url, set_dirty_bag_flag
from hs_core.models import CoreMetaData, Coverage
from hs_geo_raster_resource.models import RasterResource
from hs_file_types.models import GeoRasterLogicalFile
from ..utils import migrate_core_meta_elements


class Command(BaseCommand):
    help = "Convert all raster resources to composite resource"

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        resource_counter = 0
        create_raster_aggregation = False
        to_resource_type = 'CompositeResource'
        msg = "THERE ARE CURRENTLY {} RASTER RESOURCES PRIOR TO CONVERSION.".format(
            RasterResource.objects.all().count())
        logger.info(msg)
        print(">> {}".format(msg))

        for rast_res in RasterResource.objects.all():
            # check resource exists on irods
            istorage = rast_res.get_irods_storage()
            create_raster_aggregation = False
            if not istorage.exists(rast_res.root_path):
                err_msg = "Raster resource not found in irods (ID: {})".format(rast_res.short_id)
                logger.error(err_msg)
                print("Error:>> {}".format(err_msg))
                # skip this raster resource
                continue

            if rast_res.metadata.cellInformation is not None:
                # get the vrt file name which needs to be used to create a new folder for
                # raster aggregation
                vrt_file = None
                for res_file in rast_res.files.all():
                    if res_file.extension.lower() == '.vrt':
                        vrt_file = res_file
                        break

                create_raster_aggregation = vrt_file is not None
                if create_raster_aggregation:
                    # check resource files exist on irods
                    file_missing = False
                    for res_file in rast_res.files.all():
                        file_path = res_file.public_path
                        if not istorage.exists(file_path):
                            err_msg = "File path not found in irods:{}".format(file_path)
                            logger.error(err_msg)
                            err_msg = "Failed to convert raster resource (ID: {}). " \
                                      "Resource file is missing on irods".format(rast_res.short_id)
                            print("Error:>> {}".format(err_msg))
                            file_missing = True
                            break
                    if file_missing:
                        # skip this corrupt raster resource for migration
                        continue

            # change the resource_type
            ras_metadata_obj = rast_res.metadata
            rast_res.resource_type = to_resource_type
            rast_res.content_model = to_resource_type.lower()
            rast_res.save()
            # get the converted resource object - CompositeResource
            comp_res = rast_res.get_content_model()

            # set CoreMetaData object for the composite resource
            core_meta_obj = CoreMetaData.objects.create()
            comp_res.content_object = core_meta_obj
            # migrate raster resource core metadata elements to composite resource
            migrate_core_meta_elements(ras_metadata_obj, comp_res)

            # update url attribute of the metadata 'type' element
            type_element = comp_res.metadata.type
            type_element.url = '{0}/terms/{1}'.format(current_site_url(), to_resource_type)
            type_element.save()
            if create_raster_aggregation:
                # create a Raster aggregation
                ras_aggr = None
                try:
                    ras_aggr = GeoRasterLogicalFile.create(resource=comp_res)
                except Exception as ex:
                    err_msg = 'Failed to create raster aggregation for resource (ID: {})'
                    err_msg = err_msg.format(rast_res.short_id)
                    err_msg = err_msg + '\n' + ex.message
                    logger.error(err_msg)
                    print("Error:>> {}".format(err_msg))

                if ras_aggr is not None:
                    # set aggregation dataset title
                    ras_aggr.dataset_name = comp_res.metadata.title.value
                    ras_aggr.save()
                    # make the res files part of the aggregation
                    for res_file in comp_res.files.all():
                        ras_aggr.add_resource_file(res_file)

                    # migrate raster specific metadata to aggregation
                    for bandinfo in ras_metadata_obj.bandInformations:
                        bandinfo.content_object = ras_aggr.metadata
                        bandinfo.save()

                    # create aggregation level spatial coverage element
                    # note - the resource level spatial coverage which is a core metadata
                    # element gets populated as part of raster resource creation
                    spatial_coverage = comp_res.metadata.spatial_coverage
                    if spatial_coverage:
                        aggr_coverage = Coverage()
                        aggr_coverage.type = spatial_coverage.type
                        aggr_coverage._value = spatial_coverage._value
                        aggr_coverage.content_object = ras_aggr.metadata
                        aggr_coverage.save()

                    org_coverage = ras_metadata_obj.originalCoverage
                    if org_coverage:
                        org_coverage.content_object = ras_aggr.metadata
                        org_coverage.save()

                    cell_info = ras_metadata_obj.cellInformation
                    if cell_info:
                        cell_info.content_object = ras_aggr.metadata
                        cell_info.save()

                    # create aggregation level xml files
                    ras_aggr.create_aggregation_xml_documents()
                    msg = 'One Raster aggregation was created in resource (ID: {})'
                    msg = msg.format(comp_res.short_id)
                    logger.info(msg)
            # set resource to dirty so that resource level xml files (resource map and
            # metadata xml files) will be re-generated as part of next bag download
            comp_res.save()
            try:
                set_dirty_bag_flag(comp_res)
            except Exception as ex:
                err_msg = 'Failed to set bag flag dirty for the converted resource (ID: {})'
                err_msg = err_msg.format(rast_res.short_id)
                err_msg = err_msg + '\n' + ex.message
                logger.error(err_msg)
                print("Error:>> {}".format(err_msg))

            resource_counter += 1
            # delete the instance of RasterMetaData that was part of the original raster resource
            ras_metadata_obj.delete()
            msg = 'Raster resource (ID: {}) was converted to Composite Resource type'
            msg = msg.format(comp_res.short_id)
            logger.info(msg)

        msg = "{} RASTER RESOURCES WERE CONVERTED TO COMPOSITE RESOURCE.".format(
            resource_counter)
        logger.info(msg)
        print(">> {}".format(msg))
        msg = "THERE ARE CURRENTLY {} RASTER RESOURCES AFTER CONVERSION.".format(
            RasterResource.objects.all().count())
        logger.info(msg)
        if RasterResource.objects.all().count() > 0:
            msg = "NOT ALL RASTER RESOURCES WERE CONVERTED TO COMPOSITE RESOURCE TYPE"
            logger.error(msg)
        print(">> {}".format(msg))
