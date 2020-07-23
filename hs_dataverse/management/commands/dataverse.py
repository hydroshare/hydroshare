# -*- coding: utf-8 -*-

"""
Generate metadata and bag for a resource from Django

"""

import os
from os import listdir
import json
import requests
from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.hs_bagit import create_bag_files
from hs_core.tasks import create_bag_by_irods
from django_irods.icommands import SessionException
from django.contrib.auth.models import User
from hs_core.hydroshare import get_party_data_from_user
from django_irods import icommands
from hs_dataverse.utils import upload_dataset
import tempfile
from django_irods.views import download as download_bag_from_irods
from pprint import pprint
import shutil
#from hs_dataverse import run_tests

BUFSIZE = 4096

def export_bag(rid, options): 
    requests.packages.urllib3.disable_warnings()
    try:
        # database handle
        resource = BaseResource.objects.get(short_id=rid)
 
        # instance with proper subclass type and access
        res = resource.get_content_model()
        assert res, (resource, resource.content_model)
        print("resource is {}".format(res.short_id))
        print("content type: {}".format(res.discovery_content_type))
        if (res.discovery_content_type != 'Composite'): 
            print("resource type '{}' is not supported. Aborting.".format(res.discovery_content_type))
            exit(1)

        # create temporary directory 
        mkdir = tempfile.mkdtemp(prefix=rid, suffix='_dataverse_tempdir', dir='/tmp')

        # file handle
        istorage = res.get_irods_storage()

        root_exists = istorage.exists(res.root_path)

        if root_exists:
            # print status of metadata/bag system
            scimeta_path = os.path.join(res.root_path, 'data',
                                        'resourcemetadata.xml')
            scimeta_exists = istorage.exists(scimeta_path)
            
            if scimeta_exists:
                print("resource metadata {} found".format(scimeta_path))
                            
                if icommands.ACTIVE_SESSION:
                    session = icommands.ACTIVE_SESSION
                else:
                    raise keyerror('settings must have irods_global_session set')

                args = ('-') # redirect to stdout
                fd = session.run_safe('iget', None, scimeta_path, *args)
                #read(fd) to get file contents
                
                contents = b""
                #for temp in fd.stdout:
                #    contents += str(temp.decode('utf8'))
                
                BUFSIZE = 4096
                block = fd.stdout.read(BUFSIZE) 
                while block !=   b"": 
                    # Do stuff with byte. 
                    contents += block
                    block = fd.stdout.read(BUFSIZE) 
        
                _, mkfile_path = tempfile.mkstemp(prefix='resourcemetadata.xml', dir=mkdir)
                with open(mkfile_path, 'wb') as mkfile:
                    mkfile.write(contents)
            else:
                print("resource metadata {} not found".format(scimeta_path))

            resmap_path = os.path.join(res.root_path, 'data', 'resourcemap.xml')
            resmap_exists = istorage.exists(resmap_path)
            if resmap_exists:
                print("resource map {} found".format(resmap_path))
            else:
                print("resource map {} not found".format(resmap_path))

            bag_exists = istorage.exists(res.bag_path)
            if bag_exists:
                print("bag {} found".format(res.bag_path))
            else:
                print("bag {} NOT FOUND".format(res.bag_path))

            dirty = res.getAVU('metadata_dirty')
            print("{}.metadata_dirty is {}".format(rid, str(dirty)))

            modified = res.getAVU('bag_modified')
            print("{}.bag_modified is {}".format(rid, str(modified)))

            # make sure that the metadata file syncs with the database
            if dirty or not scimeta_exists or options['generate_metadata']:
                try:
                    create_bag_files(res)
                except ValueError as e:
                    print(("{}: value error encountered: {}".format(rid, str(e))))
                    return
                print("{}: metadata generated from Django".format(rid))
                res.setAVU('metadata_dirty', 'false')
                print("{}.metadata_dirty set to false".format(rid))
                res.setAVU('bag_modified', 'true')
                print("{}.bag_modified set to false".format(rid))

            if modified or not bag_exists or options['generate_bag']:
                create_bag_by_irods(rid)
                print("{}: bag generated from iRODs".format(rid))
                res.setAVU('bag_modified', 'false')
                print("{}.bag_modified set to false".format(rid))

                if icommands.ACTIVE_SESSION:
                    session = icommands.ACTIVE_SESSION
                else:
                    raise keyerror('settings must have irods_global_session set')

                dir = '/'.join([res.root_path, 'data/contents'])
                istorage = res.get_irods_storage()
                data = istorage.listdir(dir)
                
                for file in data[1]:
                    bag_data_path = '/'.join([res.root_path, 'data/contents', file])
                    args = ('-') # redirect to stdout
                    fd = session.run_safe('iget', None, bag_data_path, *args)

                    #contents = ''
                    #for temp in fd.stdout:
                    #    contents += str(temp.decode('utf8'))
                    #_, mkfile_path = tempfile.mkstemp(prefix=file, dir=mkdir)
                    #with open(mkfile_path, 'w') as mkfile:
                    #    mkfile.write(contents)

                    
                    contents = b""
                    block = fd.stdout.read(BUFSIZE) 
                    while block !=   b"": 
                        # Do stuff with byte. 
                        contents += block
                        block = fd.stdout.read(BUFSIZE) 
                    _, mkfile_path = tempfile.mkstemp(prefix=file, dir=mkdir)
                    with open(mkfile_path, 'wb') as mkfile:
                        mkfile.write(contents)


                #try:
                #    istorage.getFile(res.bag_path, mkfile)
                #except SessionException as e:
                #    print("bag file not found: {}".format(e.message))
                #    exit(1)



            ### get owners. An owner is a user
            ### see https://docs.djangoproject.com/en/3.0/ref/contrib/auth/
            
            owners = list(resource.raccess.owners)

            print('o:', owners)
            if len(owners) == 0:
                owner_dict = {
                    'username': '',
                    'first_name': '',
                    'last_name': '',
                    'email': '',
                    'organization': ''
                }
            else:
                for o in owners: 
                    print("username: {}".format(o.username))
                    print("first_name: {}".format(o.first_name))
                    print("last_name: {}".format(o.last_name))
                    print("email: {}".format(o.email))
                    profile = o.userprofile
                    party = get_party_data_from_user(o)
                    print("organization: {}".format(party['organization']))

                    owner_dict = {
                        'username': format(o.username),
                        'first_name': format(o.first_name),
                        'last_name': format(o.last_name),
                        'email': format(o.email),
                        'organization': format(party['organization'])
                    }

            _, mkfile_path = tempfile.mkstemp(prefix='ownerdata.json', dir=mkdir)
            with open(mkfile_path, 'w') as mkfile:
                json.dump(owner_dict, mkfile)
            # get other metadata
             

            # read extended metadata as key/value pairsi
            ext_metadata = ''
            for key, value in list(res.extra_metadata.items()):
                print(" key={}, value={}".format(key, value))
                ext_metadata = ext_metadata + key + ': ' + value + '\n'

            # get funding agency data
            funding_agency_names = []
            award_numbers = []

            for a in res.metadata.funding_agencies.all():
                funding_agency_names.append(a.agency_name)
                award_numbers.append(a.award_number) 

            # get list of contributors
            contributors = []
            for c in res.metadata.contributors.all():
                contributors.append(str(c))

            # if the resource is published, set the doi and update booleans in dict.
            doi = ''
            if res.raccess.public:
                public = True
            else: 
                public = False
            
            if res.raccess.published:
                published = True
                doi = res.doi
            else:
                published = False 

            other_metadata_dict = {
                'rid': rid,
                'public': public,
                'published': published,
                'doi': doi,
                'extended_metadata_notes': ext_metadata,
                'language': str(res.metadata.language),
                'funding_agency_names': funding_agency_names,
                'award_numbers': award_numbers,
                'contributors': contributors
            }

            _, mkfile_path = tempfile.mkstemp(prefix='other_metadata.json', dir=mkdir)
            with open(mkfile_path, 'w') as mkfile:
                json.dump(other_metadata_dict, mkfile)

        else:
            print("Resource with id {} does not exist in iRODS".format(rid))
    except BaseResource.DoesNotExist:
        print("Resource with id {} NOT FOUND in Django".format(rid))

    # before returning the temporary directory, rename all the files by 
    # removing the extra characters inserted by mkstemp()
    for file in os.listdir(mkdir):
        file_path = '/'.join([mkdir, file])
        os.rename(file_path, file_path[:-8]) # remove last 8 characters generated by tempfile
        file_path = file_path[:-8]

    return mkdir

class Command(BaseCommand):
    help = "Export a resource to DataVerse."

    def add_arguments(self, parser):

        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_ids', nargs='*', type=str)

        # Named (optional) arguments

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
            '--password',
            default=None,
            dest='password',  # value is options['password']
            help='HydroShare password'
        )

        #parser.add_argument(
        #    '--test',
        #    default=None,
        #    dest='test',  # value is options['test']
        #    help='run tests'
        #)


    def handle(self, *args, **options):
        # server url
        base_url = 'https://dataverse.harvard.edu'

        # api-token
        api_token = 'c57020c2-d954-48da-be47-4e06785ceba0'

        # parent given here
        dv = 'mydv'

        #if len(options['test']) > 0:
        #    run_tests()
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                temp_dir = export_bag(rid, options)
                upload_dataset(base_url, api_token, dv, temp_dir)
                shutil.rmtree(temp_dir, ignore_errors=False)
        else:
            print("no resource id specified: aborting")
