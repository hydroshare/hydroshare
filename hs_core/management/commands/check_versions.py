# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey


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
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    resource = get_resource_by_shortkey(rid, or_404=False)
                    check_versions(resource)
                except BaseResource.DoesNotExist:
                    msg = "resource {} not found".format(rid)
                    print(msg)
                    continue

        else:  # check all resources
            print("CHECKING ALL RESOURCES")
            available = BaseResource.objects.filter(raccess__discoverable=True)
            validated = [x.short_id for x in available if x.show_in_discover]
            queryset = BaseResource.objects.filter(short_id__in=validated)
            for r in queryset:
                try:
                    resource = get_resource_by_shortkey(r.short_id, or_404=False)
                    check_versions(resource)
                except BaseResource.DoesNotExist:
                    msg = "resource {} not found".format(r.short_id)
                    print(msg)
                    continue
