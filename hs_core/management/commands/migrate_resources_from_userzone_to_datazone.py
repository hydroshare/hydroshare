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

                    # Just to be on the safe side, it is better not to delete resources from user
                    # zone after it is migrated over to data zone in case there are issues with
                    # migration. A simple irm iRODS command can be issued to delete all resource
                    # collections afterwards if all works well after some time. Commenting the
                    # deletion statement below rather than deleting it to serve as a reminder
                    # that additional cleanup to delete all resource collections in user zone
                    # is needed after we can confirm migration is successfully.
                    # delete the original resource from user zone
                    # storage.delete(src_coll)

                    path_migrated = False
                    for res_file in resource.files.all():
                        if res_file.resource_file.name:
                            print('The resource_file field should be empty for resource {} but '
                                  'have the value of {}'.format(resource.short_id,
                                                                res_file.resource_file.name))
                            break
                        file_path = res_file.fed_resource_file.name
                        if not file_path:
                            print('The fed_resource_file field should not be empty for '
                                  'resource {}'.format(resource.short_id))
                            break
                        elif file_path.startswith(resource.resource_federation_path):
                            file_path = file_path[len(resource.resource_federation_path)+1:]
                            res_file.resource_file.name = file_path
                            res_file.fed_resource_file.name = ''
                            res_file.save()
                            path_migrated = True
                        else:
                            res_file.resource_file.name = file_path
                            res_file.fed_resource_file.name = ''
                            res_file.save()
                            path_migrated = True
                            print('fed_resource_file field does not contain absolute federation '
                                  'path which is an exception but can work after migration. '
                                  'file_path is {}'.format(file_path))
                    if path_migrated or resource.files.count() == 0:
                        # update resource federation path to point resource to data zone
                        resource.resource_federation_path = ''
                        resource.save()
                        print("Resource {} has been moved from user zone to data zone "
                              "successfully".format(resource.short_id))
                        resource_counter += 1
                    else:
                        continue
                except SessionException as ex:
                    print("Resource {} failed to move: {}".format(resource.short_id, ex.stderr))

        print("{} resources have been moved from user zone to data zone successfully".format(
            resource_counter))
