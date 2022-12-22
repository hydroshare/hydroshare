"""
This allows ownership control of a resource without a graphical user interface.

WARNING: As these routines run in administrative mode, no access control is used.
Care must be taken to generate reasonable metadata, specifically, concerning
who owns what. Non-sensical options are possible to create.
This code is not a design pattern for actually interacting with communities.

WARNING: This command cannot be executed via 'hsctl' because that doesn't honor
the strings one needs to embed community names with embedded spaces.
Please connect to the bash shell for the hydroshare container before running them.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_access_control.models.privilege import PrivilegeCodes, \
    UserResourcePrivilege
from hs_access_control.management.utilities import \
    user_from_name, resource_from_id


def usage():
    print("access_resource usage:")
    print("  access_resource [{rid} [{request} [{options}]]]")
    print("Where:")
    print("  {rid} is a resource short name.")
    print("  {request} is one of:")
    print("      list: print the users of a resource.")
    print("      user: user to add or remove.")
    print("          where options include {user-id} {add|remove}.")
    print("And options include:")
    print("  --grantor={username} -- grantor of privilege")


class Command(BaseCommand):
    help = """Manage groups."""

    def add_arguments(self, parser):

        # a command to execute
        parser.add_argument('command', nargs='*', type=str)

        parser.add_argument(
            '--grantor',
            dest='grantor',
            help='grantor of privilege'
        )

    def handle(self, *args, **options):

        if len(options['command']) > 0:
            rid = options['command'][0]
        else:
            rid = None

        if len(options['command']) > 1:
            command = options['command'][1]
        else:
            command = None

        # resolve grantor:
        if options['grantor'] is not None:
            oname = options['grantor']
        else:
            oname = 'admin'

        grantor = user_from_name(oname)
        if grantor is None:
            usage()
            exit(1)

        # not specifing a resource lists resources
        if rid is None:
            print("All resources:")
            for r in BaseResource.objects.all():
                print("  {} title='{}'".format(r.short_id, r.title))
            exit(0)

        resource = resource_from_id(rid)
        if resource is None:
            usage()
            exit(1)

        if command is None or command == 'list':

            print("resource '{}' title='{}'):".format(resource.short_id, resource.title))
            print("  owners:")
            for ugp in UserResourcePrivilege.objects.filter(resource=resource,
                                                            privilege=PrivilegeCodes.OWNER):
                print("    {} (grantor {})".format(ugp.user.username, ugp.grantor.username))
            print("  editors:")
            for ugp in UserResourcePrivilege.objects.filter(resource=resource,
                                                            privilege=PrivilegeCodes.CHANGE):
                print("    {} (grantor {})".format(ugp.user.username, ugp.grantor.username))
            print("  viewrs:")
            for ugp in UserResourcePrivilege.objects.filter(resource=resource,
                                                            privilege=PrivilegeCodes.VIEW):
                print("    {} (grantor {})".format(ugp.user.username, ugp.grantor.username))
            exit(0)

        if command == 'owner':

            if len(options['command']) < 3:
                # list owners
                print("owners of resource '{}'".format(resource.short_id))
                for ugp in UserResourcePrivilege.objects.filter(resource=resource,
                                                                privilege=PrivilegeCodes.OWNER):
                    print("    {}".format(ugp.user.username))
                exit(0)

            oname = options['command'][2]
            owner = user_from_name(oname)
            if owner is None:
                usage()
                exit(1)

            action = options['command'][3]
            if action == 'add':
                print("adding {} as owner of {}"
                      .format(owner.username, resource.short_id))
                UserResourcePrivilege.share(user=owner, resource=resource,
                                            privilege=PrivilegeCodes.OWNER, grantor=grantor)

            elif action == 'remove':
                print("removing {} as owner of {}"
                      .format(owner.username, resource.short_id))
                UserResourcePrivilege.unshare(user=owner, resource=resource, grantor=grantor)

            else:
                print("unknown owner action '{}'".format(action))
                usage()
                exit(1)

        else:
            print("unknown command '{}'.".format(command))
            usage()
            exit(1)
