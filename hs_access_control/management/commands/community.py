"""
This allows creation of a community of groups without a graphical user interface.
As these routines run in administrative mode, no access control is used.
This code is not a design pattern for actually interacting with communities.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from hs_access_control.models.community import Community
from hs_access_control.models.privilege import PrivilegeCodes, \
        UserCommunityPrivilege, GroupCommunityPrivilege


class Command(BaseCommand):
    help = "Manage communities of groups."

    def usage(self):
        print("Community usage:")
        print("  manage.py community {cname} {request} {options}")
        print("Where:")
        print("  {cname} is a community name. Use '' to embed spaces.")
        print("  {request} is one of:")
        print("      list: print the configuration of a community.")
        print("      create: create the community.")
        print("      update: update description (--description='...') for community.")
        print("      Options for create and update include:")
        print("          --owner={username}: set an owner for the community.")
        print("          --description='{description}': set the description to the text provided.")
        print("      group {gname} {request} {options}: group commands.")
        print("          {gname}: group name.")
        print("          {request} is one of:")
        print("              add: add the group to the community.")
        print("              update: update community metadata for the group.")
        print("              remove: remove the group from the community.")
        print("          Options for group requests include:")
        print("              --prohibit_view: don't allow viewing of this group's resources.")
        print("              --allow_edit: allow this group to edit other groups' resources.")

    def add_arguments(self, parser):

        # a command to execute
        parser.add_argument('command', nargs='*', type=str)

        # Named (optional) arguments
        parser.add_argument(
            '--prohibit_view',
            action='store_true',            # True for presence, False for absence
            dest='prohibit_view',           # value is options['prohibit_view']
            help="prohibit viewing of group's resources by community",
        )

        parser.add_argument(
            '--allow_edit',
            action='store_true',            # True for presence, False for absence
            dest='allow_edit',              # value is options['allow_edit']
            help="allow group to edit other groups' resources in community",
        )

        parser.add_argument(
            '--owner',
            dest='owner',
            help='owner of community (does not affect quota)'
        )

        parser.add_argument(
            '--description',
            dest='description',
            help='description of community'
        )

    def handle(self, *args, **options):

        if len(options['command']) > 0:
            cname = options['command'][0]
        else:
            cname = None

        if len(options['command']) > 1:
            command = options['command'][1]
        else:
            command = None

        # resolve owner: used in several update commands as grantor
        if options['owner'] is not None:
            oname = options['owner']
        else:
            oname = 'admin'
        try:
            owner = User.objects.get(username=oname)
        except User.DoesNotExist:
            print("owner {} does not exist.".format(oname))
            self.usage()
            exit(1)

        if options['allow_edit']:  # this is a group privilege
            privilege = PrivilegeCodes.CHANGE
        else:
            privilege = PrivilegeCodes.VIEW

        # this should probably list the active communities
        if cname is None:
            print("No community specified.")
            self.usage()
            exit(1)

        if command is None or command == 'list':
            try:
                community = Community.objects.get(name=cname)

                print("community {}:".format(community))
                print("  description: {}".format(community.description))
                print("  owners:")
                for ucp in UserCommunityPrivilege.objects.filter(community=community,
                                                                 privilege=PrivilegeCodes.OWNER):
                    print("    {} (grantor {})".format(ucp.user.username, ucp.grantor.username))

                print("  groups:")
                for gcp in GroupCommunityPrivilege.objects.filter(community=community):
                    if gcp.privilege == PrivilegeCodes.CHANGE:
                        others = "can edit community resources"
                    else:
                        others = "can view community resources"
                    if gcp.allow_view:
                        myself = 'allows view of group resources'
                    else:
                        myself = 'prohibits view of group resources'
                    print("     '{}' (grantor {}):".format(gcp.group.name, gcp.grantor.username))
                    print("         {}, {}.".format(myself, others))

            except Community.DoesNotExist:
                print("No community {} found.".format(community))

        if command == 'update' or command == 'create':
            try:
                community = Community.objects.get(name=cname)
                if options['description'] is not None:
                    community.description = options['description']
                    community.save()

                UserCommunityPrivilege.update(user=owner,
                                              community=community,
                                              privilege=PrivilegeCodes.OWNER,
                                              grantor=owner)

            except Community.DoesNotExist:  # create it

                if options['description'] is not None:
                    description = options['description']
                else:
                    description = "No description"

                print("creating community '{}' with owner '{}' and description '{}'"
                      .format(cname, owner, description))

                owner.uaccess.create_community(cname, description)

        elif command == 'group':
            # TODO: this should probably list groups
            if len(options['command']) < 3:
                print("No group name specified.")
                self.usage()
                exit(1)
            gname = options['command'][2]

            try:  # resolve community name
                community = Community.objects.get(name=cname)
            except Community.DoesNotExist:
                print("community '{}' does not exist.".format(cname))
                self.usage()
                exit(1)

            try:  # resolve group name
                group = Group.objects.get(name=gname)
            except Group.DoesNotExist:
                print("group '{}' not found.".format(gname))
                self.usage()
                exit(1)

            if (len(options['command']) < 4):
                print("No group action specified.")
                self.usage()
                exit(1)

            action = options['command'][3]

            if action == 'update' or action == 'add':
                # resolve privilege of group
                if options['allow_edit']:
                    privilege = PrivilegeCodes.CHANGE
                else:
                    privilege = PrivilegeCodes.VIEW

                try:
                    gcp = GroupCommunityPrivilege.objects.get(group=group, community=community)
                    if gcp.allow_view != (not options['prohibit_view']):
                        gcp.allow_view = not options['prohibit_view']
                        gcp.save()
                    # pass privilege changes through the privilege system to record provenance.
                    if gcp.privilege != privilege or owner != gcp.grantor:
                        GroupCommunityPrivilege.share(group=group, community=community,
                                                      privilege=privilege, grantor=owner)

                    print("updating group '{}' status in community '{}'".format(gname, cname))

                except GroupCommunityPrivilege.DoesNotExist:

                    print("adding group '{}' to community '{}'".format(gname, cname))

                    # create the privilege record
                    GroupCommunityPrivilege.share(group=group, community=community,
                                                  privilege=privilege, grantor=owner)

                    # update view status if different than default
                    gcp = GroupCommunityPrivilege.objects.get(group=group, community=community)
                    if gcp.allow_view != (not options['prohibit_view']):
                        gcp.allow_view = not options['prohibit_view']
                        gcp.save()

            elif action == 'list':
                pass

            elif action == 'remove':

                print("removing group '{}' from community '{}'".format(gname, cname))
                GroupCommunityPrivilege.unshare(group=group, community=community, grantor=owner)
