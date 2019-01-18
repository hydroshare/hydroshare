"""Removes unmodified GenericLogicalFiles found in composite resources.   This functionality is
to remove unused GenericLogicalFiles that were created by an earlier iteration of CompositeResource
that created an aggregation for every file added to a resource.
"""

from django.core.management.base import BaseCommand

from hs_composite_resource.models import CompositeResource
from hs_file_types.models.generic import GenericLogicalFile


class Command(BaseCommand):
    help = "Removes auto generated single file aggregations in the composite resource"

    def handle(self, *args, **options):
        resource_counter = 0
        generic_files = 0
        unmodified_generic_files_removed_counter = 0

        for res in CompositeResource.objects.all():
            resource_counter += 1
            for file in res.files.all():
                if type(file.logical_file) is GenericLogicalFile:
                    generic_files += 1
                    if not file.logical_file.metadata.has_modified_metadata:
                        file.logical_file.remove_aggregation()
                        unmodified_generic_files_removed_counter += 1

        print(">> {} COMPOSITE RESOURCES PROCESSED.".format(resource_counter))
        print(">> {} TOTAL GENERIC FILES FOUND".format(generic_files))
        print(">> {} TOTAL UNMODIFIED GENERIC FILES REMOVED"
              .format(unmodified_generic_files_removed_counter))
