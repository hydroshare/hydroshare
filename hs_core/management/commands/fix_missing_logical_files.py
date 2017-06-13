"""Fix missing logical file for composite resources. If there are resource files in django
for any composite resource that are not part of any logical file, each of those files are made
part of a generic logical file.

* By default, prints errors on stdout.
* Optional argument --log instead logs output to system log.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource


class Command(BaseCommand):
    help = "Set generic logical file for any resource file that is not part of any logical file."

    def add_arguments(self, parser):

        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_ids', nargs='*', type=str)

        # Named (optional) arguments
        parser.add_argument(
            '--log',
            action='store_true',  # True for presence, False for absence
            dest='log',           # value is options['log']
            help='log errors to system log',
        )

    def handle(self, *args, **options):
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    resource = BaseResource.objects.get(short_id=rid)
                except BaseResource.DoesNotExist:
                    msg = "Resource with id {} not found in Django Resources".format(rid)
                    print(msg)
                    continue
                if resource.resource_type != 'CompositeResource':
                    print("resource {} has type {}: skipping".format(resource.short_id,
                                                                     resource.resource_type))
                    continue

                print("SETTING GENERIC LOGICAL FILE FOR FILES IN RESOURCE {}".format(rid))
                for res_file in resource.files.all():
                    if not res_file.has_logical_file:
                        print("Logical file missing for file {}".format(res_file.file_name))
                resource.set_default_logical_file()

        else:  # check all composite resources
            print("SETTING GENERIC LOGICAL FILE FOR FILES IN ALL COMPOSITE RESOURCES")
            for r in BaseResource.objects.filter(resource_type="CompositeResource"):
                print("SETTING GENERIC LOGICAL FILE FOR FILES IN RESOURCE {}".format(r.short_id))
                r.set_default_logical_file()
