"""
This prints a list of publicly accessible resources in a community

"""

from django.core.management.base import BaseCommand
from hs_access_control.management.utilities import community_from_name_or_id


def usage():
    print("public usage:")
    print("  public {community-name-or-id}")
    print("Where:")
    print("  {community-name-or-id} is a community name or numeric id.")


def shorten(title, length):
    if len(title) <= length:
        return title
    else:
        return title[0:19]+'...'


class Command(BaseCommand):
    help = """List public resources."""

    def add_arguments(self, parser):

        # a command to execute
        parser.add_argument('arguments', nargs='*', type=str)

    def handle(self, *args, **options):

        if len(options['arguments']) != 1:
            usage()
            exit(1)

        community_name = options['arguments'][0]

        community = community_from_name_or_id(community_name)
        if community is None:
            usage()
            exit(1)

        print("community is {} (id={})".format(community.name, community.id))
        stuff = community.public_resource_list
        for r in stuff:
            print("{} {} type='{}' group='{}' published={}, public={}, discoverable={}"
                  .format(r["resource_id"],
                          shorten(r["resource_title"], 20),
                          r["resource_type"],
                          r["group_name"],
                          r["published"],
                          r["public"],
                          r["discoverable"]))
