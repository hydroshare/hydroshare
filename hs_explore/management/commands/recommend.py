import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
from pprint import pprint
import scipy.cluster.hierarchy as shc
from sklearn.cluster import AgglomerativeClustering
from collections import defaultdict
from scipy.spatial.distance import pdist
import scipy.spatial as sp
import random
import time
from datetime import date, timedelta
from haystack.query import SearchQuerySet
from hs_tracking.models import Variable
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import user_from_id, get_resource_by_shortkey
from django.core.management.base import BaseCommand
from hs_explore.models import ResourcePreferences, UserPreferences, GroupPreferences,\
    PropensityPreferences, OwnershipPreferences, UserInteractedResources, UserNeighbors
from hs_explore.models import RecommendedResource, RecommendedUser, RecommendedGroup, \
    GroupPreferences, GroupPrefToPair, PropensityPrefToPair, PropensityPreferences, \
    UserInteractedResources, UserNeighbors
from haystack.query import SearchQuerySet, SQ
from sklearn.metrics.pairwise import pairwise_distances
from django.contrib.auth.models import Group, User


def get_resource_to_subjects():
    resource_ids = set()
    all_subjects = set()
    resource_to_subjects = {}
    for res in BaseResource.objects.all():
        raw_subjects = [subject.value.strip() for subject in res.metadata.subjects.all()
                                .exclude(value__isnull=True)]
        subjects = [sub.lower() for sub in raw_subjects]
        all_subjects.update(subjects)
        resource_ids.add(res.short_id)
        resource_to_subjects[res.short_id] = set(subjects)
    all_subjects_list = list(all_subjects)
    res_df = pd.DataFrame(0, index=list(resource_ids), columns=all_subjects_list)
    for res, subjects in resource_to_subjects.iteritems():
	    for sub in subjects:
	        if res in res_df.index and sub in res_df.columns:
		        res_df.at[res, sub] = 1

    return res_df, resource_to_subjects

def get_users_interacted_resources(beginning, today):
    propensity = defaultdict(int)
    all_usernames = set()
    user_to_resources_set = defaultdict(set)
    triples = Variable.user_resource_matrix(beginning, today)
    for v in triples:
        username = v[0]
        res = v[1]
	all_usernames.add(username)
	user_to_resources_set[username].add(res)
    
    user_to_resources = defaultdict(list)
    for username, res_ids_set in user_to_resources_set.iteritems():
	res_ids_list = list(res_ids_set)    
        user_to_resources[username] = list(res_ids_set)
        user = user_from_id(username)
        res_list = []
        for res_id in res_ids_list:
            try:
                r = get_resource_by_shortkey(res_id)
                res_list.append(r)
            except:
                continue
        UserInteractedResources.interact(user, res_list)
    return user_to_resources, all_usernames

def get_user_cumulative_profiles(user_to_resources, res_to_subs, all_res_ids, all_subjects_list, all_usernames):
    m_ur = pd.DataFrame(0, index=list(all_usernames), columns=all_res_ids)
    for username, res_ids in user_to_resources.iteritems():
        for res_id in res_ids:
            if username in m_ur.index and res_id in m_ur.columns:
                m_ur.at[username, res_id] = 1

    m_rg = pd.DataFrame(0, index=all_res_ids, columns=all_subjects_list)
    for res_id, subs in res_to_subs.iteritems():
        for sub in subs:
            if res_id in m_rg.index and sub in m_rg.columns:
                m_rg.at[res_id, sub] = 1

    m_ur_values = m_ur.values
    m_rg_values = m_rg.values
    m_ug_values = np.matmul(m_ur_values, m_rg_values)
    m_ug = pd.DataFrame(m_ug_values, index=list(all_usernames), columns=all_subjects_list)
    
    return m_ur, m_rg, m_ug

def store_user_preferences(m_ug, user_to_resources, all_subjects_list):
    active_user_set = set()
    for username, row in m_ug.iterrows():
        if username not in user_to_resources:
            continue
        user = user_from_id(username)
        user_nonzero_index = row.nonzero()
        if len(user_nonzero_index[0]) == 0:
            continue
        prop_pref_subjects = []
        for i in user_nonzero_index[0]:
            if row.iat[i] == 0:
                break
            subject = all_subjects_list[i]
            prop_pref_subjects.append(('subject', subject, row.iat[i]))
        PropensityPreferences.prefer(user, 'Resource', prop_pref_subjects)
        PropensityPreferences.prefer(user, 'User', prop_pref_subjects)
        PropensityPreferences.prefer(user, 'Group', prop_pref_subjects)
	active_user_set.add(username)
    return active_user_set

