"""
This prints the active permissions of an access control relationship between a user and a resource.
This is invaluable for access control debugging.

"""

from django.core.management.base import BaseCommand
from hs_access_control.models.privilege import PrivilegeCodes
from hs_access_control.management.utilities import user_from_name


def usage():
    print("User usage:")
    print("  user {username}")
    print("Where:")
    print("  {username} is a user name.")


def shorten(title, length):
    if len(title) <= length:
        return title
    else:
        return title[0:19]+'...'


class Command(BaseCommand):
    help = """Print access control provenance."""

    def add_arguments(self, parser):

        # a command to execute
        parser.add_argument('username', type=str)

    def handle(self, *args, **options):

        if options['username'] is None:
            usage()
            exit(1)

        username = options['username']

        user = user_from_name(username)
        if user is None:
            usage()
            exit(1)

        print("resources: [on my resources landing page]")
        print("  OWNED by user {}:".format(user.username))
        resources = user.uaccess.get_resources_with_explicit_access(
                PrivilegeCodes.OWNER, via_user=True, via_group=False, via_community=False)
        for r in resources:
            print("     resource '{}' ({})".format(shorten(r.title, 20), r.short_id))
        print("  EDITABLE by user {}:".format(user.username))
        resources = user.uaccess.get_resources_with_explicit_access(
                PrivilegeCodes.CHANGE, via_user=True, via_group=False, via_community=False)
        for r in resources:
            print("     resource '{}' ({})".format(shorten(r.title, 20), r.short_id))
        print("  VIEWABLE by user {}:".format(user.username))
        resources = user.uaccess.get_resources_with_explicit_access(
                PrivilegeCodes.VIEW, via_user=True, via_group=False, via_community=False)
        for r in resources:
            print("     resource '{}' ({})".format(shorten(r.title, 20), r.short_id))
        print("groups: [on my resources landing page]")
        print("  OWNED by user {}:".format(user.username))
        groups = user.uaccess.get_groups_with_explicit_access(PrivilegeCodes.OWNER)
        for g in groups:
            print("     group '{}' (id={})".format(g.name, g.id))
            print("        PUBLISHED and in group '{}' (id={})".format(g.name, g.id))
            resources = g.gaccess.view_resources.filter(raccess__published=True)
            for r in resources:
                print("           resource '{}' ({})".format(shorten(r.title, 20), r.short_id))
            print("        DISCOVERABLE and in group '{}' (id={})".format(g.name, g.id))
            resources = g.gaccess.view_resources.filter(raccess__discoverable=True)
            for r in resources:
                print("           resource '{}' ({})".format(shorten(r.title, 20), r.short_id))
            print("        EDITABLE by group '{}' (id={})".format(g.name, g.id))
            resources = g.gaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
            for r in resources:
                print("           resource '{}' ({})".format(shorten(r.title, 20), r.short_id))
            print("        VIEWABLE by group '{}' (id={})".format(g.name, g.id))
            resources = g.gaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
            for r in resources:
                print("           resource '{}' ({})".format(shorten(r.title, 20), r.short_id))
            print("        VIEWABLE by group '{}' (id={})".format(g.name, g.id))

        print("  EDITABLE by user {}:".format(user.username))
        groups = user.uaccess.get_groups_with_explicit_access(PrivilegeCodes.CHANGE)
        for g in groups:
            print("     group '{}' (id={})".format(g.name, g.id))
            print("        PUBLISHED and in group '{}' (id={})".format(g.name, g.id))
            resources = g.gaccess.view_resources.filter(raccess__published=True)
            for r in resources:
                print("           resource '{}' ({})".format(shorten(r.title, 20), r.short_id))
            print("        DISCOVERABLE and in group '{}' (id={})".format(g.name, g.id))
            resources = g.gaccess.view_resources.filter(raccess__discoverable=True)
            for r in resources:
                print("           resource '{}' ({})".format(shorten(r.title, 20), r.short_id))
            print("        EDITABLE by group '{}' (id={})".format(g.name, g.id))
            resources = g.gaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
            for r in resources:
                print("           resource '{}' ({})".format(shorten(r.title, 20), r.short_id))
            print("        VIEWABLE by group '{}' (id={})".format(g.name, g.id))
            resources = g.gaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
            for r in resources:
                print("           resource '{}' ({})".format(shorten(r.title, 20), r.short_id))
            print("        VIEWABLE by group '{}' (id={})".format(g.name, g.id))

        print("  VIEWABLE by {}:".format(user.username))
        groups = user.uaccess.get_groups_with_explicit_access(PrivilegeCodes.VIEW)
        for g in groups:
            print("     group '{}' (id={})".format(g.name, g.id))
            print("        PUBLISHED and in group '{}' (id={})".format(g.name, g.id))
            resources = g.gaccess.view_resources.filter(raccess__published=True)
            for r in resources:
                print("           resource '{}' ({})".format(shorten(r.title, 20), r.short_id))
            print("        DISCOVERABLE and in group '{}' (id={})".format(g.name, g.id))
            resources = g.gaccess.view_resources.filter(raccess__discoverable=True)
            for r in resources:
                print("           resource '{}' ({})".format(shorten(r.title, 20), r.short_id))
            print("        EDITABLE by group '{}' (id={})".format(g.name, g.id))
            resources = g.gaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
            for r in resources:
                print("           resource '{}' ({})".format(shorten(r.title, 20), r.short_id))
            print("        VIEWABLE by group '{}' (id={})".format(g.name, g.id))
            resources = g.gaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
            for r in resources:
                print("           resource '{}' ({})".format(shorten(r.title, 20), r.short_id))

        print("communities: [on community landing page]")
        print("   OWNED by {}".format(user.username))
        communities = user.uaccess.get_communities_with_explicit_access(PrivilegeCodes.OWNER)
        for c in communities:
            print("     community '{}' (id={})".format(c.name, c.id))

        print("   {} has EDIT membership:".format(user.username))
        communities = user.uaccess.get_communities_with_explicit_membership(PrivilegeCodes.CHANGE)
        for c in communities:
            print("     community '{}' (id={})".format(c.name, c.id))
            print("        groups where {} is granted edit:".format(user.username))
            groups = c.get_groups_with_explicit_access(PrivilegeCodes.CHANGE)
            for g in groups:
                print("     group '{}' (id={})".format(g.name, g.id))
                print("        PUBLISHED and in group '{}' (id={})".format(g.name, g.id))
                resources = g.gaccess.view_resources.filter(raccess__published=True)
                for r in resources:
                    print("           resource '{}' ({})".format(shorten(r.title, 20), r.short_id))
                print("        DISCOVERABLE and in group '{}' (id={})".format(g.name, g.id))
                resources = g.gaccess.view_resources.filter(raccess__discoverable=True,
                                                            raccess__published=False)
                for r in resources:
                    print("           resource '{}' ({})".format(shorten(r.title, 20), r.short_id))
                print("        EDITABLE by group '{}' (id={})".format(g.name, g.id))
                resources = g.gaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
                for r in resources:
                    print("           resource '{}' ({})".format(shorten(r.title, 20), r.short_id))
                print("        VIEWABLE by group '{}' (id={})".format(g.name, g.id))
                resources = g.gaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
                for r in resources:
                    print("           resource '{}' ({})".format(shorten(r.title, 20), r.short_id))

            print("        groups where {} is granted view:".format(user.username))
            groups = c.get_groups_with_explicit_access(PrivilegeCodes.VIEW)
            for g in groups:
                print("     group '{}' (id={})".format(g.name, g.id))
                print("        PUBLISHED and in group '{}' (id={})".format(g.name, g.id))
                resources = g.gaccess.view_resources.filter(raccess__published=True)
                for r in resources:
                    print("           resource '{}' ({})".format(shorten(r.title, 20), r.short_id))
                print("        DISCOVERABLE and in group '{}' (id={})".format(g.name, g.id))
                resources = g.gaccess.view_resources.filter(raccess__discoverable=True,
                                                            raccess__published=False)
                for r in resources:
                    print("           resource '{}' ({})".format(shorten(r.title, 20), r.short_id))
                print("        EDITABLE by group '{}' (id={})".format(g.name, g.id))
                resources = g.gaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
                for r in resources:
                    print("           resource '{}' ({})".format(shorten(r.title, 20), r.short_id))
                print("        VIEWABLE by group '{}' (id={})".format(g.name, g.id))
                resources = g.gaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
                for r in resources:
                    print("           resource '{}' ({})".format(shorten(r.title, 20), r.short_id))

        print("   {} has VIEW membership:".format(user.username))
        communities = user.uaccess.get_communities_with_explicit_membership(PrivilegeCodes.VIEW)
        for c in communities:
            print("     community '{}' (id={})".format(c.name, c.id))
            print("        groups where {} has edit:".format(user.username))
            groups = c.get_groups_with_explicit_access(PrivilegeCodes.CHANGE)
            for g in groups:
                print("           group '{}' (id={})".format(g.name, g.id))
                print("              PUBLISHED and in group '{}' (id={})".format(g.name, g.id))
                resources = g.gaccess.view_resources.filter(raccess__published=True)
                for r in resources:
                    print("                 resource '{}' ({})".format(shorten(r.title, 20),
                                                                       r.short_id))
                print("              DISCOVERABLE and in group '{}' (id={})".format(g.name, g.id))
                resources = g.gaccess.view_resources.filter(raccess__discoverable=True,
                                                            raccess__published=False)
                for r in resources:
                    print("                 resource '{}' ({})".format(shorten(r.title, 20),
                                                                       r.short_id))
                print("              EDITABLE by group '{}' (id={})".format(g.name, g.id))
                resources = g.gaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
                for r in resources:
                    print("                 resource '{}' ({})".format(shorten(r.title, 20),
                                                                       r.short_id))
                print("              VIEWABLE by group '{}' (id={})".format(g.name, g.id))
                resources = g.gaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
                for r in resources:
                    print("                 resource '{}' ({})".format(shorten(r.title, 20),
                                                                       r.short_id))
            print("        groups where {} has view:".format(user.username))
            groups = c.get_groups_with_explicit_access(PrivilegeCodes.VIEW)
            for g in groups:
                print("           group '{}' (id={})".format(g.name, g.id))
                print("              PUBLISHED and in group '{}' (id={})".format(g.name, g.id))
                resources = g.gaccess.view_resources.filter(raccess__published=True)
                for r in resources:
                    print("                 resource '{}' ({})".format(shorten(r.title, 20),
                                                                       r.short_id))
                print("              DISCOVERABLE and in group '{}' (id={})".format(g.name, g.id))
                resources = g.gaccess.view_resources.filter(raccess__discoverable=True,
                                                            raccess__published=False)
                for r in resources:
                    print("                 resource '{}' ({})".format(shorten(r.title, 20),
                                                                       r.short_id))
                print("              EDITABLE by group '{}' (id={})".format(g.name, g.id))
                resources = g.gaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
                for r in resources:
                    print("                 resource '{}' ({})".format(shorten(r.title, 20),
                                                                       r.short_id))
                print("              VIEWABLE by group '{}' (id={})".format(g.name, g.id))
                resources = g.gaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
                for r in resources:
                    print("                 resource '{}' ({})".format(shorten(r.title, 20),
                                                                       r.short_id))
