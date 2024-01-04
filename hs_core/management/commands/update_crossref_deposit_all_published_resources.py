from django.core.management.base import BaseCommand, CommandError

from hs_core.hydroshare import deposit_res_metadata_with_crossref
from hs_core.models import BaseResource


class Command(BaseCommand):
    help = "Update crossref metadata deposit for all published resources"

    def handle(self, *args, **options):
        res_count = BaseResource.objects.filter(raccess__published=True).count()
        print(f"Total published resources to process: {res_count}")
        counter = 0
        for resource in BaseResource.objects.filter(raccess__published=True):
            resource = resource.get_content_model()
            response = deposit_res_metadata_with_crossref(resource)
            if not response.status_code == 200:
                err_msg = (f"Received a {response.status_code} from Crossref while depositing "
                           f"metadata for res id {resource.short_id}")
                raise CommandError(err_msg)
            counter += 1
            print(f"{counter}. Successfully deposited metadata to crossref for res id {resource.short_id}")
