# -*- coding: utf-8 -*-

"""
Check that bags can be downloaded from nginx via SENDFILE
Note that it is not possible to test this in test mode.
"""

import os
from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.hs_bagit import create_bag_files
from hs_core.tasks import create_bag_by_irods
from django_irods.views import get_nginx_ip
import requests


def check_download(rid, options):
    """ check that a bag can be generated and downloaded """
    try:
        resource = BaseResource.objects.get(short_id=rid)
        istorage = resource.get_irods_storage()

        root_exists = istorage.exists(resource.root_path)

        if root_exists:
            scimeta_path = os.path.join(resource.root_path, 'data',
                                        'resourcemetadata.xml')
            scimeta_exists = istorage.exists(scimeta_path)
            # if scimeta_exists:
            #     print("{} found".format(scimeta_path))
            # else:
            #     print("{} NOT FOUND".format(scimeta_path))

            resmap_path = os.path.join(resource.root_path, 'data', 'resourcemap.xml')
            resmap_exists = istorage.exists(resmap_path)
            # if resmap_exists:
            #     print("{} found".format(resmap_path))
            # else:
            #     print("{} NOT FOUND".format(resmap_path))

            bag_exists = istorage.exists(resource.bag_path)
            # if bag_exists:
            #     print("{} bag found".format(resource.bag_path))
            # else:
            #     print("{} BAG NOT FOUND".format(resource.bag_path))

            dirty = resource.getAVU('metadata_dirty')
            # print("{}.metadata_dirty is {}".format(rid, str(dirty)))

            modified = resource.getAVU('bag_modified')
            # print("{}.bag_modified is {}".format(rid, str(modified)))

            if dirty or not scimeta_exists or not resmap_exists:
                try:
                    create_bag_files(resource)
                except ValueError as e:
                    print("{}: value error encountered: {}".format(rid, e.message))
                    return

                # print("{} metadata generated from Django".format(rid))
                resource.setAVU('metadata_dirty', 'false')
                # print("{}.metadata_dirty set to false".format(rid))
                resource.setAVU('bag_modified', 'true')
                # print("{}.bag_modified set to true".format(rid))

            if modified or not bag_exists:
                create_bag_by_irods(rid)
                # print("{} bag generated from iRODs".format(rid))
                resource.setAVU('bag_modified', 'false')
                # print("{}.bag_modified set to false".format(rid))

            if istorage.exists(resource.bag_path):
                ip = get_nginx_ip()
                uri = resource.bag_url
                qualified = "http://{}{}".format(ip, uri)
                print("downloading {} via {}".format(resource.short_id, qualified))
                # Skip verification because of unqualified URL.
                r = requests.get(qualified, stream=True, verify=False)
                print("status code is {}".format(r.status_code))
                for chunk in r.iter_content(chunk_size=128):
                    break  # read one line
                r.connection.close()  # force close to clear up nginx

            else:
                print("{} does not exist after being generated and cannot be downloaded"
                      .format(resource.bag_path))

        else:
            print("Resource with id {} does not exist in iRODS".format(rid))
    except BaseResource.DoesNotExist:
        print("Resource with id {} NOT FOUND in Django".format(rid))


class Command(BaseCommand):
    help = "Check download of a resource bag."

    def add_arguments(self, parser):

        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_ids', nargs='*', type=str)

        # Named (optional) arguments

    def handle(self, *args, **options):

        # disable verbose warnings about not verifying ssl
        requests.packages.urllib3.disable_warnings()

        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                check_download(rid, options)
        else:
            for r in BaseResource.objects.all():
                check_download(r.short_id, options)
