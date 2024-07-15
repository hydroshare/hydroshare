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
        parser.add_argument('--dryrun', action='store_true', dest='dryrun', default=False,
                            help='Only lists the files, does not delete them.')

    def handle(self, *args, **options):
        resources_ids = options['resource_ids']
        updated_since = options['updated_since']
        dryrun = options['dryrun']
        resources = BaseResource.objects

        if resources_ids:  # an array of resource short_id to check.
            print("Removing unreferenced files in the resources provided")
            resources = resources.filter(short_id__in=resources_ids)
        elif updated_since:
            print(f"Filtering to include resources update in the last {updated_since} days")
            cuttoff_time = timezone.now() - timedelta(days=updated_since)
            resources = resources.filter(updated__gte=cuttoff_time)
        else:
            print("Removing unreferenced files for all resources.")
            resources = BaseResource.objects.all()

        istorage = IrodsStorage()

        def list_files_recursively(folder_path):
            try:
                folders, files, _ = istorage.listdir(folder_path)
            except SessionException as ex:
                print(f"Failed to list files in folder path {folder_path}: {ex.stderr}")
                return []
            files = [f"{folder_path}/{f}" for f in files]
            for folder in folders:
                sub_folder_path = f"{folder_path}/{folder}"
                try:
                    subfolders, subfiles, _ = istorage.listdir(sub_folder_path)
                except SessionException as ex:
                    print(f"Failed to list files in subfolder path {sub_folder_path}: {ex.stderr}")
                    subfiles = []
                    subfolders = []
                files += ([f"{sub_folder_path}/{f}" for f in subfiles])
                for subfolder in subfolders:
                    files += list_files_recursively(f"{sub_folder_path}/{subfolder}")
            return files

        def special_file(f):
            if f.endswith("_meta.xml") or f.endswith("_resmap.xml") or f.endswith("_schema.json"):
                return True
            return False

        total_resources = resources.count()
        current_resource_count = 1
        resources_with_dangling_rf = []
        resources_with_missing_rf = []
        for resource in resources.iterator():
            print(f"{current_resource_count}/{total_resources}")
            current_resource_count = current_resource_count + 1
            irods_files = list_files_recursively(resource.file_path)
            irods_files = [f for f in irods_files if not special_file(f)]
            res_files = ResourceFile.objects.filter(object_id=resource.id)
            res_files_with_no_file = res_files.exclude(resource_file__in=irods_files).values_list('resource_file',
                                                                                                  flat=True)
            if res_files_with_no_file:
                resources_with_dangling_rf.append(resource.short_id)
            matched_values = res_files.filter(resource_file__in=irods_files).values_list('resource_file', flat=True)
            unreferenced_irods_files = [f for f in irods_files if f not in list(matched_values)]
            if unreferenced_irods_files:
                resources_with_missing_rf.append(resource.short_id)
                print("Unreferenced irods files")
                print(" ".join(unreferenced_irods_files))
                if not dryrun:
                    for file in unreferenced_irods_files:
                        try:
                            istorage.delete(file)
                        except SessionException as ex:
                            print(f"Failed to delete {file}: {ex.stderr}")
                        except Exception as ex:
                            print(f"Failed to delete {file}: {ex.stderr}")
        print("Resources with dangling resource files")
        print(" ".join(resources_with_dangling_rf))
        print("Resources with missing resource files")
        print(" ".join(resources_with_missing_rf))
