"""This prints the state of a logical file.

* By default, prints errors on stdout.
* Optional argument --log: logs output to system log.
"""

import os
from django.conf import settings
from django.core.management.base import BaseCommand
from hs_core.models import BaseResource


def debug_resource(short_id):
    """ Debug view for resource depicts output of various integrity checking scripts """

    try:
        res = BaseResource.objects.get(short_id=short_id)
    except BaseResource.DoesNotExist:
        print("{} does not exist".format(short_id))

    # If this path is resource_federation_path, then the file is a local user file
    userpath = '/' + os.path.join(
        getattr(settings, 'HS_USER_IRODS_ZONE', 'hydroshareuserZone'),
        'home',
        getattr(settings, 'HS_LOCAL_PROXY_USER_IN_FED_ZONE', 'localHydroProxy'))

    resource = res.get_content_model()
    assert resource, (res, res.content_model)

    if not res.is_federated:
        status = 'local'
    elif res.resource_federation_path == userpath:
        status = 'user'
    else:
        status = 'federated'

    if res.raccess and res.raccess.public:
        sharing = 'public'
    else:
        sharing = 'private'

    print("{} is {} {} resource".format(short_id, sharing, status))

    # context = {
    #     'shortkey': shortkey,
    #     'creator': resource.creator,
    #     'resource': resource,
    #     'raccess': resource.raccess,
    #     'owners': resource.raccess.owners,
    #     'editors': resource.raccess.get_users_with_explicit_access(PrivilegeCodes.CHANGE),
    #     'viewers': resource.raccess.get_users_with_explicit_access(PrivilegeCodes.VIEW),
    #     'public_AVU': resource.getAVU('isPublic'),
    #     'type_AVU': resource.getAVU('resourceType'),
    #     'modified_AVU': resource.getAVU('bag_modified'),
    #     'quota_AVU': resource.getAVU('quotaUserName'),
    #     'irods_issues': irods_issues,
    #     'irods_errors': irods_errors,
    # }


class Command(BaseCommand):
    help = "Print debugging information about logical files."

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

    def handle(self, *args, **options):
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                debug_resource(rid)

        else:
            for r in BaseResource.objects.all():
                debug_resource(r.short_id)
