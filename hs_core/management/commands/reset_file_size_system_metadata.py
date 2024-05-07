
import time
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.db.models import Q

from hs_core.hydroshare import current_site_url
from hs_core.models import ResourceFile, BaseResource
from theme.models import UserQuota

current_site = current_site_url()
_BATCH_SIZE = settings.BULK_UPDATE_CREATE_BATCH_SIZE


def chunked_queryset(queryset, chunk_size=_BATCH_SIZE):
    """Slice a queryset into chunks.
    Code adapted from https://djangosnippets.org/snippets/10599/
    """
    if not queryset.exists():
        return
    queryset = queryset.order_by("pk")
    pks = queryset.values_list("pk", flat=True)
    start_pk = pks[0]
    while True:
        try:
            end_pk = pks.filter(pk__gte=start_pk)[chunk_size]
        except IndexError:
            break
        yield queryset.filter(pk__gte=start_pk, pk__lt=end_pk)
        start_pk = end_pk
    yield queryset.filter(pk__gte=start_pk)


def update_file_sizes(resources, refreshed_weeks=None, modified_weeks=None):
    total_resources = len(resources)
    print(f"Updating file sizes for {total_resources} resources in Django")
    res_count = 1
    for res in resources:
        print(f"\n{res_count}/{total_resources}: Updating file sizes for resource {res.short_id}")
        start_time = time.time()
        res_files = filter_files(res.files, refreshed_weeks=refreshed_weeks, modified_weeks=modified_weeks)
        num_files = res_files.count()
        print(f"Total files to update from resource {res.short_id}: {num_files}")
        if num_files == 0:
            print(f"Resource {res.short_id} has no files")
            continue
        print(f'{current_site}/resource/{res.short_id}: currently {res.size} bytes')
        file_counter = 0
        print("Updating files:", end=' ')
        for res_file in res_files.iterator():
            res_file.calculate_size(resource=res, save=True)
            file_counter += 1
            print(file_counter, end=', ')
            if res_file._size <= 0:
                print(f"File {res_file.short_path} was not found in iRODS.")
        time_spent = time.time() - start_time
        print(f"\nTime spent for resource {res.short_id}: {time_spent} seconds")
        print(f"Updated {file_counter} files for resource {res.short_id}")
        res_count += 1


def filter_files(file_queryset, refreshed_weeks=None, modified_weeks=None):
    if refreshed_weeks:
        print(f"Only including files whose metadata has not been refreshed in the last {refreshed_weeks} weeks")
        cuttoff_time = timezone.now() - timedelta(weeks=refreshed_weeks)
        file_queryset = file_queryset.filter(Q(filesize_cache_updated__lte=cuttoff_time)
                                             | Q(filesize_cache_updated__isnull=True))
    if modified_weeks:
        print(f"Only including resource files that have been modified in the last {modified_weeks} weeks")
        cuttoff_time = timezone.now() - timedelta(weeks=modified_weeks)
        file_queryset = file_queryset.filter(_modified_time__gte=cuttoff_time)
    return file_queryset


