from django.core.management.base import BaseCommand, CommandError

from hs_core.hydroshare import deposit_res_metadata_with_crossref
from hs_core.models import BaseResource
from hs_core import hydroshare
from requests.exceptions import HTTPError


class Command(BaseCommand):
    help = "Update crossref metadata deposit for all published resources"

    def handle(self, *args, **options):
        site_url = hydroshare.utils.current_site_url()
        res_count = BaseResource.objects.filter(raccess__published=True).count()
        print(f"Total published resources to process: {res_count}")
        counter = 0
        failures = {}
        for resource in BaseResource.objects.filter(raccess__published=True):
            print(f"{counter}. Attempting to deposit metadata to crossref for res id {resource.short_id}")
            try:
                resource = resource.get_content_model()
                response = deposit_res_metadata_with_crossref(resource)
                if not response.status_code == 200:
                    err_msg = (f"Received a {response.status_code} from Crossref while depositing "
                               f"metadata for res id {resource.short_id}")
                    raise HTTPError(err_msg)
                print(f"Successfully deposited metadata to crossref for res id {resource.short_id}")
            except (ValueError, HTTPError) as e:
                print(f"Failed depositing metadata to crossref for res id {resource.short_id}")
                print(e)
                res_url = site_url + resource.absolute_url
                failures[res_url] = str(e)
            finally:
                counter += 1
        if failures:
            print(f"{len(failures)} failures:")
            for url, err in failures.items():
                print(url)
                print(err)
            raise CommandError("One or more Crossref deposits failed")
        print("Success")
