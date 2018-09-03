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
    KeyValuePair, ResourceRecToPair, UserRecToPair, GroupRecToPair, ResourcePreferences, ResourcePrefToPair, \
    UserPreferences, UserPrefToPair, GroupPreferences, GroupPrefToPair, \
    PropensityPrefToPair, PropensityPreferences, OwnershipPrefToPair, OwnershipPreferences, UserInteractedResources, UserNeighbors
import re
from hs_tracking.models import Variable
from haystack.query import SearchQuerySet, SQ


def recommended_resources(target_user, out, target_res_preferences_set, target_jaccard_sim):
    #ind = BaseResourceIndex()

    filter_sq = None
    target_out = out
    for tp in target_res_preferences_set:
        if filter_sq is None:
            filter_sq = SQ(subject__contains=tp)
        else:
            filter_sq.add(SQ(subject__contains=tp), SQ.OR)

    if filter_sq is not None:
        target_out = out.filter(filter_sq)

    if target_out.count() == 0:
        return

    # Ownership Similarity
    # for res in ownership_out:
    #     subjects = res.subject
    #     subjects = [sub.lower() for sub in subjects]
    #     res_id = res.short_id
    #     if len(subjects) == 0:
    #         continue
    #     intersection_cardinality = len(set.intersection(*[target_res_ownership_preferences_set, set(subjects)]))
    #     union_cardinality = len(set.union(*[target_res_ownership_preferences_set, set(subjects)]))
    #     js = intersection_cardinality/float(union_cardinality)
    #     target_jaccard_sim[res_id] = js

    # Propensity SImilarity
    for res in target_out:
        subjects = res.subject
        subjects = [sub.lower() for sub in subjects]
        res_id = res.short_id
        if len(subjects) == 0:
            continue
        intersection_cardinality = len(set.intersection(*[target_res_preferences_set, set(subjects)]))
        union_cardinality = len(set.union(*[target_res_preferences_set, set(subjects)]))
        js = intersection_cardinality/float(union_cardinality)
        if res_id not in target_jaccard_sim:
            target_jaccard_sim[res_id] = js
        else:
            target_jaccard_sim[res_id] += js

    #if target_username == 'ChristinaBandaragoda':
    '''
    print("------------ Jaccard similarity for Propensity  ---------------")
    for key, value in sorted(target_jaccard_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True)[:5]:
        candidate_resource = get_resource_by_shortkey(key)
        r1 = RecommendedResource.recommend(target_user, candidate_resource, 'Propensity', round(value, 4))
        recommended_subjects = ind.prepare_subject(candidate_resource)
        recommended_subjects = [sub.lower() for sub in recommended_subjects]
        common_subjects = set.intersection(target_res_preferences_set, set(recommended_subjects))
        for cs in common_subjects:
            r1.relate('subject', cs, 1)
        print("https://www.hydroshare.org/resource/{}\n{}".format(key, value))
    '''

def recommended_groups(target_user, target_group_preferences_set):
    jaccard_groups_sim = {}
    target_user_in_groups = set()
    for g in Group.objects.filter(g2ugp__user=target_user):
        target_user_in_groups.add(g.name)
    for gp in GroupPreferences.objects.all():
        if gp.group.name in target_user_in_groups:
            continue
        all_gp = gp.preferences.all()
        group_propensity_preferences = GroupPrefToPair.objects.filter(group_pref=gp,
                                                                      pair__in=all_gp)

        group_subjects = set()
        for p in group_propensity_preferences:
            if p.pair.key == 'subject':
                group_subjects.add(p.pair.value)

        if (len(group_subjects) == 0):
            continue

        intersection_cardinality = len(set.intersection(*[target_group_preferences_set, group_subjects]))
        union_cardinality = len(set.union(*[target_group_preferences_set, group_subjects]))
        js = intersection_cardinality/float(union_cardinality)
        jaccard_groups_sim[gp.group.name] = js

    for key, value in sorted(jaccard_groups_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True)[:5]:
        candidate_group = Group.objects.get(name=key)
        rg = RecommendedGroup.recommend(target_user, candidate_group, round(value, 4))
        group_gp = GroupPreferences.objects.get(group__name=key)
        group_pref = group_gp.preferences.all()
        group_propensity_preferences = GroupPrefToPair.objects.filter(group_pref=group_gp,
                                                                      pair__in=group_pref)
        group_subjects = set()
        for p in group_propensity_preferences:
            if p.pair.key == 'subject':
                group_subjects.add(p.pair.value)
        common_subjects = set.intersection(target_group_preferences_set, group_subjects)

        for cs in common_subjects:
            if target_user.username == 'ChristinaBandaragoda':
                print("{} : {}".format(key, cs))
            rg.relate('subject', cs, 1)
        if value != 0:
            print("group {}:, {}".format(candidate_group.name, str(value)))

