from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django_irods.storage import IrodsStorage, SessionException
from hs_core.models import BaseResource


def get_quota_holder(res):
    """Get quota holder of the resource.
    return User instance of the quota holder for the resource or None if it does not exist
    """
    try:
        uname = res.getAVU("quotaUserName")
    except SessionException:
        # quotaUserName AVU does not exist, return None
        return None

    if uname:
        return User.objects.filter(username=uname).first()
    else:
        # quotaUserName AVU does not exist, return None
        return None


class Command(BaseCommand):
    help = "Migrate quota_holder info from irods AVU into Django UserQuota model."

    def handle(self, *args, **options):
        istorage = IrodsStorage()

        resources = BaseResource.objects.all()
        number_of_res = resources.count()
        counter = 1
        res_with_error = []

        if not istorage.exists(settings.IRODS_BAGIT_PATH):
            print(f"iRODS path {settings.IRODS_BAGIT_PATH} does not exist.")
            raise CommandError(f"iRODS path {settings.IRODS_BAGIT_PATH} does not exist.")

        print(f"Total number of resources: {number_of_res}")
        for res in resources:
            try:
                print(f"Migrating quota #{counter} for resource: {res.short_id}")
                quota_holder = get_quota_holder(res)
                if quota_holder is None:
                    print(f"Quota holder AVU not found for resource: {res.short_id}")
                    continue
                res.quota_holder = quota_holder
                res.save()
                counter += 1
            except Exception as ex:
                print(f"Error migrating quota for resource: {res.short_id}")
                print(ex)
                res_with_error.append(res.short_id)
                continue

        print(f"Total number of resources with error: {len(res_with_error)}")
        print(f"Resources with error: {res_with_error}")
        print("Migration completed.")
