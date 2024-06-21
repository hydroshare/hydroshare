from django.core.management.base import BaseCommand
from django_irods.storage import IrodsStorage
from hs_core.models import BaseResource, ResourceFile
from django.utils import timezone
from django_irods.icommands import SessionException
from datetime import timedelta


class Command(BaseCommand):
    help = "Check synchronization between iRODS and Django."

    def add_arguments(self, parser):
        parser.add_argument('resource_ids', nargs='*', type=str)
        parser.add_argument('--updated_since', type=int, dest='updated_since',
                            help='include only resources updated in the last X days')
        
    def handle(self, *args, **options):
        resources_ids = options['resource_ids']
        updated_since = options['updated_since']
        resources = BaseResource.objects

        if resources_ids:  # an array of resource short_id to check.
            print("Setting isPublic AVU for the resources provided")
            resources = resources.filter(short_id__in=resources_ids)
        elif updated_since:
            print(f"Filtering to include resources update in the last {updated_since} days")
            cuttoff_time = timezone.now() - timedelta(days=updated_since)
            resources = resources.filter(updated__gte=cuttoff_time)
        else:
            print("Setting isPublic AVU for all resources.")
            resources = BaseResource.objects.all()
        
        istorage = IrodsStorage()
        def list_files_recursively(folder_path):
            try:
                folders, files, _ = istorage.listdir(folder_path)
            except SessionException as ex:
                print(f"Failed to list files in {folder_path}: {ex.stderr}")
                return []
            files = [f"{folder_path}/{f}" for f in files]
            for folder in folders:
                sub_folder_path = f"{folder_path}/{folder}"
                subfolders, subfiles, _ = istorage.listdir(sub_folder_path)
                files += ([f"{sub_folder_path}/{f}" for f in subfiles])
                for subfolder in subfolders:
                    files += list_files_recursively(f"{sub_folder_path}/{subfolder}")
            return files
        for resource in resources.iterator():

            irods_files = list_files_recursively(resource.file_path)
            irods_files = [f for f in irods_files if not f.endswith("_meta.xml") or f.endswith("_resmap.xml")] # exclude agg metadata files
            res_files = ResourceFile.objects.filter(object_id=resource.id)
            unreferenced_irods_files = res_files.exclude(resource_file__in=irods_files)
            if not unreferenced_irods_files:
                print(f"Resource {resource.short_id} has no unreferenced iRODS files:")
            else:
                print(f"Unreferenced files found in Resource {resource.short_id}")