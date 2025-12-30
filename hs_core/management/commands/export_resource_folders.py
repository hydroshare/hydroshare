"""
This command exports all empty folder AVUs to actual empty folders in S3 storage for all resources.
"""
from django.core.management.base import BaseCommand

from django_s3.storage import S3Storage
from hs_core.models import BaseResource


class Command(BaseCommand):
    help = "Exports all empty folder AVUs to actual empty folders in S3 storage for all resources"

    def add_arguments(self, parser):
        # a list of user id's, or none to check all users
        parser.add_argument('resources', nargs='*', type=str)

    def handle(self, *args, **options):
        istorage = S3Storage()
        if len(options['resources']) > 0:
            for res in options['resources']:
                export_empty_folders(res, istorage)
        else:
            for res in BaseResource.objects.all():
                export_empty_folders(res, istorage)


def export_empty_folders(res, istorage):
    empty_folders = res.getAVU('empty_folders')
    if empty_folders:
        for folder in empty_folders.split(','):
            istorage.create_folder(res.short_id, folder)
    istorage.create_folder(res.short_id, "data/contents/")
    res.removeAVU(res.short_id, 'empty_folders')  # clear out the AVU after creating folders
