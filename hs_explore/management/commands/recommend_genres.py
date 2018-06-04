from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.features import Features
from django.contrib.auth.models import Group
from hs_explore.utils import Utils
from hs_explore.topic_modeling import TopicModeling
from datetime import datetime
from pprint import pprint
import pickle
import sys
from collections import defaultdict
import pandas as pd
from django.contrib.auth.models import User
from hs_core.models import BaseResource
from scipy import sparse
from sklearn.decomposition import NMF, LatentDirichletAllocation, TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import numpy.matlib
from sklearn.metrics import jaccard_similarity_score
from hs_core.search_indexes import BaseResourceIndex
from hs_explore.models import Recommend
from scipy.spatial import distance
import time

class Command(BaseCommand):
    def handle(self, *args, **options):
        ind = BaseResourceIndex()
        propensity = defaultdict(int)
        ownership = defaultdict(int)

        print("-------- build up ownership  ---------")
        ownership_start_time = time.time()
        records = Features.resource_owners()
        for user, res in records:
             if (user, res) not in propensity:
                 ownership[(user, res)] = 1
        print("resources owners")

        edits = Features.resource_editors()
        for user, res in edits:
            if (user, res) not in propensity:
                ownership[(user, res)] = 1
        print("resources editors")

        ownership_elapsed_time = time.time() - ownership_start_time
        print("ownership data acceess time cost: " + str(ownership_elapsed_time))

        print("----------- propensity -----------")
        propensity_start_time = time.time()
        views = Features.visited_resources(datetime(2017, 11, 01, 0, 0, 0, 0), datetime(2017, 11, 30, 0, 0, 0, 0))
        for user, res_set in views.iteritems():
            for res in res_set:
                if (user, res) not in propensity:
                    propensity[(user, res)] = 1
                else:
                    propensity[(user, res)] += 1
        print("resources viewed")

        downloads = Features.user_downloads(datetime(2017, 11, 01, 0, 0, 0, 0), datetime(2017, 11, 30, 0, 0, 0, 0))
        for user, res_set in downloads.iteritems():
            for res in res_set:
                if (user, res) not in propensity:
                    propensity[(user, res)] = 1
                else:
                    propensity[(user, res)] += 1
        print("resources downloads")

        apps = Features.user_apps(datetime(2017, 11, 01, 0, 0, 0, 0), datetime(2017, 11, 30, 0, 0, 0, 0))
        for user, res_set in apps.iteritems():
            for res in res_set:
                if (user, res) not in propensity:
                    propensity[(user, res)] = 1
                else:
                    propensity[(user, res)] += 1
        print("resources apped")

        favors = Features.user_favorites()
        for user, res_set in favors.iteritems():
            for res in res_set:
                if (user, res) not in propensity:
                    propensity[(user, res)] = 1
                else:
                    propensity[(user, res)] += 1
        print("resources favored")
        propensity_elapsed_time = time.time() - propensity_start_time
        print("propensity data acceess time cost: " + str(propensity_elapsed_time))
        
        print("----------------- build up group -----------------")
        user_group_dict = defaultdict(int)
        user_owned_groups = Features.user_owned_groups()
        group_start_time = time.time()

        for user, groups in user_owned_groups.iteritems():
            for group in groups:
                if (user, group) not in user_group_dict:
                    user_group_dict[(user, group)] = 1
                else:
                    user_group_dict[(user, group)] += 1

        user_edited_groups = Features.user_edited_groups()
        for user, groups in user_edited_groups.iteritems():
            for group in groups:
                if (user, group) not in user_group_dict:
                    user_group_dict[(user, group)] = 1
                else:
                    user_group_dict[(user, group)] += 1

        user_viewed_groups = Features.user_viewed_groups()
        for user, groups in user_viewed_groups.iteritems():
            for group in groups:
                if (user, group) not in user_group_dict:
                    user_group_dict[(user, group)] = 1
                else:
                    user_group_dict[(user, group)] += 1

        group_elapsed_time = time.time() - group_start_time
        print("group data acceess time cost: " + str(group_elapsed_time))

        matrices_start_time = time.time()
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

        user_usernames = set()
        for user in User.objects.all():
            if user is not None and \
               user.username != 'test' and user.username != 'demo':
                user_usernames.add(user.username)

        print(len(user_usernames))

        resource_ids = set()
        all_subjects = set()
        resource_to_subjects = {}
        for res in BaseResource.objects.all():
            subjects = ind.prepare_subject(res)
            subjects = [sub.lower() for sub in subjects]
            resource_to_subjects[res.short_id] = subjects
            all_subjects.update(subjects)
            resource_ids.add(res.short_id)

        print(len(resource_ids))
        print("subjects length")
        print(len(all_subjects))
        print("building m_ur matrix")

        m_ur = pd.DataFrame(0, index=list(user_usernames), columns=list(resource_ids))
        for k, v in propensity.iteritems():
            if k[0] in m_ur.index and k[1] in m_ur.columns:
                m_ur.at[k[0], k[1]] = v
        print("+++++++++++")
        pprint(m_ur.loc["ChristinaBandaragoda"].nonzero())
        print("+++++++++++")


        row_normalized_m_ur = m_ur.divide(m_ur.sum(axis=1), axis=0).fillna(0)
        print("++++++++++++++")
        cb_row = m_ur.loc["ChristinaBandaragoda"]
        for i in cb_row.nonzero():
            print(cb_row.iloc[i])
        print("normalized")

        cb_normalized_row = row_normalized_m_ur.loc["ChristinaBandaragoda"]
        for i in cb_normalized_row.nonzero():
            print(cb_normalized_row.iloc[i])
        print("+++++++++++++++++")

        print("building m_or matrix")

        m_or = pd.DataFrame(0, index=list(user_usernames), columns=list(resource_ids))
        for k, v in ownership.iteritems():
            if k[0] in m_or.index and k[1] in m_or.columns:
                m_or.at[k[0], k[1]] = v

        print("building m_rg matrix")
        m_rg = pd.DataFrame(0, index=list(resource_ids), columns=list(all_subjects))
        for k, subjects in resource_to_subjects.iteritems():
            for sub in subjects:
                if k in m_rg.index and sub in m_rg.columns:
                    m_rg.at[[k], [sub]] = 1

        print("`````````````` build m_ug  m_og `````````````````")
        pprint(m_rg.index)
        pprint(m_ur.values)
        pprint(m_rg.values)

        nm_ur_values = row_normalized_m_ur.values
        m_or_values = m_or.values
        m_rg_values = m_rg.values

        m_ug_values = np.matmul(nm_ur_values, m_rg_values)
        m_og_values = np.matmul(m_or_values, m_rg_values)

        pprint(m_ug_values.shape)
        pprint(m_og_values.shape)

        m_ug_matrix = pd.DataFrame(m_ug_values, index=list(user_usernames), columns=list(all_subjects))
        nm_ug_matrix = m_ug_matrix.divide(m_ug_matrix.sum(axis=1), axis=0).fillna(0)

        print("``````````` build m_uh m_hr m_urg m_ugg``````````````")
        m_uh = pd.DataFrame(0, index=list(user_usernames), columns=list(group_names))
        for k, v in user_group_dict.iteritems():
            if k[0] in m_uh.index and k[1] in m_uh.columns:
                m_uh.at[k[0], k[1]] = 1

        m_hr = pd.DataFrame(0, index=list(group_names), columns=list(resource_ids))
        for k, values in g_to_resources.iteritems():
            if k in m_hr.index:
                for v in values:
                    m_hr.at[k, v] = 1

        m_uh_values = m_uh.values
        m_hr_values = m_hr.values
        m_urg_values = np.matmul(m_uh_values, m_hr_values)
        m_urg = pd.DataFrame(m_urg_values, index=list(user_usernames), columns=list(resource_ids))
        pprint(m_urg_values.shape)
        m_ugg_values = np.matmul(m_urg_values, m_rg_values)
        m_ugg = pd.DataFrame(m_ugg_values, index=list(user_usernames), columns=list(all_subjects))
        m_ugg[m_ugg != 0] = 1

        matrices_elapsed_time = time.time() - matrices_start_time
        print("time for building all matrices: " + str(matrices_elapsed_time))

        print("========== recommendation for ChristinaBandaragoda =============")
        similarity_start_time = time.time()

        cb_ug_row = nm_ug_matrix.loc["ChristinaBandaragoda"]
        print("==== ChristinaBandaragoda nonzero cells ====")
        pprint(cb_ug_row.nonzero())
        for i in cb_ug_row.nonzero():
            print(cb_ug_row.iloc[i])

        print("**** ChristinaBandaragoda group nonzero cells *****")
        cb_ugg_row = m_ugg.loc["ChristinaBandaragoda"]
        pprint(cb_ugg_row.nonzero())
        for i in cb_ugg_row.nonzero():
            print(cb_ugg_row.iloc[i])
        m_og_matrix = pd.DataFrame(m_og_values, index=list(user_usernames), columns=list(all_subjects))

        #normalized_pog_matrix = pg_matrix.divide(pog_matrix.sum(axis=1), axis=0).fillna(0)
        m_og_matrix[m_og_matrix != 0] = 1

        print("------------ calculate similarities --------------")
        nm_ug_matrix_ones = nm_ug_matrix.copy()
        nm_ug_matrix_avg_thresh_copy = nm_ug_matrix.copy()
        nm_ug_matrix_avg_thresh = nm_ug_matrix_avg_thresh_copy.subtract(nm_ug_matrix_avg_thresh_copy.mean(axis=1), axis=0).fillna(0)
        nm_ug_matrix_ones[nm_ug_matrix_ones != 0] = 1

        nm_ug_matrix_avg_thresh[nm_ug_matrix_avg_thresh > 0] = 1
        nm_ug_matrix_avg_thresh[nm_ug_matrix_avg_thresh != 1]  = 0
        #nm_ug_matrix_avg_thresh[nm_ug_matrix_avg_thresh > nm_ug_matrix_avg_thresh.mean(axis=1)] = 1
        print("*************")
        print(nm_ug_matrix_avg_thresh.loc["ChristinaBandaragoda"])
        cb_recommends = {}
        cb_pref_probs = nm_ug_matrix.loc["ChristinaBandaragoda"].values
        cb_pref_ones = nm_ug_matrix_ones.loc["ChristinaBandaragoda"].values
        cb_thresh_ones = nm_ug_matrix_avg_thresh.loc["ChristinaBandaragoda"].values
        cb_group_ones = m_ugg.loc["ChristinaBandaragoda"].values

        cb_og_row = m_og_matrix.loc["ChristinaBandaragoda"].values

        cb_jaccard_sim = {}
        cb_cosine_sim ={}
        cb_jaccard_ones_sim = {}
        cb_cosine_ones_sim = {}
        cb_threshold_jaccard_sim = {}
        cb_threshold_cosine_sim = {}

        cb_ownership_jaccard_sim = {}
        cb_ownership_cosine_sim = {}

        cb_group_jaccard_sim = {}

        for index, row in m_rg.iterrows():
            num_of_genres = np.count_nonzero(row.values)
            if num_of_genres == 0:
                continue
            if ("ChristinaBandaragoda", index) in propensity or ("ChristinaBandaragoda", index) in ownership:
                continue

            # Jaccard similarity for probabilities
            num = 0
            dom = 0
            for x, y in zip(cb_pref_probs, row.values):
                num += min(x, y)
                dom += max(x, y)
            js = num/dom

            # Cosine similarity for probabilities
            cs = 1 / (1 + distance.cosine(cb_pref_probs, row.values))

            # Jaccard similarity for ones
            jos = jaccard_similarity_score(cb_pref_ones, row.values)

            # Cosine similarity for ones
            cos = 1 / (1 + distance.cosine(cb_pref_probs, row.values))

            # Jaccrad similarity for threshold
            jts = jaccard_similarity_score(cb_thresh_ones, row.values)

            # Cosine similarity for threshold
            cts = 1 / (1 + distance.cosine(cb_thresh_ones, row.values))

            # Jaccard similarity for ownership
            jows = jaccard_similarity_score(cb_og_row, row.values)

            # Cosine similarity for ownership
            cows = 1 / (1 + distance.cosine(cb_og_row, row.values))

            # Group Jaccard similarity 
            jps = jaccard_similarity_score(cb_group_ones, row.values)

            cb_jaccard_sim[index] = js
            cb_cosine_sim[index] = cs
            cb_jaccard_ones_sim[index] = jos
            cb_cosine_ones_sim[index] = cos
            cb_threshold_jaccard_sim[index] = jts
            cb_threshold_cosine_sim[index] = cts
            cb_ownership_jaccard_sim[index] = jows
            cb_ownership_cosine_sim[index] = cows
            cb_group_jaccard_sim[index] = jps

        print("------------ Jaccard similarity for probabilities ---------------")
        for key, value in sorted(cb_jaccard_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True):
            print (key, value)

        print("------------ Cosine similarity for probabilities ---------------")
        for key, value in sorted(cb_cosine_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True):
            print (key, value)

        print("------------ Jaccard similarity for Ones ---------------")
        for key, value in sorted(cb_jaccard_ones_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True):
            print (key, value)

        print("------------ Cosine similarity for Ones ---------------")
        for key, value in sorted(cb_cosine_ones_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True):
            print (key, value)

        print("------------ Jaccard similarity for threshold Ones ---------------")
        for key, value in sorted(cb_threshold_jaccard_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True):
            print (key, value)

        print("------------ Cosine similarity for threshold Ones ---------------")
        for key, value in sorted(cb_threshold_cosine_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True):
            print (key, value)

        print("------------ Jaccard similarity for ownership ---------------")
        for key, value in sorted(cb_ownership_jaccard_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True):
            print (key, value)

        print("------------ Cosine similarity for ownership ---------------")
        for key, value in sorted(cb_ownership_cosine_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True):
            print (key, value)

        print("------------ Jaccard similarity for group ---------------")
        for key, value in sorted(cb_group_jaccard_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True):
            print (key, value)
            
        similarity_elapsed_time = time.time() - similarity_start_time
        print("similarities calculation time cost: " + str(similarity_elapsed_time))
