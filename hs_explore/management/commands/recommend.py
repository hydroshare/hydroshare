import numpy as np
from collections import defaultdict
import scipy.spatial as sp
from datetime import date, timedelta
from haystack.query import SearchQuerySet
from hs_tracking.models import Variable
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import user_from_id, get_resource_by_shortkey
from django.core.management.base import BaseCommand
from hs_explore.models import ResourcePreferences, UserPreferences, OwnershipPreferences
from hs_explore.models import RecommendedResource, RecommendedUser, RecommendedGroup, \
    GroupPreferences, GroupPrefToPair, PropensityPrefToPair, PropensityPreferences, \
    UserInteractedResources, UserNeighbors
from haystack.query import SQ
from django.contrib.auth.models import Group, User
from operator import itemgetter


def get_resource_to_subjects():
    resource_ids = set()
    all_subjects = set()
    resource_to_subjects = {}
    for res in BaseResource.objects.all():
        if res is None or res.metadata is None or res.metadata.subjects is None:
            continue
        raw_subjects = [subject.value.strip() for subject in res.metadata.subjects.all()
                                .exclude(value__isnull=True)]
        subjects = [sub.lower() for sub in raw_subjects]
        all_subjects.update(subjects)
        resource_ids.add(res.short_id)
        resource_to_subjects[res.short_id] = set(subjects)
    all_subjects_list = list(all_subjects)
    return resource_to_subjects, all_subjects_list


def get_users_interacted_resources(beginning, today):
    all_usernames = set()
    user_to_resources_set = defaultdict(set)
    triples = Variable.user_resource_matrix(beginning, today)
    for v in triples:
        username = v[0]
        res = v[1]
        all_usernames.add(username)
        user_to_resources_set[username].add(res)
    user_to_resources = defaultdict(list)
    for username, res_ids_set in user_to_resources_set.items():
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


def get_user_cumulative_profiles(user_to_resources, res_to_subs):
    user_to_subs = {}

    for username, res_ids in user_to_resources.items():
        user_sub_to_freq = defaultdict(int)
        for res_id in res_ids:
            if res_id in res_to_subs:
                subs = res_to_subs[res_id]
                for sub in subs:
                    user_sub_to_freq[sub] += 1
        user_to_subs[username] = user_sub_to_freq
    return user_to_subs


def get_user_to_top5_keywords(user_to_subs):
    user_to_top5_keywords = defaultdict(list)
    for username, user_sub_to_freq in user_to_subs.items():
        for sub in sorted(user_sub_to_freq, key=user_sub_to_freq.get, reverse=True)[:5]:
            user_to_top5_keywords[username].append(sub)
    return user_to_top5_keywords


def store_user_preferences(user_to_subs):
    active_user_set = set()
    for username, user_sub_to_freq in user_to_subs.items():
        user = user_from_id(username)
        prop_pref_subjects = []
        active_user_set.add(username)
        for sub, freq in user_sub_to_freq.items():
            prop_pref_subjects.append(('subject', sub, freq))
        PropensityPreferences.prefer(user, 'Resource', prop_pref_subjects)
        PropensityPreferences.prefer(user, 'User', prop_pref_subjects)
        PropensityPreferences.prefer(user, 'Group', prop_pref_subjects)
    return active_user_set


def get_res_sub_vec(res_subs, all_subjects_list):
    vec_len = len(all_subjects_list)
    res_vec = np.zeros(vec_len)
    for sub in res_subs:
        ind = all_subjects_list.index(sub)
        res_vec[ind] = 1
    return res_vec


def get_user_freq_vec(sub_to_freq, all_subjects_list):
    vec_len = len(all_subjects_list)
    freq_vec = np.zeros(vec_len)
    for sub, freq in sub_to_freq.items():
        ind = all_subjects_list.index(sub)
        freq_vec[ind] = freq
    return freq_vec


def recommend_resources(res_to_subs, user_to_resources, user_to_top5_keywords, user_to_subs, all_subjects_list):
    all_res_ids = list(res_to_subs.keys())
    user_to_recommended_resources_list = {}
    for username, top5_keywords in user_to_top5_keywords.items():
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

        user_freq_vec = get_user_freq_vec(user_to_subs[username], all_subjects_list)
        top5_filter_recommendations_sim = {}
        for candidate_res in user_out:
            res_id = candidate_res.short_id
            if res_id not in all_res_ids:
                continue
            res_vec = get_res_sub_vec(res_to_subs[res_id], all_subjects_list)
            cos_sim = 1 - sp.distance.cosine(user_freq_vec, res_vec)
            if cos_sim > 0:
                top5_filter_recommendations_sim[res_id] = cos_sim

            top5_filter_sorted_list = sorted(top5_filter_recommendations_sim.items(),
                                             key=itemgetter(1), reverse=True)[:10]
        user_to_recommended_resources_list[username] = top5_filter_sorted_list
    return user_to_recommended_resources_list


