from django.core.management.base import BaseCommand

from theme.models import UserProfile


class Command(BaseCommand):
    help = "This command can be run to clear image references from the db for profile media that no longer exist"

    def handle(self, *args, **options):
        ups = UserProfile.objects.only("picture", "user").all()
        for profile in ups:
            if profile.user.is_active:
                if profile.picture and not profile.picture.storage.exists(profile.picture.name):
                    profile.picture.delete()
                    print(f"Removed profile picture reference for user {profile.user.id}: {profile.user.username}")
