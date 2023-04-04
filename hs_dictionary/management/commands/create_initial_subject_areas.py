# encoding=utf8

import sys

from csv import DictReader
from os.path import dirname

from django.core.management.base import BaseCommand
from hs_dictionary.models import SubjectArea, UncategorizedTerm
from theme.models import UserProfile
import imp

imp.reload(sys)
# sys.setdefaultencoding('utf8')


class Command(BaseCommand):
    help = 'Creates Subject Areas dataset according to subject_areas.csv'

    def handle(self, *args, **options):
        # Create subjectArea list
        # https://has.arizona.edu/research-focus-areas
        with open(dirname(__file__) + '/subject_areas.txt', "r") as txtfile:
            for sa in txtfile:
                SubjectArea.objects.get_or_create(name=sa.strip())

        # Attempt to match existing SAs from profiles
        profiles_with_sa = UserProfile.objects \
            .exclude(subject_areas__isnull=True) \
            .exclude(subject_areas='')

        subject_area_objects = SubjectArea.objects.all()

        for profile in profiles_with_sa:
            old_subject_areas = profile.subject_areas.split(',')
            old_subject_areas = [s for s in old_subject_areas]
            print('*' * 100)
            print(f'Searching user #{profile.pk} which has subject areas: {old_subject_areas}')
            new_subj_areas = []
            found_new_match = False
            for subject in old_subject_areas:
                match = [sa for sa in subject_area_objects if sa.name.lower() == subject.strip().lower()]
                if match:
                    new_subj_areas.append(match[0].name)
                    if match[0].name == subject:
                        print(f'Exact match with pre-existing subject area: {subject}')
                    else:
                        found_new_match = True
                else:
                    print(f"Unmatched subject area {subject} will remain unaltered")
                    new_subj_areas.append(subject)
            if found_new_match:
                print(f'Updating {profile} from {old_subject_areas} to {new_subj_areas}')
                profile.subject_areas = ','.join(new_subj_areas)
                profile.save()

        print("Done!")
