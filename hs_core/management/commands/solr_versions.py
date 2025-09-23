# -*- coding: utf-8 -*-
# Debug discovery code on actual resources.

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey


def check_displayed(resource, isreplacedby, replaces):
    """ create a depiction of what is displayed and what is not displayed in discover
        according to resource.show_in_discover. These are the resources that will show
        up on the discover page.
    """
    print("resource {} (show={}, disc={}, created={}) '{}':"
          .format(resource.short_id,
                  resource.show_in_discover,
                  resource.raccess.discoverable,
                  resource.created.strftime("%Y-%m-%d %H:%M:%S"),
                  resource.title))
    if resource.short_id in replaces:
        repl = replaces[resource.short_id]  # things that resource.short_id replaces
        for rid in repl:
            try:
                r = get_resource_by_shortkey(rid, or_404=False)
            except BaseResource.DoesNotExist:
                r = None
            if r is not None:
                print("    replaces {} (show={}, disc={}, created={}) '{}'"
                      .format(r.short_id,
                              r.show_in_discover,
                              r.raccess.discoverable,
                              r.created.strftime("%Y-%m-%d %H:%M:%S"),
                              r.title))
            else:
                print("    replaces {} (DELETED)".format(rid))
    if resource.short_id in isreplacedby:
        repl = isreplacedby[resource.short_id]  # things that are replaced by resource.short_id
        for rid in repl:
            try:
                r = get_resource_by_shortkey(rid, or_404=False)
            except BaseResource.DoesNotExist:
                r = None
            if r is not None:
                print("    is replaced by {} (show={}, disc={}, created={}) '{}'"
                      .format(r.short_id,
                              r.show_in_discover,
                              r.raccess.discoverable,
                              r.created.strftime("%Y-%m-%d %H:%M:%S"),
                              r.title))
            else:
                print("    is replaced by {} (DELETED)".format(rid))


def map_replacements():
    """ create a map of what resources are replaced by others. This is a tree. """
    isreplacedby = {}  # isreplacedby[x] is the number of things that are replaced by x
    replaces = {}  # replaces[x] are the number of things that x replaces.
    for r in BaseResource.objects.all():
        if r.metadata and r.metadata.relations:
            for s in r.metadata.relations.filter(type='isReplacedBy'):
                uri = s.value
                if uri.startswith('http://www.hydroshare.org/resource/'):
                    rid = uri[-32:]
                    # r.short_id "is replaced by" rid
                    if r.short_id in isreplacedby:
                        isreplacedby[r.short_id].append(rid)
                    else:
                        isreplacedby[r.short_id] = [rid]

                    # rid "replaces" r.short_id:
                    # replaces[rid] is the things rid replaces.
                    if rid in replaces:
                        replaces[rid].append(r.short_id)
                    else:
                        replaces[rid] = [r.short_id]
    return isreplacedby, replaces


class Command(BaseCommand):
    help = "Check synchronization between S3 and Django."

    def add_arguments(self, parser):
        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):
        # check versions on listed resources
        isreplacedby, replaces = map_replacements()
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    r = get_resource_by_shortkey(rid, or_404=False)
                    check_displayed(r, isreplacedby, replaces)
                except BaseResource.DoesNotExist:
                    msg = "resource {} not found".format(rid)
                    print(msg)
                    continue

        else:  # check all resources
            print("CHECKING ALL RESOURCES")
            isreplacedby, replaces = map_replacements()
            available = BaseResource.objects.filter(raccess__discoverable=True)
            for r in available:
                check_displayed(r, isreplacedby, replaces)
