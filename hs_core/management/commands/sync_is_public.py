from django.core.management.base import BaseCommand
from django_irods.exceptions import SessionException
from hs_core.models import BaseResource
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Check synchronization between S3 and Django."

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
            resources = resources.all()

        for resource in resources.iterator():
            django_public = resource.raccess.public
            isPublic = "true" if django_public else "false"
            try:
                resource.setAVU('isPublic', isPublic)
                print(f"Set isPublic AVU for {resource.short_id} to {isPublic}")
            except SessionException as ex:
                print(f"Failed to save isPublic AVU for {resource.short_id}: {ex.stderr}")
