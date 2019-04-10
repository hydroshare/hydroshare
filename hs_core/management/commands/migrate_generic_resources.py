import logging

from django.core.management.base import BaseCommand

from hs_core.models import GenericResource
from hs_core.hydroshare import current_site_url, set_dirty_bag_flag


class Command(BaseCommand):
    help = "Convert all generic resources to composite resource"

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        resource_counter = 0
        to_resource_type = 'CompositeResource'
        msg = "THERE ARE CURRENTLY {} GENERIC RESOURCES PRIOR TO CONVERSION.".format(
            GenericResource.objects.all().count())
        logger.info(msg)
        print(">> {}".format(msg))
        for gen_res in GenericResource.objects.all():
            # change the resource_type
            gen_res.resource_type = to_resource_type
            gen_res.content_model = to_resource_type.lower()
            gen_res.save()

            # get the converted resource object - CompositeResource
            comp_res = gen_res.get_content_model()

            # update url attribute of the metadata 'type' element
            type_element = comp_res.metadata.type
            type_element.url = '{0}/terms/{1}'.format(current_site_url(), to_resource_type)
            type_element.save()

            # set resource to dirty so that resource level xml files (resource map and
            # metadata xml files) will be generated as part of next bag download
            set_dirty_bag_flag(comp_res)
            resource_counter += 1

        msg = "{} GENERIC RESOURCES WERE CONVERTED TO COMPOSITE RESOURCE.".format(
            resource_counter)
        logger.info(msg)
        print(">> {}".format(msg))
        msg = "THERE ARE CURRENTLY {} GENERIC RESOURCES AFTER CONVERSION.".format(
            GenericResource.objects.all().count())
        logger.info(msg)
        print(">> {}".format(msg))
