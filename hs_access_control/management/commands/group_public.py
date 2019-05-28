"""
This prints a list of publicly accessible resources in a group

"""

from django.core.management.base import BaseCommand
from hs_access_control.management.utilities import group_from_name_or_id


def usage():
    print("group_public usage:")
    print("  group_public {group-name-or-id}")
    print("Where:")
    print("  {group-name-or-id} is a group name or numeric id.")


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
    help = """List public resources."""

    def add_arguments(self, parser):

        # a command to execute
        parser.add_argument('arguments', nargs='*', type=str)

    def handle(self, *args, **options):

        if len(options['arguments']) != 1:
            usage()
            exit(1)

        group_name = options['arguments'][0]

        group = group_from_name_or_id(group_name)
        if group is None:
            usage()
            exit(1)

        print("group is {} (id={})".format(group.name, group.id))
        stuff = group.gaccess.public_resources
        for r in stuff:
            print(("{} '{}' '{}' type='{}' group='{}' (id={}) published={} public={} " +
                  "discoverable={} created='{}' updated='{}' first author='{}'")
                  .format(r.short_id,
                          shorten(r.title, 20),
                          # equivalently: shorten(r.content_object._title.first().value, 20),
                          shorten(r.description, 20),
                          # equivalently: shorten(r.content_object._description.first().value, 20),
                          r.resource_type,
                          r.group_name,
                          r.group_id,
                          r.published,
                          r.public,
                          r.discoverable,
                          r.created,
                          r.updated,
                          r.first_creator
                          # equivalently: r.content_object.creators.filter(order=1).first()
                          ))
