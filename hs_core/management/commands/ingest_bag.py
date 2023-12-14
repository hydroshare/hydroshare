"""
This command ingests a bag into a resource.  You can provide a resource_id to ingest the bag or the command will create
a new resource to ingest the bag into.
"""
import os

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from hs_core.hydroshare import delete_resource_file, add_file_to_resource, create_resource
from hs_composite_resource.models import CompositeResource
from zipfile import ZipFile
from pathlib import Path

from hs_core.views.utils import ingest_bag


def extract_resource_id(bag_file_path):
    """Extracts the resource id by reading the root directory name inside the zip"""
    with ZipFile(bag_file_path, 'r') as zip_file:
        resource_id = Path(zip_file.namelist()[0]).parts[0]
    return resource_id


def is_hydrohsare_bagit(bag_file_path):
    """Checks for a hydroshare bagit file structure in a zip"""
    resource_id = extract_resource_id(bag_file_path)
    bagit_files = [
        os.path.join(resource_id, "bagit.txt"),
        os.path.join(resource_id, "manifest-md5.txt"),
        os.path.join(resource_id, "readme.txt"),
        os.path.join(resource_id, "tagmanifest-md5.txt"),
        os.path.join(resource_id, "data", "resourcemetadata.xml"),
        os.path.join(resource_id, "data", "resourcemap.xml")
    ]
    with ZipFile(bag_file_path, 'r') as zip_file:
        for bagit_file in bagit_files:
            if bagit_file not in zip_file.namelist():
                return False
    return True


class Command(BaseCommand):
    help = "Ingest a zipped bag archive into a resource"

    def add_arguments(self, parser):

        # a list of resource id's: none does nothing.
        parser.add_argument('bag_path', type=str)

        parser.add_argument(
            '-r',
            '--resource_id',
            type=str,
            help="Existing resource to ingest into. If omitted, the bag's resource_id will be used")

        parser.add_argument(
            '-o',
            '--overwrite',
            action='store_true',
            help="Overwrites resource if it exists on HydroShare"
        )

        parser.add_argument(
            '-u',
            '--user_id',
            type=int,
            help="The id of the user to make the owner of the resource, defaults to Hydroshare Administrator (1)",
            default=1
        )

    def handle(self, *args, **options):
        bag_path = options['bag_path']

        resource_id = options['resource_id']

        if not is_hydrohsare_bagit(bag_path):
            raise ValidationError(f"{bag_path} is not a valid HydroShare bagit zip")

        if not resource_id:
            resource_id = extract_resource_id(bag_path)

        resource_exists = CompositeResource.objects.filter(short_id=resource_id).exists()
        user = User.objects.get(id=options['user_id'])
        if resource_exists:
            if not options['overwrite']:
                raise ValidationError(f"Resource {resource_id} exists, include the overwrite command or provide "
                                      f"another resource_id.")

            res = CompositeResource.objects.get(short_id=resource_id)

            # delete all files and logical files
            for file in res.files.all():
                delete_resource_file(resource_id, file.id, user)

        else:
            res = create_resource("CompositeResource", user, "Title will be overwritten", short_id=resource_id)

        bag_file_name = os.path.basename(bag_path)
        bag_file = UploadedFile(file=open(bag_path, mode="rb"), name=bag_file_name)
        bag_res_file = add_file_to_resource(res, bag_file, save_file_system_metadata=True)
        ingest_bag(res, bag_res_file, user)
