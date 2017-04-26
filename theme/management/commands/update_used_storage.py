import csv
from collections import namedtuple
from django.core.management.base import BaseCommand
from theme.models import UserQuota, QuotaMessage

INPUT_FIELDS = namedtuple('FIELDS', 'user_name used_value storage_zone')
input_fields = INPUT_FIELDS(0, 1, 2)


class Command(BaseCommand):
    help = "Update used storage space in UserQuota table for all users in HydroShare by reading " \
           "an input file with updated values for users. Each row of the input file should list" \
           "information in the format of 'User name' 'Used value' 'Storage zone' " \
           "separated by comma. A header may also be included for informational purposes." \
           "This input file is created by a quota calculation script that runs nightly on a " \
           "HydroShare server."

    def add_arguments(self, parser):
        parser.add_argument('input_file_name_with_path', help='input file name with path')

    def handle(self, *args, **options):
        with open(options['input_file_name_with_path'], 'r') as csvfile:
            freader = csv.reader(csvfile)
            if not QuotaMessage.objects.exists():
                QuotaMessage.objects.create()
            qmsg = QuotaMessage.objects.first()
            for row in freader:
                try:
                    uname = int(row[input_fields.user_name])
                    used_val = int(row[input_fields.used_value])
                    zone = row[input_fields.storage_zone]
                    uq = UserQuota.objects.filter(user__username=uname, zone=zone).first()
                    uq.used_value = used_val
                    used_percent = used_val*100.0/uq.allocated_value
                    if used_percent >= 100 and used_percent < qmsg.hard_limit_percent:
                        if uq.remaining_grace_period < 0:
                            # triggers grace period counting
                            uq.remaining_grace_period = qmsg.grace_period
                        else:
                            # reduce remaining_grace_period by one day
                            uq.remaining_grace_period -= 1
                    elif used_percent < 100:
                        if uq.remaining_grace_period >= 0:
                            # turn grace period off now that the user is below quota soft limit
                            uq.remaining_grace_period = -1
                    uq.save()
                except ValueError:   # header row, continue
                    continue
