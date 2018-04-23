from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from django.contrib.auth.models import User
from hs_explore.models import Recommend, Status

from hs_core.hydroshare import user_from_id, get_resource_by_shortkey

import sys


class Command(BaseCommand):
    help = "Print abstract for a resource."

    def handle(self, *args, **options):
        Recommend.objects.all().delete() # clear recommendation system
        couch = user_from_id('alvacouch')
        sauk = get_resource_by_shortkey('636878cd2380443b907d25aa51a7043a')
        Recommend.recommend(couch, sauk, relevance=1.0) 
        Recommend.recommend(couch, sauk, relevance=0.5, state=Status.STATUS_VIEWED) 
        Recommend.recommend_ids('alvacouch', '636878cd2380443b907d25aa51a7043a', state=Status.STATUS_APPROVED, relevance=0.7)
        for r in Recommend.objects.all(): 
            print("user={}, resource={}, state={}, relevance={}".format(str(r.user), str(r.resource), str(r.state), str(r.relevance)))
        
