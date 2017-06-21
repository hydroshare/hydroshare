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

    def handle(self, *args, **options):

        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    resource = BaseResource.objects.get(short_id=rid)
                    istorage = resource.get_irods_storage()

                    scimeta_path = os.path.join(resource.root_path, 'data',
                                                'resourcemetadata.xml')
                    if istorage.exists(scimeta_path):
                        print("found {}".format(scimeta_path))
                    else:
                        print("{} NOT FOUND".format(scimeta_path))

                    resmap_path = os.path.join(resource.root_path, 'data',
                                               'resourcemap.xml')
                    if istorage.exists(resmap_path):
                        print("found {}".format(resmap_path))
                    else:
                        print("{} NOT FOUND".format(resmap_path))

                    if istorage.exists(resource.bag_path):
                        print("found bag {}".format(resource.bag_path))
                    else:
                        print("bag {} NOT FOUND".format(resource.bag_path))

                    dirty = istorage.getAVU(resource.root_path, 'metadata_dirty')
                    print("metadata_dirty is {}".format(str(dirty)))

                    modified = istorage.getAVU(resource.root_path, 'bag_modified')
                    print("bag_modified is {}".format(str(modified)))

                    if options['generate']:  # generate usable bag

                        create_bag_files(resource)
                        print("metadata generated for {} from Django".format(rid))
                        istorage.setAVU(resource.root_path, 'metadata_dirty', 'false')
                        print("metadata_dirty set to false for {}".format(rid))

                        create_bag_by_irods(rid)
                        print("bag generated for {} from iRODs".format(rid))
                        istorage.setAVU(resource.root_path, 'bag_modified', 'false')
                        print("bag_modified set to false for {}".format(rid))

                    elif options['generate_metadata']:

                        create_bag_files(resource)
                        print("metadata generated for {} from Django".format(rid))
                        istorage.setAVU(resource.root_path, 'metadata_dirty', 'false')
                        print("metadata_dirty set to false for {}".format(rid))

                    elif options['generate_bag']:

                        create_bag_by_irods(rid)
                        print("bag generated for {} from iRODs".format(rid))
                        istorage.setAVU(resource.root_path, 'bag_modified', 'false')
                        print("bag_modified set to false for {}".format(rid))

                    elif options['reset']:  # reset all data to pristine

                        istorage.setAVU(resource.root_path, 'metadata_dirty', 'true')
                        print("metadata_dirty set to true for {}".format(rid))
                        try:
                            istorage.delete(resource.scimeta_path)
                            print("metadata {} deleted".format(resource.scimeta_path))
                        except SessionException as ex:
                            print("delete of {} failed: {}"
                                  .format(resource.scimeta_path,
                                          ex.stderr))
                        try:
                            istorage.delete(resource.resmap_path)
                            print("map {} deleted".format(resource.resmap_path))
                        except SessionException as ex:
                            print("delete of {} failed: {}"
                                  .format(resource.resmap_path,
                                          ex.stderr))

                        istorage.setAVU(resource.root_path, 'bag_modified', 'true')
                        print("bag_modified set to true for {}".format(rid))
                        try:
                            istorage.delete(resource.bag_path)
                            print("bag {} deleted".format(resource.bag_path))
                        except SessionException as ex:
                            print("delete of {} failed: {}"
                                  .format(resource.bag_path,
                                          ex.stderr))

                    elif options['reset_metadata']:

                        istorage.setAVU(resource.root_path, 'metadata_dirty', 'true')
                        print("metadata_dirty set to true for {}".format(rid))
                        try:
                            istorage.delete(resource.scimeta_path)
                            print("metadata {} deleted".format(resource.scimeta_path))
                        except SessionException as ex:
                            print("delete of {} failed: {}"
                                  .format(resource.scimeta_path,
                                          ex.stderr))
                        try:
                            istorage.delete(resource.resmap_path)
                            print("map {} deleted".format(resource.resmap_path))
                        except SessionException as ex:
                            print("delete of {} failed: {}"
                                  .format(resource.resmap_path,
                                          ex.stderr))

                    elif options['reset_bag']:
                        istorage.setAVU(resource.root_path, 'bag_modified', 'true')
                        print("bag_modified set to true for {}".format(rid))
                        try:
                            istorage.delete(resource.bag_path)
                            print("bag {} deleted".format(resource.bag_path))
                        except SessionException as ex:
                            print("delete of {} failed: {}"
                                  .format(resource.bag_path,
                                          ex.stderr))

                except BaseResource.DoesNotExist:
                    print("Resource with id {} NOT FOUND in Django".format(rid))
