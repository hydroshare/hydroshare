import csv
from django.core.management.base import BaseCommand
from hs_core.hydroshare.utils import get_resource_by_shortkey


class Command(BaseCommand):
    help = "Fix updated date for resources fixed by fix_resource_versioning management command to address issue #4473"

    def add_arguments(self, parser):
        # csv filename with full path to load versioning chain violation resources from
        parser.add_argument('input_file', help='input csv file name with full path to load resource date to fix')

    def handle(self, *args, **options):
        input_file = options['input_file']
        with open(input_file) as f:
            reader = csv.reader(f)
            count = 0
            res_col = 0
            date_col = 1
            for row in reader:
                res_id = row[res_col]
                res_date = row[date_col]
                try:
                    res = get_resource_by_shortkey(res_id)
                except Exception:
                    print(f'Resource {res_id} does not exist', flush=True)
                    continue
                res.updated = res_date
                if res.metadata.dates.all().filter(type='modified'):
                    res_modified_date = res.metadata.dates.all().filter(type='modified')[0]
                    res_modified_date.start_date = res_date
                    res_modified_date.save()
                res.save()
                count += 1
            print(f"{count} resources have been updated with the correct date")
