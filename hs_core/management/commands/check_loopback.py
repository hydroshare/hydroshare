# -*- coding: utf-8 -*-

"""
Generate metadata and bag for a resource from Django

"""

import os
from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.hs_bagit import create_bag_files
from hs_core.tasks import create_bag_by_irods
from django_irods.icommands import SessionException
import requests


def get_nginx_ip():
    filename = os.path.join(os.path.abspath(os.path.dirname(__name__)), "tmp/nginx_ip")
    # print filename
    file = open(filename, "r")
    for line in file:
        # first line is nginx IP address
        ip = line.strip(" \r\n\t")
        break
    file.close()
    # print ip
    return ip


def check_bag(rid, options):
    try:
        resource = BaseResource.objects.get(short_id=rid)
        istorage = resource.get_irods_storage()

        root_exists = istorage.exists(resource.root_path)

        if root_exists:
            scimeta_path = os.path.join(resource.root_path, 'data',
                                        'resourcemetadata.xml')
            scimeta_exists = istorage.exists(scimeta_path)
            if scimeta_exists:
                print("{} found".format(scimeta_path))
            else:
                print("{} NOT FOUND".format(scimeta_path))

            resmap_path = os.path.join(resource.root_path, 'data', 'resourcemap.xml')
            resmap_exists = istorage.exists(resmap_path)
            if resmap_exists:
                print("{} found".format(resmap_path))
            else:
                print("{} NOT FOUND".format(resmap_path))

            bag_exists = istorage.exists(resource.bag_path)
            if bag_exists:
                print("{} bag found".format(resource.bag_path))
            else:
                print("{} BAG NOT FOUND".format(resource.bag_path))

            dirty = resource.getAVU('metadata_dirty')
            print("{}.metadata_dirty is {}".format(rid, str(dirty)))

            modified = resource.getAVU('bag_modified')
            print("{}.bag_modified is {}".format(rid, str(modified)))

            if options['generate'] or options['download']:  # generate usable bag

                if (not options['if_needed'] and not options['download']) or \
                   dirty or not scimeta_exists or not resmap_exists:
                    try:
                        create_bag_files(resource)
                    except ValueError as e:
                        print("{}: value error encountered: {}".format(rid, e.message))
                        return

                    print("{} metadata generated from Django".format(rid))
                    resource.setAVU('metadata_dirty', 'false')
                    print("{}.metadata_dirty set to false".format(rid))
                    resource.setAVU('bag_modified', 'true')
                    print("{}.bag_modified set to true".format(rid))
                    dirty = False 
                    scimeta_exists = True
                    resmap_exists = True
                    modified = True

                if (not options['if_needed'] and not options['download']) or \
                   modified or not bag_exists:
                    create_bag_by_irods(rid)
                    print("{} bag generated from iRODs".format(rid))
                    resource.setAVU('bag_modified', 'false')
                    print("{}.bag_modified set to false".format(rid))

            elif options['generate_metadata']:

                if not options['if_needed'] or dirty or not scimeta_exists or not resmap_exists:
                    try:
                        create_bag_files(resource)
                    except ValueError as e:
                        print("{}: value error encountered: {}".format(rid, e.message))
                        return
                    print("{}: metadata generated from Django".format(rid))
                    resource.setAVU('metadata_dirty', 'false')
                    print("{}.metadata_dirty set to false".format(rid))
                    resource.setAVU('bag_modified', 'true')
                    print("{}.bag_modified set to false".format(rid))

            elif options['generate_bag']:

                if not options['if_needed'] or modified or not bag_exists:
                    create_bag_by_irods(rid)
                    print("{}: bag generated from iRODs".format(rid))
                    resource.setAVU('bag_modified', 'false')
                    print("{}.bag_modified set to false".format(rid))

            elif options['reset']:  # reset all data to pristine

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

            elif options['reset_metadata']:

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

            elif options['reset_bag']:
                resource.setAVU('bag_modified', 'true')
                print("{}.bag_modified set to true".format(rid))
                try:
                    istorage.delete(resource.bag_path)
                    print("{} deleted".format(resource.bag_path))
                except SessionException as ex:
                    print("{} delete failed: {}"
                          .format(resource.bag_path,
                                  ex.stderr))

            if options['download']:
                # print("downloading {}".format(resource.bag_path))
                if istorage.exists(resource.bag_path):
                    requests.packages.urllib3.disable_warnings()
                    ip = get_nginx_ip()
                    uri = resource.bag_url
                    qualified = "http://{}{}".format(ip, uri)
                    print("downloading via {}".format(qualified))
                    # try:
                    #     r = requests.get(qualified, stream=True)
                    # except requests.exceptions.SSLError as e:
                    #     print("exception during ssl download: {}".format(e.message))
                    # Skip verification because of unqualified URL. 
                    r = requests.get(qualified, stream=True, verify=False)
                    print("status code is {}".format(r.status_code))
                    # filename = os.path.join(os.path.abspath(os.path.dirname(__name__)),
                    #      "tmp", resource.short_id + ".zip")
                    # print("filename is {}".format(filename))
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
            '--download',
            action='store_true',  # True for presence, False for absence
            dest='download',  # value is options['download']
            help='actually download the bag'
        )

    def handle(self, *args, **options):

        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                check_bag(rid, options)
        else:
            for r in BaseResource.objects.all():
                check_bag(r.short_id, options)
