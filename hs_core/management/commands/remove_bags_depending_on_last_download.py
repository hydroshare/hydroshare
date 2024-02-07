import math
from django.core.management.base import BaseCommand

from hs_core.models import BaseResource, CoreMetaData
from django.core.exceptions import ValidationError
from hs_core.hydroshare.hs_bagit import delete_bag
from hs_core.hydroshare.utils import set_dirty_bag_flag
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Remove bags for resources that haven't been downloaded recently"

    def add_arguments(self, parser):

        parser.add_argument('--weeks', type=int, dest='weeks', help='include res not downloaded in the last X weeks')

        parser.add_argument(
            '--published',
            action='store_true',  # True for presence, False for absence
            dest='published',  # value is options['published']
            help='filter to include only published resources')

        parser.add_argument(
            '--dryrun',
            action='store_true',
            dest='dryrun',
            default=False,
            help='Show cumulative size of bags to be removed without actually removing them',
        )

    def convert_size(self, size_bytes):
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return "%s %s" % (s, size_name[i])

    def handle(self, *args, **options):
        resources = []
        add_message = ""
        weeks = options['weeks']
        resources = BaseResource.objects.all()
        dryrun = options['dryrun']

        if weeks:
            print(f"FILTERING TO INCLUDE RESOURCES THAT HAVE NOT BEEN DOWNLOADED IN THE LAST {weeks} WEEKS")
            add_message += f" (including only resources not downloaded in last {weeks} weeks)"
            cuttoff_time = timezone.now() - timedelta(weeks=weeks)
            meta_ids = CoreMetaData.objects.filter(Q(dates__type="bag_last_downloaded"),
                                                   Q(dates__start_date__isnull=True)
                                                   | Q(dates__start_date__lte=cuttoff_time)
                                                   ).values_list('id', flat=True)
            resources = BaseResource.objects.filter(object_id__in=meta_ids)

        if options['published']:
            print("FILTERING TO INCLUDE ONLY PUBLISHED RESOURCES")
            add_message += " (including only published resources)"
            resources = resources.filter(raccess__published=True)
        if dryrun:
            print("Dry run mode: bags will not be removed. Size will be shown.")
            add_message += " (dry run)"
        cumulative_size = 0
        count = len(resources)
        counter = 1
        print(f"Iterating {count} resources...")
        for res in resources:
            converted_size = self.convert_size(cumulative_size)
            print(f"{counter}/{count}: cumulative thus far = {converted_size}")
            try:
                src_file = res.bag_path
                istorage = res.get_irods_storage()
                if not dryrun:
                    delete_bag(res, istorage)
                    set_dirty_bag_flag(res)
                fsize = istorage.size(src_file)
                cumulative_size += fsize
                print(f"Size for {src_file} = {fsize}")
            except ValidationError as ve:
                print(f"Bag not removed for {res.short_id}: {ve}")
            counter += 1
        converted_size = self.convert_size(cumulative_size)
        print(f"Total cumulative size{add_message}: {converted_size}")
