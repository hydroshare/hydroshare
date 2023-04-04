# encoding=utf8

import sys

from os.path import dirname

from django.core.management.base import BaseCommand
from hs_dictionary.models import SubjectArea
from theme.models import UserProfile
import imp

imp.reload(sys)


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
                print(f"Searching for a match with '{subject}'")
                match = [sa for sa in subject_area_objects if sa.name.lower() == subject.strip().lower()]
                if match:
                    new_subj_areas.append(match[0].name)
                    if match[0].name == subject:
                        print(f'- Exact match with pre-existing subject area: {subject}')
                    else:
                        print(f'- Near match with pre-existing subject area: {subject}')
                        found_new_match = True
                else:
                    if subject.strip() == subject:
                        print(f"- Unmatched subject area '{subject}' will remain unaltered")
                        new_subj_areas.append(subject)
                    else:
                        print(f"- Unmatched subject area '{subject}' contains whitespace that will be stripped")
                        new_subj_areas.append(subject.strip())
                        found_new_match = True
            if found_new_match:
                print(f'Updating {profile} from {old_subject_areas} to {new_subj_areas}')
                profile.subject_areas = ','.join(new_subj_areas)
                profile.save()
            else:
                print('No changes will be made to this profiles subject areas')

        print("Done!")
