
import csv
import math
import time
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.conf import settings
from django_irods.icommands import SessionException
from django_irods.storage import IrodsStorage
from django.utils.timezone import now

from hs_core.hydroshare import convert_file_size_to_unit
from hs_core.hydroshare import current_site_url
from hs_core.models import ResourceFile
from theme.models import UserQuota

current_site = current_site_url()
_BATCH_SIZE = settings.BULK_UPDATE_CREATE_BATCH_SIZE


def get_dz_quota_usage_from_irods(username):
    """
    Query iRODS AVU to get quota usage for a user reported in iRODS quota microservices
    :param username: the user name to get quota usage for.
    :return: the quota usage from iRODS data zone
    :raises: ValidationError if quota usage cannot be retrieved from iRODS
    """
    attname = username + '-usage'
    istorage = IrodsStorage()
    # get quota size for user in iRODS data zone by retrieving AVU set on irods bagit path
    # collection
    try:
        uqDataZoneSize = istorage.getAVU(settings.IRODS_BAGIT_PATH, attname)
        if uqDataZoneSize is None:
            # user may not have resources in data zone, so corresponding quota size AVU may not
            # exist for this user
            uqDataZoneSize = -1
        else:
            uqDataZoneSize = float(uqDataZoneSize)
    except SessionException:
        # user may not have resources in data zone, so corresponding quota size AVU may not exist
        # for this user
        uqDataZoneSize = -1

    if uqDataZoneSize < 0:
        err_msg = 'no quota size AVU in data zone and user zone for user {}'.format(username)
        print(err_msg)
        raise ValidationError(err_msg)
    else:
        used_val = uqDataZoneSize
    return used_val


