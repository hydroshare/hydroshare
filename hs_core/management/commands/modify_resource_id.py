# -*- coding: utf-8 -*-

"""
Modify the resource id of an existing resource

"""

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from hs_core.models import BaseResource, short_id
from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_core.hydroshare.hs_bagit import create_bag
from uuid import UUID
from django.db import transaction, IntegrityError
from django_s3.exceptions import SessionException


class Command(BaseCommand):
    help = "Modify the resource id of an existing resource"

    def add_arguments(self, parser):

        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_id', type=str, help=('Required. The existing id (short_id) of'
                                                           ' the resource'))
        parser.add_argument('new_resource_id', type=str,
                            help=('Optional. The new id (short_id) for the resource. A random one '
                                  'is generated if none is provided. Must be a valid string '
                                  'representation of a uuid hex'))

    def handle(self, *args, **options):

        if not options['resource_id']:
            raise CommandError('resource_id argument is required')
        res_id = options['resource_id']
        try:
            res = get_resource_by_shortkey(res_id, or_404=False)
        except ObjectDoesNotExist:
            raise CommandError("No Resource found for id {}".format(res_id))

        if options['new_resource_id']:
            try:
                UUID(options['new_resource_id'])
                new_res_id = options['new_resource_id']
            except Exception as e:
                raise CommandError('new_resource_id {} must be a valid uuid hex string'
                                   .format(options['new_resource_id']), e)

            try:
                if BaseResource.objects.get(short_id=new_res_id):
                    raise CommandError('resource with id {} already exists'.format(new_res_id))
            except ObjectDoesNotExist:
                pass
        else:
            new_res_id = short_id()

        storage = res.get_s3_storage()

        if storage.exists(res.bag_path):
            try:
                storage.delete(res.bag_path)
                print("{} deleted".format(res.bag_path))
            except SessionException as ex:
                print("{} delete failed: {}".format(res.bag_path, ex.stderr))
                raise EnvironmentError()

        try:
            with transaction.atomic():
                print("Deleting existing bag")
                res.setAVU("bag_modified", True)
                res.setAVU('metadata_dirty', 'true')

                print("Updating BaseResource short_id from {} to {}".format(res_id, new_res_id))
                res.short_id = new_res_id
                res.save()

                print("Updating resource slug")
                res.set_slug('resource/{}'.format(new_res_id))

                print("Updating Resource files short_path")
                for file in res.files.all():
                    file_name = file.short_path.split('data/contents/')[1]
                    file.set_short_path(file_name)

                print("Updating metadata identifiers")
                for i in res.metadata.identifiers.all():
                    i.url = i.url.replace(res_id, new_res_id)
                    i.save()

                print("Updating logical_files metadata")
                for aggregation in res.logical_files:
                    aggregation.metadata.is_dirty = True
                    aggregation.metadata.save()
        except IntegrityError:
            raise EnvironmentError("Error occurred  while updating")

        print("Moving Resource files")
        storage.moveFile(res_id, new_res_id)

        print("Creating Bag")
        create_bag(res)

        print(("Resource id successfully update from {} to {}".format(res_id, new_res_id)))
