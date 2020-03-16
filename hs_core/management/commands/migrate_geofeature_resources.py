import logging

from django.core.management.base import BaseCommand

from hs_core.hydroshare import current_site_url, set_dirty_bag_flag
from hs_core.models import CoreMetaData, Coverage
from hs_file_types.models import GeoFeatureLogicalFile
from hs_geographic_feature_resource.models import GeographicFeatureResource
from ..utils import migrate_core_meta_elements


class Command(BaseCommand):
    help = "Convert all geofeature resources to composite resource"

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        resource_counter = 0
        to_resource_type = 'CompositeResource'
        msg = "THERE ARE CURRENTLY {} GEOFEATURE RESOURCES PRIOR TO CONVERSION.".format(
            GeographicFeatureResource.objects.all().count())
        logger.info(msg)
        print(">> {}".format(msg))

        for gf_res in GeographicFeatureResource.objects.all():
            # check resource exists on irods
            istorage = gf_res.get_irods_storage()
            if not istorage.exists(gf_res.root_path):
                err_msg = "Geofeature resource not found in irods (ID: {})".format(gf_res.short_id)
                logger.error(err_msg)
                print("Error:>> {}".format(err_msg))
                # skip this geofeature resource for migration
                continue

            create_gf_aggregation = False
            if gf_res.has_required_content_files() and \
                    gf_res.metadata.geometryinformation is not None:
                create_gf_aggregation = True

            if create_gf_aggregation:
                # check resource files exist on irods
                file_missing = False
                for res_file in gf_res.files.all():
                    file_path = res_file.public_path
                    if not istorage.exists(file_path):
                        err_msg = "File path not found in irods:{}".format(file_path)
                        logger.error(err_msg)
                        err_msg = "Failed to convert geofeature resource (ID: {}). " \
                                  "Resource file is missing on irods"
                        err_msg = err_msg.format(gf_res.short_id)
                        print("Error:>> {}".format(err_msg))
                        file_missing = True
                        break
                if file_missing:
                    # skip this corrupt geofeature resource for migration
                    continue

            # change the resource_type
            gf_metadata_obj = gf_res.metadata
            gf_res.resource_type = to_resource_type
            gf_res.content_model = to_resource_type.lower()
            gf_res.save()
            # get the converted resource object - CompositeResource
            comp_res = gf_res.get_content_model()

            # set CoreMetaData object for the composite resource
            core_meta_obj = CoreMetaData.objects.create()
            comp_res.content_object = core_meta_obj

            # migrate geofeature resource core metadata elements to composite resource
            migrate_core_meta_elements(gf_metadata_obj, comp_res)

            # update url attribute of the metadata 'type' element
            type_element = comp_res.metadata.type
            type_element.url = '{0}/terms/{1}'.format(current_site_url(), to_resource_type)
            type_element.save()
            if create_gf_aggregation:
                # create a Geofeature aggregation
                gf_aggr = None
                try:
                    gf_aggr = GeoFeatureLogicalFile.create(resource=comp_res)
                except Exception as ex:
                    err_msg = 'Failed to create Geofeature aggregation for resource (ID: {})'
                    err_msg = err_msg.format(gf_res.short_id)
                    err_msg = err_msg + '\n' + ex.message
                    logger.error(err_msg)
                    print("Error:>> {}".format(err_msg))

                if gf_aggr is not None:
                    # set aggregation dataset title
                    gf_aggr.dataset_name = comp_res.metadata.title.value
                    gf_aggr.save()
                    # make the res files part of the aggregation
                    for res_file in comp_res.files.all():
                        gf_aggr.add_resource_file(res_file)

                    # migrate geofeature specific metadata to aggregation
                    for fieldinfo in gf_metadata_obj.fieldinformations.all():
                        fieldinfo.content_object = gf_aggr.metadata
                        fieldinfo.save()

                    # create aggregation level coverage elements
                    for coverage in comp_res.metadata.coverages.all():
                        aggr_coverage = Coverage()
                        aggr_coverage.type = coverage.type
                        aggr_coverage._value = coverage._value
                        aggr_coverage.content_object = gf_aggr.metadata
                        aggr_coverage.save()

                    org_coverage = gf_metadata_obj.originalcoverage
                    if org_coverage:
                        org_coverage.content_object = gf_aggr.metadata
                        org_coverage.save()

                    geom_info = gf_metadata_obj.geometryinformation
                    if geom_info:
                        geom_info.content_object = gf_aggr.metadata
                        geom_info.save()

                    # create aggregation level keywords
                    keywords = [sub.value for sub in comp_res.metadata.subjects.all()]
                    gf_aggr.metadata.keywords = keywords

                    # create aggregation level xml files
                    gf_aggr.create_aggregation_xml_documents()
                    msg = 'One Geofeature aggregation was created in resource (ID: {})'
                    msg = msg.format(comp_res.short_id)
                    logger.info(msg)

            comp_res.save()
            # set resource to dirty so that resource level xml files (resource map and
            # metadata xml files) will be re-generated as part of next bag download
            try:
                set_dirty_bag_flag(comp_res)
            except Exception as ex:
                err_msg = 'Failed to set bag flag dirty for the converted resource (ID: {})'
                err_msg = err_msg.format(gf_res.short_id)
                err_msg = err_msg + '\n' + ex.message
                logger.error(err_msg)
                print("Error:>> {}".format(err_msg))

            resource_counter += 1
            # delete the instance of GeographicFeatureMetaData that was part of the original
            # geofeature resource
            gf_metadata_obj.delete()
            msg = 'Geofeature resource (ID: {}) was converted to Composite Resource type'
            msg = msg.format(comp_res.short_id)
            logger.info(msg)

        msg = "{} GEOFEATURE RESOURCES WERE CONVERTED TO COMPOSITE RESOURCE.".format(
            resource_counter)
        logger.info(msg)
        print(">> {}".format(msg))
        msg = "THERE ARE CURRENTLY {} GEOFEATURE RESOURCES AFTER CONVERSION.".format(
            GeographicFeatureResource.objects.all().count())
        logger.info(msg)
        if GeographicFeatureResource.objects.all().count() > 0:
            msg = "NOT ALL GEOFEATURE RESOURCES WERE CONVERTED TO COMPOSITE RESOURCE TYPE"
            logger.error(msg)
        print(">> {}".format(msg))
