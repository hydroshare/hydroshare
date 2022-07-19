# -*- coding: utf-8 -*-

"""
Fix duplicate author "order" values

Related to https://github.com/hydroshare/hydroshare/issues/4695
"""

from django.core.management.base import BaseCommand
from hs_core.models import Creator
from hs_core.models import BaseResource


class Command(BaseCommand):
    help = "Fix duplicate author 'order' values"

    def handle(self, *args, **options):

        resources_obj_ids = BaseResource.objects.values('object_id')
        for id in resources_obj_ids:
            creators = Creator.objects.filter(object_id=id['object_id']).order_by('order')
            for index, creator in enumerate(creators):
                if index == 0:
                    if creator.order != 1:
                        print(f"""Bad first creator order for
                            hs_core_creator id = {creator.id},
                            object_id = {creator.object_id},
                            order = {creator.order},
                            Expected order = 1
                            """)
                        creator.order = 1
                else:
                    previous = index-1
                    if creator.order != creators[previous].order + 1:
                        print(f"""Bad creator order for
                            hs_core_creator id = {creator.id},
                            object_id = {creator.object_id},
                            order = {creator.order},
                            Expected order = {index}
                            """)
                        creator.order = creators[previous].order + 1
                creator.save()
