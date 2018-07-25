from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.features import Features
from django.contrib.auth.models import Group
from hs_explore.utils import Utils
from datetime import datetime
from pprint import pprint
import sys
from collections import defaultdict
import pandas as pd
from django.contrib.auth.models import User
from hs_core.models import BaseResource
from scipy import sparse
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import numpy.matlib
from sklearn.metrics import jaccard_similarity_score
from hs_core.search_indexes import BaseResourceIndex
from scipy.spatial import distance
import time
from hs_core.hydroshare.utils import user_from_id, group_from_id, get_resource_by_shortkey
from django.db.models import Q
from hs_explore.models import RecommendedResource, RecommendedUser, RecommendedGroup, \
    KeyValuePair, ResourceRecToPair, UserRecToPair, GroupRecToPair, UserPreferences, UserPrefToPair, GroupPreferences, GroupPrefToPair
import re
from hs_tracking.models import Variable
from haystack.query import SearchQuerySet, SQ


class Command(BaseCommand):
    help = "make recommendations for all users."

    def handle(self, *args, **options):
        ind = BaseResourceIndex()
        rec_types = ['Ownership', 'Propensity']
        RecommendedResource.clear()
        #RecommendedUser.clear()
        #RecommendedGroup.clear()
        #out = SearchQuerySet()
        start_time = time.time()
        for up in UserPreferences.objects.filter(user__username='ChristinaBandaragoda'):
            #for rec_type in rec_types:
            target_username = up.user.username
            print(target_username)
            target_user = user_from_id(target_username)
            all_p = up.preferences.all()
            ownership_preferences = UserPrefToPair.objects.filter(user_pref=up, pair__in=all_p, state='Seen', pref_type='Ownership')
            propensity_preferences = UserPrefToPair.objects.filter(user_pref=up, pair__in=all_p, state='Seen', pref_type='Propensity')
            #preferences = up.preferences.filter(pref_type=rec_type)
            interacted_resources = up.interacted_resources.all()
            #subjects = []
            target_ownership_preferences_set = set()
            target_propensity_preferences_set = set()
            target_own_interact_res = set()
            if (ownership_preferences.count() == 0 and propensity_preferences.count() == 0) or (interacted_resources.count() == 0):
                continue
            for p in ownership_preferences:
                if p.pair.key == 'subject':
                    if target_username == 'ChristinaBandaragoda':
                        print("Ownership: {}".format( p.pair.value))
                    target_ownership_preferences_set.add(p.pair.value)
            
            for p in propensity_preferences:
                if p.pair.key == 'subject':
                    if target_username == 'ChristinaBandaragoda':
                        print("Propensity : {}".format(p.pair.value))
                    target_propensity_preferences_set.add(p.pair.value)

            for r in interacted_resources:
                target_own_interact_res.add(r.short_id)

            #short_ids = [res.short_id for res in list(target_own_interact_res)]
            short_ids = list(target_own_interact_res)
            target_jaccard_sim = {}
            out = SearchQuerySet() 
            out = out.exclude(short_id__in=short_ids)
            
            ownership_filter_sq = None
            ownership_out = out
            for tp in target_ownership_preferences_set:
                if ownership_filter_sq is None:
                    ownership_filter_sq = SQ(subject__exact=tp)
                else:
                    ownership_filter_sq.add(SQ(subject__exact=tp), SQ.OR)
            
            if ownership_filter_sq is not None: 
                ownership_out = out.filter(ownership_filter_sq)

            if ownership_out.count() == 0:
                continue 

            propensity_filter_sq = None
            propensity_out = out
            for tp in target_propensity_preferences_set:
                if propensity_filter_sq is None:
                    propensity_filter_sq = SQ(subject__exact=tp)
                else:
                    propensity_filter_sq.add(SQ(subject__exact=tp), SQ.OR)

            if propensity_filter_sq is not None:
                propensity_out = out.filter(propensity_filter_sq)

            if propensity_out.count() == 0:
                continue

            #for res in Ba_eResource.objects.filter(Q(raccess__discoverable=True) | Q(raccess__public=True)).exclude(short_id__in=short_ids):
            for res in ownership_out:
                subjects = res.subject
                #subjects = ind.prepare_subject(res)
                subjects = [sub.lower() for sub in subjects]
                res_id = res.short_id
                if len(subjects) == 0:
                    continue
                intersection_cardinality = len(set.intersection(*[target_ownership_preferences_set, set(subjects)]))
                union_cardinality = len(set.union(*[target_ownership_preferences_set, set(subjects)]))
                js = intersection_cardinality/float(union_cardinality)
                target_jaccard_sim[res_id] = js


            for res in propensity_out:
                subjects = res.subject
                #subjects = ind.prepare_subject(res)
                subjects = [sub.lower() for sub in subjects]
                res_id = res.short_id
                if len(subjects) == 0:
                    continue
                intersection_cardinality = len(set.intersection(*[target_propensity_preferences_set, set(subjects)]))
                union_cardinality = len(set.union(*[target_propensity_preferences_set, set(subjects)]))
                js = intersection_cardinality/float(union_cardinality)
                if res_id not in target_jaccard_sim:
                    target_jaccard_sim[res_id] = js
                else:
                    target_jaccard_sim[res_id] += js

            if target_username == 'ChristinaBandaragoda':
                print("------------ Jaccard similarity for Combination  ---------------")
                for key, value in sorted(target_jaccard_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True)[:5]:
                    candidate_resource = get_resource_by_shortkey(key)
                    r1 = RecommendedResource.recommend(target_user, candidate_resource, 'Combination', round(value, 4))
                    recommended_subjects = ind.prepare_subject(candidate_resource)
                    recommended_subjects = [sub.lower() for sub in recommended_subjects]
                    common_subjects = set.union(set.intersection(target_ownership_preferences_set, set(recommended_subjects)),
                                                set.intersection(target_propensity_preferences_set, set(recommended_subjects)))
                    for cs in common_subjects:
                        r1.relate('subject', cs, 1)
                    print("https://www.hydroshare.org/resource/{}\n{}".format(key, value))
            '''           
            if up.neighbors.all().count() == 0:
                continue 
            print("========== Making user recommendations =============")
            jaccard_users_sim = {}
            for neighbor in up.neighbors.all():
                try:
                    neighbor_up = UserPreferences.objects.get(user=neighbor)
                    neighbor_pref = neighbor_up.preferences.all()
                    neighbor_subjects = set()
                    for p in neighbor_pref:
                        if p.key == 'subject':
                            neighbor_subjects.add(p.value)
                   
                    if (len(neighbor_subjects) == 0):
                        continue
                     
                    intersection_cardinality = len(set.intersection(*[target_preferences_set, neighbor_subjects]))
                    union_cardinality = len(set.union(*[target_preferences_set, neighbor_subjects]))
                    js = intersection_cardinality/float(union_cardinality)
                    jaccard_users_sim[neighbor.username] = js
                except:
                    pass                

            for key, value in sorted(jaccard_users_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True)[:5]:
                candidate_user = user_from_id(key)
                r2 = RecommendedUser.recommend(target_user, candidate_user, round(value, 4))
                neighbor_up = UserPreferences.objects.get(user__username=key)
                neighbor_pref = neighbor_up.preferences.all()
                neighbor_subjects = set()
                for p in neighbor_pref:
                    if p.key == 'subject':
                        neighbor_subjects.add(p.value)
                #recommended_subjects = ug_dict[key]
                common_subjects = set.intersection(target_preferences_set, neighbor_subjects)

                for cs in common_subjects:
                    r2.relate('subject', cs, 1)

                print("user {}:, {}".format(candidate_user.username, str(value)))
            '''
        elapsed_time = time.time() - start_time
        print("time for recommending resources: " + str(elapsed_time))
