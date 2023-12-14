from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist

from hs_core.hydroshare.utils import get_resource_by_shortkey


class Command(BaseCommand):
    help = "Deletes all hanging logical files for the specified resource"

    def add_arguments(self, parser):

        # ID of a resource for which hanging logical files to be deleted
        parser.add_argument('resource_id', type=str, help=('Required. The existing id (short_id) of'
                                                           ' the resource'))

    def handle(self, *args, **options):

        if not options['resource_id']:
            raise CommandError('resource_id argument is required')
        res_id = options['resource_id']
        try:
            res = get_resource_by_shortkey(res_id, or_404=False)
        except ObjectDoesNotExist:
            raise CommandError("No Resource found for id {}".format(res_id))

        if res.resource_type != "CompositeResource":
            raise CommandError("Resource is not of CompositeResource type")

        total_deleted_aggregations = res.cleanup_aggregations()
        msg = "{} logical file(s) were deleted for resource id:{}".format(total_deleted_aggregations, res_id)
        self.stdout.write(self.style.SUCCESS(msg))
