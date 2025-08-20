import logging
import requests
import base64

from django.conf import settings
from django.core.management.base import BaseCommand

from hs_core.models import BaseResource

logger = logging.getLogger(__name__)


def deposit_res_metadata_with_datacite(res):
    """
    Deposit resource metadata with DataCite using the Fabrica-style payload.
    """
    print(f"Depositing metadata for resource {res.short_id} with DataCite...")
    try:
        token = base64.b64encode(
            f"{settings.DATACITE_USERNAME}:{settings.DATACITE_PASSWORD}".encode()
        ).decode()
        headers = {
            "accept": "application/vnd.api+json",
            "content-type": "application/json",
            "authorization": f"Basic {token}"
        }

        response = requests.post(
            url=settings.DATACITE_API_URL,
            data=res.get_datacite_deposit_json(),
            headers=headers,
            timeout=10,
            verify=False,
        )
        if 400 <= response.status_code < 500:
            print(f"⚠️ Client error (4xx) for resource {res.short_id}: {response.text}")
            return None

        print(f"Response status code: {response.status_code} {response.text}")
        response.raise_for_status()
        print(f"✅ Metadata deposited successfully with DataCite for resource {res.short_id}")
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error depositing metadata with DataCite for {res.short_id}: {e}")
        return None


class Command(BaseCommand):
    help = "Migrate all resources from Crossref to DataCite"

    def handle(self, *args, **options):
        published_resources = BaseResource.public_resources.filter(raccess__published=True)

        total = published_resources.count()
        print(f"📦 Total published resources to process: {total}")
        count = 0

        for res in published_resources.iterator():
            res = res.get_content_model()
            if not res.metadata:
                logger.warning(f"Resource {res.short_id} has no metadata. Skipping.")
                continue

            print(f"🔄 Processing resource: {res.short_id}")

            deposit_res_metadata_with_datacite(res)

            print(f"✅ Finished processing resource: {res.short_id}")
            count += 1
            # break  # Remove this break to process all resources

        print(f"🎉 Finished processing {count} resources.")
