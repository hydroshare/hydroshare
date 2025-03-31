"""This lists all the large resources and their statuses.
   This helps in checking that they download properly.

* By default, prints errors on stdout.
* Optional argument --log: logs output to system log.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_access_control.models import PrivilegeCodes


def has_subfolders(resource):
    for f in resource.files.all():
        if '/' in f.short_path:
            return True
    return False


def measure_resource(short_id):
    """ Print size and sharing status of a resource """

    try:
        res = BaseResource.objects.get(short_id=short_id)
    except BaseResource.DoesNotExist:
        print("{} does not exist".format(short_id))

    resource = res.get_content_model()
    assert resource, (res, res.content_model)

    istorage = resource.get_s3_storage()
    if resource.raccess.public:
        status = "public"
    elif resource.raccess.discoverable:
        status = "discoverable"
    else:
        status = "private"

    if istorage.exists(resource.file_path):
        print(("{} {} {} {} {} {}".format(resource.size, short_id, status, resource.storage_type,
                                          resource.resource_type, resource.title)))
    else:
        print(("{} {} {} {} {} {} NO FILES".format('-', short_id, status,
                                                         resource.storage_type,
                                                         resource.resource_type,
                                                         resource.title)))


class Command(BaseCommand):
    help = "Print size information."

    def add_arguments(self, parser):

        # a list of resource id's: none does nothing.
        parser.add_argument('resource_ids', nargs='*', type=str)

        # Named (optional) arguments
        parser.add_argument(
            '--log',
            action='store_true',  # True for presence, False for absence
            dest='log',           # value is options['log']
            help='log errors to system log',
        )

        parser.add_argument(
            '--type',
            dest='type',
            help='limit to resources of a particular type'
        )

        parser.add_argument(
            '--storage',
            dest='storage',
            help='limit to specific storage medium (local, user, federated)'
        )

        parser.add_argument(
            '--access',
            dest='access',
            help='limit to specific access class (public, discoverable, private)'
        )

        parser.add_argument(
            '--owned_by',
            dest='owned_by',
            help='limit to resources owned by specific user'
        )

        parser.add_argument(
            '--has_subfolders',
            action='store_true',  # True for presence, False for absence
            dest='has_subfolders',  # value is options['has_subfolders']
            help='limit to resources with subfolders'
        )

        parser.add_argument(
            '--brief',
            action='store_true',  # True for presence, False for absence
            dest='brief',  # value is options['brief']
            help='create brief listing (resource id only)'
        )

    def measure_filtered_resource(self, resource, options):
        if (options['type'] is None or resource.resource_type == options['type']) and \
           (options['storage'] is None or resource.storage_type == options['storage']) and \
           (options['access'] != 'public' or resource.raccess.public) and \
           (options['access'] != 'discoverable' or resource.raccess.discoverable) and \
           (options['access'] != 'private' or not resource.raccess.discoverable) and \
           (not options['has_subfolders'] or has_subfolders(resource)):
            storage = resource.get_s3_storage()
            if options['brief']:
                print(resource.short_id)
            else:
                if storage.exists(resource.root_path):
                    measure_resource(resource.short_id)
                else:
                    print("{} does not exist in S3".format(resource.short_id))

    def handle(self, *args, **options):
        if options['owned_by'] is not None:
            owner = User.objects.get(username=options['owned_by'])
            for r in BaseResource.objects.filter(r2urp__user=owner,
                                                 r2urp__privilege=PrivilegeCodes.OWNER):
                self.measure_filtered_resource(r, options)

        elif len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                resource = get_resource_by_shortkey(rid)
                self.measure_filtered_resource(resource, options)

        else:
            for resource in BaseResource.objects.all():
                self.measure_filtered_resource(resource, options)
