# encoding=utf8

import sys

from os.path import dirname

from django.core.management.base import BaseCommand
from hs_dictionary.models import SubjectArea
import importlib

importlib.reload(sys)


class Command(BaseCommand):
    help = 'Creates Subject Areas dataset according to subject_areas.csv'

    def handle(self, *args, **options):
        # Create subjectArea list
        # https://has.arizona.edu/research-focus-areas

        if SubjectArea.objects.all().count() > 0:
            print('There are existing SubjectAreas in the dictionary. Aborting!')
            return

        with open(dirname(__file__) + '/subject_areas.txt', "r") as txtfile:
            for sa in txtfile:
                print(f'Adding SubjectArea: {sa} to dictionary')
                SubjectArea.objects.get_or_create(name=sa.strip())

        print("Done!")
