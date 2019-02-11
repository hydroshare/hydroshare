import os
import logging

from django.core.management.base import BaseCommand

from hs_core.hydroshare import current_site_url, set_dirty_bag_flag
from hs_core.models import ResourceFile, CoreMetaData, Coverage
from hs_core.views.utils import rename_irods_file_or_folder_in_django
from hs_app_netCDF.models import NetcdfResource, NetcdfMetaData
from hs_file_types.models import NetCDFLogicalFile


class Command(BaseCommand):
    help = "Convert all multidimentional resources to composite resource"

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        resource_counter = 0
        to_resource_type = 'CompositeResource'
        msg = "THERE ARE CURRENTLY {} MULTIDIMENSIONAL RESOURCES PRIOR TO CONVERSION.".format(
            NetcdfResource.objects.all().count())
        logger.info(msg)
        print(">> {}".format(msg))
        print(">> There are currently {} NetCDFMetaData objects".format(
            NetcdfMetaData.objects.all().count()))
        for nc_res in NetcdfResource.objects.all():
            # get the nc file name which needs to be used to create a new folder
            nc_file = None
            txt_file = None
            bad_res_msg = ''
            if nc_res.files.count() == 2:
                for res_file in nc_res.files.all():
                    if res_file.extension.lower() == '.nc':
                        nc_file = res_file
                    elif res_file.file_name.lower().endswith('header_info.txt'):
                        txt_file = res_file

                # if nc_file is None:
                #     bad_res_msg = "NetCDF file is missing. Can't migrate resource (ID:{})"
            # else:
            #     bad_res_msg = "Resource doesn't contain the two expected files. " \
            #                   "Can't migrate resource (ID:{})"

            # if bad_res_msg:
            #     bad_res_msg = bad_res_msg.format(nc_res.short_id)
            #     logger.error(bad_res_msg)
            #     print("ERROR >> {}".format(bad_res_msg))
            #     continue
            create_nc_aggregation = nc_file is not None and txt_file is not None
            if create_nc_aggregation:
                # create a new folder based on nc file name
                folder_name = nc_file.file_name[:-3]
                ResourceFile.create_folder(nc_res, folder=folder_name)
                # move the the two resource files to this new folder
                istorage = nc_res.get_irods_storage()
                for res_file in nc_res.files.all():
                    tgt_path = 'data/contents/{}/{}'.format(folder_name, res_file.file_name)
                    src_full_path = res_file.public_path
                    tgt_full_path = os.path.join(nc_res.root_path, tgt_path)

                    istorage.moveFile(src_full_path, tgt_full_path)
                    rename_irods_file_or_folder_in_django(nc_res, src_full_path, tgt_full_path)

            # change the resource_type
            nc_metadata_obj = nc_res.metadata
            nc_res.resource_type = to_resource_type
            nc_res.content_model = to_resource_type.lower()
            nc_res.save()
            # get the converted resource object - CompositeResource
            comp_res = nc_res.get_content_model()
            print('>>1 Composite resource metadata type:{}'.format(type(comp_res.metadata)))

            # set CoreMetaData object for the composite resource
            comp_res.content_object = CoreMetaData()
            comp_res.save()
            title_element = nc_metadata_obj.title
            title_element.content_object = comp_res.metadata
            title_element.save()
            type_element = nc_metadata_obj.type
            type_element.content_object = comp_res.metadata
            type_element.save()
            lang_element = nc_metadata_obj.language
            lang_element.content_object = comp_res.metadata
            lang_element.save()
            rights_element = nc_metadata_obj.rights
            rights_element.content_object = comp_res.metadata
            rights_element.save()

            des_element = nc_metadata_obj.description
            if des_element:
                des_element.content_object = comp_res.metadata
                des_element.save()
            for creator in nc_metadata_obj.creators.all():
                creator.content_object = comp_res.metadata
                creator.save()
            for contributor in nc_metadata_obj.contributors.all():
                contributor.content_object = comp_res.metadata
                contributor.save()
            for subject in nc_metadata_obj.subjects.all():
                subject.content_object = comp_res.metadata
                subject.save()

            for coverage in nc_metadata_obj.coverages.all():
                coverage.content_object = comp_res.metadata
                coverage.save()
            print('>>2 Composite resource metadata type:{}'.format(type(comp_res.metadata)))
            # update url attribute of the metadata 'type' element
            type_element = comp_res.metadata.type
            type_element.url = '{0}/terms/{1}'.format(current_site_url(), to_resource_type)
            type_element.save()
            if create_nc_aggregation:
                # create a NetCDF aggregation
                nc_aggr = NetCDFLogicalFile.create(resource=comp_res)
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

                # need to create aggregation level coverage elements
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

                keywords = [sub.value for sub in comp_res.metadata.subjects.all()]
                nc_aggr.metadata.keywords = keywords
                # set aggregation metadata to dirty to force aggregation level xml file generation
                # upon resource/aggregation download
                # nc_aggr.metadata.is_dirty = True
                nc_aggr.metadata.save()
                # create aggregation level xml files
                nc_aggr.create_aggregation_xml_documents()
                msg = 'One NetCDF aggregation was created in resource (ID: {})'
                msg = msg.format(comp_res.short_id)
                logger.info(msg)
            # set resource to dirty so that resource level xml files (resource map and
            # metadata xml files) will be generated as part of next bag download
            set_dirty_bag_flag(comp_res)
            resource_counter += 1
            # delete the instance of NetCdfMetaData that was part of the original netcdf resource
            nc_metadata_obj.delete()

        msg = "{} MULTIDIMENSIONAL RESOURCES WERE CONVERTED TO COMPOSITE RESOURCE.".format(
            resource_counter)
        logger.info(msg)
        print(">> {}".format(msg))
        msg = "THERE ARE CURRENTLY {} MULTIDIMENSIONAL RESOURCES AFTER CONVERSION.".format(
            NetcdfResource.objects.all().count())
        logger.info(msg)
        print(">> {}".format(msg))
        print(">> There are currently {} NetCDFMetaData objects".format(
            NetcdfMetaData.objects.all().count()))