class Command(BaseCommand):
    help = "Output potential quota inconsistencies between iRODS and Django resource aggregate filesize for all users"

    def add_arguments(self, parser):
        parser.add_argument('output_file_name_with_path', type=str, help='output file name with path')
        parser.add_argument('--update', action='store_true', help='fix inconsistencies by recalculating in django')
        parser.add_argument('--reset', action='store_true', help='reset resource file size in django when inconsistent')
        parser.add_argument('--no_compare', action='store_true', help='reset/update filesizes without comparing quotas')
        parser.add_argument('--uid', type=str, help='filter to just a single user by uid')
        parser.add_argument('--min_quota_use_avu', type=int,
                            help='filter to just users with AVU quota use above this size in GB')
        parser.add_argument('--min_quota_django_model', type=int,
                            help='filter to django UserQuota use above this size in GB')
        parser.add_argument('--desc', action='store_true', help='order by descending quota use in iRODS Datazone')
        parser.add_argument('--rel_tol', help='relative tolerance for comparing quota sizes, default is 0.01')

    def handle(self, *args, **options):
        uid = options['uid'] if options['uid'] else None
        update = options['update'] if options['update'] else False
        desc = options['desc'] if options['desc'] else False
        reset = options['reset'] if options['reset'] else False
        no_compare = options['no_compare'] if options['no_compare'] else False
        min_quota_use_avu = int(options['min_quota_use_avu']) if options['min_quota_use_avu'] else 0
        min_quota_django_model = int(options['min_quota_django_model']) if options['min_quota_django_model'] else 0
        rel_tol = float(options['rel_tol']) if options['rel_tol'] else 0.01

        if no_compare:
            if not update and not reset:
                print('Error: --no_compare option must be used with --update or --reset option')
                return
            if options['rel_tol']:
                print('Warning: --rel_tol option is ignored when --no_compare is used')
                print('Update or reset will be done even if comparison is within the tolerance.')
            print('Using --no_compare option. Will reset/update file sizes even when no incosistency is detected.')

        if min_quota_use_avu and min_quota_django_model:
            print('Using --min_quota_use_avu and --min_quota_django_model')
            if min_quota_use_avu != min_quota_django_model:
                print('Warning: min_quota_use_avu and min_quota_django_model are different')
            print('First quotas will be filtered by django model. Then users will be filtered by iRODS AVU.')

        if update and reset:
            print('Cannot use both --update and --reset options together')
            return
        uqs = UserQuota.objects.filter(user__is_active=True) \
            .filter(user__is_superuser=False)
        if uid:
            try:
                user = User.objects.get(id=uid, is_active=True, is_superuser=False)
            except User.DoesNotExist:
                print(f'Active user with id {uid} not found')
            uqs = uqs.filter(user=user)
        if desc:
            uqs = uqs.order_by('-used_value')
        num_uqs = uqs.count()
        print(f"Number of user quotas to check: {num_uqs}")
        counter = 1
        csvfile = open(options['output_file_name_with_path'], 'w')
        w = csv.writer(csvfile)
        fields = [
            'User',
            'Starting summed resource sizes in Django',
            'Updated summed resource sizes in Django',
            'Quota reported in iRODS Datazone'
        ]
        w.writerow(fields)
        for uq in uqs:
            start_time = time.time()
            user = uq.user
            print("\n" + "*" * 80)
            print(f'{counter}/{num_uqs}: Checking quota for user {user.username}, {current_site}/user/{user.id}/')
            if min_quota_django_model > 0 and uq.used_value < min_quota_django_model:
                print(f"Skipping {user.username}. Use={uq.used_value}GB is less than {min_quota_django_model}")
                continue
            used_value_irods_dz = 0.0
            try:
                used_value_irods_dz = get_dz_quota_usage_from_irods(user.username)
            except ValidationError:
                # purposely ignore the error and continue to check for inconsistencies
                # assumes that the user may not have any resources in the data zone
                pass
            used_value_irods_dz = convert_file_size_to_unit(used_value_irods_dz, "gb")
            if used_value_irods_dz < min_quota_use_avu:
                print(f"Quota usage in iRODS Datazone AVU is below {min_quota_use_avu} GB. Skipping.")
                continue
            # sum the resources sizes for all resources that the user is the quota holder for
            owned_resources = user.uaccess.owned_resources
            # filter resources above size limit
            held_resources = []
            total_size = 0
            for res in owned_resources:
                if res.get_quota_holder() == user:
                    held_resources.append(res)
                    res_size = res.size
                    print(f"Resource {res.short_id} is held by {user.username}, size: {res_size} bytes")
                    total_size += res_size
            converted_total_size_django = convert_file_size_to_unit(int(total_size), 'gb')
            print(f"Quota usage in iRODS Datazone from AVU: {used_value_irods_dz} GB")
            print(f"Aggregate size of resources in Django: {converted_total_size_django} GB")
            is_close = math.isclose(used_value_irods_dz, converted_total_size_django, rel_tol=rel_tol)
            if not is_close or no_compare:
                django_updated = ''
                print('{} reported in django vs {} reported in iRODS for user {}'.format(
                    converted_total_size_django, used_value_irods_dz, user.username), flush=True)

                if update:
                    print("Attempting to fix any inconsistency by updating file sizes in django")
                    res_files = []
                    updated_size = 0
                    for res in held_resources:
                        res_files = res.files.exclude(_size=0)
                        num_files = res_files.count()
                        print(f"Total files in resource {res.short_id}: {num_files}")
                        if num_files == 0:
                            print(f"Resource {res.short_id} has no files.")
                            continue
                        print(f'{current_site}/resource/{res.short_id}: currently {res.size} bytes')
                        file_counter = 0
                        # exclude files with size 0 as they don't exist in iRODS
                        print("Updating files:")
                        for res_file in res_files.iterator():
                            # this is an expensive operation (3 irods calls per file) - about 1 min for 100 files
                            # size, checksum and modified time are obtained from irods and assigned to
                            # relevant fields of the resource file object
                            res_file.calculate_size(resource=res, save=False)
                            file_counter += 1
                            print(f"{file_counter}/{num_files}")
                            if res_file._size <= 0:
                                print(f"File {res_file.short_path} was not found in iRODS.")

                        ResourceFile.objects.bulk_update(res_files, '_size', batch_size=_BATCH_SIZE)
                        print(f"Updated {file_counter} files for resource {res.short_id}")
                        res.refresh_from_db()
                        print(f'{current_site}/resource/{res.short_id}: now {res.size} bytes')
                        # keep track of the updated size so that we can compare again
                        updated_size += res.size
                    converted_updated_size_django = convert_file_size_to_unit(int(updated_size), 'gb')
                    django_updated = converted_updated_size_django
                    if not math.isclose(used_value_irods_dz, converted_updated_size_django, rel_tol=rel_tol):
                        print("Even after updating, an inconsistency remains!")
                        print(f"Quota usage in iRODS Datazone AVU: {used_value_irods_dz} GB")
                        print(f"Updated Total size of resources in Django: {converted_updated_size_django} GB")

                elif reset:
                    print("Resetting file size cache in django")
                    for res in held_resources:
                        print(f'Resetting all filesizes in {current_site}/resource/{res.short_id}')
                        res.files.update(_size=-1)
                        # set the updated date to now so that nightly celery task can update the size
                        res.updated = now().isoformat()
                        res_modified_date = res.metadata.dates.all().filter(type='modified').first()
                        if res_modified_date:
                            res.metadata.update_element('date', res_modified_date.id)
                        else:
                            res.metadata.create_element('date', type='modified', start_date=res.updated)
                    django_updated = 'reset'
                else:
                    print('No action taken. Use --update or --reset to fix inconsistencies')
                w.writerow([uq.user.username, converted_total_size_django, django_updated, used_value_irods_dz])
            else:
                print(f"Quota deemed consistent for user {user.username}, using {rel_tol} relative tolerance")
            counter += 1
            # Print the amount of time spent for this user
            time_spent = time.time() - start_time
            print(f"Time spent for user {user.username}: {time_spent} seconds")
        csvfile.close()
        print("Done")
