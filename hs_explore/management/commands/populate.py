from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from django.contrib.auth.models import User, Group
from hs_core.hydroshare.utils import user_from_id, group_from_id, get_resource_by_shortkey
from hs_explore.models import RecommendedResource, RecommendedGroup, RecommendedUser, KeyValuePair
from pprint import pprint


class Command(BaseCommand):
    def handle(self, *args, **options):
        RecommendedResource.clear()
        RecommendedUser.clear()
        RecommendedGroup.clear()
        KeyValuePair.clear()

        user = user_from_id('alvacouch')
        candidate_user = user_from_id('dtarb')
        candidate_resource = get_resource_by_shortkey('636878cd2380443b907d25aa51a7043a')
        candidate_group = Group.objects.get(name='Landlab')
        r1 = RecommendedResource.recommend(user, candidate_resource, 
                                           keywords=(('subject', 'gerbils', 20.0),))
        r1.relate('subject', 'warthogs', 30.0) 

        r2 = RecommendedUser.recommend(user, candidate_user, 
                                       keywords=(('subject', 'presentation', 30.0),))
        r3 = RecommendedGroup.recommend(user, candidate_group, 
                                        keywords=(('subject', 'agriculture', 10.0),))

        for r in RecommendedGroup.objects.all(): 
            for g in r.keywords.all():
                print("r={} g={} k={} v={}".format(r.user.username, r.candidate_group.name, g.key, g.value))

