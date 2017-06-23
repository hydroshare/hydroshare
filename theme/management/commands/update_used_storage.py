import csv
from collections import namedtuple

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

from theme.models import UserQuota, QuotaMessage
from theme.utils import get_quota_message
from hs_core.hydroshare import convert_file_size_to_unit

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
                    if len(row) < 3:
                        # some fields are empty, ignore this row
                        continue
                    uname = row[input_fields.user_name]
                    if not uname:
                        # user name is empty, ignore this row
                        continue
                    uname = uname.strip()
                    if not uname:
                        # user name is empty after stripping, ignore this row
                        continue

                    used_val = row[input_fields.used_value]
                    if not used_val:
                        # used_value is empty, ignore this row
                        continue
                    used_val = used_val.strip()
                    if not used_val:
                        # used_val is empty after stripping, ignore this row
                        continue
                    used_val = int(used_val)

                    zone = row[input_fields.storage_zone]
                    if not zone:
                        # zone is empty, ignore this row
                        continue
                    zone = zone.strip()
                    if not zone:
                        # zone is empty after stripping, ignore this row
                        continue

                    uq = UserQuota.objects.filter(user__username=uname, zone=zone).first()
                    if uq is None:
                        # the quota row does not exist in Django
                        continue
                    uq.used_value = convert_file_size_to_unit(used_val, uq.unit)
                    uq.save()
                    used_percent = uq.used_value*100.0/uq.allocated_value
                    if used_percent >= qmsg.soft_limit_percent:
                        if used_percent < qmsg.hard_limit_percent:
                            if uq.remaining_grace_period < 0:
                                # triggers grace period counting
                                uq.remaining_grace_period = qmsg.grace_period
                            else:
                                # reduce remaining_grace_period by one day
                                uq.remaining_grace_period -= 1
                        else:
                            # set grace period to 0 when user quota exceeds hard limit
                            uq.remaining_grace_period = 0
                        uq.save()
                        user = uq.user
                        uemail = user.email
                        msg_str = 'Dear ' + uname + ':\n\n'
                        msg_str += get_quota_message(user)

                        msg_str += '\n\nHydroShare Support'
                        subject = 'Quota warning'
                        # send email for people monitoring and follow-up as needed
                        send_mail(subject, msg_str, settings.DEFAULT_FROM_EMAIL,
                                  [uemail])
                    else:
                        if uq.remaining_grace_period >= 0:
                            # turn grace period off now that the user is below quota soft limit
                            uq.remaining_grace_period = -1
                            uq.save()

                except ValueError as ex:   # header row, continue
                    print "Skip the header row:" + ex.message
                    continue
