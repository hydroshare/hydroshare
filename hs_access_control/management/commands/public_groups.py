"""
This prints a list of publicly accessible resources in a group

"""

from django.core.management.base import BaseCommand
from hs_access_control.models import GroupAccess


def usage():
    print("group_public usage:")
    print("  group_public ")


def shorten(title, length):
    if len(title) <= length:
        return title
    else:
        return title[0:19]+'...'


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

        for g in GroupAccess.public_groups(): 
            n = g.gaccess.public_resources.count()
            print("group is {} (id={}, public_resources={})".format(g.name, g.id, n))
