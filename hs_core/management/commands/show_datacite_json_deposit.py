from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError

from hs_core.hydroshare.utils import get_resource_by_shortkey


class Command(BaseCommand):
    help = "Print Datacite metadata deposit for a published resource"

    def add_arguments(self, parser):

        # ID of a published resource for which datacite metadata needs to be printed
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

        datacite_deposit_json = resource.get_datacite_deposit_json()
        print(datacite_deposit_json)
