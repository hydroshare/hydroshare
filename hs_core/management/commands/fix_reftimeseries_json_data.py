from django.core.management.base import BaseCommand

from hs_file_types.models import RefTimeseriesLogicalFile


class Command(BaseCommand):
    help = "Saves content of resource file (json data file) in ref timeseries logical file metadata field " \
           "json_file_content"

    def handle(self, *args, **options):
        aggr_counter = 0
        print(f"Total Ref Timeseries Aggregations found:{RefTimeseriesLogicalFile.objects.count()}")
        for aggr in RefTimeseriesLogicalFile.objects.all().iterator():
            res_json_file = aggr.files.all().first()
            if res_json_file:
                if res_json_file.resource_file:
                    json_file_content = res_json_file.resource_file.read()
                else:
                    json_file_content = res_json_file.fed_resource_file.read()
                aggr.metadata.json_file_content = json_file_content.decode()
                aggr.metadata.save()
                msg = "Saved json file data to aggregation metadata field for aggregation:"
                print(msg)
                print(res_json_file.storage_path)
                print()
                aggr_counter += 1
            else:
                print("Aggregation json file was not found")

        print(f"Number of Ref Timeseries Aggregations updated:{aggr_counter}")
