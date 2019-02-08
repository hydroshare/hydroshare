from django.views.generic import TemplateView  # ListView
import re
from hs_tracking.models import Variable
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
    UserPreferences, UserPrefToPair, GroupPreferences, GroupPrefToPair, \
    PropensityPrefToPair, PropensityPreferences, OwnershipPrefToPair, OwnershipPreferences, \
     UserInteractedResources, UserNeighbors
from hs_core.models import get_user
from django.contrib.auth.decorators import login_required
from django.core import serializers


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
        json_res_list = []
        #RecommendedResource.clear()
        recommended_recs = RecommendedResource.objects.filter(user=target_user)
        recommended_recs.delete()

        out = SearchQuerySet() 
        out = out.filter(recommend_to_users=target_username)
        rpp = PropensityPreferences.objects.get(user=target_user)
        rop = OwnershipPreferences.objects.get(user=target_user)

        rpp.reject('Resource', gk, gv)
        rop.reject('Resource', gk, gv)
        all_pp = rpp.preferences.all()
        all_op = rop.preferences.all()

        ownership_preferences = OwnershipPrefToPair.objects.filter(own_pref=rop,
                                                                   pair__in=all_op,
                                                                   state='Seen',
                                                                   pref_for='Resource')
        propensity_preferences = PropensityPrefToPair.objects.filter(prop_pref=rpp,
                                                                     pair__in=all_pp,
                                                                     state='Seen',
                                                                     pref_for='Resource')

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
       
        for res in res_list:
            json_res = res.to_json()
            json_keywords = [json.dumps(keyword) for keyword in json_res['keywords']]
            json_res['keywords'] = json.dumps(json_keywords)
            json_res_list.append(json.dumps(json_res))
                
            ''' 
            json_res = {}
            json_res['user'] = res.user.username
            json_res['candidate_resource_id'] = res.candidate_resource.short_id
            json_res['candidate_resource_title'] = res.candidate_resource.title
            json_res['relevance'] = res.relevance
            json_res['rec_type'] = res.rec_type
            json_res['state'] = res.state

            keywords = []
            for keyword in res.keywords.all():
                kw = {'key': keyword.key, 'value': keyword.value}
                keywords.append(json.dumps(kw))
            json_res['keywords'] =json.dumps(keywords)

             
            json_res_list.append(json.dumps(json_res))
            '''

        data = json.dumps(json_res_list) 
        #res_list = RecommendedResource.objects\
        #    .filter(state__lte=Status.STATUS_EXPLORED, user__username=target_username)\
        #    .order_by('-relevance')[:Status.RECOMMENDATION_LIMIT]
        #data = serializers.serialize('json', res_list)
        return HttpResponse(data, content_type='json')
        #return render(request, 'recommended_resources.html', {'resource_list': res_list})
    elif update_part == 'users':
        user_list = []
        recommended_users = RecommendedUser.filter(user=target_user)
        recommended_users.delete()

        rpp = PropensityPreferences.objects.get(user=target_user)

        rpp.reject('User', gk, gv)
        all_pp = rpp.preferences.all()

        propensity_preferences = PropensityPrefToPair.objects.filter(prop_pref=rpp,
                                                                     pair__in=all_pp,
                                                                     state='Seen',
                                                                     pref_for='User')
        target_propensity_preferences_set = set()

        for p in propensity_preferences:
            if p.pair.key == 'subject':
                target_propensity_preferences_set.add(p.pair.value)

        user_neighbors = UserNeighbors.objects.get(user=target_user)
        
        for neighbor in user_neighbors.neighbors.all():
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

    else:
        group_list = []
        recommended_gps = RecommendedGroup.objects.filter(user=target_user)
        recommended_gps.delete()
        
        rpp = PropensityPreferences.objects.get(user=target_user)

        rpp.reject('Group', gk, gv)
        all_pp = rpp.preferences.all()

        propensity_preferences = PropensityPrefToPair.objects.filter(prop_pref=rpp,
                                                                     pair__in=all_pp,
                                                                     state='Seen',
                                                                     pref_for='Group')
        target_propensity_preferences_set = set()

        for p in propensity_preferences:
            if p.pair.key == 'subject':
                target_propensity_preferences_set.add(p.pair.value)


        for gp in GroupPreferences.objects.all():
            group = gp.group
            all_gp = gp.preferences.all()
            gp_preferences = GroupPrefToPair.objects.filter(group_pref=gp,
                                                            pair__in=all_gp)
            gp_propensity_preferences_set = set()

            for p in gp_preferences:
                if p.pair.key == 'subject':
                    gp_propensity_preferences_set.add(p.pair.value)

            intersection_cardinality = len(set.intersection(*[target_propensity_preferences_set, gp_propensity_preferences_set]))
            union_cardinality = len(set.union(*[target_propensity_preferences_set, gp_propensity_preferences_set]))
            js = intersection_cardinality/float(union_cardinality)
            r3 = RecommendedGroup.recommend(target_user, group, round(js, 4))
            common_subjects = set.intersection(target_propensity_preferences_set, gp_propensity_preferences_set)
            for cs in common_subjects:
                r3.relate('subject', cs, 1)
            group_list.append(r3)

        group_list.sort(key=lambda x: x.relevance, reverse=True)
        return render(request, 'recommended_groups.html', {'group_list': group_list[:5]})


@login_required
def init_recs(request):
    target_user = get_user(request)
    target_username = target_user.username
    resource_list = RecommendedResource.objects\
            .filter(state__lte=Status.STATUS_EXPLORED, user__username=target_username)\
            .order_by('-relevance')[:Status.RECOMMENDATION_LIMIT]
    for r in resource_list:
        if r.state == Status.STATUS_NEW:
            r.shown()

    user_list = RecommendedUser.objects\
            .filter(state__lte=Status.STATUS_EXPLORED, user__username=target_username)\
            .order_by('-relevance')[:Status.RECOMMENDATION_LIMIT]

    for r in user_list:
        if r.state == Status.STATUS_NEW:
            r.shown()

    group_list = RecommendedGroup.objects\
            .filter(state__lte=Status.STATUS_EXPLORED, user__username=target_username)\
            .order_by('-relevance')[:Status.RECOMMENDATION_LIMIT]

    for r in group_list:
        if r.state == Status.STATUS_NEW:
            r.shown()

    return render(request, 'recommendations.html', {'resource_list': resource_list, 'user_list': user_list, 'group_list': group_list})


def init_explore(request):
    #return render_to_response('recommendations.html')
    if request.is_ajax():
        target_user = get_user(request)
        target_username = target_user.username
        resource_list = RecommendedResource.objects\
                .filter(state__lte=Status.STATUS_EXPLORED, user__username=target_username)\
                .order_by('-relevance')[:Status.RECOMMENDATION_LIMIT]
        for r in resource_list:
            if r.state == Status.STATUS_NEW:
                r.shown()

        user_list = RecommendedUser.objects\
                .filter(state__lte=Status.STATUS_EXPLORED, user__username=target_username)\
                .order_by('-relevance')[:Status.RECOMMENDATION_LIMIT]

        for r in user_list:
            if r.state == Status.STATUS_NEW:
                r.shown()

        group_list = RecommendedGroup.objects\
                .filter(state__lte=Status.STATUS_EXPLORED, user__username=target_username)\
                .order_by('-relevance')[:Status.RECOMMENDATION_LIMIT]

        for r in group_list:
            if r.state == Status.STATUS_NEW:
                r.shown()

        return render(request, 'recommendations.html', {'resource_list': resource_list, 'user_list': user_list, 'group_list': group_list})    
    else:    
        return render(request, 'recommendations.html', {})