def store_recommended_resources(user_to_recommended_resources_list, res_to_subs):
    for username, recommend_resources_list in user_to_recommended_resources_list.items():
        user = user_from_id(username)
        user_preferences = PropensityPreferences.objects.get(user=user)
        user_preferences_pairs = user_preferences.preferences.all()
        user_resources_preferences = PropensityPrefToPair.objects.\
                                                filter(prop_pref=user_preferences,
                                                       pair__in=user_preferences_pairs,
                                                       state='Seen',
                                                       pref_for='Resource')
        user_res_preferences_set = set()
        user_res_pref_to_weight = {}
        for p in user_resources_preferences:
            if p.pair.key == 'subject':
                user_res_preferences_set.add(p.pair.value)
                user_res_pref_to_weight[p.pair.value] = p.weight

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
                r.relate('subject', cs, user_res_pref_to_weight[cs])


def cal_nn(user_to_subs, all_subjects_list):
    user_to_users = {}
    for user1, subs1 in user_to_subs.items():
        if user1 not in user_to_users:
            user_to_users[user1] = defaultdict(float)
        user1_to_user_sim = user_to_users[user1]
        user1_freq_vec = get_user_freq_vec(user_to_subs[user1], all_subjects_list)
        for user2, subs2 in user_to_subs.items():
            if user1 == user2:
                continue
            if user2 in user_to_users:
                user2_to_user_sim = user_to_users[user2]
                user1_to_user_sim[user2] = user2_to_user_sim[user1]
            else:
                user2_freq_vec = get_user_freq_vec(user_to_subs[user2], all_subjects_list)
                cos_sim = 1 - sp.distance.cosine(user1_freq_vec, user2_freq_vec)
                user1_to_user_sim[user2] = cos_sim
    return user_to_users


def get_user_knn(user_to_users):
    user_to_knn = defaultdict(list)
    for username, user_to_user_sim in user_to_users.items():
        for neigh in sorted(user_to_user_sim, key=user_to_user_sim.get, reverse=True)[:10]:
            user_to_knn[username].append(neigh)

    return user_to_knn


def store_nn(user_to_knn):
    for username, neighbors_usernames in user_to_knn.items():
        neighbors = []
        try:
            user = user_from_id(username)
            for neighbor_username in neighbors_usernames:
                try:
                    neighbor = user_from_id(neighbor_username)
                    neighbors.append(neighbor)
                except:
                    continue
            UserNeighbors.relat_neighbors(user, neighbors)
        except:
            continue


def recommend_users(user_to_users, user_to_knn):
    user_to_recommended_users_list = {}
    for username, nn in user_to_knn.items():
        user_to_user_sim = user_to_users[username]
        user_top10_nn = {}
        for neighbor in nn:
            if user_to_user_sim[neighbor] > 0:
                user_top10_nn[neighbor] = user_to_user_sim[neighbor]
        user_to_recommended_users_list[username] = user_top10_nn
    return user_to_recommended_users_list


def store_recommended_users(user_to_recommended_users_list):
    for username, recommended_users_list in user_to_recommended_users_list.items():
        user = user_from_id(username)
        user_preferences = PropensityPreferences.objects.get(user=user)
        user_preferences_pairs = user_preferences.preferences.all()
        user_users_preferences = PropensityPrefToPair.objects.\
                                                filter(prop_pref=user_preferences,
                                                       pair__in=user_preferences_pairs,
                                                       state='Seen',
                                                       pref_for='User')
        user_preferences_set = set()
        user_user_pref_to_weight = {}
        for p in user_users_preferences:
            if p.pair.key == 'subject':
                user_preferences_set.add(p.pair.value)
                user_user_pref_to_weight[p.pair.value] = p.weight

        for neighbor_name, sim in recommended_users_list.items():
            neighbor = user_from_id(neighbor_name)
            neighbor_preferences = PropensityPreferences.objects.get(user=neighbor)
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
                r.relate('subject', cs, user_user_pref_to_weight[cs])


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


