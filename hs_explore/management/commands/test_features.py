from datetime import date, timedelta
import time
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from hs_core.hydroshare import get_resource_by_shortkey
from hs_core.hydroshare.features import Features
from hs_core.models import BaseResource 
from haystack.query import SearchQuerySet, SQ
from pprint import pprint

def more_like_this(res):
    results = SearchQuerySet().more_like_this(res)
    return results

class Command(BaseCommand):

    def add_arguments(self, parser):
        # a list of resource id's: none does nothing.
        parser.add_argument('users', nargs='*', type=str)

    def handle(self, *args, **options):
        if len(options['users']) > 0:
            for u in options['users']:
                user = User.objects.get(username=u)
                # today = date.today()
                today = date(2017,11,1) 
                beginning = today - timedelta(days=14)
                rids = Features.visits_for_one_user(beginning, today, user)
                rids = Features.existing(rids) 
                for r in rids:
                    print("user {} visited {}".format(user.username, r))
                    for s in Features.subjects(r): 
                        print("   subject is {}".format(s.encode('ascii', 'ignore')))
                    resource = BaseResource.objects.get(short_id=r)  # must be type BaseResource
                    if resource.raccess.public or resource.raccess.discoverable: 
                        print("more like this...")
                        res = SearchQuerySet().filter(short_id=r)
                        for t in res: 
                            print("resource id is {}".format(t.id))
                        # for r in more_like_this(resource): 
                        #     print("    {} {}".format(r.short_id, r.title.encode('ascii', 'ignore')))
                rids = Features.apps_for_one_user(beginning, today, user)
                rids = Features.existing(rids) 
                for r in rids:
                    print("user {} opened app for {}".format(user.username, r))
                    for s in Features.subjects(r): 
                        print("   subject is {}".format(s.encode('ascii', 'ignore')))
                    resource = BaseResource.objects.get(short_id=r)  # must be type BaseResource
                    if resource.raccess.public or resource.raccess.discoverable: 
                        print("more like this...")
                        res = SearchQuerySet().filter(short_id=r)
                        for t in res: 
                            print("resource id is {}".format(t.id))
                        # for r in more_like_this(resource): 
                        #     print("    {} {}".format(r.short_id, r.title.encode('ascii', 'ignore')))
                rids = Features.creates_for_one_user(beginning, today, user)
                rids = Features.existing(rids) 
                for r in rids:
                    print("user {} created {}".format(user.username, r))
                    for s in Features.subjects(r): 
                        print("   subject is {}".format(s.encode('ascii', 'ignore')))
                    resource = BaseResource.objects.get(short_id=r)  # must be type BaseResource
                    if resource.raccess.public or resource.raccess.discoverable: 
                        print("more like this...")
                        res = SearchQuerySet().filter(short_id=r)
                        for t in res: 
                            print("resource id is {}".format(t.id))
                        # for r in more_like_this(resource): 
                        #     print("    {} {}".format(r.short_id, r.title.encode('ascii', 'ignore')))
                rids = Features.downloads_for_one_user(beginning, today, user)
                rids = Features.existing(rids) 
                for r in rids:
                    print("user {} downloaded {}".format(user.username, r))
                    for s in Features.subjects(r): 
                        print("   subject is {}".format(s.encode('ascii', 'ignore')))
                    resource = BaseResource.objects.get(short_id=r)  # must be type BaseResource
                    if resource.raccess.public or resource.raccess.discoverable: 
                        print("more like this...")
                        res = SearchQuerySet().filter(short_id=r)
                        for t in res: 
                            print("resource id is {}".format(t.id))
                        # for r in more_like_this(resource): 
                        #     print("    {} {}".format(r.short_id, r.title.encode('ascii', 'ignore')))
        else:
            print("no users found.")



from pprint import pprint
import re


