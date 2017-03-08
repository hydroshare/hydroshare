import csv
from collections import namedtuple
from django.core.management.base import BaseCommand
from theme.models import UserQuota

INPUT_FIELDS = namedtuple('FIELDS', 'user_id used_value storage_zone')
input_fields = INPUT_FIELDS(0, 1, 2)


class Command(BaseCommand):
    help = "Update used storage space in UserQuota table for all users in HydroShare by reading " \
           "an input file with updated values for users. Each row of the input file should list" \
           "information in the format of 'User id' 'Used value' 'Storage zone' " \
           "separated by a space. A header may also be included for informational purposes." \
           "This input file is created by a quota monitoring script that runs nightly on a " \
           "HydroShare server."

    def add_arguments(self, parser):
        parser.add_argument('input_file_name_with_path')

    def handle(self, *args, **options):
        with open(options['input_file_name_with_path'], 'r') as csvfile:
            freader = csv.reader(csvfile, delimiter=' ')
            for row in freader:
                try:
                    uid = int(row[input_fields.user_id])
                    used_val = int(row[input_fields.used_value])
                    zone = row[input_fields.storage_zone]
                    uq = UserQuota.objects.filter(user__id=uid, zone=zone).first()
                    uq.used_value = used_val
                    uq.save()
                except ValueError: # header row, continue
                    continue
