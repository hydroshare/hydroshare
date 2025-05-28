from django.core.management.base import BaseCommand
from hs_access_control.models import UserResourcePrivilege
from hs_labels.models import UserResourceFlags
from hs_core.models import UserResource

class Command(BaseCommand):
    help = 'Populate UserResource table from UserResourcePrivilege and UserResourceFlags tables'

    def handle(self, *args, **options):
        self.stdout.write("Starting population of UserResource table...")

        # Process privileges
        count_privileges = 0
        for urp in UserResourcePrivilege.objects.all():
            UserResource.objects.update_or_create(
                user=urp.user,
                resource=urp.resource,
                defaults={'permission': urp.privilege}
            )
            count_privileges += 1

        self.stdout.write(f"Processed {count_privileges} UserResourcePrivilege entries.")

        # Process flags
        count_flags = 0
        for urf in UserResourceFlags.objects.all():
            ur, _ = UserResource.objects.get_or_create(
                user=urf.user,
                resource=urf.resource
            )
            if urf.kind == 1:  # FAVORITE
                ur.is_favorite = True
            elif urf.kind == 2:  # MINE
                ur.is_discovered = True
            ur.save()
            count_flags += 1

        self.stdout.write(f"Processed {count_flags} UserResourceFlags entries.")
        self.stdout.write("Finished populating UserResource table.")
        # print each record in UserResource table
        # for ur in UserResource.objects.all():
        #     self.stdout.write(f"user: {ur.user.username}, resource: {ur.resource.short_id}, permission: {ur.permission}, is_favorite: {ur.is_favorite}, is_discovered: {ur.is_discovered}")
