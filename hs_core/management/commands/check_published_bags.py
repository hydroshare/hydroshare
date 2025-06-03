"""
Check for published resources and create bags if necessary.
"""
from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from django_s3.storage import S3Storage
from hs_core.tasks import create_bag_by_s3


class Command(BaseCommand):
    help = "Check for published resources and create bags if necessary."

    def handle(self, *args, **options):
        published_res = BaseResource.objects.filter(raccess__published=True)
        istorage = S3Storage()
        for res in published_res:
            print(f"Checking resource {res.short_id} for bag creation...")
            if res.getAVU("bag_modified") == True or not istorage.exists(res.bag_path):
                print(f"Resource {res.short_id} has been modified, creating bag...")
                try:
                    create_bag_by_s3(res.short_id)
                except Exception as e:
                    print(f"Error creating bag for resource {res.short_id}: {e}")
            else:
                print(f"Resource {res.short_id} has not been modified and bag exists, skipping bag creation.")
