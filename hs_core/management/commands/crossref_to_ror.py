from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
import requests
import asyncio

from hs_core.models import FundingAgency


@sync_to_async
def get_funding_records():
    return list(FundingAgency.objects.all())


@sync_to_async
def get_resource(record_id):
    resource = None
    funding_agency = FundingAgency.objects.filter(id=record_id).first()
    if funding_agency:
        metadata = funding_agency.metadata
    if metadata:
        resource = metadata.resource
    return resource


async def update_record(record):
    from hs_core.tasks import update_crossref_meta_deposit
    print("*" * 80)
    print(f"Checking funder record {record.id} with agency url {record.agency_url}")
    if record.agency_url is not None:
        doi_prefixes = ('http://dx.doi.org/10.13039/', 'https://doi.org/10.13039/')
        doi_id_parts = []
        for doi_prefix in doi_prefixes:
            if doi_prefix in record.agency_url:
                doi_id_parts = record.agency_url.split(doi_prefix)
                break
        if len(doi_id_parts) == 2:
            fundref_id = record.agency_url.split(doi_prefix)[1]
            url = f"https://api.ror.org/v2/organizations?query=%22{fundref_id}%22"
            print(f"Querying ROR API with url {url}")
            response = requests.get(url, verify=False)
            if response.status_code == 200:
                response_json = response.json()
                items = response_json.get('items', None)
                if items:
                    item = items[0]
                    print(f"Replacing old funder id {record.agency_url} with new id {item['id']}")
                    agency_name_new = [n['value'] for n in item['names'] if 'ror_display' in n['types']][0]
                    record.agency_name = agency_name_new
                    record.agency_url = item['id']
                    await sync_to_async(record.save)()
                    # Update metadata.
                    resource = await get_resource(record.id)
                    if resource:
                        update_crossref_meta_deposit.apply_async((resource.short_id,))
                    else:
                        print(f"Resource not found for funder record {record.id}")
            else:
                print(f"Failed to query ROR API with url {url}")
                print(f"Response status code: {response.status_code}")
        else:
            print(f"DOI parts not found in funder record {record.id} with agency url {record.agency_url}")
    else:
        print(f"Skipping funder record {record.id} with empty agency url")


async def get_funder_records():
    funding_records = await get_funding_records()
    await asyncio.gather(*(update_record(record) for record in funding_records))


def migrate_from_crossref_to_ror():
    """Migrate from CrossRef to ROR asynchronously"""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_funder_records())


class Command(BaseCommand):
    help = "Migrate funding agency data from Crossref to ROR"

    def handle(self, *args, **options):
        migrate_from_crossref_to_ror()