def recommended_users(target_user, target_user_preferences_set):
    jaccard_users_sim = {}
    try:
        user_neighbors = UserNeighbors.objects.get(user=target_user)
    except:
        return
    if user_neighbors.neighbors.count() == 0:
        return

    # all_up = up.preferences.all()
    # target_user_propensity_preferences = UserPrefToPair.objects.filter(user_pref=up,
    #                                                                    pair__in=all_up,
    #                                                                    state='Seen',
    #                                                                    pref_type='Propensity')
    # target_user_propensity_preferences_set = set()
    # for p in target_user_propensity_preferences:
    #     if p.pair.key == 'subject':
    #         target_user_propensity_preferences_set.add(p.pair.value)

    for neighbor in user_neighbors.neighbors.all():
        try:
            neighbor_up = PropensityPreferences.objects.get(user=neighbor)
            neighbor_pref = neighbor_up.preferences.all()
            neighbor_propensity_preferences = PropensityPrefToPair.objects.filter(prop_pref=neighbor_up, 
                                                                                  pair__in=neighbor_pref, 
                                                                                  state='Seen', 
                                                                                  pref_for='User')
            neighbor_subjects = set()
            for p in neighbor_propensity_preferences:
                if p.pair.key == 'subject':
                    neighbor_subjects.add(p.pair.value)

            if (len(neighbor_subjects) == 0):
                continue

            intersection_cardinality = len(set.intersection(*[target_user_preferences_set, neighbor_subjects]))
            union_cardinality = len(set.union(*[target_user_preferences_set, neighbor_subjects]))
            js = intersection_cardinality/float(union_cardinality)
            if js - 0 < 0.00000001:
                break
            jaccard_users_sim[neighbor.username] = js
        except:
            continue
    if len(jaccard_users_sim) == 0:
        return

    for key, value in sorted(jaccard_users_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True)[:5]:
        candidate_user = user_from_id(key)
        r2 = RecommendedUser.recommend(target_user, candidate_user, round(value, 4))
        neighbor_up = PropensityPreferences.objects.get(user__username=key)
        neighbor_pref = neighbor_up.preferences.all()
        neighbor_propensity_preferences = PropensityPrefToPair.objects.filter(prop_pref=neighbor_up, 
                                                                              pair__in=neighbor_pref, 
                                                                              state='Seen', 
                                                                              pref_for='User')
        neighbor_subjects = set()
        for p in neighbor_propensity_preferences:
            if p.pair.key == 'subject':
                neighbor_subjects.add(p.pair.value)
        common_subjects = set.intersection(target_user_preferences_set, neighbor_subjects)

        for cs in common_subjects:
            if target_user.username == 'ChristinaBandaragoda':
                print("{} : {}".format(key, cs))
            r2.relate('subject', cs, 1)

        print("user {}:, {}".format(candidate_user.username, str(value)))


