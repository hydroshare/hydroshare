import logging
import requests
import base64
import time
import json
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand

from hs_core.models import BaseResource
from hs_core.hydroshare.resource import get_datacite_url

logger = logging.getLogger(__name__)


def deposit_res_metadata_with_datacite(res, datacite_url, test_mode=False):
    """
    Deposit resource metadata with DataCite using the Fabrica-style payload.
    """
    print(f"Depositing metadata for resource {res.short_id} with DataCite...")

    try:
        # Get the JSON payload and modify it for testing
        json_payload = res.get_datacite_deposit_json(test_mode=test_mode)

        # Parse the JSON so we can modify it for test mode
        payload_dict = json.loads(json_payload)

        # For test mode, modify the payload
        if test_mode:
            # Remove the "event" attribute from attributes
            if "event" in payload_dict["data"]["attributes"]:
                del payload_dict["data"]["attributes"]["event"]
                print("🚧 TEST MODE: Removed 'event' attribute from payload")

            # Also ensure suffix has "-test4" appended
            original_suffix = payload_dict["data"]["attributes"].get("suffix", "")
            if not original_suffix.endswith("-test4"):
                new_suffix = (
                    f"{original_suffix}-test4"
                    if not original_suffix.endswith("-test")
                    else original_suffix.replace("-test", "-test4")
                )
                payload_dict["data"]["attributes"]["suffix"] = new_suffix
                print(f"🚧 TEST MODE: Updated suffix to '{new_suffix}'")

            # also ensure that the identifier uses the test prefix
            original_doi = payload_dict["data"]["attributes"]['identifiers'][0].get("identifier", "")
            new_identifier = f"{original_doi}-test4"
            payload_dict["data"]["attributes"]['identifiers'][0]["identifier"] = new_identifier
            print(f"🚧 TEST MODE: Updated identifier to '{new_identifier}'")

            # update the doi as well
            original_doi_value = payload_dict["data"]["attributes"].get("doi", "")
            new_doi_value = f"{original_doi_value}-test4"
            payload_dict["data"]["attributes"]["doi"] = new_doi_value
            print(f"🚧 TEST MODE: Updated doi to '{new_doi_value}'")

        # For debugging: print the JSON being sent
        print("JSON Payload being sent:")
        print(json.dumps(payload_dict, indent=2))

        if test_mode:
            print(f"🚧 TEST MODE: Would deposit metadata for resource {res.short_id}")
            print(f"🚧 TEST MODE: Using URL: {get_datacite_url()}")
            print("🚧 TEST MODE: Payload prepared with 'test2' suffix and no 'event' attribute")

        # Convert back to JSON string for the actual API call
        json_payload = json.dumps(payload_dict)

        token = base64.b64encode(
            f"{settings.DATACITE_USERNAME}:{settings.DATACITE_PASSWORD}".encode()
        ).decode()
        headers = {
            "accept": "application/vnd.api+json",
            "content-type": "application/json",
            "authorization": f"Basic {token}"
        }

        response = requests.post(
            url=get_datacite_url(),
            data=json_payload,
            headers=headers,
            timeout=10
        )

        if 400 <= response.status_code < 500:
            print(f"⚠️ Client error (4xx) for resource {res.short_id}: {response.text}")
            return None

        print(f"Response status code: {response.status_code}")
        print(f"Response text: {response.text}")
        response.raise_for_status()
        print(f"✅ Metadata deposited successfully with DataCite for resource {res.short_id}")
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error depositing metadata with DataCite for {res.short_id}: {e}")
        return None


class Command(BaseCommand):
    help = "Migrate all resources from Crossref to DataCite"

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Run in test mode (does not make actual API calls)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=1,
            help='Limit the number of resources to process (default: 1)',
        )

    def handle(self, *args, **options):
        datacite_url = f"{get_datacite_url()}/hs.{settings.DATACITE_PREFIX}"
        start_time = time.time()
        published_resources = BaseResource.objects.filter(raccess__published=True)

        total = published_resources.count()
        print(f"📦 Total published resources to process: {total}")
        print(f"🎯 Processing limit: {options['limit']}")
        print(f"🧪 Test mode: {'ON' if options['test'] else 'OFF'}")

        count = 0
        limit = options['limit']

        for res in published_resources.iterator():
            if count >= limit:
                print(f"⏹️ Reached limit of {limit} resources. Stopping.")
                break

            res = res.get_content_model()
            if not res.metadata:
                logger.warning(f"Resource {res.short_id} has no metadata. Skipping.")
                continue

            print(f"\n{'=' * 80}")
            print(f"🔄 Processing resource {count + 1}/{limit}: {res.short_id}")
            print(f"{'=' * 80}")
            res_start_time = time.time()

            result = deposit_res_metadata_with_datacite(res, datacite_url, test_mode=options['test'])
            if result is None:
                print(f"❌ Failed to deposit metadata for resource {res.short_id}.")
            else:
                print(f"✅ Successfully processed resource {res.short_id}.")
            res_duration = timedelta(seconds=int(time.time() - res_start_time))
            print(f"✅ Finished processing resource: {res.short_id} | {res.metadata.title} | Time taken: {res_duration}")
            count += 1

        total_duration = timedelta(seconds=int(time.time() - start_time))
        print(f"🎉 Finished processing {count} resources | Time taken: {total_duration}")
