from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError

from hs_core.enums import CrossRefSubmissionStatus
from hs_core.hydroshare import (deposit_res_metadata_with_crossref,
                                get_resource_doi)
from hs_core.hydroshare.utils import get_resource_by_shortkey


class Command(BaseCommand):
    help = "Update crossref metadata deposit for a published resource"

    def add_arguments(self, parser):

        # ID of a published resource for which crossref metadata needs to be updated
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
        if CrossRefSubmissionStatus.PENDING.value in resource.doi:
            raise CommandError("Resource has a pending crossref deposit request. Please try again later.")

        print(f"Updating CrossRef metadata for resource id {resource.short_id}")
        response = deposit_res_metadata_with_crossref(resource)
        if not response.status_code == 200:
            err_msg = (f"Failed to update. Received a {response.status_code} from CrossRef while depositing "
                       f"metadata for res id {resource.short_id}")
            raise CommandError(err_msg)
        else:
            resource.doi = get_resource_doi(resource.short_id, flag=CrossRefSubmissionStatus.UPDATE_PENDING.value)
            resource.save()
        print(f"Successfully deposited metadata to CrossRef for resource id {resource.short_id}")
