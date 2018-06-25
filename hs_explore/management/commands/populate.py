from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from django.contrib.auth.models import User, Group
from hs_core.hydroshare.utils import user_from_id, group_from_id, get_resource_by_shortkey
from hs_explore.models import RecommendedResource, RecommendedGroup, RecommendedUser
from pprint import pprint


class Command(BaseCommand):
    def handle(self, *args, **options):
        user = user_from_id('alvacouch')
        candidate_user = user_from_id('dtarb')
        candidate_resource = get_resource_by_shortkey('636878cd2380443b907d25aa51a7043a')
        candidate_group = Group.objects.get(name='Landlab')
        RecommendedResource.recommend(user, candidate_resource)
        RecommendedUser.recommend(user, candidate_user)
        RecommendedGroup.recommend(user, candidate_group)
