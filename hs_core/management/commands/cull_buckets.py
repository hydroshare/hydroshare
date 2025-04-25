"""
This command download a production bag and ingests into a resource.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from hs_core.models import BaseResource
from django_s3.storage import S3Storage


class Command(BaseCommand):
    help = "Remove buckets from inactive users and active users with no resources"

    def add_arguments(self, parser):
        # a list of user id's, or none to check all users
        parser.add_argument('usernames', nargs='*', type=str)

    def handle(self, *args, **options):
        istorage = S3Storage()

        if len(options['usernames']) > 0:  # an array of resource short_id to check.
            for username in options['usernames']:
                cull_bucket(username, istorage)
        else:
            for user in User.objects.all():
                cull_bucket(user.username, istorage)


def cull_bucket(username, istorage):
    user = User.objects.get(username=username)
    bucket_name = user.userprofile.bucket_name

    if user.is_active:
        resources = BaseResource.objects.filter(quota_holder_id=user.id)
        if not resources.exists():
            istorage.delete_bucket(bucket_name)
            print(f"deleted no resource {user.username} bucket {bucket_name}")
        else:
            print(f"no action on {user.username} bucket {bucket_name}")
    else:
        istorage.delete_bucket(bucket_name)
        print(f"deleted inactive {user.username} bucket {bucket_name}")
