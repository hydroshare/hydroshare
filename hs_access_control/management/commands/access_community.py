"""
This allows creation of a community of groups without a graphical user interface.

WARNING: As these routines run in administrative mode, no access control is used.
Care must be taken to generate reasonable metadata, specifically, concerning
who owns what. Non-sensical options are possible to create.
This code is not a design pattern for actually interacting with communities.

WARNING: This command cannot be executed via 'hsctl' because that doesn't honor
the strings one needs to embed community names with embedded spaces.
Please connect to the bash shell for the hydroshare container before running them.
"""

from django.core.management.base import BaseCommand
from django.core.files import File
from hs_access_control.models.community import Community
from hs_access_control.models.privilege import PrivilegeCodes, \
    UserGroupPrivilege, UserCommunityPrivilege, GroupCommunityPrivilege
from hs_access_control.management.utilities import community_from_name_or_id, \
    group_from_name_or_id, user_from_name
from hs_access_control.models.invite import GroupCommunityRequest
import os


def usage():
    print("access_community usage:")
    print("  access_community [{cname} [{request} [{options}]]]")
    print("Where:")
    print("  {cname} is a community name or id. Use '' to embed spaces.")
    print("  {request} is one of:")
    print("      list: print the configuration of a community.")
    print("      create: create the community.")
    print("      Options for create and update include:")
    print("          --owner={username}: set an owner for the community.")
    print("          --description='{description}': set the description to the text provided.")
    print("          --purpose='{purpose}': set the purpose to the text provided.")
    print("      update: update metadata for community.")
    print("      remove: remove community.")
    print("      rename: rename community.")
    print("      group {gname} {request} {options}: group commands.")
    print("          {gname}: group name or id.")
    print("          {request} is one of:")
    print("              add: add the group to the community.")
    print("              update: update community metadata for the group.")
    print("              remove: remove the group from the community.")
    print("              invite: invite the group to join the community.")
    print("              request: make a request from a group owner to join the community.")
    print("              approve: approve a request or invitation.")
    print("              decline: decline a request or invitation.")
    print("      owner {oname} {request}: owner commands")
    print("          {oname}: owner name.")
    print("          {request} is one of:")
    print("              [blank]: list community owners")
    print("              add: add an owner for the community.")
    print("              remove: remove an owner from the community.")
    print("      banner {path-to-banner}: upload a banner.")


