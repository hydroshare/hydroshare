from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError

from hs_core.hydroshare import get_resource_by_shortkey
from hs_core.models import ResourceFile


class Command(BaseCommand):
    help = "Updates modified_time, checksum, size for all files of a resources in DB for a given resource"

    def add_arguments(self, parser):
        parser.add_argument('--resource_id', type=str, required=True,
                            help='The existing id (short_id) of the resource for which the files need to be updated.')

    def handle(self, *args, **options):
        res_id = options['resource_id']
        try:
            res = get_resource_by_shortkey(res_id, or_404=False)
        except ObjectDoesNotExist:
            raise CommandError(f"No Resource was found for id: {res_id}")
        if res.resource_type != "CompositeResource":
            raise CommandError(f"Specified resource (ID:{res_id}) is not a Resource")

        res_files = []
        _BATCH_SIZE = settings.BULK_UPDATE_CREATE_BATCH_SIZE
        print(f"Total files in resource {res_id}: {res.files.all().count()}")
        file_counter = 0
        # exclude files with size 0 as they don't exist in S3
        for res_file in res.files.exclude(_size=0).iterator():
            # this is an expensive operation (3 S3 calls per file) - about 1 min for 100 files
            # size, checksum and modified time are obtained from S3 and assigned to
            # relevant fields of the resource file object
            res_file.set_system_metadata(resource=res, save=False)
            res_files.append(res_file)
            file_counter += 1
            print(f"Updated file count: {file_counter}")
            if res_file._size <= 0:
                print(f"File {res_file.short_path} was not found in S3.")

        if res_files:
            ResourceFile.objects.bulk_update(res_files, ResourceFile.system_meta_fields(), batch_size=_BATCH_SIZE)
            print(f"Updated {file_counter} files for resource {res_id}")
        else:
            print(f"Resource {res_id} contains no files.")
