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
        
        UserPreferences.clear()
        GroupPreferences.clear()
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
        views = Features.visited_resources(datetime(2017, 11, 15, 0, 0, 0, 0), datetime(2017, 11, 30, 0, 0, 0, 0))
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

        downloads = Features.user_downloads(datetime(2017, 11, 15, 0, 0, 0, 0), datetime(2017, 11, 30, 0, 0, 0, 0))
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

        apps = Features.user_apps(datetime(2017, 11, 15, 0, 0, 0, 0), datetime(2017, 11, 30, 0, 0, 0, 0)) 
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

        user_group_dict = defaultdict(int)
        user_owned_groups = Features.user_owned_groups()
        group_start_time = time.time()

        for user, groups in user_owned_groups.iteritems():
            for group in groups:
                if (user, group) not in user_group_dict:
                    user_group_dict[(user, group)] = 1

        user_edited_groups = Features.user_edited_groups()
        for user, groups in user_edited_groups.iteritems():
            for group in groups:
                if (user, group) not in user_group_dict:
                    user_group_dict[(user, group)] = 1

        user_viewed_groups = Features.user_viewed_groups()
        for user, groups in user_viewed_groups.iteritems():
            for group in groups:
                if (user, group) not in user_group_dict:
                    user_group_dict[(user, group)] = 1

        group_elapsed_time = time.time() - group_start_time
        print("group data access time cost: " + str(group_elapsed_time))
        
        group_names = set()
        for group in Group.objects.all():
            if group is not None and \
               group.name != 'test' and group.name != 'demo':
                group_names.add(group.name)

        g_to_resources = {}
        for gname in group_names:
            g = Group.objects.get(name=gname)
            g_resources_set = set()
            resources_editable = Features.resources_editable_via_group(g)
            g_resources_set.update(resources_editable)
            resources_viewable = Features.resources_viewable_via_group(g)
            g_resources_set.update(resources_viewable)
            if gname not in g_to_resources:
                g_to_resources[gname] = g_resources_set
            else:
                g_to_resources[gname] = g_to_resources[gname].update(g_resources_set)

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
        
        m_uh = pd.DataFrame(0, index=list(user_usernames), columns=list(group_names))
        for k, v in user_group_dict.iteritems():
            if k[0] in m_uh.index and k[1] in m_uh.columns:
                m_uh.at[k[0], k[1]] = 1

        m_hr = pd.DataFrame(0, index=list(group_names), columns=list(resource_ids))
        for k, values in g_to_resources.iteritems():
            if k in m_hr.index:
                for v in values:
                    m_hr.at[k, v] = 1
        '''
        m_hr_values = m_hr.values
        m_hg_values = np.matmul(m_hr_values, m_rg_values)
        m_hg = pd.DataFrame(m_hg_values, index=list(group_names), columns=all_subjects_list)
        m_hg[m_hg != 0] = 1
        '''
        
        ug_jac_sim = 1 - pairwise_distances(nm_ug_ones, metric = "hamming")
        ug_jac_sim = pd.DataFrame(ug_jac_sim, index=nm_ug_ones.index, columns=nm_ug_ones.index)
        knn = 10
        order = np.argsort(-ug_jac_sim.values, axis=1)[:, :knn]
        ug_nearest_neighbors = pd.DataFrame(ug_jac_sim.columns[order],
                              columns=['neighbor{}'.format(i) for i in range(1, knn+1)],
                              index=ug_jac_sim.index) 
       
        og_jac_sim = 1 - pairwise_distances(nm_og_ones, metric = "hamming")
        og_jac_sim = pd.DataFrame(og_jac_sim, index=nm_og_ones.index, columns=nm_og_ones.index)
        knn = 10
        order = np.argsort(-og_jac_sim.values, axis=1)[:, :knn]
        og_nearest_neighbors = pd.DataFrame(og_jac_sim.columns[order],
                              columns=['neighbor{}'.format(i) for i in range(1, knn+1)],
                              index=og_jac_sim.index)
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print(nm_ug_ones.shape)
        print(ug_jac_sim.shape)
        print(ug_nearest_neighbors.shape)
        #for nn in res_nearest_neighbors.loc['ChristinaBandaragoda']:
        #    print(nn)
        print("+++++++")
        print(nm_og_ones.shape)
        print(og_jac_sim.shape)
        print(og_nearest_neighbors.shape)
        print("~~~~~~~~~~~~~~~~~~~~~~~")                
        
        matrices_elapsed_time = time.time() - matrices_start_time
        print("build matrices time cost: " + str(matrices_elapsed_time))
        
        print("-------- store user ownership preferences objects ---------")
        store_users_start_time = time.time()
        for index, row in m_og.iterrows():
            if index not in users_interested_resources:
                continue
            if index != 'ChristinaBandaragoda':
                continue
            print("building {} ownership prefrences".format(index))
            current_user = user_from_id(index)
            user_nonzero_index = row.nonzero()
            if len(user_nonzero_index[0]) == 0:
                continue
            user_subjects = []
            sorted_row = (-row).argsort()
            
            #for i in user_nonzero_index[0]:
            for i in sorted_row[:5]:
                if row.iat[i] == 0:
                    break
                subject = all_subjects_list[i]
                if index == 'ChristinaBandaragoda':
                    print(subject)
                    print("loc : {}, at : {}".format(m_og.at[index, subject], row.iat[i]))
                user_subjects.append(('subject', subject, row.iat[i]))
            interested_resources = []
            for rid in users_interested_resources[index]:
                try:
                    r = get_resource_by_shortkey(rid)
                    interested_resources.append(r)
                except:
                    pass
            neighbors = []
            for username in og_nearest_neighbors.loc[index]:
                if username == index:
                    continue
                try:
                    user = user_from_id(username)
                    neighbors.append(user)
                except:
                    pass
            UserPreferences.prefer(current_user, 'Ownership', user_subjects, interested_resources, neighbors)
        store_users_elapsed_time = time.time() - store_users_start_time
        print("time for storing users ownership preferences: " + str(store_users_elapsed_time))
        
        print("-------- store user propensity preferences objects ---------")
        store_users_start_time = time.time()
        for index, row in m_ug.iterrows():
            if index not in users_interested_resources:
                continue
            if index != 'ChristinaBandaragoda':
                continue
            current_user = user_from_id(index)
            user_nonzero_index = row.nonzero()
            if len(user_nonzero_index[0]) == 0:
                continue

            user_subjects = []

            sorted_row = (-row).argsort()
            #for i in user_nonzero_index[0]:
            for i in sorted_row[:5]:
                if row.iat[i] == 0:
                    break
                subject = all_subjects_list[i]
                if index == 'ChristinaBandaragoda':
                    print(subject)
                    print("loc : {}, at : {}".format(m_ug.at[index, subject], row.iat[i]))
                user_subjects.append(('subject', subject, row.iat[i]))
            interested_resources = []
            for rid in users_interested_resources[index]:
                try:
                    r = get_resource_by_shortkey(rid)
                    interested_resources.append(r)
                except:
                    pass
            neighbors = []
            for username in ug_nearest_neighbors.loc[index]:
                if username == index:
                    continue
                try:
                    user = user_from_id(username)
                    neighbors.append(user)
                except:
                    pass
            UserPreferences.prefer(current_user, 'Propensity', user_subjects, interested_resources, neighbors)
        store_users_elapsed_time = time.time() - store_users_start_time
        print("time for storing users propensity preferences: " + str(store_users_elapsed_time))
        
        '''
        print("------- store group preferences objects -------")
        store_groups_start_time = time.time()
        for index, row in m_hg.iterrows():
            current_group = Group.objects.get(name=index)
            gp = GroupPreferences.prefer(current_group)
            group_nonzero_index = row.nonzero()
            group_subjects = []
            for i in group_nonzero_index[0]:
                subject = all_subjects_list[i]
                gp.relate('subject', subject, m_hg.loc[index, subject])
        store_groups_elapsed_time = time.time() - store_groups_start_time
        print("time for storing groups: " + str(store_groups_elapsed_time))
        '''
