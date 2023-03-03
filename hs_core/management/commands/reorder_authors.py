# -*- coding: utf-8 -*-

"""
Fix duplicate author "order" values

Related to https://github.com/hydroshare/hydroshare/issues/4695
"""

from django.core.management.base import BaseCommand, CommandError
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import set_dirty_bag_flag


class Command(BaseCommand):
    help = "Fix duplicate author 'order' values"

    def add_arguments(self, parser):
        # ID of a resource for which users should be re-ordered
        parser.add_argument('--resource_id', type=str, help=('Required. The id (short_id) of'
                                                             ' the resource'))

    def handle(self, *args, **options):
        if not options['resource_id']:
            raise CommandError('resource_id argument is required')
        res_id = options['resource_id']
        res = BaseResource.objects.filter(short_id=res_id).first()
        if not res:
            raise CommandError('No resource found for the provided resource_id')
        if res.raccess.published:
            raise CommandError(f"Resource id: {res_id} is already published--can't update author order.")
        if res.metadata is not None:
            creators = res.metadata.creators.all()
            is_dirty = False
            for index, creator in enumerate(creators, start=1):
                if creator.order != index:
                    print("*" * 100)
                    print(f"Author out of order.\nR:{res.short_id}"
                          f"\nExpected: {index}, got: {creator.order}")
                    creator.order = index
                    creator.save()
                    is_dirty = True
            if is_dirty:
                set_dirty_bag_flag(res)
