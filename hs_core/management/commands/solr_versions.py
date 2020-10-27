# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey
from pprint import pprint


def check_displayed(resource, isreplacedby, replaces):
    uri = 'http://www.hydroshare.org/resource/'+resource.short_id
    print("resource {} (show={}, disc={}) '{}':".format(resource.short_id,
                                                        resource.show_in_discover,
                                                        resource.raccess.discoverable, 
                                                        resource.title))
    if resource.short_id in replaces: 
        repl = replaces[resource.short_id];  # things that resource.short_id replaces 
        for rid in repl:
            try:
                r = get_resource_by_shortkey(rid, or_404=False)
            except BaseResource.DoesNotExist:
                r = None
            if r is not None:
                print("    replaces {} (show={}, disc={}) '{}'".format(r.short_id,
                                                                       r.show_in_discover,
                                                                       r.raccess.discoverable,
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
                print("    is replaced by {} (show={}, disc={}) '{}'".format(r.short_id,
                                                                             r.show_in_discover,
                                                                             r.raccess.discoverable,
                                                                             r.title))
            else:
                print("    is replaced by {} (DELETED)".format(rid))


def map_replacements():
    
    isreplacedby = {}  # isreplacedby[x] is the number of things that are replaced by x
    replaces = {}  # replaces[x] are the number of things that x replaces. 
    for r in BaseResource.objects.all():
        if r.metadata and r.metadata.relations:
            stuff = []
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
    # print("isreplacedby")
    # pprint(isreplacedby)
    # print("replaces")
    # pprint(replaces)
    return isreplacedby, replaces


def check_versions(resource):
    if resource.metadata is not None and resource.metadata.relations is not None:
        versions = resource.metadata.relations.all().filter(type='isVersionOf')
        if versions.count() > 0:
            print("checking isVersionOf for {} '{}'".format(resource.short_id,
                                                            resource.title))
            for v in versions:
                version = v.value
                if version.startswith("http://www.hydroshare.org/resource/"):
                    version = version[-32:]  # strip header
                    try:
                        rv = get_resource_by_shortkey(version, or_404=False)
                    except BaseResource.DoesNotExist:
                        rv = None
                    if rv is not None:
                        print("    {} {} {} '{}'".format(version,
                                                         rv.raccess.discoverable,
                                                         rv.raccess.public,
                                                         rv.title))
                    else:
                        print("    {} VERSON DELETED".format(version))
                else:
                    print("    NONSTANDARD VERSION {}".format(version))
        replaces = resource.metadata.relations.all().filter(type='isReplacedBy')
        if replaces.count() > 0:
            print("checking isReplacedBy for {} '{}'".format(resource.short_id,
                                                             resource.title))
            for r in replaces:
                replacement = r.value
                if replacement.startswith("http://www.hydroshare.org/resource/"):
                    replacement = replacement[-32:]
                    try:
                        rv = get_resource_by_shortkey(replacement, or_404=False)
                    except BaseResource.DoesNotExist:
                        rv = None
                    if rv is not None:
                        print("    {} {} {} '{}'".format(replacement,
                                                         rv.raccess.discoverable,
                                                         rv.raccess.public,
                                                         rv.title))
                    else:
                        print("    {} REPLACEMENT DELETED".format(replacement))
                else:
                    print("    NONSTANDARD REPLACEMENT {}".format(replacement))
        if (resource.raccess.discoverable and not resource.show_in_discover):
            print("resource {} exhibit=False".format(resource.short_id))
    else:
        print("no metadata for {}".format(resource.short_id))


class Command(BaseCommand):
    help = "Check synchronization between iRODS and Django."

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