def get_user_to_top5_keywords(m_ug_freq):
    all_subjects_list = list(m_ug_freq.columns.values)
    user_to_top5_keywords = defaultdict(list)
    for username, row in m_ug_freq.iterrows():
        sorted_row = (-row).argsort()
        for i in sorted_row[:5]:
            if row.iat[i] == 0:
                break
            subject = all_subjects_list[i]
	    user_to_top5_keywords[username].append(subject)

    return user_to_top5_keywords

def recommend_resources(res_to_subs, user_to_resources, user_to_top5_keywords, m_ug, res_df):
    all_res_ids = list(res_df.index)
    user_to_recommended_resources_list = {}
    for username, top5_keywords in user_to_top5_keywords.iteritems():
	if len(top5_keywords) == 0 or not top5_keywords:
	    continue
        user_resources = user_to_resources[username]
	if len(user_resources) == 0 or not user_resources:
	    continue

        top5_keywords_set = set(top5_keywords)
        out = SearchQuerySet()
        out = out.exclude(short_id__in=user_resources)
        filter_sq = None
        user_out = out
        for single_keyword in top5_keywords_set:
            if filter_sq is None:
                filter_sq = SQ(subject__contains=single_keyword)
            else:
                filter_sq.add(SQ(subject__contains=single_keyword), SQ.OR)

        if filter_sq is not None:
            user_out = out.filter(filter_sq)

        if user_out.count() == 0:
            continue

	user_freq_vec = m_ug.loc[username].values
	top5_filter_recommendations_sim = {}
	    
        for candidate_res in user_out:
            res_id = candidate_res.short_id
            if res_id not in all_res_ids:
		continue
	    res_vec = res_df.loc[res_id].values
            cos_sim = 1 - sp.distance.cosine(user_freq_vec, res_vec)
	    if cos_sim > 0:
                top5_filter_recommendations_sim[res_id] = cos_sim

	    top5_filter_sorted_list = sorted(top5_filter_recommendations_sim.iteritems(), key=lambda (k, v): (v, k), reverse=True)[:10]
        user_to_recommended_resources_list[username] = top5_filter_sorted_list
    return user_to_recommended_resources_list

def store_recommended_resources(user_to_recommended_resources_list, res_to_subs):
    for username, recommend_resources_list in user_to_recommended_resources_list.iteritems():
	user = user_from_id(username)
        user_preferences = PropensityPreferences.objects.get(user = user)
        user_preferences_pairs = user_preferences.preferences.all()
        user_resources_preferences = PropensityPrefToPair.objects.\
                                                filter(prop_pref=user_preferences,
                                                       pair__in=user_preferences_pairs,
                                                       state='Seen',
                                                       pref_for='Resource')
        user_res_preferences_set = set()
        for p in user_resources_preferences:
            if p.pair.key == 'subject':
                user_res_preferences_set.add(p.pair.value)

        for res_id, sim in recommend_resources_list:
            recommended_res = get_resource_by_shortkey(res_id)
            r = RecommendedResource.recommend(user,
                                            recommended_res,
                                            'Propensity',
                                            round(sim, 4))
            recommended_subjects = res_to_subs[res_id]
            common_subjects = set.intersection(user_res_preferences_set,
                                                set(recommended_subjects))
            for cs in common_subjects:
                r.relate('subject', cs, 1)

def cal_nn_matrix(m_ug):
    nonzero_m_ug = m_ug[(m_ug.T != 0).any()]
    ug_jac_sim = 1 - pairwise_distances(nonzero_m_ug, metric="cosine")
    ug_jac_sim = pd.DataFrame(ug_jac_sim, index=nonzero_m_ug.index,
                              columns=nonzero_m_ug.index)
    knn = 10
    order = np.argsort(-ug_jac_sim.values, axis=1)[:, :knn]
    ug_nearest_neighbors = pd.DataFrame(ug_jac_sim.columns[order],
                                        columns=['neighbor{}'
                                                    .format(i) for i in range(1, knn+1)],
                                        index=ug_jac_sim.index)

    return ug_nearest_neighbors

def store_nn(ug_nearest_neighbors):
    for username, ranked_neighbors in ug_nearest_neighbors.iterrows():
	try:
	    user = user_from_id(username)
	    neighbors = []
            if len(ranked_neighbors) == 0 or not ranked_neighbors:
                continue

	    for neighbor_name in ranked_neighbors.values:
                if username == neighbor_name:
                    continue
                try:
                    neighbor = user_from_id(neighbor_name)
                    neighbors.append(neighbor)
                except:
                    continue
            UserNeighbors.relate_neighbos(current_user, neighbors)
        except:
            continue

