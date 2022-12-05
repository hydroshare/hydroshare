# -*- coding: utf-8 -*-

"""
Update GeospatialRelation objects with text from the geoconnex API

* By default, prints errors on stdout.
* Optional argument --log instead logs output to system log.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey, update_geoconnex_texts


class Command(BaseCommand):
    help = "Update GeospatialRelation objects with text from the geoconnex API."

    def add_arguments(self, parser):

        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    resource = get_resource_by_shortkey(rid)
                except BaseResource.DoesNotExist:
                    msg = f"Resource with id {rid} not found in Django Resources"
                    print(msg)
                    continue

                relations = resource.metadata.geospatialrelations.all()
                if relations:
                    for relation in relations:
                        print(f"CHECKING RELATION '{relation.text}' FOR RESOURCE '{rid}', ")
                        relation.check_text()
                else:
                    print(f"RESOURCE {rid} HAS NO GEOSPATIAL RELATIONS")

        else:  # check all resources
            print("CHECKING RELATIONS FOR ALL RESOURCES")
            update_geoconnex_texts()
