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
    KeyValuePair, ResourceRecToPair, UserRecToPair, GroupRecToPair, UserPreferences
import simplejson as json


class Command(BaseCommand):
    help = "make recommendations for a user."
    
    def handle(self, *args, **options):
        ind = BaseResourceIndex()
        propensity = defaultdict(int)
        ownership = defaultdict(int)
        user_usernames = set()
        users_own_resources = {}
        test_user = user_from_id("dtarb")
        p = 'hi'
        UserPreferences.prefer(test_user, p)
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

        downloads = Features.user_downloads(datetime(2017, 11, 15, 0, 0, 0, 0), datetime(2017, 11, 30, 0, 0, 0, 0))
        for user, res_set in downloads.iteritems():
            for res in res_set:
                if (user, res) not in propensity:
                    propensity[(user, res)] = 1
                else:
                    propensity[(user, res)] += 1

        apps = Features.user_apps(datetime(2017, 11, 15, 0, 0, 0, 0), datetime(2017, 11, 30, 0, 0, 0, 0)) 
        for user, res_set in apps.iteritems():
            for res in res_set:
                if (user, res) not in propensity:
                    propensity[(user, res)] = 1
                else:
                    propensity[(user, res)] += 1

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
                m_or.at[k[0], k[1]] = 1
        
        m_rg = pd.DataFrame(0, index=list(resource_ids), columns=all_subjects_list)
        for k, subjects in resource_to_subjects.iteritems():
            for sub in subjects:
                if k in m_rg.index and sub in m_rg.columns:
                    m_rg.at[[k], [sub]] = 1
        
        m_ur_values = m_ur.values
        nm_ur_values = row_normalized_m_ur.values
        #m_or_values = m_or.values
        m_rg_values = m_rg.values
        
        m_ug_values = np.matmul(m_ur_values, m_rg_values)
        nm_ug_values = np.matmul(nm_ur_values, m_rg_values)
        #m_og_values = np.matmul(m_or_values, m_rg_values)

        m_ug = pd.DataFrame(m_ug_values, index=list(user_usernames), columns=all_subjects_list)
        nm_ug = pd.DataFrame(nm_ug_values, index=list(user_usernames), columns=all_subjects_list)
        '''
        m_og = pd.DataFrame(m_og_values, index=list(user_usernames), columns=all_subjects_list)
        m_og[m_og != 0] = 1
        '''
        
        m_uh = pd.DataFrame(0, index=list(user_usernames), columns=list(group_names))
        for k, v in user_group_dict.iteritems():
            if k[0] in m_uh.index and k[1] in m_uh.columns:
                m_uh.at[k[0], k[1]] = 1

        m_hr = pd.DataFrame(0, index=list(group_names), columns=list(resource_ids))
        for k, values in g_to_resources.iteritems():
            if k in m_hr.index:
                for v in values:
                    m_hr.at[k, v] = 1

        #m_uh_values = m_uh.values
        m_hr_values = m_hr.values
        '''
        m_uhr_values = np.matmul(m_uh_values, m_hr_values)
        m_uhr = pd.DataFrame(m_uhr_values, index=list(user_usernames), columns=list(resource_ids))

        m_uhg_values = np.matmul(m_uhr_values, m_rg_values)
        m_uhg = pd.DataFrame(m_uhg_values, index=list(user_usernames), columns=all_subjects_list)
        m_uhg[m_uhg != 0] = 1
        '''
        m_hg_values = np.matmul(m_hr_values, m_rg_values)
        m_hg = pd.DataFrame(m_hg_values, index=list(group_names), columns=all_subjects_list)
        m_hg[m_hg != 0] = 1
        '''
        public_discoverable_m_rg = pd.DataFrame(0, index=list(public_discoverable_resource_ids), columns=all_subjects_list)
        for k, subjects in public_discoverable_resource_to_subjects.iteritems():
            for sub in subjects:
                if k in public_discoverable_m_rg.index and sub in public_discoverable_m_rg.columns:
                    public_discoverable_m_rg.at[[k], [sub]] = 1
        '''
        nm_ug_ones = nm_ug.copy()
        nm_ug_ones[nm_ug_ones != 0] = 1
        matrices_elapsed_time = time.time() - matrices_start_time
        print("-------- make user preferences objects ---------")
        for index, row in m_ug.iterrows():
            current_user = user_from_id(index)
            user_nonzero_index = row.nonzero()
            user_subjects = []
            for i in user_nonzero_index[0]:
                user_subjects.add(all_subjects_list[i])
            user_subjects_json = json.dumps(user_subjects)
            UserPreferences.prefer(current_user, user_subjects_json)
        
        print("-----------------")
        print("time for building all matrices: " + str(matrices_elapsed_time))
        write_to_csv_start_time = time.time()
        m_ur.to_csv("hs_explore/management/commands/matrices/m_ur.csv", encoding='utf-8')
        m_or.to_csv("hs_explore/management/commands/matrices/m_or.csv", encoding='utf-8')
        m_ug.to_csv("hs_explore/management/commands/matrices/m_ug.csv", encoding='utf-8')
        nm_ug.to_csv("hs_explore/management/commands/matrices/nm_ug.csv", encoding='utf-8')  
        m_uh.to_csv("hs_explore/management/commands/matrices/m_uh.csv", encoding='utf-8')
        m_hg.to_csv("hs_explore/management/commands/matrices/m_hg.csv", encoding='utf-8')
        nm_ug_ones.to_csv("hs_explore/management/commands/matrices/nm_ug_ones.csv", encoding='utf-8') 
        write_elapsed_time = time.time() - write_to_csv_start_time
        print("time for writing to csv: " + str(write_elapsed_time))
