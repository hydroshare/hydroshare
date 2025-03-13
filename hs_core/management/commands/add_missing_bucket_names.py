"""
This command searches for users missing UserProfile._bucketname and assigns it a valid bucket name.
"""
from django.core.management.base import BaseCommand

from theme.utils import get_user_profiles_missing_bucket_name


class Command(BaseCommand):
    help = "Assign bucket names to users missing them"

    def add_arguments(self, parser):
        # a list of usernames, or none to check all users
        parser.add_argument('usernames', nargs='*', type=str)

    def handle(self, *args, **options):
        usernames = options.get('usernames', [])
        bad_ups = get_user_profiles_missing_bucket_name(usernames)
        for up in bad_ups:
            print(f"Assigning bucket name to user {up.user.username}")
            up._assign_bucket_name()
            up.save()
        print("Done")
