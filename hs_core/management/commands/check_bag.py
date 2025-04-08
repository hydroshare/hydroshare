# -*- coding: utf-8 -*-

"""
Generate metadata and bag for a resource from Django

"""

import os
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.hs_bagit import create_bag_metadata_files
from hs_core.tasks import create_bag_by_s3
from django_s3.exceptions import SessionException


def check_bag(rid, options):
    requests.packages.urllib3.disable_warnings()
    try:
        resource = BaseResource.objects.get(short_id=rid)
        istorage = resource.get_s3_storage()

        root_exists = istorage.exists(resource.root_path)

        if root_exists:
            # print status of metadata/bag system
            scimeta_path = os.path.join(resource.root_path, 'data',
                                        'resourcemetadata.xml')
            scimeta_exists = istorage.exists(scimeta_path)
            if scimeta_exists:
                print("resource metadata {} found".format(scimeta_path))
            else:
                print("resource metadata {} NOT FOUND".format(scimeta_path))

            resmap_path = os.path.join(resource.root_path, 'data', 'resourcemap.xml')
            resmap_exists = istorage.exists(resmap_path)
            if resmap_exists:
                print("resource map {} found".format(resmap_path))
            else:
                print("resource map {} NOT FOUND".format(resmap_path))

            bag_exists = istorage.exists(resource.bag_path)
            if bag_exists:
                print("bag {} found".format(resource.bag_path))
            else:
                print("bag {} NOT FOUND".format(resource.bag_path))

            dirty = resource.getAVU('metadata_dirty')
            print("{}.metadata_dirty is {}".format(rid, str(dirty)))

            modified = resource.getAVU('bag_modified')
            print("{}.bag_modified is {}".format(rid, str(modified)))

            if options['reset']:  # reset all data to pristine
                resource.setAVU('metadata_dirty', 'true')
                print("{}.metadata_dirty set to true".format(rid))
                try:
                    istorage.delete(resource.scimeta_path)
                    print("{} deleted".format(resource.scimeta_path))
                except SessionException as ex:
                    print("{} delete failed: {}"
                          .format(resource.scimeta_path,
                                  ex.stderr))
                try:
                    istorage.delete(resource.resmap_path)
                    print("{} deleted".format(resource.resmap_path))
                except SessionException as ex:
                    print("{} delete failed: {}"
                          .format(resource.resmap_path,
                                  ex.stderr))

                resource.setAVU('bag_modified', 'true')
                print("{}.bag_modified set to true".format(rid))
                try:
                    istorage.delete(resource.bag_path)
                    print("{} deleted".format(resource.bag_path))
                except SessionException as ex:
                    print("{} delete failed: {}"
                          .format(resource.bag_path,
                                  ex.stderr))

            if options['reset_metadata']:
                resource.setAVU('metadata_dirty', 'true')
                print("{}.metadata_dirty set to true".format(rid))
                try:
                    istorage.delete(resource.scimeta_path)
                    print("{} deleted".format(resource.scimeta_path))
                except SessionException as ex:
                    print("delete of {} failed: {}"
                          .format(resource.scimeta_path,
                                  ex.stderr))
                try:
                    istorage.delete(resource.resmap_path)
                    print("{} deleted".format(resource.resmap_path))
                except SessionException as ex:
                    print("{} delete failed: {}"
                          .format(resource.resmap_path,
                                  ex.stderr))

            if options['reset_bag']:
                resource.setAVU('bag_modified', 'true')
                print("{}.bag_modified set to true".format(rid))
                try:
                    istorage.delete(resource.bag_path)
                    print("{} deleted".format(resource.bag_path))
                except SessionException as ex:
                    print("{} delete failed: {}"
                          .format(resource.bag_path,
                                  ex.stderr))

            if options['generate']:  # generate usable bag
                if not options['if_needed'] or dirty or not scimeta_exists or not resmap_exists:
                    try:
                        create_bag_metadata_files(resource)
                    except ValueError as e:
                        print(("{}: value error encountered: {}".format(rid, str(e))))
                        return

                    print("{} metadata generated from Django".format(rid))
                    resource.setAVU('metadata_dirty', 'false')
                    resource.setAVU('bag_modified', 'true')
                    print("{}.metadata_dirty set to false".format(rid))

                if not options['if_needed'] or modified or not bag_exists:
                    create_bag_by_s3(rid)
                    print("{} bag generated".format(rid))
                    resource.setAVU('bag_modified', 'false')
                    print("{}.bag_modified set to false".format(rid))

            if options['generate_metadata']:
                if not options['if_needed'] or dirty or not scimeta_exists or not resmap_exists:
                    try:
                        create_bag_metadata_files(resource)
                    except ValueError as e:
                        print(("{}: value error encountered: {}".format(rid, str(e))))
                        return
                    print("{}: metadata generated from Django".format(rid))
                    resource.setAVU('metadata_dirty', 'false')
                    print("{}.metadata_dirty set to false".format(rid))
                    resource.setAVU('bag_modified', 'true')
                    print("{}.bag_modified set to false".format(rid))

            if options['generate_bag']:
                if not options['if_needed'] or modified or not bag_exists:
                    create_bag_by_s3(rid)
                    print("{}: bag generated".format(rid))
                    resource.setAVU('bag_modified', 'false')
                    print("{}.bag_modified set to false".format(rid))

            if options['download_bag']:
                if options['password']:
                    server = getattr(settings, 'FQDN_OR_IP', 'www.hydroshare.org')
                    uri = "https://{}/hsapi/resource/{}/".format(server, rid)
                    print("download uri is {}".format(uri))
                    r = requests.get(uri, verify=False, stream=True,
                                     auth=requests.auth.HTTPBasicAuth(options['login'],
                                                                      options['password']))
                    print("download return status is {}".format(str(r.status_code)))
                    print("redirects:")
                    for thing in r.history:
                        print("...url: {}".format(thing.url))
                    filename = 'tmp/check_bag_block'
                    with open(filename, 'wb') as fd:
                        for chunk in r.iter_content(chunk_size=128):
                            fd.write(chunk)
                else:
                    print("cannot download bag without username and password.")

            if options['open_bag']:
                if options['password']:
                    server = getattr(settings, 'FQDN_OR_IP', 'www.hydroshare.org')
                    uri = "https://{}/hsapi/resource/{}/".format(server, rid)
                    print("download uri is {}".format(uri))
                    r = requests.get(uri, verify=False, stream=True,
                                     auth=requests.auth.HTTPBasicAuth(options['login'],
                                                                      options['password']))
                    print("download return status is {}".format(str(r.status_code)))
                    print("redirects:")
                    for thing in r.history:
                        print("...url: {}".format(thing.url))
                    filename = 'tmp/check_bag_block'
                    with open(filename, 'wb') as fd:
                        for chunk in r.iter_content(chunk_size=128):
                            fd.write(chunk)
                            break
                else:
                    print("cannot open bag without username and password.")
        else:
            print("Resource with id {} does not exist in S3".format(rid))
    except BaseResource.DoesNotExist:
        print("Resource with id {} NOT FOUND in Django".format(rid))


