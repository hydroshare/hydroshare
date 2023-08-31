from django.conf import settings
from django.core.management.base import BaseCommand

from hs_composite_resource.models import CompositeResource
from hs_core.models import ResourceFile


class Command(BaseCommand):
    # This command should be run only once to update all resource files in the DB
    # This will take a long time to finish (about 1 min for 100 files)
    # for updating files of a single resource, use command 'update_res_files_system_metadata'
    help = "Updates modified_time, checksum, size for all files of all resources in DB"

    def add_arguments(self, parser):
        # Since this command will take a long time to finish, we should update only resources with at least 200 files
        # as for resources with less than 200 files, the update can happen on the fly when the resource is accessed
        # without any timeout issue
        parser.add_argument('--minimum_files_count', type=int, default=200,
                            help='Minimum number of files the resource must have for the files to get updated.')

    def handle(self, *args, **options):
        min_files_count = options['minimum_files_count']
        _BATCH_SIZE = settings.BULK_UPDATE_CREATE_BATCH_SIZE
        resources = CompositeResource.objects.all().iterator()
        resource_counter = 0
        for res in resources:
            file_count = res.files.all().count()
            if file_count <= min_files_count:
                print(f"Resource {res.short_id} contains less than {min_files_count} files. Skipping.")
                continue
            resource_counter += 1
            res_files = []

            print(f"Total files in resource {res.short_id}: {file_count}")
            file_counter = 0
            # exclude files with size 0 as they don't exist in iRODS
            for res_file in res.files.exclude(_size=0).iterator():
                # this is an expensive operation (3 irods calls per file) - about 1 min for 100 files
                # size, checksum and modified time are obtained from irods and assigned to
                # relevant fields of the resource file object
                res_file.set_system_metadata(resource=res, save=False)

                res_files.append(res_file)
                file_counter += 1
                if file_counter % 10 == 0:
                    print(f"Updated file count: {file_counter}")
                if res_file._size <= 0:
                    print(f"WARNING: File {res_file.short_path} was not found in iRODS.")

            ResourceFile.objects.bulk_update(res_files, ResourceFile.system_meta_fields(), batch_size=_BATCH_SIZE)
            print(f"Updated {file_counter} files for resource {res.short_id}\n")

        print(f"Updated files for {resource_counter} resources")
