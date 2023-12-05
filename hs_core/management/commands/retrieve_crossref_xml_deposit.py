import requests

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_core.enums import CrossRefSubmissionStatus


class Command(BaseCommand):
    help = "Retrieves metadata deposit from crossref for a published resource"

    def add_arguments(self, parser):
        # ID of a published resource for which metadata needs to be retrieved from crossref
        parser.add_argument(
            "resource_id",
            type=str,
            help="Required. The existing id (short_id) of" " the published resource",
        )

    def handle(self, *args, **options):
        if not options["resource_id"]:
            raise CommandError("resource_id argument is required")
        res_id = options["resource_id"]
        try:
            resource = get_resource_by_shortkey(res_id, or_404=False)
        except ObjectDoesNotExist:
            raise CommandError("No Resource found for id {}".format(res_id))
        if not resource.raccess.published:
            raise CommandError("Resource is not a published resource")
        if CrossRefSubmissionStatus.PENDING in resource.doi:
            raise CommandError(
                "Resource has a pending crossref deposit request. Please try again later."
            )
        if CrossRefSubmissionStatus.FAILURE in resource.doi:
            raise CommandError("Crossref for metadata deposit request for this resource has failed.")

        # make a request to crossref to get the xml deposit for this resource
        # here is the url format for crossref to get the xml deposit for a resource:
        # https://doi.crossref.org/servlet/query?pid={email}&format=unixref&id={DOI}

        res_doi = resource.doi[len("https://doi.org/"):]
        email = settings.DEFAULT_SUPPORT_EMAIL
        url = f"https://doi.crossref.org/servlet/query?pid={email}&format=unixref&id={res_doi}"
        requests.packages.urllib3.disable_warnings()  # turn off SSL warnings
        print(
            f"Retrieving metadata deposit for res id {res_id}, DOI:{res_doi} from crossref"
        )
        print()
        response = requests.get(url, verify=False)
        if not response.status_code == 200:
            err_msg = (
                f"Received a {response.status_code} from Crossref while retrieving "
                f"metadata for res id {res_id}"
            )
            raise CommandError(err_msg)
        else:
            print(f"Successfully retrieved metadata from crossref for res id {res_id}")
            print()
            print(response.text)
