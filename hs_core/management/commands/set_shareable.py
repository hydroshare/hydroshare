"""Set the shareable bit for a resource to True or False
   This is a workaround for the fact that published, unshareable i
   resources can't be added to collections.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey


def check_shareable(rid, options):
    try:
        resource = get_resource_by_shortkey(rid, or_404=False)
    except BaseResource.DoesNotExist:
        print("{}: does not exist".format(rid))
        return

    print("{}: shareable bit is now {}".format(rid, resource.raccess.shareable))
    if options['on'] and not options['off']:
        print("{}: changing sharable bit to True".format(rid))
        resource.raccess.shareable = True
        resource.raccess.save()
    elif options['off'] and not options['on']:
        print("{}: changing sharable bit to False".format(rid))
        resource.raccess.shareable = False
        resource.raccess.save()
    elif options['off'] and options['on']:
        print("{}: conflicting options for shareable bit. No action taken.".format(rid))


class Command(BaseCommand):
    help = "edit the shareable bit of a resource."

    def add_arguments(self, parser):

        # a list of resource id's: none does nothing.
        parser.add_argument('resource_ids', nargs='*', type=str)

        # Named (optional) arguments
        parser.add_argument(
            '--on',
            action='store_true',  # True for presence, False for absence
            dest='on',            # value is options['on']
            help='turn shareable on',
        )

        parser.add_argument(
            '--off',
            action='store_true',  # True for presence, False for absence
            dest='off',           # value is options['off']
            help='turn shareable off'
        )

    def handle(self, *args, **options):
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                check_shareable(rid, options)
        else:
            for resource in BaseResource.objects.all():
                check_shareable(resource.short_id)
