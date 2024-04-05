
import csv
import math
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.conf import settings
from django_irods.icommands import SessionException

from django_irods.storage import IrodsStorage
from hs_core.hydroshare import convert_file_size_to_unit
from theme.models import UserQuota
from hs_core.hydroshare import current_site_url
from hs_core.models import ResourceFile

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
        parser.add_argument('output_file_name_with_path', help='output file name with path')
        parser.add_argument('--update', action='store_true', help='fix inconsistencies by recalculating in django')
        parser.add_argument('--reset', action='store_true', help='reset resource file size in django when inconsistent')
        parser.add_argument('--uid', help='filter to just a single user by uid')

    def handle(self, *args, **options):
        quota_report_list = []
        uid = options['uid'] if options['uid'] else None
        update = options['update']
        reset = options['reset']

        if update and reset:
            print('Cannot use both --update and --reset options together')
            return
        uqs = UserQuota.objects.filter(user__is_active=True).filter(user__is_superuser=False)
        if uid:
            uqs = uqs.filter(user__id=uid)
        for uq in uqs:
            user = uq.user
            print("\n" + "*" * 80)
            print(f'Checking quota for user {user.username}, {current_site}/user/{user.id}/')
            used_value_irods_dz = 0.0
            try:
                used_value_irods_dz = get_dz_quota_usage_from_irods(user.username)
            except ValidationError:
                pass
            used_value_irods_dz = convert_file_size_to_unit(used_value_irods_dz, "gb")
            print(f"Quota usage in iRODS Datazone: {used_value_irods_dz} GB")

            # sum the resources sizes for all resources that the user is the quota holder for
            owned_resources = user.uaccess.owned_resources
            held_resources = []
            total_size = 0
            for res in owned_resources:
                if res.get_quota_holder() == user:
                    held_resources.append(res)
                    res_size = res.size
                    print(f"Resource {res.short_id} is held by {user.username}, size: {res_size} bytes")
                    total_size += res_size
            converted_total_size_django = convert_file_size_to_unit(int(total_size), 'gb')
            print(f"Total size of resources in Django: {converted_total_size_django} GB")

            if not math.isclose(used_value_irods_dz, converted_total_size_django, abs_tol=0.1):
                # report inconsistency
                report_dict = {
                    'user': uq.user.username,
                    'django': converted_total_size_django,
                    'irods': used_value_irods_dz}
                quota_report_list.append(report_dict)
                print('quota incosistency: {} reported in django vs {} reported in iRODS for user {}'.format(
                    converted_total_size_django, used_value_irods_dz, user.username), flush=True)

                if update:
                    print("Attempting to fix the inconsistency by updating file sizes in django")
                    res_files = []
                    for res in held_resources:
                        print(f"Total files in resource {res.short_id}: {res.files.all().count()}")
                        print(f'{current_site}/resource/{res.short_id}: currently {res.size} bytes')
                        file_counter = 0
                        # exclude files with size 0 as they don't exist in iRODS
                        for res_file in res.files.exclude(_size=0).iterator():
                            # this is an expensive operation (3 irods calls per file) - about 1 min for 100 files
                            # size, checksum and modified time are obtained from irods and assigned to
                            # relevant fields of the resource file object
                            res_file.set_system_metadata(resource=res, save=False)
                            res_files.append(res_file)
                            file_counter += 1
                            print(f"Updated file count: {file_counter}")
                            if res_file._size <= 0:
                                print(f"File {res_file.short_path} was not found in iRODS.")

                        if res_files:
                            ResourceFile.objects.bulk_update(res_files,
                                                             ResourceFile.system_meta_fields(), batch_size=_BATCH_SIZE)
                            print(f"Updated {file_counter} files for resource {res.short_id}")
                            res.refresh_from_db()
                            print(f'{current_site}/resource/{res.short_id}: now {res.size} bytes')
                        else:
                            print(f"Resource {res.short_id} contains no files.")

                elif reset:
                    print("Resetting file size cache in django")
                    for res in held_resources:
                        print(f'Resetting all filesizes in {current_site}/resource/{res.short_id}')
                        res.files.update(_size=-1)
                else:
                    print('No action taken. Use --update or --reset to fix inconsistencies')

        if quota_report_list:
            with open(options['output_file_name_with_path'], 'w') as csvfile:
                w = csv.writer(csvfile)
                fields = [
                    'User',
                    'Usage of summed resource sizes in Django',
                    'Quota reported in iRODS Datazone'
                ]
                w.writerow(fields)

                for q in quota_report_list:
                    values = [
                        q['user'],
                        q['django'],
                        q['irods']
                    ]
                    w.writerow([str(v) for v in values])
        else:
            print('No quota inconsistencies found')
