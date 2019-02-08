from django.views.generic import TemplateView  # ListView
import re
from hs_tracking.models import Variable
from django.http import HttpResponse
from hs_core.hydroshare.utils import user_from_id, group_from_id, get_resource_by_shortkey
from django.db.models import Q
from hs_core.search_indexes import BaseResourceIndex
from datetime import datetime
import time
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from hs_core.models import BaseResource
from django.template.loader import render_to_string
from django.shortcuts import render_to_response, render
from haystack.query import SearchQuerySet, SQ
import json
from django.http import HttpResponse
from django.template.response import TemplateResponse
from hs_explore.models import RecommendedResource, RecommendedUser, \
    RecommendedGroup, Status, KeyValuePair, ResourceRecToPair, UserRecToPair, \
    GroupRecToPair, ResourcePreferences, ResourcePrefToPair, \
    UserPreferences, UserPrefToPair, GroupPreferences, GroupPrefToPair
from hs_core.models import get_user
from django.contrib.auth.decorators import login_required


@login_required
def update_recs(request):
    ind = BaseResourceIndex()
    target_user = get_user(request)
    target_username = target_user.username
    print("target user: " + target_username)
    update_part = str(request.GET['recommended_part'])
    gk = str(request.GET['genre_key'])
    gv = str(request.GET['genre_value'])

    if update_part == 'resources':
        res_list = []
        #RecommendedResource.clear()
        recommended_recs = RecommendedResource.objects.get(user=target_user)
        recommended_recs.delete()
        out = SearchQuerySet() 
        out = out.filter(recommend_to_users=target_username)
        rp = ResourcePreferences.objects.get(user=target_user)
        rp.reject(gk, gv)
        all_p = rp.preferences.all()
        ownership_preferences = ResourcePrefToPair.objects.filter(res_pref=rp,
                                                                  pair__in=all_p,
                                                                  state='Seen',
                                                                  pref_type='Ownership')
        propensity_preferences = ResourcePrefToPair.objects.filter(res_pref=rp,
                                                                   pair__in=all_p,
                                                                   state='Seen',
                                                                   pref_type='Propensity')

        target_ownership_preferences_set = set()
        target_propensity_preferences_set = set()

        for p in ownership_preferences:
            if p.pair.key == 'subject':
                target_ownership_preferences_set.add(p.pair.value)

        for p in propensity_preferences:
            if p.pair.key == 'subject':
                target_propensity_preferences_set.add(p.pair.value)


        for thing in out:
            res = get_resource_by_shortkey(thing.short_id)

            subjects = ind.prepare_subject(res)
            subjects = [sub.lower() for sub in subjects]
            res_id = res.short_id
            intersection_cardinality = len(set.intersection(*[target_ownership_preferences_set, set(subjects)]))
            union_cardinality = len(set.union(*[target_ownership_preferences_set, set(subjects)]))
            js1 = intersection_cardinality/float(union_cardinality)

            intersection_cardinality = len(set.intersection(*[target_propensity_preferences_set, set(subjects)]))
            union_cardinality = len(set.union(*[target_propensity_preferences_set, set(subjects)]))
            js2 = intersection_cardinality/float(union_cardinality)
            js = js1 + js2

            r1 = RecommendedResource.recommend(target_user, res, 'Combination', round(js, 4))
            common_subjects = set.union(set.intersection(target_ownership_preferences_set, set(subjects)),
                                        set.intersection(target_propensity_preferences_set, set(subjects)))
            for cs in common_subjects:
                r1.relate('subject', cs, 1)
            res_list.append(r1)
        res_list.sort(key=lambda x: x.relevance, reverse=True)
        return render(request, 'recommended_resources.html', {'resource_list': res_list})
    elif update_part == 'users':
        user_list = []
        recommended_users = RecommendedUser.get(user=target_user)
        recommended_users.delete()
        up = UserPreferences.objects.get(user=target_user)
        up.reject(gk, gv)
        all_p = up.preferences.all()
        propensity_preferences = UserPrefToPair.objects.filter(user_pref=up,
                                                               pair__in=all_p,
                                                               state='Seen',
                                                               pref_type='Propensity')

        target_propensity_preferences_set = set()

        for p in propensity_preferences:
            if p.pair.key == 'subject':
                target_propensity_preferences_set.add(p.pair.value)

        for neighbor in up.neighbors.all():
            neighbor_up = UserPreferences.objects.get(user=neighbor)
            neighbor_pref = neighbor_up.preferences.all()
            neighbor_propensity_preferences = UserPrefToPair.objects.filter(user_pref=neighbor_up,
                                                                            pair__in=neighbor_pref,
                                                                            pref_type='Propensity')
            neighbor_subjects = set()
            for p in neighbor_propensity_preferences:
                if p.pair.key == 'subject':
                    neighbor_subjects.add(p.pair.value)

            intersection_cardinality = len(set.intersection(*[target_propensity_preferences_set, neighbor_subjects]))
            union_cardinality = len(set.union(*[target_propensity_preferences_set, neighbor_subjects]))
            js = intersection_cardinality/float(union_cardinality)
            r2 = RecommendedUser.recommend(target_user, neighbor, round(js, 4))

            common_subjects = set.intersection(target_propensity_preferences_set, neighbor_subjects)

            for cs in common_subjects:
                r2.relate('subject', cs, 1)
            user_list.append(r2)
        
        user_list.sort(key=lambda x: x.relevance, reverse=True)
        return render(request, 'recommended_users.html', {'user_list': user_list[:5]})
    '''
    else:
        groups_list = []
        recommended_gps = RecommendedGroup.get(user=target_user)
        recommended_gps.delete()
        gp = GroupPreferences.objects.get(user=target_user)
        gp.reject(gk, gv)
        all_p = gp.preferences.all()
        propensity_preferences = GroupPrefToPair.objects.filter(user_pref=gp,
                                                                pair__in=all_p,
                                                                state='Seen')

        target_propensity_preferences_set = set()

        for p in propensity_preferences:
            if p.pair.key == 'subject':
                target_propensity_preferences_set.add(p.pair.value)

        for neighbor in up.neighbors.all():
            neighbor_up = UserPreferences.objects.get(user=neighbor)
            neighbor_pref = neighbor_up.preferences.all()
            neighbor_propensity_preferences = UserPrefToPair.objects.filter(user_pref=neighbor_up,
                                                                            pair__in=neighbor_pref,
                                                                            pref_type='Propensity')
            neighbor_subjects = set()
            for p in neighbor_propensity_preferences:
                if p.pair.key == 'subject':
                    neighbor_subjects.add(p.pair.value)

            intersection_cardinality = len(set.intersection(*[target_propensity_preferences_set, neighbor_subjects]))
            union_cardinality = len(set.union(*[target_propensity_preferences_set, neighbor_subjects]))
            js = intersection_cardinality/float(union_cardinality)
            r2 = RecommendedUser.recommend(target_user, neighbor, round(js, 4))

            common_subjects = set.intersection(target_propensity_preferences_set, neighbor_subjects)

            for cs in common_subjects:
                r2.relate('subject', cs, 1)
            user_list.append(r2)

        user_list.sort(key=lambda x: x.relevance, reverse=True)
        return render(request, 'recommended_users.html', {'user_list': user_list[:5]})
        '''
