from django.core.management.base import BaseCommand

from hs_file_types.utils import get_supported_aggregation_types
from hs_tools_resource.models import ToolResource


class Command(BaseCommand):
    help = "Migrate tool resource metadata old fields to new fields."

    def handle(self, *args, **options):
        res_count = ToolResource.objects.count()
        log_msg = f"Total Tool Resources:{res_count}"
        print(log_msg)
        res_count = 0
        system_supported_aggr_type_names = get_supported_aggregation_types().keys()
        for res in ToolResource.objects.all().iterator():
            if res.metadata is None:
                log_msg = f"Tool Resource with ID:{res.short_id} missing metadata object. Skipping this resource"
                print(log_msg, flush=True)
                continue
            res_count += 1
            print(f"Migrating metadata for Tool Resource:{res.short_id}", flush=True)
            print("=" * 50)
            supported_aggr_type = res.metadata._deprecated_supported_agg_types.first()
            if supported_aggr_type is not None:
                print(f"Migrating supported aggregation types from deprecated field:")
                aggr_types = [aggr_type.description for aggr_type in supported_aggr_type.supported_agg_types.all()]
                print(aggr_types)
                for aggr_type in aggr_types:
                    if aggr_type in system_supported_aggr_type_names and \
                            aggr_type not in res.metadata.supported_agg_types:
                        res.metadata.supported_agg_types.append(aggr_type)
                res.metadata.save()
                print("Migrated supported aggregation types to new field:")
                print(res.metadata.supported_agg_types, flush=True)
            print("-" * 50)
