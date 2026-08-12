"""Removes all aggregations (content types / logical files) from a composite resource.

Resource files are NOT deleted — they are detached from their aggregations and left in place.
"""

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError

from hs_core.hydroshare.utils import get_resource_by_shortkey


class Command(BaseCommand):
    help = "Removes all content-type aggregations from a composite resource (files are kept)"

    def add_arguments(self, parser):
        parser.add_argument(
            "resource_id",
            type=str,
            help="Short ID of the composite resource",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Skip confirmation prompt",
        )

    def handle(self, *args, **options):
        res_id = options["resource_id"]

        try:
            res = get_resource_by_shortkey(res_id, or_404=False)
        except ObjectDoesNotExist:
            raise CommandError("No resource found for id: {}".format(res_id))

        if res.resource_type != "CompositeResource":
            raise CommandError(
                "Resource {} is not a CompositeResource (type: {})".format(
                    res_id, res.resource_type
                )
            )

        # Collect aggregations eagerly — logical_files is a generator and the queryset
        # will change as we delete, so we snapshot the list first.
        aggregations = list(res.logical_files)
        count = len(aggregations)

        if count == 0:
            self.stdout.write("No aggregations found for resource {}.".format(res_id))
            return

        if not options["force"]:
            self.stdout.write(
                "This will remove {} aggregation(s) from resource {} (files will NOT be deleted).".format(
                    count, res_id
                )
            )
            confirm = input("Continue? [y/N] ").strip().lower()
            if confirm != "y":
                self.stdout.write("Aborted.")
                return

        removed = 0
        for aggr in aggregations:
            type_name = aggr.type_name()
            try:
                aggr.remove_aggregation()
                removed += 1
                self.stdout.write("  Removed {} aggregation".format(type_name))
            except Exception as e:
                self.stderr.write(
                    "  Failed to remove {} aggregation: {}".format(type_name, e)
                )

        self.stdout.write(
            self.style.SUCCESS(
                "{}/{} aggregation(s) removed from resource {}.".format(removed, count, res_id)
            )
        )
