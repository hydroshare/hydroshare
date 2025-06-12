from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from hs_access_control.models.privilege import UserResourcePrivilege
from hs_core.models import BaseResource
from hs_access_control.models import PrivilegeCodes
from django_s3.utils import bucket_and_name, normalized_bucket_name


def new_quota_holder(connection, resource_id, new_quota_holder_id):
    src_bucket, src_name = bucket_and_name(resource_id)
    dst_bucket = normalized_bucket_name(new_quota_holder_id)
    dest_name = src_name

    bucket = connection.Bucket(src_bucket)
    for file in bucket.objects.filter(Prefix=src_name):
        src_file_path = file.key
        dst_file_path = file.key.replace(src_name, dest_name)
        connection.Bucket(dst_bucket).copy(
            {
                "Bucket": src_bucket,
                "Key": src_file_path,
            },
            dst_file_path,
        )


def set_quota_holder(resource, quota_holder):
    istorage = resource.get_s3_storage()
    new_quota_holder(istorage.connection, resource.short_id, quota_holder.username)

    resource.quota_holder = quota_holder
    resource.save()


class Command(BaseCommand):
    """
    Migrate published resources to published user quota holder
    """
    help = "Migrate published resources to published user quota holder"

    def handle(self, *args, **options):
        published_user = User.objects.get(username="published")
        resources = BaseResource.objects.filter(raccess__published=True).exclude(quota_holder=published_user)
        count = 0
        for res in resources:
            print('Fixing resource: {}'.format(res.short_id))
            try:
                UserResourcePrivilege.share(user=published_user, resource=res,
                                            privilege=PrivilegeCodes.OWNER, grantor=res.quota_holder)
                set_quota_holder(res, published_user)
                count += 1
            except Exception as ex:
                print(res.short_id + ' raised Exception when setting quota holder: '
                      + str(ex))
                continue

        print('{} resources with missing quota holder have been fixed'.format(count))