def recommend_users(m_ug, ug_nearest_neighbors):
    user_to_recommended_users_list = {}
    for username, ranked_neighbors in ug_nearest_neighbors.iterrows():
	if username not in m_ug.index:
	    continue
	user_vec = m_ug.loc[username].values
	user = user_from_id(username)
	if len(ranked_neighbors.values) == 0:
	    continue
	user_top10_nearest_neighbors = {}
	for neighbor_name in ranked_neighbors.values:
	    neighbor = user_from_id(neighbor_name)
	    if neighbor_name in m_ug.index:
		if neighbor_name  == username:
		    continue
		neighbor_vec = m_ug.loc[neighbor_name].values
	        cos_sim = 1 - sp.distance.cosine(user_vec, neighbor_vec)
                if cos_sim > 0:
		    user_top10_nearest_neighbors[neighbor_name] = cos_sim
	user_to_recommended_users_list[username] = user_top10_nearest_neighbors
    return user_to_recommended_users_list

def store_recommended_users(user_to_recommended_users_list):
    for username, recommended_users_list in user_to_recommended_users_list.iteritems():
        user = user_from_id(username)
        user_preferences = PropensityPreferences.objects.get(user = user)
        user_preferences_pairs = user_preferences.preferences.all()
        user_resources_preferences = PropensityPrefToPair.objects.\
                                                filter(prop_pref=user_preferences,
                                                       pair__in=user_preferences_pairs,
                                                       state='Seen',
                                                       pref_for='User')
        user_preferences_set = set()
        for p in user_resources_preferences:
            if p.pair.key == 'subject':
                user_preferences_set.add(p.pair.value)	

        for neighbor_name, sim in recommended_users_list.iteritems():
            neighbor = user_from_id(neighbor_name)
            neighbor_pref_subjects = []
            neighbor_preferences = PropensityPreferences.objects.get(user = neighbor)
            neighbor_preferences_pairs = neighbor_preferences.preferences.all()
            neighbor_resources_preferences = PropensityPrefToPair.objects.\
                                                    filter(prop_pref=neighbor_preferences,
                                                           pair__in=neighbor_preferences_pairs,
                                                           state='Seen',
                                                           pref_for='User')
            neighbor_preferences_set = set()
            for p in neighbor_resources_preferences:
                if p.pair.key == 'subject':
                    neighbor_preferences_set.add(p.pair.value)

            r = RecommendedUser.recommend(user, neighbor, round(sim, 4))
            common_subjects = set.intersection(user_preferences_set, neighbor_preferences_set)

            for cs in common_subjects:
                r.relate('subject', cs, 1)


def get_group_to_held_resources_and_members(res_to_subs):
    group_to_res = defaultdict(list)
    group_to_members = defaultdict(list)
    group_to_subjects = defaultdict(set)
    for group in Group.objects.filter(gaccess__active=True):
        if group is not None and \
           group.name != 'test' and group.name != 'demo':
            group_name = group.name
            for res in group.gaccess.view_resources:
                group_to_res[group_name].append(res.short_id)
		if res.short_id in res_to_subs:
		    subjects = res_to_subs[res.short_id]
		    group_to_subjects[group_name].update(subjects)

	    group_members = User.objects.filter(u2ugp__group=group)
	    for member in group_members:
		member_name = member.username
		group_to_members[group_name].append(member_name)

    return group_to_res, group_to_subjects, group_to_members

def get_group_profiles(group_to_subjects, all_subjects_list, group_to_members, m_ug, active_user_set):
    all_group_names = list(group_to_subjects.keys())
    m_hg = pd.DataFrame(0, index=all_group_names, columns=all_subjects_list)

    for group_name, members in group_to_members.iteritems():
        group_subjects = group_to_subjects[group_name]
	for member_name in members:
	    if member_name  not in active_user_set:
		continue
            member = user_from_id(member_name)
            
	    member_preferences = PropensityPreferences.objects.get(user = member)
            member_preferences_pairs = member_preferences.preferences.all()
            member_resources_preferences = PropensityPrefToPair.objects.\
                                                    filter(prop_pref=member_preferences,
                                                           pair__in=member_preferences_pairs,
                                                           state='Seen',
                                                           pref_for='Group')
	    member_preferences_set = set()
            for p in member_resources_preferences:
                if p.pair.key == 'subject':
                    member_preferences_set.add(p.pair.value)

   	    for member_subject in member_preferences_set:
		if member_subject in group_subjects:
		    if group_name in m_hg.index and member_subject in m_hg.columns and \
		       member_subject in m_ug.columns:
			m_hg.at[group_name, member_subject] += m_ug.at[member_name, member_subject]
    return m_hg

def store_group_preferences(m_hg, all_subjects_list):
    active_groups_set = set()
    for group_name, row in m_hg.iterrows():
        group = Group.objects.get(name=group_name)
        group_nonzero_index = row.nonzero()
        group_subjects = []
        for i in group_nonzero_index[0]:
            subject = all_subjects_list[i]
            group_subjects.append(('subject', subject, row.iat[i]))
        GroupPreferences.prefer(group, group_subjects)
	active_groups_set.add(group_name)
    return active_groups_set

