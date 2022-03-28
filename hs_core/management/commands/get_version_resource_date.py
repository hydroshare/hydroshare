import csv
from django.core.management.base import BaseCommand
from hs_core.hydroshare.utils import get_resource_by_shortkey


class Command(BaseCommand):
    help = "Output last modified date for resources in the input list with three columns, version_of_resource, " \
           "resource, and replaced_by_resource, which was used also for fixing resources with versioning chain " \
           "violations. This command was written to fix last modified date resulting from fixing resource with " \
           "versioning chain violations by retrieving a database file with correct last modified data and update " \
           "those resources affected by running versioning chain fix management command with correct last modified date"

    def add_arguments(self, parser):
        # csv filename with full path to load versioning chain violation resources from
        parser.add_argument('input_file', help='input csv file name with full path to be processed and '
                                               'load versioning chain violation resources from')

    def handle(self, *args, **options):
        input_file = options['input_file']
        wf = open('version_res_date.csv', 'w')
        writer = csv.writer(wf)
        with open(input_file) as f:
            reader = csv.reader(f)
            headers = next(reader)
            version_of_col = 0
            res_col = 1
            replace_by_col = 2
            if len(headers) < 3 or headers[version_of_col].lower() != 'isversionof' or \
                    headers[res_col].lower() != 'resource' \
                    or headers[replace_by_col].lower() != 'isreplacedby':
                print('headers are not correct, exit', flush=True)
                return
            res_list = []
            for row in reader:
                if row[version_of_col]:
                    res_list.append(row[version_of_col])
                if row[res_col]:
                    res_list.append(row[res_col])
                if row[replace_by_col]:
                    res_list.append(row[replace_by_col])
            print(len(res_list))
            res_list = set(res_list)
            for res_id in res_list:
                try:
                    res = get_resource_by_shortkey(res_id)
                except Exception:
                    print(f'Resource {res_id} does not exist', flush=True)
                    continue
                # note that res.updated cannot be used to retrieve last modified date for a resource since updated
                # field is defined in a TimeStamped model in Mezzanine which was inherited by Displayable model
                # which was linked to Mezzanine pages. Since HydroShare resources are Mezzanina pages, all HydroShare
                # resources have this updated field. This updated field is updated more often than when HydroShare was
                # really modified from Mezzanine, so it cannot be used to indicate the last updated date for HydroShare
                # resources. Instead, HydroShare dates metadata data needs to be checked to retrieve the last updated
                # date for HydroShare resources
                writer.writerow([res_id, res.metadata.dates.all().filter(type='modified')[0].start_date])
            wf.close()
