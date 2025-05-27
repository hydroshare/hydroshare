from django.core.management.base import BaseCommand, CommandError

from hs_core.enums import CrossRefSubmissionStatus
from hs_core.hydroshare import deposit_res_metadata_with_crossref
from hs_core.models import BaseResource
from hs_core import hydroshare
from requests.exceptions import HTTPError


class Command(BaseCommand):
    help = "Update crossref metadata deposit for published resources that are stuck in pending state"

    def handle(self, *args, **options):
        site_url = hydroshare.utils.current_site_url()
        bad_resources = BaseResource.objects.filter(
            raccess__published=True,
            doi__endswith=CrossRefSubmissionStatus.PENDING)
        res_count = bad_resources.count()
        print(f"Total published resources to process: {res_count}")
        counter = 0
        failures = {}
        for resource in bad_resources:

            # update the doi to swap CrossRefSubmissionStatus.PENDING with CrossRefSubmissionStatus.PENDING.value
            resource.doi = resource.doi.replace(
                CrossRefSubmissionStatus.PENDING, CrossRefSubmissionStatus.PENDING.value
            )
            resource.save()

            # update all of the res.metadata.identifiers that have name="doi" to use the enum value
            identifier = resource.metadata.identifiers.filter(name="doi").first()
            if identifier:
                # .update() doesn't work because we don't permit modification of the doi field using that method
                # identifier.update(identifier.id, url=resource.doi) # this doesn't work
                identifier.url = resource.doi
                identifier.save()
                print(f"Updated DOI in metadata for resource {resource.short_id} to {resource.doi}")
            else:
                print(f"No DOI identifier found in metadata for resource {resource.short_id}")

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