def recommend_groups(m_ug, m_hg, group_to_members):
    user_to_recommended_groups_list = {}
    for username, user_freq_pref in m_ug.iterrows():
	user_vec = user_freq_pref.values
	groups_to_sim = {}
	for group_name, group_freq_pref in m_hg.iterrows():
	    if username in group_to_members[group_name]:
		continue
	    group_vec = group_freq_pref.values
	    cos_sim = 1 - sp.distance.cosine(user_vec, group_vec)
            if cos_sim > 0:
		groups_to_sim[group_name] = cos_sim
	    top10_sorted_group_list = sorted(groups_to_sim.iteritems(), key=lambda (k, v): (v, k), reverse=True)[:10]
        user_to_recommended_groups_list[username] = top10_sorted_group_list
    return user_to_recommended_groups_list

def store_recommended_groups(user_to_recommended_groups_list, active_user_set, active_groups_set):
    for username, recommended_groups_list in user_to_recommended_groups_list.iteritems():
	if username not in active_user_set:
	    continue
	user = user_from_id(username)
        user_preferences = PropensityPreferences.objects.get(user = user)
        user_preferences_pairs = user_preferences.preferences.all()
        user_group_preferences = PropensityPrefToPair.objects.\
                                                filter(prop_pref=user_preferences,
                                                       pair__in=user_preferences_pairs,
                                                       state='Seen',
                                                       pref_for='Group')
        user_preferences_set = set()
        for p in user_group_preferences:
            if p.pair.key == 'subject':
                user_preferences_set.add(p.pair.value)

	for group_name, sim in recommended_groups_list:
            if group_name not in active_groups_set:
		continue
            group_gp = GroupPreferences.objects.get(group__name=group_name)
            group_pref = group_gp.preferences.all()
            group_propensity_preferences = GroupPrefToPair.objects.filter(group_pref=group_gp,
                                                                          pair__in=group_pref)
            group_subjects = set()
            for p in group_propensity_preferences:
                if p.pair.key == 'subject':
                    group_subjects.add(p.pair.value)

            group = Group.objects.get(name=group_name)
            r = RecommendedGroup.recommend(user, group, round(sim, 4))
            common_subjects = set.intersection(user_preferences_set, group_subjects)

            for cs in common_subjects:
                r.relate('subject', cs, 1)

def clear_old_data():
    ResourcePreferences.clear()
    UserPreferences.clear()
    GroupPreferences.clear()
    PropensityPreferences.clear()
    OwnershipPreferences.clear()
    UserInteractedResources.clear()
    UserNeighbors.clear()
    RecommendedResource.clear()
    RecommendedUser.clear()
    RecommendedGroup.clear()

def main():
    clear_old_data()
    
    res_df, res_to_subs = get_resource_to_subjects()
    all_subjects_list = list(res_df.columns.values)
    all_res_ids = list(res_df.index)

    # month = random.randint(1, 12)
    # day = random.randint(1, 28)
    end_date = date(2018, 07, 31)
    # d = 6
    start_date = end_date - timedelta(days=6)
    user_to_resources, all_usernames = get_users_interacted_resources(start_date, end_date)
    m_ur, m_rg, m_ug = get_user_cumulative_profiles(user_to_resources, res_to_subs, all_res_ids, all_subjects_list, all_usernames)
    active_user_set = store_user_preferences(m_ug, user_to_resources, all_subjects_list)
    user_to_top5_keywords = get_user_to_top5_keywords(m_ug)
    user_to_recommended_resources_list = recommend_resources(res_to_subs, user_to_resources, user_to_top5_keywords, m_ug, res_df)
    store_recommended_resources(user_to_recommended_resources_list, res_to_subs)
    ug_nearest_neighbors = cal_nn_matrix(m_ug)
    user_to_recommended_users_list = recommend_users(m_ug, ug_nearest_neighbors)
    store_recommended_users(user_to_recommended_users_list)
    group_to_res, group_to_subjects, group_to_members = get_group_to_held_resources_and_members(res_to_subs)
    m_hg = get_group_profiles(group_to_subjects, all_subjects_list, group_to_members, m_ug, active_user_set)
    active_groups_set = store_group_preferences(m_hg, all_subjects_list)
    user_to_recommended_groups_list = recommend_groups(m_ug, m_hg, group_to_members)
    store_recommended_groups(user_to_recommended_groups_list, active_user_set, active_groups_set) 
    
class Command(BaseCommand):
    help = "Compare jaccard and cosine for user short-term data"

    def handle(self, *args, **options):
        main()

