"""
This allows creation of a user without a graphical user interface.

WARNING: As these routines run in administrative mode, no access control is used.
Care must be taken to generate reasonable metadata, specifically, concerning
who owns what. Non-sensical options are possible to create.
This code is not a design pattern for actually interacting with communities.

WARNING: This command cannot be executed via 'hsctl' because that doesn't honor
the strings one needs to embed community names with embedded spaces.
Please connect to the bash shell for the hydroshare container before running them.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hs_core import hydroshare


def usage():
    print("access_user usage:")
    print("  access_user [{uname} [{request} [{options}]]]")
    print("Where:")
    print("  {uname} is a user name.")
    print("  {command} is one of:")
    print("      list: print the configuration of a user.")
    print("      create: create the user.")
    print("      update: update metadata for user.")
    print("      Options for create and update include:")
    print("          --email={email}: email of user. Required when creating a user.")
    print("          --first='{first name}': first name of user.")
    print("          --last='{last name}': last name of user.")


class Command(BaseCommand):
    help = """Manage users"""

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
            '--first',
            dest='first',
            help='first name of user'
        )

        parser.add_argument(
            '--last',
            dest='last',
            help='last name of user'
        )

        parser.add_argument(
            '--email',
            dest='email',
            help='email of user'
        )

    def handle(self, *args, **options):

        if options['syntax']:
            usage()
            exit(1)

        if len(options['command']) > 0:
            uname = options['command'][0]
        else:
            uname = None

        if len(options['command']) > 1:
            command = options['command'][1]
        else:
            command = None

        # not specifing a community lists active communities
        if uname is None:
            print("All users:")
            for u in User.objects.all():
                print("  '{}' ({})".format(u.username, u.id))
            exit(0)

        if command is None or command == 'list':
            try:
                user = User.objects.get(username=uname)
            except User.DoesNotExist:
                print("user '{}' does not exist.".format(uname))
                usage()
                exit(1)

            print("user '{}' ({}):".format(user.username, user.id))
            print("  email: {}".format(user.email))
            print("  first: {}".format(user.first_name))
            print("  last: {}".format(user.last_name))

        # These are idempotent actions. Creating a user twice does nothing.
        elif command == 'update' or command == 'create':
            try:
                user = User.objects.get(username=uname)
                if 'email' in options:
                    user.email = options['email']
                    user.save()
                if 'first' in options:
                    user.first_name = options['first']
                    user.save()
                if 'last' in options:
                    user.last_name = options['last']
                    user.save()

            except User.DoesNotExist:  # create it

                if options['email'] is not None:
                    email = options['email']
                else:
                    print("Email must be specified to create a user.")
                    usage()
                    exit(1)
                if options['first'] is not None:
                    first = options['first']
                else:
                    first = "T.C."

                if options['last'] is not None:
                    last = options['last']
                else:
                    last = "Mitts"

                print("creating user '{}'".format(uname))

                user = hydroshare.create_account(
                    email,
                    username=uname,
                    first_name=first,
                    last_name=last,
                    superuser=False,
                    groups=[]
                )

        else:
            print("unknown command '{}'.".format(command))
            usage()
            exit(1)
