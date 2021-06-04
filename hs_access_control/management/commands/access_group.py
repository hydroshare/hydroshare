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
from hs_access_control.models.group import Community
from hs_access_control.models.privilege import PrivilegeCodes, \
        UserGroupPrivilege, UserCommunityPrivilege, UserGroupPrivilege
from hs_access_control.management.utilities import group_from_name_or_id, \
        group_from_name_or_id, user_from_name


def usage():
    print("access_group usage:")
    print("  access_group [{uname} [{request} [{options}]]]")
    print("Where:")
    print("  {uname} is a group name. Use '' to embed spaces.")
    print("  {request} is one of:")
    print("      list: print the configuration of a group.")
    print("      create: create the group.")
    print("      update: update metadata for group.")
    print("      Options for create and update include:")
    print("          --owner={username}: set an owner for the group.")
    print("          --description='{description}': set the description to the text provided.")
    print("          --purpose='{purpose}': set the purpose to the text provided.")
    print("      group {uname} {request} {options}: group commands.")
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

        if len(options['command']) > 0:
            uname = options['command'][0]
        else:
            uname = None

        if len(options['command']) > 1:
            command = options['command'][1]
        else:
            command = None

        # resolve owner: used in several update commands as grantor
        if options['owner'] is not None:
            oname = options['owner']
        else:
            oname = 'admin'

        owner = user_from_name(oname)
        if owner is None:
            usage()
            exit(1)

        privilege = PrivilegeCodes.VIEW

        # not specifing a group lists active groups
        if uname is None:
            print("All communities:")
            for c in Community.objects.all():
                print("  '{}' (id={})".format(c.name, str(c.id)))
            exit(0)

        if command is None or command == 'list':
            group = group_from_name_or_id(uname)
            if group is None:
                usage()
                exit(1)

            print("group '{}' (id={}):".format(group.name, group.id))
            print("  description: {}".format(group.description))
            print("  purpose: {}".format(group.purpose))
            print("  owners:")
            for ucp in UserCommunityPrivilege.objects.filter(group=group,
                                                             privilege=PrivilegeCodes.OWNER):
                print("    {} (grantor {})".format(ucp.user.username, ucp.grantor.username))

            print("  member groups:")
            for gcp in UserGroupPrivilege.objects.filter(group=group):
                if gcp.privilege == PrivilegeCodes.CHANGE:
                    others = "can edit group resources"
                else:
                    others = "can view group resources"
                print("     '{}' (id={}) (grantor={}):"
                      .format(gcp.group.name, gcp.group.id, gcp.grantor.username))
                print("         {}.".format(others))
                print("         '{}' (id={}) owners are:".format(gcp.group.name, str(gcp.group.id)))
                for ugp in UserGroupPrivilege.objects.filter(group=gcp.group,
                                                             privilege=PrivilegeCodes.OWNER):
                    print("             {}".format(ugp.user.username))
            exit(0)

        # These are idempotent actions. Creating a group twice does nothing.
        if command == 'update' or command == 'create':
            try:
                group = Community.objects.get(name=uname)
                if options['description'] is not None:
                    group.description = options['description']
                    group.save()
                if options['purpose'] is not None:
                    group.purpose = options['purpose']
                    group.save()

                UserCommunityPrivilege.update(user=owner,
                                              group=group,
                                              privilege=PrivilegeCodes.OWNER,
                                              grantor=owner)

            except Community.DoesNotExist:  # create it

                if options['description'] is not None:
                    description = options['description']
                else:
                    description = "No description"
                purpose = options['purpose']

                print("creating group '{}' with owner '{}' and description '{}'"
                      .format(uname, owner, description))

                owner.uaccess.create_group(uname, description, purpose=purpose)

        elif command == 'owner':
            # at this point, group must exist
            group = group_from_name_or_id(uname)
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
                UserCommunityPrivilege.unshare(user=owner, group=group, grantor=owner)

            else:
                print("unknown owner action '{}'".format(action))
                usage()
                exit(1)

        elif command == 'group':

            # at this point, group must exist
            group = group_from_name_or_id(uname)
            if group is None:
                usage()
                exit(1)

            # not specifying a group should list groups
            if len(options['command']) < 3:
                print("Community '{}' groups:")
                for gcp in UserGroupPrivilege.objects.filter(group=group):
                    if gcp.privilege == PrivilegeCodes.CHANGE:
                        others = "can edit group resources"
                    else:
                        others = "can view group resources"
                    print("    '{}' (grantor {}):".format(gcp.group.name, gcp.grantor.username))
                    print("         {}.".format(others))
                exit(0)

            uname = options['command'][2]
            group = group_from_name_or_id(uname)
            if group is None:
                usage()
                exit(1)

            if len(options['command']) < 4:
                print("group groups: no action specified.")
                usage()
                exit(1)

            action = options['command'][3]

            if action == 'update' or action == 'add':
                # resolve privilege of group
                privilege = PrivilegeCodes.VIEW

                try:
                    print("Updating group '{}' (id={}) status in group '{}' (id={})."
                          .format(uname, str(group.id), uname, str(group.id)))
                    gcp = UserGroupPrivilege.objects.get(group=group, group=group)
                    # pass privilege changes through the privilege system to record provenance.
                    if gcp.privilege != privilege or owner != gcp.grantor:
                        UserGroupPrivilege.share(group=group, group=group,
                                                      privilege=privilege, grantor=owner)

                except UserGroupPrivilege.DoesNotExist:
                    print("Adding user '{}' (id={}) to group '{}' (id={})"
                          .format(uname, str(group.id), uname, str(group.id)))

                    # create the privilege record
                    UserGroupPrivilege.share(group=group, user=user,
                                             privilege=privilege, grantor=owner)

                    # update view status if different than default
                    gcp = UserGroupPrivilege.objects.get(group=group, group=group)

            elif action == 'remove':

                print("removing group '{}' (id={}) from group '{}' (id={})"
                      .format(group.name, str(group.id), group.name, str(group.id)))
                UserGroupPrivilege.unshare(group=group, group=group, grantor=owner)

            else:
                print("unknown group command '{}'.".format(action))
                usage()
                exit(1)

        elif command == 'remove':
            group = group_from_name_or_id(uname)
            if group is None:
                usage()
                exit(1)

            print("removing group '{}' (id={}).".format(group.name, group.id))
            group.delete()

        else:
            print("unknown command '{}'.".format(command))
            usage()
            exit(1)
