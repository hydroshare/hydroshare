# -*- coding: utf-8 -*-

"""
Check synchronization between iRODS and Django

This checks that:

1. every ResourceFile corresponds to an iRODS file
2. every iRODS file in {short_id}/data/contents corresponds to a ResourceFile
3. every iRODS directory {short_id} corresponds to a Django resource

* By default, prints errors on stdout.
* Optional argument --log instead logs output to system log.
"""

from django.core.management.base import BaseCommand

from hs_composite_resource.models import CompositeResource
from hs_core.models import BaseResource
from hs_core.management.utils import check_irods_files, check_for_dangling_irods


class Command(BaseCommand):
    help = "Check synchronization between iRODS and Django."

    def add_arguments(self, parser):

        # a list of resource id's, or none to check all resources
        parser.add_argument("resource_ids", nargs="*", type=str)

        # Named (optional) arguments
        parser.add_argument(
            "--log",
            action="store_true",  # True for presence, False for absence
            dest="log",  # value is options['log']
            help="log errors to system log",
        )

        # Named (optional) arguments
        parser.add_argument(
            "--sync_ispublic",
            action="store_true",  # True for presence, False for absence
            dest="sync_ispublic",
            help="synchronize iRODS isPublic AVU with Django",
        )
        parser.add_argument(
            "--clean_irods",
            action="store_true",  # True for presence, False for absence
            dest="clean_irods",
            help="delete unreferenced iRODS files",
        )
        parser.add_argument(
            "--clean_django",
            action="store_true",  # True for presence, False for absence
            dest="clean_django",
            help="delete unreferenced Django file objects",
        )
        # Named (optional) arguments
        parser.add_argument(
            "--unreferenced",
            action="store_true",  # True for presence, False for absence
            dest="unreferenced",
            help="check for unreferenced iRODS directories",
        )

    def handle(self, *args, **options):
        if options["unreferenced"]:
            print("LOOKING FOR IRODS RESOURCES NOT IN DJANGO")
            check_for_dangling_irods(
                echo_errors=not options["log"],
                log_errors=options["log"],
                return_errors=False,
            )

        elif (
            len(options["resource_ids"]) > 0
        ):  # an array of resource short_id to check.
            for rid in options["resource_ids"]:
                try:
                    resource = BaseResource.objects.get(short_id=rid)
                except BaseResource.DoesNotExist:
                    msg = "Resource with id {} not found in Django Resources".format(
                        rid
                    )
                    print(msg)

                print("LOOKING FOR FILE ERRORS FOR RESOURCE {}".format(rid))
                if options["clean_irods"]:
                    print(" (deleting unreferenced iRODs files)")
                if options["clean_django"]:
                    print(" (deleting Django file objects without files)")
                if options["sync_ispublic"]:
                    print(" (correcting isPublic in iRODs)")
                check_irods_files(
                    resource,
                    stop_on_error=False,
                    echo_errors=not options["log"],
                    log_errors=options["log"],
                    return_errors=False,
                    clean_irods=options["clean_irods"],
                    clean_django=options["clean_django"],
                    sync_ispublic=options["sync_ispublic"],
                )

        else:  # check all resources
            print("LOOKING FOR FILE ERRORS FOR ALL RESOURCES")
            if options["clean_irods"]:
                print(" (deleting unreferenced iRODs files)")
            if options["clean_django"]:
                print(" (deleting Django file objects without files)")
            if options["sync_ispublic"]:
                print(" (correcting isPublic in iRODs)")
            for r in BaseResource.objects.all():
                if r.resource_type == "CompositeResource":
                    r = CompositeResource.objects.get(short_id=r.short_id)
                check_irods_files(
                    r,
                    stop_on_error=False,
                    echo_errors=not options["log"],  # Don't both log and echo
                    log_errors=options["log"],
                    return_errors=False,
                    clean_irods=options["clean_irods"],
                    clean_django=options["clean_django"],
                    sync_ispublic=options["sync_ispublic"],
                )