class Command(BaseCommand):
    help = """Manage communities of groups."""

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

        if options['syntax']:
            usage()
            exit(1)

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
        if owner is None:
            usage()
            exit(1)

        privilege = PrivilegeCodes.VIEW

        # not specifing a community lists active communities
        if cname is None:
            print("All communities:")
            for c in Community.objects.all():
                print("  '{}' (id={})".format(c.name, str(c.id)))
            usage()
            exit(0)

        if command is None or command == 'list':
            community = community_from_name_or_id(cname)
            if community is None:
                usage()
                exit(1)

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
                print("     '{}' (id={}) (grantor={}):"
                      .format(gcp.group.name, gcp.group.id, gcp.grantor.username))
                print("         {}.".format(others))
                print("         '{}' (id={}) owners are:".format(gcp.group.name, str(gcp.group.id)))
                for ugp in UserGroupPrivilege.objects.filter(group=gcp.group,
                                                             privilege=PrivilegeCodes.OWNER):
                    print("             {}".format(ugp.user.username))
            print("  invitations and requests:")
            for gcr in GroupCommunityRequest.objects.filter(community=community, redeemed=False):
                if (gcr.group_owner is None):
                    print("     '{}' (id={}) invited (by community owner={}):"
                          .format(gcr.group.name, gcr.group.id, gcr.community_owner.username))
                else:
                    print("     '{}' (id={}) requested membership (by group owner={}):"
                          .format(gcr.group.name, gcr.group.id, gcr.group_owner.username))
            exit(0)

        # These are idempotent actions. Creating a community twice does nothing.
        if command == 'update' or command == 'create':
            community = community_from_name_or_id(cname)
            if community is not None:
                community = Community.objects.get(name=community.name)
                print("updating community {}".format(community.name))
                if options['description'] is not None:
                    community.description = options['description']
                    community.save()
                    print("   updated description")
                if options['purpose'] is not None:
                    community.purpose = options['purpose']
                    community.save()
                    print("   updated purpose")

                UserCommunityPrivilege.update(user=owner,
                                              community=community,
                                              privilege=PrivilegeCodes.OWNER,
                                              grantor=owner)
                print("   updated ownership")

            else:  # if it does not exist, create it
                if options['description'] is not None:
                    description = options['description']
                else:
                    description = ""
                purpose = options['purpose']

                print("creating community '{}' with owner '{}' and description '{}'"
                      .format(cname, owner, description))

                owner.uaccess.create_community(cname, description, purpose=purpose)

        elif command == 'remove':
            # at this point, community must exist
            community = community_from_name_or_id(cname)
            if community is None:
                print("community '{}' does not exist".format(cname))
                exit(1)
            print("removing community '{}' (id={})".format(community.name, community.id))
            community.delete()

        elif command == 'rename':
            # at this point, community must exist
            community = community_from_name_or_id(cname)
            if community is None:
                print("community '{}' does not exist".format(cname))
                exit(1)

            nname = options['command'][2]
            print("renaming community '{}' (id={}) to '{}'".format(community.name, community.id, nname))
            community.name = nname
            community.save()

        elif command == 'owner':
            # at this point, community must exist
            community = community_from_name_or_id(cname)
            if community is None:
                usage()
                exit(1)

            if len(options['command']) < 3:
                # list owners
                print("owners of community '{}' (id={})".format(community.name, str(community.id)))
                for ucp in UserCommunityPrivilege.objects.filter(community=community,
                                                                 privilege=PrivilegeCodes.OWNER):
                    print("    {}".format(ucp.user.username))
                exit(0)

            oname = options['command'][2]
            owner = user_from_name(oname)
            if owner is None:
                usage()
                exit(1)

            if len(options['command']) < 4:
                print("user {} is a potential owner of community '{}' (id={})"
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
            if community is None:
                usage()
                exit(1)

            # not specifying a group should list groups
            if len(options['command']) < 3:
                print("Community '{}' groups:")
                for gcp in GroupCommunityPrivilege.objects.filter(community=community):
                    if gcp.privilege == PrivilegeCodes.CHANGE:
                        others = "can edit community resources"
                    else:
                        others = "can view community resources"
                    print("    '{}' (grantor {}):".format(gcp.group.name, gcp.grantor.username))
                    print("         {}.".format(others))
                exit(0)

            gname = options['command'][2]
            group = group_from_name_or_id(gname)
            if group is None:
                usage()
                exit(1)

            if len(options['command']) < 4:
                print("community groups: no action specified.")
                usage()
                exit(1)

            action = options['command'][3]

            if action == 'update' or action == 'add':
                # resolve privilege of group
                privilege = PrivilegeCodes.VIEW

                try:
                    print("Updating group '{}' (id={}) status in community '{}' (id={})."
                          .format(gname, str(group.id), cname, str(community.id)))
                    gcp = GroupCommunityPrivilege.objects.get(group=group, community=community)
                    # pass privilege changes through the privilege system to record provenance.
                    if gcp.privilege != privilege or owner != gcp.grantor:
                        GroupCommunityPrivilege.share(group=group, community=community,
                                                      privilege=privilege, grantor=owner)
                    else:
                        print("Group '{}' is already a member of community '{}'"
                              .format(gname, cname))

                except GroupCommunityPrivilege.DoesNotExist:
                    print("Adding group '{}' (id={}) to community '{}' (id={})"
                          .format(gname, str(group.id), cname, str(community.id)))

                    # create the privilege record
                    GroupCommunityPrivilege.share(group=group, community=community,
                                                  privilege=privilege, grantor=owner)

                    # update view status if different than default
                    gcp = GroupCommunityPrivilege.objects.get(group=group, community=community)

            elif action == 'invite':
                # resolve privilege of group
                privilege = PrivilegeCodes.VIEW

                try:
                    print("Inviting group '{}' (id={}) to community '{}' (id={})."
                          .format(gname, str(group.id), cname, str(community.id)))
                    gcp = GroupCommunityPrivilege.objects.get(group=group, community=community)
                    # pass privilege changes through the privilege system to record provenance.
                    if gcp.privilege != privilege or owner != gcp.grantor:
                        community_owner = community.first_owner
                        message, _ = GroupCommunityRequest.create_or_update(
                            community=community, requester=community_owner, group=group)
                        print(message)
                    else:
                        print("Group '{}' is already a member of community '{}'"
                              .format(group.name, community.name))

                except GroupCommunityPrivilege.DoesNotExist:
                    print("Adding group '{}' (id={}) to community '{}' (id={})"
                          .format(gname, str(group.id), cname, str(community.id)))

                    community_owner = community.first_owner
                    message, _ = GroupCommunityRequest.create_or_update(
                        community=community, requester=community_owner, group=group)
                    print(message)

                # update gcp for result of situation
                try:
                    gcp = GroupCommunityPrivilege.objects.get(group=group, community=community)
                except GroupCommunityPrivilege.DoesNotExist:
                    gcp = None

            elif action == 'request':
                # resolve privilege of group
                privilege = PrivilegeCodes.VIEW

                print("Requesting that group '{}' (id={}) join community '{}' (id={})."
                      .format(gname, str(group.id), cname, str(community.id)))
                try:
                    gcp = GroupCommunityPrivilege.objects.get(group=group, community=community)
                    # pass privilege changes through the privilege system to record provenance.
                    if gcp.privilege != privilege or owner != gcp.grantor:
                        group_owner = group.gaccess.first_owner
                        message, _ = GroupCommunityRequest.create_or_update(
                            community=community, requester=group_owner, group=group)
                        print(message)
                    else:
                        print("Group '{}' is already a member of community '{}'"
                              .format(group.name, community.name))

                except GroupCommunityPrivilege.DoesNotExist:
                    group_owner = group.gaccess.first_owner
                    message, _ = GroupCommunityRequest.create_or_update(
                        community=community, requester=group_owner, group=group)

                # update gcp for result of situation
                try:
                    gcp = GroupCommunityPrivilege.objects.get(group=group, community=community)
                except GroupCommunityPrivilege.DoesNotExist:
                    gcp = None

            elif action == 'approve':

                try:
                    gcr = GroupCommunityRequest.objects.get(community=community, group=group)
                except GroupCommunityRequest.DoesNotExist:
                    print("GroupCommunityRequest for community '{}' and group '{}' does not exist."
                          .format(cname, gname))

                if (gcr.redeemed):
                    print("request connecting '{}' and '{}' is already redeemed."
                          .format(community.name, group.name))
                    exit(1)
                elif (gcr.community_owner is None):
                    community_owner = community.first_owner
                    print("owner '{}' of community '{}' approves request from group '{}'"
                          .format(community_owner.username, cname, gname))
                    message, _ = gcr.approve_request(responder=community_owner)
                else:
                    group_owner = group.gaccess.first_owner
                    print("owner '{}' of group '{}' approves invitation from community '{}'"
                          .format(group_owner.username, gname, cname))
                    message, _ = gcr.accept_invitation(responder=group_owner)

                # update gcp for result of situation
                try:
                    gcp = GroupCommunityPrivilege.objects.get(group=group, community=community)
                except GroupCommunityPrivilege.DoesNotExist:
                    gcp = None

            elif action == 'decline':

                try:
                    gcr = GroupCommunityRequest.objects.get(community=community, group=group)
                except GroupCommunityRequest.DoesNotExist:
                    print("GroupCommunityRequest for community '{}' and group '{}' does not exist."
                          .format(cname, gname))

                if (gcr.redeemed):
                    print("request connecting '{}' and '{}' is already redeemed."
                          .format(community.name, group.name))
                    exit(1)
                elif (gcr.community_owner is None):
                    community_owner = community.first_owner
                    print("owner '{}' of community '{}' declines request from group '{}'"
                          .format(community_owner.username, cname, gname))
                    message, _ = gcr.decline_group_request(responder=community_owner)
                else:
                    group_owner = group.gaccess.first_owner
                    print("owner '{}' of group '{}' declines invitation from community '{}'"
                          .format(group_owner.username, gname, cname))
                    message, _ = gcr.decline_invitation(responder=group_owner)

                # update gcp for result of situation
                try:
                    gcp = GroupCommunityPrivilege.objects.get(group=group, community=community)
                except GroupCommunityPrivilege.DoesNotExist:
                    gcp = None

            elif action == 'remove':

                print("removing group '{}' (id={}) from community '{}' (id={})"
                      .format(group.name, str(group.id), community.name, str(community.id)))
                GroupCommunityPrivilege.unshare(group=group, community=community, grantor=owner)

            else:
                print("unknown group command '{}'.".format(action))
                usage()
                exit(1)

        elif command == 'banner':
            # upload a banner
            community = community_from_name_or_id(cname)
            if community is None:
                usage()
                exit(1)
            if len(options['command']) > 2:
                pname = options['command'][2]
                nname = os.path.basename(pname)
                community.picture.save(nname, File(open(pname, 'rb')))
            else:
                print("no file name given for banner image")
                usage()
                exit(1)

        elif command == 'remove':
            community = community_from_name_or_id(cname)
            if community is None:
                usage()
                exit(1)

            print("removing community '{}' (id={}).".format(community.name, community.id))
            community.delete()

        else:
            print("unknown command '{}'.".format(command))
            usage()
            exit(1)
