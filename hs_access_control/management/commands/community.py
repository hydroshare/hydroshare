"""
This allows creation of a community of groups without a graphical user interface.

WARNING: As these routines run in administrative mode, no access control is used.
Care must be taken to generate reasonable metadata, specifically, concerning
who owns what. Non-sensical options are possible to create.
This code is not a design pattern for actually interacting with communities.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from hs_access_control.models.community import Community
from hs_access_control.models.privilege import PrivilegeCodes, \
        UserGroupPrivilege, UserCommunityPrivilege, GroupCommunityPrivilege

import re


def usage():
    print("Community usage:")
    print("  community [{cname} [{request} [{options}]]]")
    print("Where:")
    print("  {cname} is a community name. Use '' to embed spaces.")
    print("  {request} is one of:")
    print("      list: print the configuration of a community.")
    print("      create: create the community.")
    print("      update: update metadata for community.")
    print("      Options for create and update include:")
    print("          --owner={username}: set an owner for the community.")
    print("          --description='{description}': set the description to the text provided.")
    print("          --purpose='{purpose}': set the purpose to the text provided.")
    print("      group {gname} {request} {options}: group commands.")
    print("          {gname}: group name.")
    print("          {request} is one of:")
    print("              add: add the group to the community.")
    print("              update: update community metadata for the group.")
    print("              remove: remove the group from the community.")
    print("          Options for group metadata update include:")
    print("              --prohibit_view: don't allow viewing of this group's resources.")
    print("              --allow_edit: allow this group to edit other groups' resources.")
    print("      owner {oname} {request}: owner commands")
    print("      owner {oname} {request}: owner commands")
    print("          {oname}: owner name.")
    print("          {request} is one of:")
    print("              [blank]: list community owners")
    print("              add: add an owner for the community.")
    print("              remove: remove an owner from the community.")


def group_from_name_or_id(gname):
    """ return a group object given either an id or a name """

    RE_INT = re.compile(r'^([1-9]\d*|0)$')
    if RE_INT.match(gname):
        try:
            gid = int(gname)
            group = Group.objects.get(id=gid)
            return group
        except Group.DoesNotExist:
            print("group with id {} does not exist.".format(str(gid)))
            usage()
            exit(1)

    else:  # interpret as name
        groups = Group.objects.filter(name=gname)
        if groups.count() == 0:
            print("group '{}' not found.".format(gname))
            usage()
            exit(1)
        elif groups.count() == 1:
            group = groups[0]
            return group
        else:
            print("Group name {} is not unique. Please use group id instead:".format(gname))
            for g in groups:
                print("   '{}' (id={})".format(g.name, str(g.id)))
            exit(1)


def community_from_name_or_id(cname):
    """ return a group object given either an id or a name """

    RE_INT = re.compile(r'^([1-9]\d*|0)$')
    if RE_INT.match(cname):
        try:
            cid = int(cname)
            group = Community.objects.get(id=cid)
            return group
        except Community.DoesNotExist:
            print("community with id {} does not exist.".format(str(cid)))
            usage()
            exit(1)

    else:  # interpret as name
        communities = Community.objects.filter(name=cname)
        if communities.count() == 0:
            print("community with name '{}' does not exist.".format(cname))
            usage()
            exit(1)
        elif communities.count() == 1:
            community = communities[0]
            return community
        else:
            print("Community name '{}' is not unique. Please use community id instead:"
                  .format(cname))
            for g in communities:
                print("   '{}' (id={})".format(g.name, str(g.id)))
            exit(1)


def user_from_name(uname):
    try:
        return User.objects.get(username=uname)
    except User.DoesNotExist:
        print("user with username '{}' does not exist.".format(uname))
        usage()
        exit(1)


class Command(BaseCommand):
    help = """Manage communities of groups."""

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

        parser.add_argument(
            '--purpose',
            dest='purpose',
            help='purpose of community'
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
        owner = user_from_name(oname)

        if options['allow_edit']:  # this is a group privilege
            privilege = PrivilegeCodes.CHANGE
        else:
            privilege = PrivilegeCodes.VIEW

        # not specifing a community lists active communities
        if cname is None:
            print("All communities:")
            for c in Community.objects.all():
                print("  '{}' (id={})".format(c.name, str(c.id)))
            exit(0)

        if command is None or command == 'list':
            community = community_from_name_or_id(cname)
            print("community '{}' (id={}):".format(community.name, community.id))
            print("  description: {}".format(community.description))
            print("  purpose: {}".format(community.purpose))
            print("  owners:")
            for ucp in UserCommunityPrivilege.objects.filter(community=community,
                                                             privilege=PrivilegeCodes.OWNER):
                print("    {} (grantor {})".format(ucp.user.username, ucp.grantor.username))

            print("  member groups:")
            for gcp in GroupCommunityPrivilege.objects.filter(community=community):
                if gcp.privilege == PrivilegeCodes.CHANGE:
                    others = "can edit community resources"
                else:
                    others = "can view community resources"
                if gcp.allow_view:
                    myself = 'allows view of group resources'
                else:
                    myself = 'prohibits view of group resources'
                print("     '{}' (id={}) (grantor={}):"
                      .format(gcp.group.name, gcp.group.id, gcp.grantor.username))
                print("         {}, {}.".format(myself, others))
                print("         '{}' (id={}) owners are:".format(gcp.group.name, str(gcp.group.id)))
                for ugp in UserGroupPrivilege.objects.filter(group=gcp.group,
                                                             privilege=PrivilegeCodes.OWNER):
                    print("             {}".format(ugp.user.username))
            exit(0)

        # These are idempotent actions. Creating a community twice does nothing.
        if command == 'update' or command == 'create':
            try:
                community = Community.objects.get(name=cname)
                if options['description'] is not None:
                    community.description = options['description']
                    community.save()
                if options['purpose'] is not None:
                    community.purpose = options['purpose']
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
                purpose = options['purpose']

                print("creating community '{}' with owner '{}' and description '{}'"
                      .format(cname, owner, description))

                owner.uaccess.create_community(cname, description, purpose=purpose)

        elif command == 'owner':
            # at this point, community must exist
            community = community_from_name_or_id(cname)

            if len(options['command']) < 3:
                # list owners
                print("owners of community '{}' (id={})".format(community.name, str(community.id)))
                for ucp in UserCommunityPrivilege.objects.filter(community=community,
                                                                 privilege=PrivilegeCodes.OWNER):
                    print("    {}".format(ucp.user.username))
                exit(0)

            oname = options['command'][2]
            owner = user_from_name(oname)
            if len(options['command']) < 4:
                print("user {} owns community '{}' (id={})"
                      .format(owner.username, community.name, str(community.id)))
            action = options['command'][3]

            if action == 'add':
                print("adding {} as owner of {} (id={})"
                      .format(owner.username, community.name, str(community.id)))
                UserCommunityPrivilege.share(user=owner, community=community,
                                             privilege=PrivilegeCodes.OWNER, grantor=owner)

            elif action == 'remove':
                print("removing {} as owner of {} (id={})"
                      .format(owner.username, community.name, str(community.id)))
                UserCommunityPrivilege.unshare(user=owner, community=community, grantor=owner)

            else:
                print("unknown owner action '{}'".format(action))
                usage()
                exit(1)

        elif command == 'group':
            # at this point, community must exist
            community = community_from_name_or_id(cname)

            # not specifying a group should list groups
            if len(options['command']) < 3:
                print("Community '{}' groups:")
                for gcp in GroupCommunityPrivilege.objects.filter(community=community):
                    if gcp.privilege == PrivilegeCodes.CHANGE:
                        others = "can edit community resources"
                    else:
                        others = "can view community resources"
                    if gcp.allow_view:
                        myself = 'allows view of group resources'
                    else:
                        myself = 'prohibits view of group resources'
                    print("    '{}' (grantor {}):".format(gcp.group.name, gcp.grantor.username))
                    print("         {}, {}.".format(myself, others))
                exit(0)

            gname = options['command'][2]
            group = group_from_name_or_id(gname)

            if len(options['command']) < 4:
                print("community groups: no action specified.")
                usage()
                exit(1)

            action = options['command'][3]

            if action == 'update' or action == 'add':
                # resolve privilege of group
                if options['allow_edit']:
                    privilege = PrivilegeCodes.CHANGE
                else:
                    privilege = PrivilegeCodes.VIEW

                try:
                    print("Updating group '{}' (id={}) status in community '{}' (id={})."
                          .format(gname, str(group.id), cname, str(community.id)))
                    gcp = GroupCommunityPrivilege.objects.get(group=group, community=community)
                    if gcp.allow_view != (not options['prohibit_view']):
                        gcp.allow_view = not options['prohibit_view']
                        gcp.save()
                    # pass privilege changes through the privilege system to record provenance.
                    if gcp.privilege != privilege or owner != gcp.grantor:
                        GroupCommunityPrivilege.share(group=group, community=community,
                                                      privilege=privilege, grantor=owner)

                except GroupCommunityPrivilege.DoesNotExist:
                    print("Adding group '{}' (id={}) to community '{}' (id={})"
                          .format(gname, str(group.id), cname, str(community.id)))

                    # create the privilege record
                    GroupCommunityPrivilege.share(group=group, community=community,
                                                  privilege=privilege, grantor=owner)

                    # update view status if different than default
                    gcp = GroupCommunityPrivilege.objects.get(group=group, community=community)
                    if gcp.allow_view != (not options['prohibit_view']):
                        gcp.allow_view = not options['prohibit_view']
                        gcp.save()

            elif action == 'remove':

                print("removing group '{}' (id={}) from community '{}' (id={})"
                      .format(group.name, str(group.id), community.name, str(community.id)))
                GroupCommunityPrivilege.unshare(group=group, community=community, grantor=owner)

            else:
                print("unknown group command '{}'.".format(action))
                usage()
                exit(1)

        elif command == 'remove':
            community = community_from_name_or_id(cname)
            print("removing community '{}' (id={}).".format(community.name, community.id))
            community.delete()

        else:
            print("unknown command '{}'.".format(command))
            usage()
            exit(1)
