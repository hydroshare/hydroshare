"""
This allows membership control of a group without a graphical user interface.

WARNING: As these routines run in administrative mode, no access control is used.
Care must be taken to generate reasonable metadata, specifically, concerning
who owns what. Non-sensical options are possible to create.
This code is not a design pattern for actually interacting with communities.

WARNING: This command cannot be executed via 'hsctl' because that doesn't honor
the strings one needs to embed community names with embedded spaces.
Please connect to the bash shell for the hydroshare container before running them.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from hs_access_control.models.privilege import PrivilegeCodes, \
        UserGroupPrivilege, GroupResourcePrivilege
from hs_access_control.management.utilities import \
        group_from_name_or_id, user_from_name, resource_from_id


def usage():
    print("access_group usage:")
    print("  access_group [{gname} [{request} [{options}]]]")
    print("Where:")
    print("  {gname} is a group name. Use '' to embed spaces.")
    print("  {request} is one of:")
    print("      list: print the configuration of a group.")
    print("      resource: resource to add or remove.")
    print("          where options include {guid} {add|remove}.")
    print("      owner: owner to add or remove.")
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

        # parser.add_argument(
        #     '--description',
        #     dest='description',
        #     help='description of group'
        # )

        # parser.add_argument(
        #     '--purpose',
        #     dest='purpose',
        #     help='purpose of group'
        # )

    def handle(self, *args, **options):

        if len(options['command']) > 0:
            gname = options['command'][0]
        else:
            gname = None

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

        privilege = PrivilegeCodes.VIEW

        # not specifing a group lists groups
        if gname is None:
            print("All groups:")
            for g in Group.objects.all():
                print("  '{}' (id={})".format(g.name, str(g.id)))
            exit(0)

        if command is None or command == 'list':
            group = group_from_name_or_id(gname)
            if group is None:
                usage()
                exit(1)

            print("group '{}' (id={}):".format(group.name, group.id))
            print("  owners:")
            for ugp in UserGroupPrivilege.objects.filter(group=group,
                                                         privilege=PrivilegeCodes.OWNER):
                print("    {} (grantor {})".format(ugp.user.username, ugp.grantor.username))
            print("  resources:")
            for grp in GroupResourcePrivilege.objects.filter(group=group):
                print("    {} '{}' (grantor {}) privilege {}"
                      .format(grp.resource.short_id, grp.resource.title, grp.grantor.username,
                              PrivilegeCodes.NAMES[grp.privilege]))
            exit(0)

        if command == 'owner':
            # at this point, group must exist
            group = group_from_name_or_id(gname)
            if group is None:
                usage()
                exit(1)

            if len(options['command']) < 3:
                # list owners
                print("owners of group '{}' (id={})".format(group.name, str(group.id)))
                for ugp in UserGroupPrivilege.objects.filter(group=group,
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
                print("adding {} as owner of {} (id={})"
                      .format(owner.username, group.name, str(group.id)))
                UserGroupPrivilege.share(user=owner, group=group,
                                         privilege=PrivilegeCodes.VIEW, grantor=grantor)

            elif action == 'remove':
                print("removing {} as owner of {} (id={})"
                      .format(owner.username, group.name, str(group.id)))
                UserGroupPrivilege.unshare(user=owner, group=group, grantor=grantor)

            else:
                print("unknown owner action '{}'".format(action))
                usage()
                exit(1)

        elif command == 'resource':

            # at this point, community must exist
            group = group_from_name_or_id(gname)
            if group is None:
                usage()
                exit(1)

            # not specifying a resource should list resources
            if len(options['command']) < 3:
                print("Group '{}' ({}) resources:".format(group.name, group.id))
                for grp in GroupResourcePrivilege.objects.filter(group=group):
                    if grp.privilege == PrivilegeCodes.CHANGE:
                        others = "can edit"
                    else:
                        others = "can view"
                    print("    '{}' ({}) (grantor {}):".format(grp.group.name, grp.group.id, grp.grantor.username))
                    print("         {}.".format(others))
                exit(0)

            # next thing is resource ID.
            rid = options['command'][2]
            resource = resource_from_id(rid)
            if resource is None:
                usage()
                exit(1)

            if len(options['command']) < 4:
                print("no resource command specified.")
                usage()
                exit(1)

            action = options['command'][3]

            if action == 'add':
                # resolve privilege of group
                privilege = PrivilegeCodes.VIEW
                print("Adding resource {} to group '{}' (id={}) ."
                      .format(rid, gname, str(group.id)))
                GroupResourcePrivilege.share(group=group, resource=resource, privilege=privilege, grantor=grantor)
            elif action == 'remove':

                print("removing resource {} from group '{}' (id={})"
                      .format(rid, group.name, str(group.id)))
                GroupResourcePrivilege.unshare(group=group, resource=resource, grantor=grantor)

            else:
                print("unknown resource command '{}'.".format(action))
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
