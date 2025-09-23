from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from hs_core.models import BaseResource
from django_s3.storage import S3Storage


def exists(bucket_object):
    try:
        bucket_object.load()
        return True
    except Exception as e:
        if '404' in str(e):
            return False
        else:
            raise e


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
                try:
                    for file in istorage.connection.Bucket(bucket_name).objects.filter(Prefix=res.short_id):
                        if exists(istorage.connection.Object("published", file.key)):
                            istorage.connection.Object(bucket_name, file.key).delete()
                        else:
                            print('File {} does not exist in published bucket'.format(file.key))
                except Exception as e:
                    print('Failure deleting resource {} on Bucket {}'.format(res.short_id, bucket_name))
                    print(str(e))

        print('{} resources deleted src files after published migration'.format(count))
