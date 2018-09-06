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
from datetime import date, timedelta
from hs_core.hydroshare.utils import user_from_id, group_from_id, get_resource_by_shortkey
from django.db.models import Q
from hs_explore.models import RecommendedResource, RecommendedUser, RecommendedGroup, \
    KeyValuePair, ResourceRecToPair, UserRecToPair, GroupRecToPair, ResourcePreferences, ResourcePrefToPair, \
    UserPreferences, UserPrefToPair, GroupPreferences, GroupPrefToPair, \
    PropensityPrefToPair, PropensityPreferences, OwnershipPrefToPair, OwnershipPreferences, UserInteractedResources, UserNeighbors
import simplejson as json
from sklearn.metrics.pairwise import pairwise_distances


class Command(BaseCommand):
    help = "make recommendations for a user."

    def handle(self, *args, **options):
        ind = BaseResourceIndex()

        propensity = defaultdict(int)
        ownership = defaultdict(int)

        user_usernames = set()

        users_own_resources = {}
        users_interested_resources = {}

        today = date(2018,07,31)
        beginning = today - timedelta(days=30)

        ResourcePreferences.clear()
        UserPreferences.clear()
        GroupPreferences.clear()
        PropensityPreferences.clear()
        OwnershipPreferences.clear()
        UserInteractedResources.clear()
        UserNeighbors.clear()
        ownership_start_time = time.time()
        for user in User.objects.all():
            if user is not None and \
               user.username != 'test' and user.username != 'demo':
                user_usernames.add(user.username)
                users_own_resources[user.username] = BaseResource.objects.filter(Q(r2urp__user=user) |
                                        Q(r2grp__group__g2ugp__user=user) |
                                        Q(r2url__user=user)).distinct()

        for user, resources in users_own_resources.iteritems():
            for res in resources:
                if (user, res.short_id) not in ownership:
                    ownership[(user, res.short_id)] = 1
                else:
                    ownership[(user, res.short_id)] += 1
                if user not in users_interested_resources:
                    users_interested_resources[user] = set([res.short_id])
                else:
                    users_interested_resources[user].add(res.short_id)

        ownership_elapsed_time = time.time() - ownership_start_time
        print("ownership data access time cost: " + str(ownership_elapsed_time))

        propensity_start_time = time.time()
        views = Features.visited_resources(beginning, today)
        for user, res_set in views.iteritems():
            for res in res_set:
                if (user, res) not in propensity:
                    propensity[(user, res)] = 1
                else:
                    propensity[(user, res)] += 1
                if user not in users_interested_resources:
                    users_interested_resources[user] = set([res])
                else:
                    users_interested_resources[user].add(res)

        downloads = Features.user_downloads(beginning, today)
        for user, res_set in downloads.iteritems():
            for res in res_set:
                if (user, res) not in propensity:
                    propensity[(user, res)] = 1
                else:
                    propensity[(user, res)] += 1
                if user not in users_interested_resources:
                    users_interested_resources[user] = set([res])
                else:
                    users_interested_resources[user].add(res)

        apps = Features.user_apps(beginning, today)
        for user, res_set in apps.iteritems():
            for res in res_set:
                if (user, res) not in propensity:
                    propensity[(user, res)] = 1
                else:
                    propensity[(user, res)] += 1
                if user not in users_interested_resources:
                    users_interested_resources[user] = set([res])
                else:
                    users_interested_resources[user].add(res)

        propensity_elapsed_time = time.time() - propensity_start_time
        print("propensity data access time cost: " + str(propensity_elapsed_time))

        group_names = set()
        user_group_dict = defaultdict(int)
        group_to_resources = {}
        for group in Group.objects.all():
            if group is not None and \
               group.name != 'test' and group.name != 'demo':
                group_members = User.objects.filter(u2ugp__group=group)
                group_resources = BaseResource.objects.filter(r2grp__group=group)
                group_name = group.name
                group_names.add(group_name)
                for member in group_members:
                    member_name = member.username
                    if (member_name, group_name) not in user_group_dict:
                        user_group_dict[(member_name, group_name)] = 1
                    for resource in group_resources:
                        if propensity[(member_name, resource.short_id)] != 0:
                            if group_name not in group_to_resources:
                                group_to_resources[group_name] = set([resource.short_id])
                            else:
                                group_to_resources[group_name].add(resource.short_id)

        matrices_start_time = time.time()
        resource_ids = set()
        all_subjects = set()
        resource_to_subjects = {}

        public_discoverable_resource_ids = set()
        public_discoverable_all_subjects = set()
        public_discoverable_resource_to_subjects = {}

        for res in BaseResource.objects.all():
            subjects = ind.prepare_subject(res)
            subjects = [sub.lower() for sub in subjects]
            resource_to_subjects[res.short_id] = subjects
            all_subjects.update(subjects)
            resource_ids.add(res.short_id)
            if res.raccess.public or res.raccess.discoverable:
                public_discoverable_resource_ids.add(res.short_id)
                public_discoverable_all_subjects.update(subjects)
                public_discoverable_resource_to_subjects[res.short_id] = subjects

        all_subjects_list = list(all_subjects)

        print("------------------ build matrices ---------------------")
        m_ur = pd.DataFrame(0, index=list(user_usernames), columns=list(resource_ids))
        for k, v in propensity.iteritems():
            if k[0] in m_ur.index and k[1] in m_ur.columns:
                m_ur.at[k[0], k[1]] = v
        row_normalized_m_ur = m_ur.divide(m_ur.sum(axis=1), axis=0).fillna(0)

        m_or = pd.DataFrame(0, index=list(user_usernames), columns=list(resource_ids))
        for k, v in ownership.iteritems():
            if k[0] in m_or.index and k[1] in m_or.columns:
                m_or.at[k[0], k[1]] = v
        row_normalized_m_or = m_or.divide(m_or.sum(axis=1), axis=0).fillna(0)

        m_rg = pd.DataFrame(0, index=list(resource_ids), columns=all_subjects_list)
        for k, subjects in resource_to_subjects.iteritems():
            for sub in subjects:
                if k in m_rg.index and sub in m_rg.columns:
                    m_rg.at[[k], [sub]] = 1

        m_ur_values = m_ur.values
        nm_ur_values = row_normalized_m_ur.values
        m_rg_values = m_rg.values

        m_ug_values = np.matmul(m_ur_values, m_rg_values)
        nm_ug_values = np.matmul(nm_ur_values, m_rg_values)

        m_ug = pd.DataFrame(m_ug_values, index=list(user_usernames), columns=all_subjects_list)
        nm_ug = pd.DataFrame(nm_ug_values, index=list(user_usernames), columns=all_subjects_list)
        nm_ug_ones = nm_ug.copy()
        nm_ug_ones[nm_ug_ones != 0] = 1

        m_or_values = m_or.values
        nm_or_values = row_normalized_m_or.values
        m_rg_values = m_rg.values

        m_og_values = np.matmul(m_or_values, m_rg_values)
        nm_og_values = np.matmul(nm_or_values, m_rg_values)

        m_og = pd.DataFrame(m_og_values, index=list(user_usernames), columns=all_subjects_list)
        nm_og = pd.DataFrame(nm_og_values, index=list(user_usernames), columns=all_subjects_list)

        nm_og_ones = nm_og.copy()
        nm_og_ones[nm_og_ones != 0] = 1
        m_hr = pd.DataFrame(0, index=list(group_names), columns=list(resource_ids))
        for k, values in group_to_resources.iteritems():
            if k in m_hr.index:
                for v in values:
                    m_hr.at[k, v] = 1
        m_hr_values = m_hr.values
        m_hg_values = np.matmul(m_hr_values, m_rg_values)
        m_hg = pd.DataFrame(m_hg_values, index=list(group_names), columns=all_subjects_list)


        nonzero_nm_ug_ones = nm_ug_ones[(nm_ug_ones.T != 0).any()]
        ug_jac_sim = 1 - pairwise_distances(nonzero_nm_ug_ones, metric = "hamming")
        ug_jac_sim = pd.DataFrame(ug_jac_sim, index=nonzero_nm_ug_ones.index, columns=nonzero_nm_ug_ones.index)
        knn = 10
        order = np.argsort(-ug_jac_sim.values, axis=1)[:, :knn]
        ug_nearest_neighbors = pd.DataFrame(ug_jac_sim.columns[order],
                              columns=['neighbor{}'.format(i) for i in range(1, knn+1)],
                              index=ug_jac_sim.index)

        nonzero_nm_og_ones = nm_og_ones[(nm_og_ones.T != 0).any()]
        og_jac_sim = 1 - pairwise_distances(nonzero_nm_og_ones, metric = "hamming")
        og_jac_sim = pd.DataFrame(og_jac_sim, index=nonzero_nm_og_ones.index, columns=nonzero_nm_og_ones.index)
        order = np.argsort(-og_jac_sim.values, axis=1)[:, :knn]
        og_nearest_neighbors = pd.DataFrame(og_jac_sim.columns[order],
                              columns=['neighbor{}'.format(i) for i in range(1, knn+1)],
                              index=og_jac_sim.index)

        matrices_elapsed_time = time.time() - matrices_start_time
        print("build matrices time cost: " + str(matrices_elapsed_time))
        print("--------- store user interacted resources  -----------")
        for key, value in users_interested_resources.iteritems():
            current_user = user_from_id(key)
            interested_resources = []
            for v in value:
                try:
                    r = get_resource_by_shortkey(v)
                    interested_resources.append(r)
                except:
                    continue
            UserInteractedResources.interact(current_user, interested_resources)

        print("-------- store user ownership preferences objects ---------")
        store_users_start_time = time.time()
        
        for index, row in m_og.iterrows():
            # skip users with no interests
            if index not in users_interested_resources:
                continue

            current_user = user_from_id(index)
            user_nonzero_index = row.nonzero()

            if len(user_nonzero_index[0]) == 0:
                continue
            own_pref_subjects = []
            sorted_row = (-row).argsort()

            #for i in user_nonzero_index[0]:
            for i in sorted_row[:5]:
                if row.iat[i] == 0:
                    break
                subject = all_subjects_list[i]
                own_pref_subjects.append(('subject', subject, row.iat[i]))
           
            OwnershipPreferences.prefer(current_user, 'Resource', own_pref_subjects)
            OwnershipPreferences.prefer(current_user, 'User', own_pref_subjects)
            OwnershipPreferences.prefer(current_user, 'Group', own_pref_subjects)
 
            #UserPreferences.prefer(current_user, 'Ownership', res_pref_subjects, neighbors)
        store_users_elapsed_time = time.time() - store_users_start_time
        print("time for storing users ownership preferences: " + str(store_users_elapsed_time))


        print("-------- store user propensity preferences objects ---------")
        store_users_start_time = time.time()
        for index, row in m_ug.iterrows():
            if index not in users_interested_resources:
                continue
            #if index != 'ChristinaBandaragoda':
            #    continue
            current_user = user_from_id(index)
            user_nonzero_index = row.nonzero()
            if len(user_nonzero_index[0]) == 0:
                continue

            prop_pref_subjects = []

            sorted_row = (-row).argsort()
            #for i in user_nonzero_index[0]:
            for i in sorted_row[:5]:
                if row.iat[i] == 0:
                    break
                subject = all_subjects_list[i]
                prop_pref_subjects.append(('subject', subject, row.iat[i]))
            
            neighbors = []
            if len(ug_nearest_neighbors.loc[index]) == 0:
                continue

            for username in ug_nearest_neighbors.loc[index]:
                if username == index:
                    continue
                try:
                    user = user_from_id(username)
                    neighbors.append(user)
                except:
                    continue

            PropensityPreferences.prefer(current_user, 'Resource', prop_pref_subjects)
            PropensityPreferences.prefer(current_user, 'User', prop_pref_subjects)
            PropensityPreferences.prefer(current_user, 'Group', prop_pref_subjects)
            #UserInteractedResources.interact(current_user, interested_resources)
            UserNeighbors.relate_neighbos(current_user, neighbors)
        store_users_elapsed_time = time.time() - store_users_start_time
        print("time for storing users propensity preferences: " + str(store_users_elapsed_time))
        
        print("------- store group preferences objects -------")
        store_groups_start_time = time.time()
        for index, row in m_hg.iterrows():
            current_group = Group.objects.get(name=index)
            group_nonzero_index = row.nonzero()
            group_subjects = []
            if len(group_nonzero_index[0]) != 0:
                print(index)
            for i in group_nonzero_index[0]:
                subject = all_subjects_list[i]
                if index == 'Landlab':
                    print("group {} : {}".format(index, subject))
                group_subjects.append(('subject', subject, row.iat[i]))
            GroupPreferences.prefer(current_group, group_subjects)
        store_groups_elapsed_time = time.time() - store_groups_start_time
        print("time for storing groups: " + str(store_groups_elapsed_time))
