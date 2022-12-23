"""
This allows creation of a group without a graphical user interface.

WARNING: As these routines run in administrative mode, no access control is used.
Care must be taken to generate reasonable metadata, specifically, concerning
who owns what. Non-sensical options are possible to create.
This code is not a design pattern for actually interacting with communities.

WARNING: This command cannot be executed via 'hsctl' because that doesn't honor
the strings one needs to embed group names with embedded spaces.
Please connect to the bash shell for the hydroshare container before running them.
"""

from django.core.management.base import BaseCommand
from hs_access_control.models.privilege import PrivilegeCodes, UserGroupPrivilege
from hs_access_control.management.utilities import group_from_name_or_id, \
    user_from_name
from django.contrib.auth.models import Group


def usage():
    print("access_group usage:")
    print("  access_group [{gname} [{request} [{options}]]]")
    print("Where:")
    print("  {gname} is a group name. Use '' to embed spaces.")
    print("  {request} is one of:")
    print("      list: print the configuration of a group.")
    print("      create: create the group.")
    print("      update: update metadata for group.")
    print("      Options for create and update include:")
    print("          --owner={username}: set an owner for the group.")
    print("          --description='{description}': set the description to the text provided.")
    print("          --purpose='{purpose}': set the purpose to the text provided.")
    print("      user {uname} {request} {options}: user commands.")
    print("          {uname}: user name.")
    print("          {request} is one of:")
    print("              add: add the user to the group.")
    print("              remove: remove the user from the group.")
    print("      owner {oname} {request}: owner commands")
    print("          {oname}: owner name.")
    print("          {request} is one of:")
    print("              [blank]: list group owners")
    print("              add: add an owner for the group.")
    print("              remove: remove an owner from the group.")


class Command(BaseCommand):
    help = """Manage groups of users."""

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
            '--owner',
            dest='owner',
            help='owner of group (does not affect quota)'
        )

        parser.add_argument(
            '--description',
            dest='description',
            help='description of group'
        )

        parser.add_argument(
            '--purpose',
            dest='purpose',
            help='purpose of group'
        )

    def handle(self, *args, **options):

        if options['syntax']:
            usage()
            exit(1)

        if len(options['command']) > 0:
            gname = options['command'][0]
        else:
            gname = None

        if len(options['command']) > 1:
            command = options['command'][1]
        else:
            command = None

        if options['owner'] is not None:
            oname = options['owner']
        else:
            oname = 'admin'

        owner = user_from_name(oname)
        if owner is None:
            usage()
            exit(1)

        # not specifing a group lists active groups
        if gname is None:
            print("All groups:")
            for g in Group.objects.all():
                print("  '{}' (id={})".format(g.name, str(g.id)))
            exit(0)

        elif command is None or command == 'list':
            group = group_from_name_or_id(gname)
            if group is None:
                usage()
                exit(1)

            print("group '{}' (id={}):".format(group.name, group.id))
            print("  description: {}".format(group.gaccess.description))
            print("  purpose: {}".format(group.gaccess.purpose))
            print("  owners:")
            for ucp in UserGroupPrivilege.objects.filter(group=group,
                                                         privilege=PrivilegeCodes.OWNER):
                print("    {} (grantor {})".format(ucp.user.username, ucp.grantor.username))

            exit(0)

        # These are idempotent actions. Creating a group twice does nothing.
        elif command == 'update' or command == 'create':
            try:
                group = Group.objects.get(name=gname)
                # if it exists, update it
                print("updating group {}".format(gname))
                if options['description'] is not None:
                    group.description = options['description']
                    group.save()
                    print("   updated description")
                if options['purpose'] is not None:
                    group.purpose = options['purpose']
                    group.save()
                    print("   updated purpose")
                UserGroupPrivilege.update(user=owner,
                                          group=group,
                                          privilege=PrivilegeCodes.OWNER,
                                          grantor=owner)

                print("   updated ownership")
            except Group.DoesNotExist:  # create it

                if options['description'] is not None:
                    description = options['description']
                else:
                    description = ""

                if options['purpose'] is not None:
                    purpose = options['purpose']
                else:
                    purpose = "No purpose"

                print("creating group '{}' with owner '{}' and description '{}'"
                      .format(gname, owner, description))

                owner.uaccess.create_group(gname, description, purpose=purpose)

        elif command == 'owner':
            # at this point, group must exist
            group = group_from_name_or_id(gname)
            if group is None:
                usage()
                exit(1)

            if len(options['command']) < 3:
                # list owners
                print("owners of group '{}' (id={})".format(group.name, str(group.id)))
                for ucp in UserGroupPrivilege.objects.filter(group=group,
                                                             privilege=PrivilegeCodes.OWNER):
                    print("    {}".format(ucp.user.username))
                exit(0)

            oname = options['command'][2]
            owner = user_from_name(oname)
            if owner is None:
                usage()
                exit(1)

            if len(options['command']) < 4:
                print("user {} owns group '{}' (id={})"
                      .format(owner.username, group.name, str(group.id)))
            action = options['command'][3]

            if action == 'add':
                print("adding {} as owner of {} (id={})"
                      .format(owner.username, group.name, str(group.id)))
                UserGroupPrivilege.share(user=owner, group=group,
                                         privilege=PrivilegeCodes.OWNER, grantor=owner)

            elif action == 'remove':
                print("removing {} as owner of {} (id={})"
                      .format(owner.username, group.name, str(group.id)))
                UserGroupPrivilege.unshare(user=owner, group=group, grantor=owner)

            else:
                print("unknown owner action '{}'".format(action))
                usage()
                exit(1)

        elif command == 'user':
            # at this point, group must exist
            group = group_from_name_or_id(gname)
            if group is None:
                usage()
                exit(1)

            if len(options['command']) < 3:
                print("members of group '{}' (id={})".format(group.name, str(group.id)))
                for ucp in UserGroupPrivilege.objects.filter(group=group):
                    print("    {}".format(ucp.user.username))
                exit(0)

            uname = options['command'][2]
            user = user_from_name(uname)
            if user is None:
                usage()
                exit(1)

            if len(options['command']) < 4 or options['command'][3] == 'list':
                # list whether the user is a member of the group
                if UserGroupPrivilege.objects.filter(group=group, user=user).exists():

                    print("group '{}' (id={}) has member {}"
                          .format(group.name, str(group.id), user.username))
                else:
                    print("group '{}' (id={}) does not have member {}"
                          .format(group.name, str(group.id), user.username))
                exit(1)

            action = options['command'][3]

            if action == 'add':
                print("adding {} to {} (id={})"
                      .format(user.username, group.name, str(group.id)))
                UserGroupPrivilege.share(user=user, group=group,
                                         privilege=PrivilegeCodes.VIEW, grantor=owner)

            elif action == 'remove':
                print("removing {} from {} (id={})"
                      .format(user.username, group.name, str(group.id)))
                UserGroupPrivilege.unshare(user=user, group=group, grantor=owner)

            else:
                print("unknown user action '{}'".format(action))
                usage()
                exit(1)

        elif command == 'remove':
            group = group_from_name_or_id(gname)
            if group is None:
                usage()
                exit(1)

            print("removing group '{}' (id={}).".format(group.name, group.id))
            group.delete()

        else:
            print("unknown command '{}'.".format(command))
            usage()
            exit(1)
