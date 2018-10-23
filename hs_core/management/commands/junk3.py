# -*- coding: utf-8 -*-

"""
Test whether irods is corrupting output from icommands
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey
from django_irods.icommands import SessionException
import os

# import logging
# from django_irods.storage import IrodsStorage


def is_ascii(s):
    return all(ord(c) < 128 for c in s)


class Command(BaseCommand):
    help = "Check synchronization between iRODS and Django."

    def add_arguments(self, parser):

        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):
        next = False
        find = '58e0450944834429b359eb9670215816'
        for r in BaseResource.objects.all():
            if next:
                print("{} is next after {}".format(r.short_id, find))
                exit(0)
            elif r.short_id == find:
                next = True
