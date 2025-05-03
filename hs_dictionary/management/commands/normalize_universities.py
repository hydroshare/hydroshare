# encoding=utf8

import sys

from csv import DictReader
from os.path import dirname

from django.core.management.base import BaseCommand
from hs_dictionary.models import University, UncategorizedTerm
from theme.models import UserProfile
import importlib

importlib.reload(sys)
sys.setdefaultencoding('utf8')


class Command(BaseCommand):
    help = 'Normalizes the University dataset according to normalize_universities.csv'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dryrun',
            action='store_true',
            dest='dryrun',
            default=False,
            help='Delete poll instead of closing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dryrun']

        with open(dirname(__file__) + '/normalize_universities.csv', "r") as csvfile:
            transliterations = list(DictReader(csvfile))
            profiles_with_organization = UserProfile.objects \
                .exclude(organization__isnull=True) \
                .exclude(organization='')

            for profile in profiles_with_organization:
                organization = profile.organization.strip().lower()
                match = [tl for tl in transliterations if tl['Old'].lower() == organization][0]
                new_match = match['New'].strip()
                if (match['Secondary']):
                    secondary_match = match['Secondary'].strip()
                else:
                    secondary_match = None

                if (len(match) == 0):
                    print("Warning: unmatched organization %s" % profile.organization)

                new_organization = new_match
                if (secondary_match):
                    new_organization = "%s,%s" % (new_match, secondary_match)

                if (dry_run):
                    print("[DRY RUN] Would rename %s to %s" %
                          (profile.organization, new_organization))
                else:
                    profile.organization = new_organization
                    profile.save()

                if new_match and not University.objects.filter(name=new_match).first():
                    if (dry_run):
                        print("[DRY RUN] Would create dictionary term: %s" % new_match)
                    else:
                        UncategorizedTerm.objects.get_or_create(name=new_match)

                if secondary_match and not University.objects.filter(name=secondary_match).first():
                    if (dry_run):
                        print("[DRY RUN] Would create dictionary term: %s" % secondary_match)
                    else:
                        UncategorizedTerm.objects.get_or_create(name=secondary_match)

        print("Done!")
