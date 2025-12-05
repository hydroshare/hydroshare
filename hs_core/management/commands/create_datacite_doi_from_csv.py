import logging
import requests
import base64
import time
import csv
import json
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from hs_core.hydroshare.resource import get_datacite_url

logger = logging.getLogger(__name__)


def deposit_res_metadata_with_datacite(res_doi, metadata):
    """
    Deposit resource metadata with DataCite using the Fabrica-style payload.
    """
    datacite_url = get_datacite_url()
    try:
        token = base64.b64encode(f"{settings.DATACITE_USERNAME}:{settings.DATACITE_PASSWORD}".encode()).decode()
        headers = {
            "accept": "application/vnd.api+json",
            "content-type": "application/json",
            "authorization": f"Basic {token}"
        }
        doi_url = f"{datacite_url}/{settings.DATACITE_PREFIX}/hs.{res_doi}"
        response = requests.put(
            url=doi_url,
            json=metadata,
            headers=headers,
            timeout=10
        )

        if 400 <= response.status_code < 500:
            print(f"❌ Client error (4xx) for resource {res_doi}: {response.text} \n {json.dumps(metadata)}")
            return None

        response.raise_for_status()
        print(f"✅ Metadata deposited successfully with DataCite for resource {res_doi}")
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error depositing metadata with DataCite for {res_doi}: {e}")
        return None


class Command(BaseCommand):
    help = "Migrate resources from CSV to DataCite"

    def handle(self, *args, **options):
        start_time = time.time()
        csv_file_path = 'doi_list.csv'
        total = sum(1 for _ in open(csv_file_path)) - 1
        print(f"📦 Total resources to process: {total}")
        count = 0

        with open(csv_file_path, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                res_doi = row['DOI'].split('/')[-1]
                title = row['Title'][2:-2]
                authors = [author.strip() for author in row['Authors'].split(';') if author.strip()]

                metadata = {
                    "data": {
                        "type": "dois",
                        "attributes": {
                            "url": row['DOI'],
                            "doi": f"{settings.DATACITE_PREFIX}/hs.{res_doi}",
                            "prefix": settings.DATACITE_PREFIX,
                            "event": "publish",
                            "titles": [{"title": title}],
                            "dates": [
                                {"dateType": "Issued", "date": row['IssuedDate']},
                                {"dateType": "Updated", "date": row['Date updated']}
                            ],
                            "publisher": {
                                "name": "Consortium of Universities for the Advancement of Hydrologic Science, Inc",
                                "lang": "en",
                                "publisherIdentifier": "https://ror.org/04s2bx355",
                                "publisherIdentifierScheme": "ROR",
                                "schemeUri": "https://ror.org"
                            },
                            "publicationYear": row['IssuedDate'].split('-')[0],
                            "language": "en",
                            "types": {
                                "resourceTypeGeneral": "Dataset",
                                "resourceType": "Technical Report",
                                "schemaOrg": "Dataset",
                                "bibtex": "misc",
                                "citeproc": "dataset"
                            },
                            "schemaVersion": "http://datacite.org/schema/kernel-4",
                            "state": "findable"
                        }
                    }
                }
                if authors and len(authors) > 0:
                    metadata['data']['attributes'].update({
                        "creators": [{"name": author.strip()} for author in authors if author.strip()],
                    })
                else:
                    metadata['data']['attributes'].update({
                        "creators": [{"name": "Unknown"}],
                    })

                print(f"🔄 Processing resource: Title: {title}")
                res_start_time = time.time()

                deposit_res_metadata_with_datacite(res_doi, metadata)
                res_duration = timedelta(seconds=int(time.time() - res_start_time))
                print(f"✅ Finished processing resource: Title: {title} | Time taken: {res_duration}")
                count += 1
                # break  # Remove this break to process all rows

        total_duration = timedelta(seconds=int(time.time() - start_time))
        print(f"🎉 Finished processing {count} resources | Time taken: {total_duration}")
