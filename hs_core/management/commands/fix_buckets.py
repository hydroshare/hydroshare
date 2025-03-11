"""
This command searches theme.model._bucketname and removes it if it is not a valid bucket name.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Analyze and remove erroneous bucket names"

    def add_arguments(self, parser):
        # a list of user id's, or none to check all users
        parser.add_argument('usernames', nargs='*', type=str)

    def handle(self, *args, **options):
        if len(options['usernames']) > 0:  # an array of resource short_id to check.
            for username in options['usernames']:
                check_bucket(username)
        else:
            for user in User.objects.all():
                check_bucket(user.username)


def check_bucket(username):
    user = User.objects.get(username=username)
    if len(user.userprofile._bucket_name) < 3:
        bucketname = user.userprofile._bucket_name
        user.userprofile._bucket_name = None
        user.userprofile.save()
        print(f"removed bucket name {bucketname} for user {user.username}")
