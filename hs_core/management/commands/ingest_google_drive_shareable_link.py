import gdown
import tempfile
import os
from django.core.management.base import BaseCommand
from django_irods.storage import IrodsStorage


class Command(BaseCommand):
    help = "Ingest a zipped bag archive into a resource"

    def add_arguments(self, parser):

        # a list of resource id's: none does nothing.
        parser.add_argument('shareable_link', type=str)
        parser.add_argument('resource_file_path', type=str)

    def handle(self, *args, **options):
        shareable_link = options['shareable_link']
        resource_file_path = options['resource_file_path']
        with tempfile.TemporaryDirectory() as temp_dir:         
            file_id = shareable_link.split('/')[-1].split('?')[0]
            dfile = os.path.join(temp_dir, file_id)
            gdown.download(url=shareable_link, output=dfile, fuzzy=True)
            istorage = IrodsStorage()
            istorage.saveFile(dfile, resource_file_path)
