from django.core.management.base import BaseCommand

from hs_core.models import BaseResource
from hs_core.hydroshare import set_dirty_bag_flag


class Command(BaseCommand):
    help = "Copies license URL as license statement if a value for license is missing in any resource"

    def handle(self, *args, **options):
        resource_counter = 0
        print(f"Total resources found:{BaseResource.objects.count()}")
        for res in BaseResource.objects.all().iterator():
            res = res.get_content_model()
            if res.metadata is None:
                print(f"Not fixing license. Metadata object is missing for this resource:{res.short_id}")
                continue
            rights = res.metadata.rights
            if rights is None:
                print(f"Not fixing license. Rights metadata object is missing for this resource:{res.short_id}")
                continue

            if len(rights.statement.strip()) == 0:
                rights.statement = rights.url
                rights.save()
                set_dirty_bag_flag(res)
                resource_counter += 1
                print(f"Fixed license for resource:{res.short_id}")

        print(f"Number of resources for which licence was fixed:{resource_counter}")
