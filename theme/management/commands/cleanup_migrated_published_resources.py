from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from hs_core.models import BaseResource
from django_s3.utils import S3Storage


class Command(BaseCommand):
    """
    Cleanup migrated published resource data from source quota holder
    """
    help = "Cleanup migrated published resource data from source quota holder"

    def handle(self, *args, **options):
        published_user = User.objects.get(username="published")
        resources = BaseResource.objects.filter(raccess__published=True)
        count = 0
        istorage = S3Storage()
        for res in resources:
            count += 1
            print('Cleaning up resource: {}'.format(res.short_id))
            # not sure which owner was the old quota holder, so check them all
            for owner in res.raccess.owners.exclude(username=published_user.username):
                bucket_name = owner.userprofile.bucket_name
                for file in istorage.connection.Bucket(bucket_name).objects.filter(Prefix=res.short_id):
                    if istorage.connection.Object("published", file.key).exists():
                        istorage.connection.Object(bucket_name, file.key).delete()
                    else:
                        print('File {} does not exist in published bucket'.format(file.key))

        print('{} resources deleted src files after published migration'.format(count))
