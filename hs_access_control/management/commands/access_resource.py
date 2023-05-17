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
from hs_access_control.models.privilege import PrivilegeCodes, UserResourcePrivilege, GroupResourcePrivilege
from hs_access_control.management.utilities import user_from_name, resource_from_id, group_from_name_or_id


def usage():
    print("access_resource usage:")
    print("  access_resource [{rid} [{request} [{options}]]*]")
    print("Where:")
    print("  {rid} is a resource short name.")
    print("  {request} is one of:")
    print("      list: print the owners of a resource.")
    print("      owner {username} {add|remove}: add or remove an owner.")
    print("      user {username} {add|remove}: add or remove a VIEW user.")
    print("      group {group_name_or_id} {add|remove}: add or remove a group.")
    print("      access {private|discoverable|public}: whether resource is private or public.")
    print("And options include:")
    print("  --grantor={username} -- grantor of privilege")
    print("requests can be strung together in one command.")


class Command(BaseCommand):
    help = """Manage resource users."""

    def add_arguments(self, parser):

        # a command to execute
        parser.add_argument('command', nargs='*', type=str)

        parser.add_argument(
            '--syntax',
            action='store_true',  # True for presence, False for absence
            dest='syntax',  # value is options['syntax']
            help='print help message',
        )

        parser.add_argument(
            '--grantor',
            dest='grantor',
            help='grantor of privilege'
        )

    def handle(self, *args, **options):

        if options['syntax']:
            usage()
            exit(1)

        if options['command']:
            rid = options['command'].pop(0)
        else:
            rid = None

        # not specifing a resource lists resources
        if rid is None:
            print("All resources:")
            for r in BaseResource.objects.all():
                print("  {} title='{}'".format(r.short_id, r.title))
            exit(0)

        resource = resource_from_id(rid)
        if resource is None:
            print("resource {} not found.".format(rid))
            usage()
            exit(1)

        # resolve grantor:
        if options['grantor'] is not None:
            oname = options['grantor']
        else:
            oname = 'admin'

        grantor = user_from_name(oname)
        if grantor is None:
            print("grantor {} not found.".format(oname))
            usage()
            exit(1)

        while options['command']:
            command = options['command'].pop(0)

            if command == 'list':

                print("resource '{}' title='{}':".format(resource.short_id, resource.title))
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

            elif command == 'owner':

                if not options['command']:
                    # list owners
                    print("owners of resource '{}'".format(resource.short_id))
                    for ugp in UserResourcePrivilege.objects.filter(resource=resource,
                                                                    privilege=PrivilegeCodes.OWNER):
                        print("    {}".format(ugp.user.username))
                    exit(0)

                oname = options['command'].pop(0)
                owner = user_from_name(oname)
                if owner is None:
                    print("owner {} not found.".format(oname))
                    usage()
                    exit(1)

                action = options['command'].pop(0)
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

            elif command == 'user':  # share with user

                if not options['command']:
                    # list non-owner users
                    print("non-owner users of resource '{}'".format(resource.short_id))
                    for ugp in UserResourcePrivilege.objects.filter(resource=resource,
                                                                    privilege__gt=PrivilegeCodes.OWNER):
                        print("    {}".format(ugp.user.username))
                    exit(0)

                uname = options['command'].pop(0)
                user = user_from_name(uname)
                if user is None:
                    print("user {} not found.".format(uname))
                    usage()
                    exit(1)

                action = options['command'].pop(0)
                if action == 'add':
                    print("adding {} as user of {}"
                          .format(owner.username, resource.short_id))
                    UserResourcePrivilege.share(user=user, resource=resource,
                                                privilege=PrivilegeCodes.VIEW, grantor=grantor)

                elif action == 'remove':
                    print("removing {} as user of {}"
                          .format(owner.username, resource.short_id))
                    UserResourcePrivilege.unshare(user=owner, resource=resource, grantor=grantor)

                else:
                    print("unknown user action '{}'".format(action))
                    usage()
                    exit(1)

            elif command == 'group':  # share with group

                if not options['command']:
                    # list groups
                    print("groups for resource '{}'".format(resource.short_id))
                    for ugp in GroupResourcePrivilege.objects.filter(resource=resource):
                        print("    {} ({})".format(ugp.group.name, ugp.group.id))
                    exit(0)

                gname = options['command'].pop(0)
                group = group_from_name_or_id(gname)
                if group is None:
                    print("group {} not found.".format(gname))
                    usage()
                    exit(1)

                action = options['command'].pop(0)
                if action == 'add':
                    print("adding {} as group for {}"
                          .format(group.name, resource.short_id))
                    GroupResourcePrivilege.share(group=group, resource=resource,
                                                 privilege=PrivilegeCodes.VIEW, grantor=grantor)

                elif action == 'remove':
                    print("removing {} as user of {}"
                          .format(owner.username, resource.short_id))
                    UserResourcePrivilege.unshare(user=owner, resource=resource, grantor=grantor)

                else:
                    print("unknown user action '{}'".format(action))
                    usage()
                    exit(1)

            elif command == 'access':  # public or private

                if not options['command']:
                    # print status of resource
                    print("resource publication status:")
                    print("   discoverable={}".format(resource.discoverable))
                    print("   public      ={}".format(resource.public))
                    print("   published   ={}".format(resource.published))
                    exit(0)

                status = options['command'].pop(0)
                if status == 'private':
                    print("{}: making private".format(resource.short_id))
                    resource.set_discoverable(False)

                elif status == 'discoverable':
                    print("{}: making discoverable".format(resource.short_id))
                    resource.set_discoverable(True)

                elif status == 'public':
                    print("{}: making public".format(resource.short_id))
                    resource.set_public(True)

                else:
                    print("unrecognized access status '{}'".format(action))
                    usage()
                    exit(1)

            else:
                print("unknown command '{}'.".format(command))
                usage()
                exit(1)
