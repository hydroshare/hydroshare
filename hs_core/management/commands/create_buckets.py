"""
This command creates empty buckets on a new minio server for every active user with resources.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from hs_core.models import BaseResource
from django_irods.storage import S3Storage


class Command(BaseCommand):
    help = "Create buckets for active users with resources"

    def add_arguments(self, parser):
        # a list of user id's, or none to check all users
        parser.add_argument('usernames', nargs='*', type=str)

    def handle(self, *args, **options):
        istorage = S3Storage()

        if len(options['usernames']) > 0:  # an array of resource short_id to check.
            for username in options['usernames']:
                create_bucket(username, istorage)
        else:
            for user in User.objects.all():
                create_bucket(user.username, istorage)


def create_bucket(username, istorage):
    user = User.objects.get(username=username)
    bucket_name = user.userprofile.bucket_name

    if user.is_active:
        resources = BaseResource.objects.filter(quota_holder_id=user.id)
        if resources.exists():
            if not istorage.bucket_exists(bucket_name):
                istorage.create_bucket(bucket_name)
                print(f"created bucket {bucket_name} for user {user.username}")
