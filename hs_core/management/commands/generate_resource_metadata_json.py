from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist

from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_core.hydroshare.resource import save_resource_metadata_json


class Command(BaseCommand):
    help = "Generate and save JSON representation of a resource's metadata and aggregation metadata."

    def add_arguments(self, parser):
        parser.add_argument(
            "resource_id",
            type=str,
            help=("Required. The existing id (short_id) of the resource to generate metadata for"),
        )

    def handle(self, *args, **options):
        if not options["resource_id"]:
            raise CommandError("resource_id argument is required")
        res_id = options["resource_id"]
        try:
            resource = get_resource_by_shortkey(res_id, or_404=False)
        except ObjectDoesNotExist:
            raise CommandError(f"No Resource found for id {res_id}")

        # Save the metadata JSON file to storage (S3)
        save_resource_metadata_json(resource)
        print(f"Resource level metadata and aggregation metadata JSON files saved to storage for resource: {res_id}")

        # check the metadata json file paths are on S3
        storage = resource.get_s3_storage()
        json_file_path = resource.metadata_json_file_path
        if storage.exists(json_file_path):
            print(f"Resource level metadata JSON file was created at: {json_file_path}")
        else:
            print(">> Resource level metadata JSON file was not created")
        for logical_file in resource.logical_files:
            aggr_name = logical_file.get_aggregation_type_name()
            json_file_path = logical_file.metadata_json_file_path
            if storage.exists(json_file_path):
                print(f"Aggregation level metadata JSON file was created for {aggr_name} at: {json_file_path}")
            else:
                print(f">> Aggregation level metadata JSON file was not created for {aggr_name}")