class Command(BaseCommand):
    help = "Reset the filesize cached in django. Optionally update the file size cache by querying iRODS."

    def add_arguments(self, parser):
        parser.add_argument('--update', action='store_true', help='update file size cache in Django by querying iRODS')
        parser.add_argument('--uid', type=int, help='filter to just a single user by uid')
        parser.add_argument('--resource_id', type=str , help='filter to just a single resource by id')
        parser.add_argument('--min_quota_django_model', type=int, help='filter to django UserQuota above this (in GB)')
        parser.add_argument('--refreshed_weeks', type=int, dest='refreshed_weeks',
                            help='include files not refreshed in the last X weeks')
        parser.add_argument('--modified_weeks', type=int,
                            help='include files that have been modified in the last X weeks')

    def handle(self, *args, **options):
        update = options['update'] if options['update'] else False
        uid = options['uid'] if options['uid'] else None
        resource_id = options['resource_id'] if options['resource_id'] else None
        min_quota_django_model = int(options['min_quota_django_model']) if options['min_quota_django_model'] else 0
        refreshed_weeks = options['refreshed_weeks'] if options['refreshed_weeks'] else None
        modified_weeks = options['modified_weeks'] if options['modified_weeks'] else None

        resources_to_modify = []

        if resource_id:
            if min_quota_django_model or uid:
                raise CommandError("Cannot filter by resource_id in addition to min_quota_django_model or uid")
            try:
                res = BaseResource.objects.get(short_id=resource_id)
                resources_to_modify = [res]
            except ObjectDoesNotExist as e:
                print(f"Resource with id {resource_id} not found: {e}")
                raise CommandError(f"Resource with id {resource_id} not found: {e}")
        elif uid:
            if min_quota_django_model:
                raise CommandError("Cannot filter by uid in addition to min_quota_django_model")
            try:
                user = User.objects.get(id=uid, is_active=True, is_superuser=False)
                resources_to_modify = user.uaccess.owned_resources
            except User.DoesNotExist:
                print(f'Active user with id {uid} not found')
        elif min_quota_django_model > 0:
            uqs = UserQuota.objects.filter(user__is_active=True) \
                .filter(user__is_superuser=False)
            if min_quota_django_model > 0:
                uqs = uqs.filter(used_value__gt=min_quota_django_model).order_by('-used_value')
            num_uqs = uqs.count()
            counter = 1
            print(f'Found {num_uqs} users with quota above {min_quota_django_model} GB')
            start_time = time.time()
            for uq in uqs:
                user = uq.user
                print(f'{counter}/{num_uqs}: \
                      Getting resources for user: {user.username}, {current_site}/user/{user.id}/')
                owned_resources = user.uaccess.owned_resources
                for res in owned_resources:
                    if res.get_quota_holder() == user:
                        resources_to_modify.append(res)
                counter += 1
            time_spent = time.time() - start_time
            print(f"Time spent collecting resources for {num_uqs} users: {time_spent} seconds")
        else:
            res_files = ResourceFile.objects.all()
            if not refreshed_weeks and not modified_weeks:
                # updating all files will time out, so we don't permit it.
                raise CommandError("No filter specified. You must specify at least one filter.")
            res_files = filter_files(res_files, refreshed_weeks=refreshed_weeks, modified_weeks=modified_weeks)
            num_files = res_files.count()
            print(f"Total files: {num_files}")
            if update and num_files > 0:
                file_counter = 1
                chunk_number = 1
                for chunk in chunked_queryset(res_files):
                    start_time = time.time()
                    print(f"Chunk {chunk_number}/{(num_files // _BATCH_SIZE) + 1}")
                    for res_file in chunk.iterator():
                        print(file_counter, end=', ')
                        res_file.calculate_size(resource=res_file.resource, save=True)
                        file_counter += 1
                    time_spent = time.time() - start_time
                    print(f"Time spent for chunk {chunk_number}: {time_spent} seconds")
                    chunk_number += 1
            else:
                # reset the cache for the files
                res_files.update(_size=-1)
            print("Done")
            return

        if update:
            update_file_sizes(resources_to_modify, refreshed_weeks=refreshed_weeks, modified_weeks=modified_weeks)
        else:
            for res in resources_to_modify:
                print(f'Resetting filesizes in {current_site}/resource/{res.short_id}')

                # using res.files instead of res.files.exclude(size=0) in case 0 values are cached incorrectly
                res_files = filter_files(res.files, refreshed_weeks=refreshed_weeks, modified_weeks=modified_weeks)
                res_files.update(_size=-1)

                # set the updated date to now so that nightly celery task can update the size
                res.updated = timezone.now().isoformat()
                res_modified_date = res.metadata.dates.all().filter(type='modified').first()
                if res_modified_date:
                    res.metadata.update_element('date', res_modified_date.id)
                else:
                    res.metadata.create_element('date', type='modified', start_date=res.updated)
        print("Done")
