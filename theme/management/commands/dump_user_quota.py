import csv
from django.core.management.base import BaseCommand
from theme.models import UserQuota, QuotaMessage
from mezzanine.conf import settings


class Command(BaseCommand):
    help = ("Output quota allocations for all users in {s_name}").format(s_name=settings.XDCI_SITE_NAME_MIXED)

    def add_arguments(self, parser):
        parser.add_argument('output_file_name_with_path', help='output file name with path')

    def handle(self, *args, **options):
        with open(options['output_file_name_with_path'], 'w') as csvfile:
            w = csv.writer(csvfile)
            if not QuotaMessage.objects.exists():
                QuotaMessage.objects.create()
            qmsg = QuotaMessage.objects.first()
            fields = [
                'User id',
                'User name',
                'Allocated quota value',
                'Quota unit',
                'Storage zone',
                'Quota soft limit percent: ' + str(qmsg.soft_limit_percent)
            ]
            w.writerow(fields)

            for uq in UserQuota.objects.filter(
                    user__is_active=True).filter(user__is_superuser=False):
                values = [
                    uq.user.id,
                    uq.user.username,
                    uq.allocated_value,
                    uq.unit,
                    uq.zone
                ]
                w.writerow([unicode(v).encode("utf-8") for v in values])
