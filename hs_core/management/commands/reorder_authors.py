# -*- coding: utf-8 -*-

"""
Fix duplicate author "order" values

Related to https://github.com/hydroshare/hydroshare/issues/4695
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import set_dirty_bag_flag


class Command(BaseCommand):
    help = "Fix duplicate author 'order' values"

    def handle(self, *args, **options):
        resources = BaseResource.objects.filter(raccess__published=False).only('object_id', 'short_id')
        for res in resources:
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
