import csv
from django.core.management.base import BaseCommand
from theme.models import UserQuota


class Command(BaseCommand):
    help = "Output quota allocations and used values for all users in HydroShare"

    def add_arguments(self, parser):
        parser.add_argument('output_file_name_with_path', help='output file name with path')

    def handle(self, *args, **options):
        with open(options['output_file_name_with_path'], 'w') as csvfile:
            w = csv.writer(csvfile)
            fields = [
                'User id',
                'User name',
                'User email',
                'Allocated quota value',
                'Used quota value',
                'UserZone value',
                'DataZone value',
                'Quota unit',
            ]
            w.writerow(fields)

            for uq in UserQuota.objects.filter(
                    user__is_active=True).filter(user__is_superuser=False):
                values = [
                    uq.user.id,
                    uq.user.username,
                    uq.user.email,
                    uq.allocated_value,
                    uq.used_value,
                    uq.user_zone_value,
                    uq.data_zone_value,
                    uq.unit,
                ]
                w.writerow([str(v) for v in values])
