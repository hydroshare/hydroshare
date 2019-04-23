import os
import logging

from django.core.management.base import BaseCommand

from hs_core.hydroshare import current_site_url, set_dirty_bag_flag
from hs_core.models import ResourceFile, CoreMetaData, Coverage
from hs_core.views.utils import rename_irods_file_or_folder_in_django
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

        for r_res in RasterResource.objects.all():
            if r_res.metadata.cellInformation is not None:
                # get the vrt file name which needs to be used to create a new folder for
                # raster aggregation
                vrt_file = None
                for res_file in r_res.files.all():
                    if res_file.extension.lower() == '.vrt':
                        vrt_file = res_file
                        break

                create_raster_aggregation = vrt_file is not None
                if create_raster_aggregation:
                    # create a new folder based on vrt file name
                    folder_name = vrt_file.file_name[:-4]
                    ResourceFile.create_folder(r_res, folder=folder_name)
                    # move the all the resource files to this new folder
                    istorage = r_res.get_irods_storage()
                    for res_file in r_res.files.all():
                        tgt_path = 'data/contents/{}/{}'.format(folder_name, res_file.file_name)
                        src_full_path = res_file.public_path
                        tgt_full_path = os.path.join(r_res.root_path, tgt_path)

                        istorage.moveFile(src_full_path, tgt_full_path)
                        rename_irods_file_or_folder_in_django(r_res, src_full_path, tgt_full_path)

            # change the resource_type
            ras_metadata_obj = r_res.metadata
            r_res.resource_type = to_resource_type
            r_res.content_model = to_resource_type.lower()
            r_res.save()
            # get the converted resource object - CompositeResource
            comp_res = r_res.get_content_model()

            # set CoreMetaData object for the composite resource
            core_meta_obj = CoreMetaData.objects.create()
            comp_res.content_object = core_meta_obj
            comp_res.save()
            # migrate raster resource core metadata elements to composite resource
            migrate_core_meta_elements(ras_metadata_obj, comp_res)

            # update url attribute of the metadata 'type' element
            type_element = comp_res.metadata.type
            type_element.url = '{0}/terms/{1}'.format(current_site_url(), to_resource_type)
            type_element.save()
            if create_raster_aggregation:
                # create a Raster aggregation
                ras_aggr = GeoRasterLogicalFile.create(resource=comp_res)
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
            set_dirty_bag_flag(comp_res)
            resource_counter += 1
            # delete the instance of NetCdfMetaData that was part of the original netcdf resource
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