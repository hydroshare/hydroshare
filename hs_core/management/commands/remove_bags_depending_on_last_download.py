import math

from datetime import timedelta
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from hs_core.models import BaseResource
from hs_core.hydroshare.hs_bagit import delete_bag
from hs_core.hydroshare.utils import set_dirty_bag_flag


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

        parser.add_argument(
            '--dirty',
            action='store_true',
            dest='dirty',
            default=False,
            help='Only remove bags that have the bag_modified flag set. \
            For removing bags that have been modified since the last download.',
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
        dirty = options['dirty']

        if weeks:
            if weeks < 8 and not dirty:
                raise ValidationError("--weeks must be at least 8 weeks. This is to prevent deleting all bags.")
            print(f"FILTERING TO INCLUDE RESOURCES THAT HAVE NOT BEEN DOWNLOADED IN THE LAST {weeks} WEEKS")
            add_message += f" (including only resources not downloaded in last {weeks} weeks)"
            cuttoff_time = timezone.now() - timedelta(weeks=weeks)
            resources = BaseResource.objects.filter(Q(bag_last_downloaded__lte=cuttoff_time)
                                                    | Q(bag_last_downloaded__isnull=True))
        else:
            if not dryrun and not dirty:
                raise ValidationError("Must specify either --weeks, --dryrun, or --dirty to prevent removing all bags.")

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
            if dirty and not res.getAVU('bag_modified'):
                print(f"Skipping {res.short_id} because the bag is not dirty")
                continue
            try:
                src_file = res.bag_path
                istorage = res.get_irods_storage()
                fsize = istorage.size(src_file)
                if not dryrun:
                    delete_bag(res, istorage, raise_on_exception=True)
                    set_dirty_bag_flag(res)
                cumulative_size += fsize
                print(f"Size for {src_file} = {fsize}")
            except Exception as e:
                print(f"Issue removing bag for {res.short_id}: {e}")
            counter += 1
        converted_size = self.convert_size(cumulative_size)
        print(f"Total cumulative size{add_message}: {converted_size}")
