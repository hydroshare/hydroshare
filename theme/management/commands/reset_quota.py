from django.core.management.base import BaseCommand
from theme.models import UserQuota


class Command(BaseCommand):
    help = "Reset quota by forcing recalculation of quota for all users."

    def handle(self, *args, **options):
        uqs = UserQuota.objects.all()
        number_of_users = uqs.count()
        counter = 1
        users_with_error = []
        print(f"Total number of users: {number_of_users}")
        for uq in uqs:
            try:
                print(f"Resetting quota #{counter} for user: {uq.user.username}")
                _, _ = uq.get_used_value_by_zone(refresh=True)
                counter += 1
            except Exception as ex:
                users_with_error.append(uq.user.username)
                print(f"Error resetting quota for user: {uq.user.username}")
                print(f"Error message: {ex}")
                continue
        print("Quota reset completed.")
        print(f"Number of users with error: {len(users_with_error)}")
        print(f"Users with error: {users_with_error}")
