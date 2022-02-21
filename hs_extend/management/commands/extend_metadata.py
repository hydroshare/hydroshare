# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey
from pprint import pprint


def index_resource(r):
    """ index a resource with computed metadata """
    # prints everything you might take into account when computing HUC metadata.
    if r.metadata:  # a small number of objects don't have any metadata.
        print("computing metadata for resource {}".format(r.short_id))
        if r.resource_type != 'CompositeResource':
            for c in r.metadata.coverages.all():
                if c.type == 'point' or c.type == 'box':
                    print("whole resource coverage of type {}".format(c.type))
                    value = c.value
                    pprint(value)
                    # use your code to compute all HUC codes that are relevant.
    else:  # it's a Composite Resource
        for lfo in r.logical_files:
            if lfo.metadata:
                for c in lfo.metadata.coverages.all():
                    if c.type == 'point' or c.type == 'box':
                        value = c.value
                        print("logical file coverage of type {}".format(c.type))
                        pprint(value)
                        # use your code to compute all HUC codes that are relevant.
            else:
                print("resource {} has no metadata".format(r.short_id))


class Command(BaseCommand):
    help = "Computed extended metadata for discovery"

    def add_arguments(self, parser):
        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    resource = get_resource_by_shortkey(rid)
                except BaseResource.NotFoundException:
                    msg = "resource {} not found".format(rid)
                    print(msg)
                    continue
                index_resource(resource)

        else:  # check all resources
            print("Indexing all resources")
            for r in BaseResource.objects.all():
                try:
                    resource = get_resource_by_shortkey(r.short_id)
                except BaseResource.NotFoundException:
                    msg = "resource {} not found".format(r.short_id)
                    print(msg)
                    continue
                index_resource(resource)
