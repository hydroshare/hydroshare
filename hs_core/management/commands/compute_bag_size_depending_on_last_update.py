import math
from django.core.management.base import BaseCommand, CommandError

from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Compute the size of the bagit archive size/storage for resources that haven't been updated recently"

    def add_arguments(self, parser):

        parser.add_argument('--weeks', type=int, dest='weeks', help='include res not updated in the last X weeks')

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

        if weeks:
            print(f"FILTERING TO INCLUDE RESOURCES NOT UPDATED IN UPDATED IN LAST {weeks} WEEKS")
            add_message = f"for resources not updated in last {weeks} weeks"
            cuttoff_time = timezone.now() - timedelta(weeks=weeks)
            resources = resources.filter(updated__lte=cuttoff_time)
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
                fsize = istorage.size(src_file)
                cumulative_size += fsize
                print(f"Size for {src_file} = {fsize}")
            except ValidationError as ve:
                print(f"Size not computed for {res.short_id}: {ve}")
            counter += 1
        converted_size = self.convert_size(cumulative_size)
        print(f"Total cumulative size {add_message}: {converted_size}")
