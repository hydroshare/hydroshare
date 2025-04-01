""" Add an owner to a resource or resources

Usage: add_owner {username} {resource list}
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_access_control.models.privilege import UserResourcePrivilege, PrivilegeCodes
from django_s3.exceptions import SessionException
from django.db import transaction


def set_quota_holder(resource, user):
    try:
        resource.set_quota_holder(user, user)
    except SessionException as ex:
        # some resources copied from www for testing do not exist in the S3 backend,
        # hence need to skip these test artifects
        print(resource.short_id + ' raised SessionException when setting quota holder: '
              + ex.stderr)
    except AttributeError as ex:
        # when federation is not set up correctly, istorage does not have a session
        # attribute, hence raise AttributeError - ignore for testing
        print((resource.short_id + ' raised AttributeError when setting quota holder: '
              + str(ex)))
    except ValueError as ex:
        # when federation is not set up correctly, istorage does not have a session
        # attribute, hence raise AttributeError - ignore for testing
        print((resource.short_id + ' raised ValueError when setting quota holder: '
              + str(ex)))


class Command(BaseCommand):
    help = "add owner to resource"

    def add_arguments(self, parser):

        parser.add_argument('new_owner', type=str)

        parser.add_argument(
            '--owned_by',
            dest='owned_by',
            help='prior owner of the resources'
        )

        parser.add_argument(
            '--set_quota_holder',
            action='store_true',  # True for presence, False for absence
            dest='set_quota_holder',  # value is options['set_quota_holder']
            help='set quota holder as new owner')

        # a list of resource id's: none does nothing.
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):
        user = User.objects.get(username=options['new_owner'])
        admin = User.objects.get(username='admin')

        if options['owned_by'] is not None:
            prior = User.objects.get(username=options['owned_by'])
            for res in BaseResource.objects.filter(r2urp__user=prior,
                                                   r2urp__privilege=PrivilegeCodes.OWNER):
                with transaction.atomic():
                    resource = res.get_content_model()
                    UserResourcePrivilege.share(user=user,
                                                resource=resource,
                                                privilege=PrivilegeCodes.OWNER,
                                                grantor=admin)
                    print("added owner {} to {}".format(options['new_owner'], resource.short_id))
                    if options['set_quota_holder']:
                        set_quota_holder(resource, user)
                        print("set quota holder to {} for {}".format(options['new_owner'],
                              resource.short_id))

        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.

            for rid in options['resource_ids']:
                resource = get_resource_by_shortkey(rid, or_404=False)
                with transaction.atomic():
                    UserResourcePrivilege.share(user=user,
                                                resource=resource,
                                                privilege=PrivilegeCodes.OWNER,
                                                grantor=admin)
                    print("added owner {} to {}".format(options['new_owner'], rid))
                    if options['set_quota_holder']:
                        set_quota_holder(resource, user)
                        print("set quota holder to {} for {}".format(options['new_owner'],
                              resource.short_id))