class Command(BaseCommand):
    help = "Create metadata files and bag for a resource."

    def add_arguments(self, parser):

        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_ids', nargs='*', type=str)

        # Named (optional) arguments

        parser.add_argument(
            '--reset',
            action='store_true',  # True for presence, False for absence
            dest='reset',  # value is options['reset']
            help='delete metadata and bag and start over'
        )

        parser.add_argument(
            '--reset_metadata',
            action='store_true',  # True for presence, False for absence
            dest='reset_metadata',  # value is options['reset_metadata']
            help='delete metadata files and start over'
        )

        parser.add_argument(
            '--reset_bag',
            action='store_true',  # True for presence, False for absence
            dest='reset_bag',  # value is options['reset_bag']
            help='delete bag and start over'
        )

        parser.add_argument(
            '--generate',
            action='store_true',  # True for presence, False for absence
            dest='generate',  # value is options['generate']
            help='force generation of metadata and bag'
        )

        parser.add_argument(
            '--generate_metadata',
            action='store_true',  # True for presence, False for absence
            dest='generate_metadata',  # value is options['generate_metadata']
            help='force generation of metadata and bag'
        )

        parser.add_argument(
            '--generate_bag',
            action='store_true',  # True for presence, False for absence
            dest='generate_bag',  # value is options['generate_bag']
            help='force generation of metadata and bag'
        )

        parser.add_argument(
            '--if_needed',
            action='store_true',  # True for presence, False for absence
            dest='if_needed',  # value is options['if_needed']
            help='generate only if not present'
        )

        parser.add_argument(
            '--download_bag',
            action='store_true',  # True for presence, False for absence
            dest='download_bag',  # value is options['download_bag']
            help='try downloading the bag'
        )

        parser.add_argument(
            '--open_bag',
            action='store_true',  # True for presence, False for absence
            dest='open_bag',  # value is options['open_bag']
            help='try opening the bag in http without downloading'
        )

        parser.add_argument(
            '--login',
            default='admin',
            dest='login',  # value is options['login']
            help='HydroShare login name'
        )

        parser.add_argument(
            '--password',
            default=None,
            dest='password',  # value is options['password']
            help='HydroShare password'
        )

    def handle(self, *args, **options):

        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                check_bag(rid, options)
        else:
            for r in BaseResource.objects.all():
                check_bag(r.short_id, options)
