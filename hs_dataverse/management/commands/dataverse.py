# -*- coding: utf-8 -*-

"""
Generate metadata and bag for a resource from Django,
the uploads the resource to dataverse. Call with:
./hsctl managepy dataverse <rid>
use --generate_bag to upload the files
"""
from django.core.management.base import BaseCommand
from hs_dataverse.utils import export_bag
from hs_dataverse.utils import upload_dataset
import shutil
from hs_dataverse.utils import evaluate_json_template
import json


class Command(BaseCommand):
    help = "Export a resource to DataVerse."

    def add_arguments(self, parser):
        """
        adds an argument to the command class instance

        :param self: the command object
        :param parser: the parser to which the argument should be added
        :return: nothing
        """

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

    def handle(self, *args, **options):
        """
        driver to handle the command

        :param self: the command object
        :param args: pointer to the arguments (unused)
        :param options: additional optional parameters to the command line call
        :return: nothing
        """
       
        base_url = 'https://dataverse.harvard.edu'  # server url
        api_token = 'c57020c2-d954-48da-be47-4e06785ceba0'  # api-token
        dv = 'mydv'  # parent given here
        
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                temp_dir = export_bag(rid, options)
                upload_dataset(base_url, api_token, dv, temp_dir)
                shutil.rmtree(temp_dir, ignore_errors=False)
        else:
            print("no resource id specified: aborting")
