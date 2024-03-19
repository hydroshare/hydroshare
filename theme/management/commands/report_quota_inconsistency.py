
import csv
import math
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError

from hs_core.hydroshare import convert_file_size_to_unit
from theme.models import UserQuota
from hs_core.hydroshare.resource import get_quota_usage_from_irods


class Command(BaseCommand):
    help = "Output potential quota inconsistencies between iRODS and Django for all users in HydroShare"

    def add_arguments(self, parser):
        parser.add_argument('output_file_name_with_path', help='output file name with path')

    def handle(self, *args, **options):
        quota_report_list = []
        for uq in UserQuota.objects.filter(
                user__is_active=True).filter(user__is_superuser=False):
            used_value = 0.0
            uz = 0.0
            dz = 0.0
            try:
                uz, dz = get_quota_usage_from_irods(uq.user.username)
                used_value = uz + dz
            except ValidationError:
                pass
            used_value = convert_file_size_to_unit(used_value, "gb")
            if not math.isclose(used_value, uq.used_value, abs_tol=0.1):
                # report inconsistency
                report_dict = {
                    'user': uq.user.username,
                    'django total': uq.used_value,
                    'django user zone': uq.user_zone_value,
                    'django data zone': uq.data_zone_value,
                    'irods total': used_value,
                    'irods user zone': uz,
                    'irods data zone': dz, }
                quota_report_list.append(report_dict)
                print('quota incosistency: {} reported in django vs {} reported in iRODS for user {}'.format(
                    uq.used_value, used_value, uq.user.username), flush=True)

        if quota_report_list:
            with open(options['output_file_name_with_path'], 'w') as csvfile:
                w = csv.writer(csvfile)
                fields = [
                    'User'
                    'Quota reported in Django',
                    'Quota reported in iRODS'
                ]
                w.writerow(fields)

                for q in quota_report_list:
                    values = [
                        q['user'],
                        q['django'],
                        q['irods']
                    ]
                    w.writerow([str(v) for v in values])
