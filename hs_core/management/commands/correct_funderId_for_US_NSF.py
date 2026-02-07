import requests
import logging
import base64
from django.core.management.base import BaseCommand
from django.conf import settings
from hs_core.hydroshare.resource import get_datacite_url

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update DataCite DOIs funding references'

    def add_arguments(self, parser):
        parser.add_argument(
            '--identify',
            action='store_true',
            help='Only list DOIs without updating',
        )

    def handle(self, *args, **options):
        datacite_url = get_datacite_url()
        prefix = settings.DATACITE_PREFIX
        token = base64.b64encode(
            f"{settings.DATACITE_USERNAME}:{settings.DATACITE_PASSWORD}".encode()
        ).decode()

        identify_mode = options['identify']

        try:
            query_url = (
                f"{datacite_url}"
                f"?query=prefix:{prefix}%20AND%20fundingReferences.funderName:NSF"
                "%20AND%20fundingReferences.funderIdentifier:https\\://ror.org/01822d048"
                f"&prefix={prefix}"
                "&fields%5Bdois%5D=doi,url,fundingReferences&page[size]=2000"
            )

            logger.info(f"Fetching DOIs from DataCite for prefix: {prefix}")
            self.stdout.write(f"Fetching DOIs from DataCite for prefix: {prefix}")

            response = requests.get(
                query_url,
                headers={'accept': 'application/vnd.api+json', 'authorization': f'Basic {token}'},
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            dois = data.get('data', [])

            logger.info(f'Found {len(dois)} DOIs')
            self.stdout.write(f'Found {len(dois)} DOIs\n')

            if identify_mode:
                self.stdout.write(self.style.WARNING('🔍 IDENTIFY MODE - Listing DOIs only:\n'))
                for item in dois:
                    doi_id = item['id']
                    self.stdout.write(f'  • {doi_id}')
                self.stdout.write(f'\n✅ Total DOIs identified: {len(dois)}')
                return

            success_count = 0
            error_count = 0

            for item in dois:
                doi_id = item['id']
                funding_refs = item['attributes'].get('fundingReferences', [])

                updated = False
                for ref in funding_refs:
                    if (
                        ref.get('funderName') == 'NSF'
                        and ref.get('funderIdentifier') == 'https://ror.org/01822d048'
                    ):
                        ref['funderIdentifier'] = 'https://ror.org/021nxhr62'
                        updated = True

                if updated:
                    try:
                        logger.info(f"Updating DOI: {doi_id}")
                        update_response = requests.put(
                            f"{datacite_url}/{doi_id}",
                            headers={
                                'accept': 'application/vnd.api+json',
                                'content-type': 'application/vnd.api+json',
                                'authorization': f'Basic {token}'
                            },
                            json={'data': {'attributes': {'fundingReferences': funding_refs}}},
                            timeout=30
                        )
                        update_response.raise_for_status()

                        logger.info(f'Successfully updated {doi_id}')
                        self.stdout.write(self.style.SUCCESS(f'✅ Updated {doi_id}'))
                        success_count += 1
                    except requests.exceptions.RequestException as e:
                        error_msg = f'Failed to update {doi_id}: {str(e)}'
                        logger.error(error_msg)
                        self.stdout.write(self.style.ERROR(f'❌ {error_msg}'))
                        error_count += 1

            logger.info(f'Update complete. Success: {success_count}, Errors: {error_count}')
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Update complete. Success: {success_count}, Errors: {error_count}'
                )
            )

        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to fetch DOIs: {str(e)}')
            self.stdout.write(self.style.ERROR(f'❌ Failed to fetch DOIs: {str(e)}'))
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}')
            self.stdout.write(self.style.ERROR(f'❌ Unexpected error: {str(e)}'))
