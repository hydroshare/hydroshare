from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError

from hs_core.enums import DataciteSubmissionStatus
from hs_core.hydroshare import (update_res_metadata_with_datacite,
                                get_resource_doi)
from hs_core.hydroshare.utils import get_resource_by_shortkey


class Command(BaseCommand):
    help = "Update Datacite metadata deposit for a published resource"

    def add_arguments(self, parser):

        # ID of a published resource for which datacite metadata needs to be updated
        parser.add_argument('resource_id', type=str, help=('Required. The existing id (short_id) of'
                                                           ' the published resource'))

    def handle(self, *args, **options):

        if not options['resource_id']:
            raise CommandError('resource_id argument is required')
        res_id = options['resource_id']
        try:
            resource = get_resource_by_shortkey(res_id, or_404=False)
        except ObjectDoesNotExist:
            raise CommandError("No Resource found for id {}".format(res_id))
        if not resource.raccess.published:
            raise CommandError("Resource is not a published resource")

        # this should check both 'pending' and 'update_pending' flags in doi
        if DataciteSubmissionStatus.PENDING.value in resource.doi:
            raise CommandError("Resource has a pending datacite deposit request. Please try again later.")

        print(f"Updating Datacite metadata for resource id {resource.short_id}")
        response = update_res_metadata_with_datacite(resource)
        if not response.status_code == 200:
            err_msg = (f"Failed to update. Received a {response.status_code} from Datacite while depositing "
                       f"metadata for res id {resource.short_id}")
            raise CommandError(err_msg)
        else:
            resource.doi = get_resource_doi(resource.short_id, flag=DataciteSubmissionStatus.UPDATE_PENDING.value)
            resource.save()
        print(f"Successfully deposited metadata to Datacite for resource id {resource.short_id}")
