"""
This prints a list of groups possessing public resources and thus having a product page.

"""

from django.core.management.base import BaseCommand
from hs_access_control.models import GroupAccess


def usage():
    print("groups_with_public_resources usage:")
    print("  groups_with_public_resources ")


def shorten(title, length):
    if len(title) <= length:
        return title
    else:
        return title[0:19] + '...'


def access_type(thing):
    if thing['published']:
        return 'published'
    elif thing['public']:
        return 'public'
    elif thing['discoverable']:
        return 'discoverable'
    else:
        return 'private'


class Command(BaseCommand):
    help = """List public groups."""

    def handle(self, *args, **options):

        for g in GroupAccess.groups_with_public_resources():
            # n = g.gaccess.public_resources.count()
            print("group is {} (id={})".format(g.name, g.id))
