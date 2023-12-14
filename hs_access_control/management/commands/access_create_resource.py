"""
This allows ownership control of a resource without a graphical user interface.

WARNING: As these routines run in administrative mode, no access control is used.
Care must be taken to generate reasonable metadata, specifically, concerning
who owns what. Non-sensical options are possible to create.
This code is not a design pattern for actually interacting with communities.

WARNING: This command cannot be executed via 'hsctl' because that doesn't honor
the strings one needs to embed community names with embedded spaces.
Please connect to the bash shell for the hydroshare container before running them.
"""

from django.core.management.base import BaseCommand
from hs_access_control.management.utilities import user_from_name
from hs_core.hydroshare.resource import create_resource


def usage():
    print("access_create_resource usage:")
    print("  access_create_resource [{options}]")
    print("Where options include:")
    print("  owner {username} -- make this user the owner")
    print("  title {title} -- title of resource")
    print("  abstract {abstract} -- title of resource")
    print("  keywords {keywords} -- subjects for resource")
    print("  access {private|discoverable|public} -- access for resource")
    print("Options may be strung together on one line.")


class Command(BaseCommand):
    help = """Create a resource for testing."""

    def add_arguments(self, parser):

        # a command to execute
        parser.add_argument('command', nargs='*', type=str)

        parser.add_argument(
            '--syntax',
            action='store_true',  # True for presence, False for absence
            dest='syntax',  # value is options['syntax']
            help='print help message',
        )

    def handle(self, *args, **options):

        if options['syntax']:
            usage()
            exit(1)

        abstract = 'No abstract'
        title = 'No title'
        subjects = 'foo,bar'
        subjects = tuple(subjects.split(','))
        access = 'private'
        oname = 'admin'
        owner = user_from_name('admin')
        files = None

        while options['command']:
            command = options['command'].pop(0)
            if command == 'title':
                title = options['command'].pop(0)
            elif command == 'abstract':
                abstract = options['command'].pop(0)
            elif command == 'subjects':
                subjects = options['command'].pop(0)
                subjects = tuple(subjects.split(','))
            elif command == 'files':
                files = options['command'].pop(0)
                files = files.split(',')
            elif command == 'access':
                access = options['command'].pop(0)
                if access not in ['private', 'discoverable', 'public']:
                    print("unrecognized access '{}'".format(access))
                    usage()
                    exit(1)
            elif command == 'owner':
                oname = options['command'].pop(0)
            else:
                owner = user_from_name(oname)
                if owner is None:
                    print("no owner '{}'".format(oname))
                    usage()
                    exit(1)
                print("unknown resource attribute '{}'".format(command))

        print("creating resource with attributes:")
        print("  title={}".format(title))
        print("  abstract={}".format(abstract))
        print("  subjects={}".format(subjects))
        print("  owner={}".format(oname))
        print("  access={}".format(access))
        print("  files={}".format(files))

        fds = tuple([open(f, 'rb') for f in files])

        metadata_dict = [
            {'description': {'abstract': abstract}},
        ]

        res = create_resource(
            resource_type='CompositeResource',
            owner=owner,
            title=title,
            keywords=subjects,
            metadata=metadata_dict,
            files=fds
        )

        if access == 'discoverable':
            res.set_discoverable(True)
        elif access == 'public':
            res.set_public(True)
        # default is 'private'

        print(res.short_id)
