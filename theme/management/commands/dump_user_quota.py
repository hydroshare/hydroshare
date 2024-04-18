import os
import pandas as pd
from django_irods.storage import IrodsStorage
from django.conf import settings
from hs_tools_resource.utils import convert_size
from theme.models import UserQuota
from django.core.management.base import BaseCommand
from hs_core.hydroshare import current_site_url


class Command(BaseCommand):
    help = "Output quota allocations and used values for all users in HydroShare"

    def add_arguments(self, parser):
        parser.add_argument('output_file_name_with_path', help='output file name with path')

        parser.add_argument(
            '--exceeded',
            action='store_true',  # True for presence, False for absence
            dest='exceeded',  # value is options['exceeded']
            help='show only users who have exceeded their quota',
        )
        parser.add_argument(
            '--expand_held_resources',
            action='store_true',  # True for presence, False for absence
            dest='expand',
            help='iterate over all resources to find those held by the user',
        )

    def handle(self, *args, **options):
        output_file_name_with_path = options['output_file_name_with_path']
        current_site = current_site_url()
        exceeded = options['exceeded']
        expand = options['expand']
        fields = [
            'User id',
            'User name',
            'User email',
            'Allocated quota value',
            'Used quota value (uz+dz)',
            'Remaining quota value',
            'Django UserQuota model UserZone value',
            'Django UserQuota model DataZone value',
            'Quota unit',
            'Grace period ends',
            'DataZone Bagit AVU Size (bytes)',
            'UserZone Bagit AVU Size (bytes)',
            'DataZone Bagit AVU Converted Size',
            'UserZone Bagit AVU Converted Size',
        ]
        if expand:
            fields.append('Total size of held resources (quota holder)')
        print(','.join(fields))

        user_quotas = UserQuota.objects.all()
        user_quotas.filter(user__is_active=True).filter(user__is_superuser=False)
        istorage = IrodsStorage()
        uz_bagit_path = os.path.join(
            '/', settings.HS_USER_IRODS_ZONE, 'home',
            settings.HS_IRODS_PROXY_USER_IN_USER_ZONE,
            settings.IRODS_BAGIT_PATH
        )
        data = []
        for uq in user_quotas:
            used = uq.used_value
            user = uq.user
            allocated = uq.allocated_value
            if exceeded and used < allocated:
                continue
            # TODO: update this to use the new quota usage
            dz_bytes = istorage.getAVU(settings.IRODS_BAGIT_PATH,
                                       f'{user.username}-usage')
            if dz_bytes is None:
                dz_bytes = 0
            dz = convert_size(int(dz_bytes))
            uz_bytes = istorage.getAVU(uz_bagit_path,
                                       f'{user.username}-usage')
            if uz_bytes is None:
                uz_bytes = 0
            uz = convert_size(int(uz_bytes))
            values = [
                user.id,
                user.username,
                user.email,
                allocated,
                used,
                uq.remaining,
                uq.user_zone_value,
                uq.data_zone_value,
                uq.unit,
                uq.grace_period_ends,
                dz_bytes,
                uz_bytes,
                dz,
                uz
            ]
            if expand:
                owned_resources = user.uaccess.owned_resources
                total_size = 0
                for res in owned_resources:
                    if res.quota_holder == user:
                        res_size = res.size
                        converted_size = convert_size(int(res_size))
                        print(f'{user.username} holds {current_site}/resource/{res.short_id}: {converted_size}')
                        total_size += res_size
                converted_total_size = convert_size(int(total_size))
                total_held = f'Total size of held resources for {user.username}: {converted_total_size}'
                values.append(converted_total_size)
                print(total_held)
            data.append(values)
            print(','.join([str(v) for v in values]))

        df = pd.DataFrame(data, columns=fields)
        df.to_csv(output_file_name_with_path, index=False)
        with pd.option_context('display.max_rows', None, 'display.max_columns', None):
            print(df)