class Command(BaseCommand):
    help = "make recommendations for all users."

    def handle(self, *args, **options):
        RecommendedResource.clear()
        RecommendedUser.clear()
        RecommendedGroup.clear()
        start_time = time.time()
        counter = 0
        active_users = []
        ind = BaseResourceIndex()
        for pp in PropensityPreferences.objects.all():
            target_username = pp.user.username
            active_users.append(target_username)
            print(target_username)
            target_user = user_from_id(target_username)
            all_p = pp.preferences.all()

            resource_preferences = PropensityPrefToPair.objects.filter(prop_pref=pp, pair__in=all_p, state='Seen', pref_for='Resource')
            user_preferences = PropensityPrefToPair.objects.filter(prop_pref=pp, pair__in=all_p, state='Seen', pref_for='User')
            group_preferences = PropensityPrefToPair.objects.filter(prop_pref=pp, pair__in=all_p, state='Seen', pref_for='Group')            
            
            target_interacted_resources = UserInteractedResources.objects.get(user=target_user)

            target_res_preferences_set = set()
            target_ownership_resource_preferences_set = set()
            target_user_preferences_set = set()
            target_group_preferences_set = set()
            target_interacted_res_set = set()

            if (resource_preferences.count() == 0 and user_preferences.count() == 0 and group_preferences.count() == 0):
                continue
            if target_interacted_resources.interacted_resources.count() == 0:
                continue

            for p in resource_preferences:
                if p.pair.key == 'subject':
                    target_res_preferences_set.add(p.pair.value)

            for p in user_preferences:
                if p.pair.key == 'subject':
                    target_user_preferences_set.add(p.pair.value)

            for p in group_preferences:
                if p.pair.key == 'subject':
                    target_group_preferences_set.add(p.pair.value)


            for r in target_interacted_resources.interacted_resources.all():
                target_interacted_res_set.add(r.short_id)

            target_interacted_res_short_ids = list(target_interacted_res_set)

            out = SearchQuerySet()
            out = out.exclude(short_id__in=target_interacted_res_short_ids)

            target_res_jaccard_sim = {}
            recommended_resources(target_user, out, target_res_preferences_set, target_res_jaccard_sim)
            try:
                op = OwnershipPreferences.objects.get(user=target_user)
                all_op = op.preferences.all()
                ownership_resource_preferences = OwnershipPrefToPair.objects.filter(own_pref=op, pair__in=all_op, state='Seen', pref_for='Resource')
                #target_ownership_resource_preferences_set = set()
                for p in ownership_resource_preferences:
                    if p.pair.key == 'subject':
                        target_ownership_resource_preferences_set.add(p.pair.value)
                print("@@@@@@@ active users ownership resources")
                recommended_resources(target_user, out, target_ownership_resource_preferences_set, target_res_jaccard_sim)
            except:
                pass    
            print("------------ Jaccard similarity for Combination ---------------")
            for key, value in sorted(target_res_jaccard_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True)[:5]:
                candidate_resource = get_resource_by_shortkey(key)
                r1 = RecommendedResource.recommend(target_user, candidate_resource, 'Combination', round(value, 4))
                recommended_subjects = ind.prepare_subject(candidate_resource)
                recommended_subjects = [sub.lower() for sub in recommended_subjects]
                common_subjects = set.union(set.intersection(target_res_preferences_set, set(recommended_subjects)),
                                            set.intersection(target_ownership_resource_preferences_set, set(recommended_subjects)))
                for cs in common_subjects:
                    r1.relate('subject', cs, 1)
                print("https://www.hydroshare.org/resource/{}\n{}".format(key, value))
            
            print("========== Making group recommendations =============")
            if len(target_group_preferences_set) != 0:
                recommended_groups(target_user, target_group_preferences_set)

            print("========== Making user recommendations =============")
            recommended_users(target_user, target_user_preferences_set)
            counter += 1
        counter2 = 0 
        for op in OwnershipPreferences.objects.exclude(user__username__in=active_users):
            target_username = op.user.username
            print("Only ownership : " + target_username)
            target_user = user_from_id(target_username)
            all_p = op.preferences.all()

            ownership_resource_preferences = OwnershipPrefToPair.objects.filter(own_pref=op, pair__in=all_p, state='Seen', pref_for='Resource')

            target_interacted_resources = UserInteractedResources.objects.get(user=target_user)

            target_ownership_res_preferences_set = set()
            target_interacted_res_set = set()

            if (resource_preferences.count() == 0 and user_preferences.count() == 0 and group_preferences.count() == 0):
                continue
            if target_interacted_resources.interacted_resources.count() == 0:
                continue

            for p in ownership_resource_preferences:
                if p.pair.key == 'subject':
                    target_ownership_res_preferences_set.add(p.pair.value)

            for r in target_interacted_resources.interacted_resources.all():
                target_interacted_res_set.add(r.short_id)

            target_interacted_res_short_ids = list(target_interacted_res_set)

            out = SearchQuerySet()
            out = out.exclude(short_id__in=target_interacted_res_short_ids)
            target_res_jaccard_sim = {}
            recommended_resources(target_user, out, target_ownership_res_preferences_set, target_res_jaccard_sim)
            
            print("------------ Jaccard similarity for Combination  ---------------")
            for key, value in sorted(target_res_jaccard_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True)[:5]:
                candidate_resource = get_resource_by_shortkey(key)
                r1 = RecommendedResource.recommend(target_user, candidate_resource, 'Combination', round(value, 4))
                recommended_subjects = ind.prepare_subject(candidate_resource)
                recommended_subjects = [sub.lower() for sub in recommended_subjects]
                common_subjects = set.intersection(target_ownership_res_preferences_set, set(recommended_subjects))
                for cs in common_subjects:
                    r1.relate('subject', cs, 1)
                print("https://www.hydroshare.org/resource/{}\n{}".format(key, value))
            counter2 += 1
        elapsed_time = time.time() - start_time
        print("time for recommending resources: " + str(elapsed_time) + " for " + str(counter) +  " + " + str(counter2))
