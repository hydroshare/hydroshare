"""
This command sets up S3 eventing for all user buckets.
"""
import subprocess
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from django_s3.storage import S3Storage


class Command(BaseCommand):
    help = "Setup S3 eventing for all user buckets"

    def add_arguments(self, parser):
        # a list of user id's, or none to check all users
        parser.add_argument('usernames', nargs='*', type=str)

    def handle(self, *args, **options):
        istorage = S3Storage()
        if len(options['usernames']) > 0:  # an array of resource short_id to check.
            for username in options['usernames']:
                set_s3_events(username, istorage)
        else:
            for user in User.objects.all():
                set_s3_events(user.username, istorage)


def set_s3_events(username, istorage):
    user = User.objects.get(username=username)
    bucket_name = user.userprofile.bucket_name
    if istorage.bucket_exists(bucket_name):
        print(f"Setting S3 events for bucket: {bucket_name}")
        try:
            subprocess.run(["mc", "event", "add", f"hydroshare/{bucket_name}",
                            "arn:minio:sqs::RESOURCEFILE:kafka", "--event", "put,delete"], check=True)
        except Exception as e:
            print(f"Eventing may already exist for {bucket_name}: {e}")
    else:
        print(f"Bucket {bucket_name} does not exist, cannot set S3 events")
