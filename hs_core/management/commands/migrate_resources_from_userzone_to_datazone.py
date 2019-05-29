import os

from django.core.management.base import BaseCommand

from hs_core.models import BaseResource

from django_irods.storage import IrodsStorage
from django_irods.icommands import SessionException


class Command(BaseCommand):
    help = "Migrate all resources in iRODS user zone to iRODS data zone"

    def handle(self, *args, **options):
        resource_counter = 0
        storage = IrodsStorage()
        avu_list = ['bag_modified', 'metadata_dirty', 'isPublic', 'resourceType']
        for resource in BaseResource.objects.all():
            if resource.storage_type == 'user':
                # resource is in user zone, so migrate it to data zone
                # copy files from iRODS user zone to data zone
                try:
                    src_coll = resource.root_path
                    tgt_coll = resource.short_id

                    if storage.exists(tgt_coll):
                        storage.delete(tgt_coll)
                    storage.copyFiles(src_coll, tgt_coll)
                    # copy AVU over for the resource collection from iRODS user zone to data zone

                    for avu_name in avu_list:
                        value = storage.getAVU(src_coll, avu_name)
                        # bag_modified AVU needs to be set to true for the new resource so the bag
                        # can be regenerated in the data zone
                        if avu_name == 'bag_modified':
                            storage.setAVU(tgt_coll, avu_name, 'true')
                        # everything else gets copied literally
                        else:
                            storage.setAVU(tgt_coll, avu_name, value)

                    # delete the original resource from user zone
                    storage.delete(src_coll)
                    # update resource federation path to point resource to data zone
                    resource.resource_federation_path = ''
                    resource.save()
                    print("Resource {} has been moved from user zone to data zone "
                          "successfully".format(resource.short_id))
                    resource_counter += 1
                except SessionException as ex:
                    print("Resource {} failed to move: {}".format(resource.short_id, ex.stderr))

        print("{} resources have been moved from user zone to data zone successfully".format(
            resource_counter))