def get_group_profiles(group_to_subjects, group_to_members, user_to_subs):
    group_to_profiles = {}
    for group_name, members in group_to_members.items():
        group_subjecst = group_to_subjects[group_name]
        if group_name not in group_to_profiles:
            group_to_profiles[group_name] = defaultdict(int)
        group_profile = group_to_profiles[group_name]
        for member_name in members:
            if member_name not in user_to_subs:
                continue
            member_to_sub_freq = user_to_subs[member_name]
            for sub, freq in member_to_sub_freq.items():
                if sub in group_subjecst:
                    group_profile[sub] += freq
    return group_to_profiles


def store_group_preferences(group_to_profiles, all_subjects_list):
    active_groups_set = set()
    for group_name, group_to_sub_freq in group_to_profiles.items():
        group = Group.objects.get(name=group_name)
        group_subjects = []
        for sub, freq in group_to_sub_freq.items():
            group_subjects.append(('subject', sub, freq))
        GroupPreferences.prefer(group, group_subjects)
        active_groups_set.add(group_name)
    return active_groups_set


def recommend_groups(group_to_profiles, user_to_subs, group_to_members, all_subjects_list):
    user_to_recommended_groups_list = {}
    for username, user_to_sub_freq in user_to_subs.items():
        user_vec = get_user_freq_vec(user_to_sub_freq, all_subjects_list)
        groups_to_sim = {}
        for group_name, group_to_sub_freq in group_to_profiles.items():
            if username in group_to_members[group_name]:
                continue
            group_vec = get_user_freq_vec(group_to_sub_freq, all_subjects_list)
            cos_sim = 1 - sp.distance.cosine(user_vec, group_vec)
            if cos_sim > 0:
                groups_to_sim[group_name] = cos_sim
        top10_sorted_group_list = sorted(groups_to_sim.items(),
                                         key=itemgetter(1), reverse=True)[:10]
        user_to_recommended_groups_list[username] = top10_sorted_group_list
    return user_to_recommended_groups_list


def store_recommended_groups(user_to_recommended_groups_list, active_user_set, active_groups_set):
    for username, recommended_groups_list in user_to_recommended_groups_list.items():
        if username not in active_user_set:
            continue
        user = user_from_id(username)
        user_preferences = PropensityPreferences.objects.get(user=user)
        user_preferences_pairs = user_preferences.preferences.all()
        user_group_preferences = PropensityPrefToPair.objects.\
                                                filter(prop_pref=user_preferences,
                                                       pair__in=user_preferences_pairs,
                                                       state='Seen',
                                                       pref_for='Group')
        user_preferences_set = set()
        user_group_pref_to_weight = {}
        for p in user_group_preferences:
            if p.pair.key == 'subject':
                user_preferences_set.add(p.pair.value)
                user_group_pref_to_weight[p.pair.value] = p.weight

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
                r.relate('subject', cs, user_group_pref_to_weight[cs])


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
    res_to_subs, all_subjects_list = get_resource_to_subjects()
    end_date = date(2018, 5, 31)
    start_date = end_date - timedelta(days=30)
    user_to_resources, all_usernames = get_users_interacted_resources(start_date, end_date)
    user_to_subs = get_user_cumulative_profiles(user_to_resources, res_to_subs)
    user_to_top5_keywords = get_user_to_top5_keywords(user_to_subs)
    active_user_set = store_user_preferences(user_to_subs)
    user_to_recommended_resources_list = recommend_resources(res_to_subs, user_to_resources,
                                                             user_to_top5_keywords, user_to_subs,
                                                             all_subjects_list)
    store_recommended_resources(user_to_recommended_resources_list, res_to_subs)
    user_to_users = cal_nn(user_to_subs, all_subjects_list)
    user_to_knn = get_user_knn(user_to_users)
    store_nn(user_to_knn)
    user_to_recommended_users_list = recommend_users(user_to_users, user_to_knn)
    store_recommended_users(user_to_recommended_users_list)
    group_to_res, group_to_subjects,\
                  group_to_members = get_group_to_held_resources_and_members(res_to_subs)
    group_to_profiles = get_group_profiles(group_to_subjects, group_to_members, user_to_subs)
    active_groups_set = store_group_preferences(group_to_profiles, all_subjects_list)
    user_to_recommended_groups_list = recommend_groups(group_to_profiles,
                                                       user_to_subs,
                                                       group_to_members,
                                                       all_subjects_list)
    store_recommended_groups(user_to_recommended_groups_list, active_user_set, active_groups_set)


class Command(BaseCommand):
    help = "Make recommendations using dictionary representations for data."

    def handle(self, *args, **options):
        main()
