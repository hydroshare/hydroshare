import logging
import requests
import base64
import time
import csv
import json
from datetime import timedelta, datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from hs_core.hydroshare.resource import get_datacite_url

logger = logging.getLogger(__name__)


def deposit_res_metadata_with_datacite(res_doi, metadata, test_mode=False):
    """
    Deposit resource metadata with DataCite using the Fabrica-style payload.
    """
    try:
        # Generate the authorization token
        token = base64.b64encode(f"{settings.DATACITE_USERNAME}:{settings.DATACITE_PASSWORD}".encode()).decode()
        headers = {
            "accept": "application/vnd.api+json",
            "content-type": "application/json",
            "authorization": f"Basic {token}"
        }

        # Modify the payload for test mode
        if test_mode:
            # Remove the "event" key
            if "event" in metadata["data"]["attributes"]:
                del metadata["data"]["attributes"]["event"]
                print("🚧 TEST MODE: Removed 'event' key from payload")

            # Append "test-<timestamp>" to the DOI
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            metadata["data"]["attributes"]["doi"] += f"-test-{timestamp}"
            print(f"🚧 TEST MODE: Updated DOI to '{metadata['data']['attributes']['doi']}'")
            print(f"🚧 TEST MODE: Would deposit metadata for resource {res_doi}")
            print(f"🚧 TEST MODE: Payload: {metadata}")

        # Send the POST request to deposit metadata
        datacite_url = get_datacite_url()
        doi_url = f"{datacite_url}/{res_doi}"
        response = requests.put(
            url=doi_url,
            json=metadata,
            headers=headers,
            timeout=10
        )

        # Handle client errors (4xx)
        if 400 <= response.status_code < 500:
            print(f"❌ Client error (4xx) for resource {res_doi}: {response.text} \n {json.dumps(metadata, indent=2)}")
            return None

        # Raise an exception for server errors (5xx)
        response.raise_for_status()
        print(f"✅ Metadata deposited successfully with DataCite for resource {res_doi} \n {response.text}")
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error depositing metadata with DataCite for {res_doi}: {e}\n {response.text}")
        return None


class Command(BaseCommand):
    help = "Migrate resources from CSV to DataCite"
    # COMMAND: python manage.py create_datacite_doi_from_csv --test --limit 1 --file_name create_dois.csv

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Run in test mode (does not make actual API calls)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of resources to process (default: process all)',
        )
        parser.add_argument(
            '--file_name',
            type=str,
            default='create_dois.csv',
            help='Path to the CSV file containing resource data',
        )

    def handle(self, *args, **options):
        start_time = time.time()
        csv_file_path = options['file_name']
        total = sum(1 for _ in open(csv_file_path)) - 1
        print(f"📦 Total resources to process: {total}")

        test_mode = options['test']
        limit = options['limit']

        count = 0

        with open(csv_file_path, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                # Stop processing if the limit is reached
                if limit is not None and count >= limit:
                    print(f"⏹️ Reached limit of {limit} resources. Stopping.")
                    break

                # Extract DOI and metadata fields from the row
                res_doi = row['DOI'].split('/')[-1]
                title = row['title'][2:-2]  # Remove extra quotes
                authors = [author.strip() for author in row['author'].split(';') if author.strip()]
                status = row['status'].lower()
                url = row['resource']
                final_doi = f"{settings.DATACITE_PREFIX}/hs.{res_doi}"
                if status == 'deleted':
                    print("Resource is deleted, using tombstone URL")
                    url = row['tombstone_url']
                    final_doi = f"{settings.DATACITE_PREFIX}/{res_doi}"
                # Construct the metadata payload
                metadata = {
                    "data": {
                        "type": "dois",
                        "attributes": {
                            "url": url,
                            "doi": final_doi,
                            "prefix": settings.DATACITE_PREFIX,
                            "event": "publish",
                            "titles": [{"title": title}],
                            "descriptions": [{
                                "description": row['description'],
                                "descriptionType": "Abstract",
                                "lang": "en"
                            }],
                            "dates": [
                                {"dateType": "Issued", "date": row['published']},
                                {"dateType": "Updated", "date": row['deposited']}
                            ],
                            "publisher": {
                                "name": "Consortium of Universities for the Advancement of Hydrologic Science, Inc",
                                "lang": "en",
                                "publisherIdentifier": "https://ror.org/04s2bx355",
                                "publisherIdentifierScheme": "ROR",
                                "schemeUri": "https://ror.org"
                            },
                            "publicationYear": row['published'].split('-')[0],
                            "language": "en",
                            "types": {
                                "resourceTypeGeneral": "Dataset",
                                "resourceType": "Technical Report",
                                "schemaOrg": "Dataset",
                                "bibtex": "misc",
                                "citeproc": "dataset"
                            },
                            "schemaVersion": "http://datacite.org/schema/kernel-4",
                        }
                    },
                    "relationships": {
                        "client": {
                            "data": {
                                "type": "repositories",
                                "id": f"{settings.DATACITE_USERNAME}"
                            }
                        }
                    }
                }

                # Add authors to the metadata
                if authors:
                    metadata['data']['attributes'].update({
                        "creators": [{"name": author} for author in authors],
                    })
                else:
                    metadata['data']['attributes'].update({
                        "creators": [{"name": "Unknown"}],
                    })

                print(f"🔄 Processing resource: DOI: {row['DOI']} Title: {title}")
                res_start_time = time.time()

                deposit_res_metadata_with_datacite(final_doi, metadata, test_mode=test_mode)

                res_duration = timedelta(seconds=int(time.time() - res_start_time))
                print(f"✅ Finished processing resource: DOI: {row['DOI']} Title: {title} | Time taken: {res_duration}")
                count += 1

        total_duration = timedelta(seconds=int(time.time() - start_time))
        print(f"🎉 Finished processing {count} resources | Time taken: {total_duration}")
