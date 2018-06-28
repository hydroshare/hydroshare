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
from hs_core.hydroshare import user_from_id
from django.db.models import Q
#import seaborn as sns
import matplotlib.pyplot as plt


class Command(BaseCommand):
    help = "make recommendations for a user."
    
    def add_arguments(self, parser):

        # a list of user id's
        parser.add_argument('user_ids', nargs='*', type=str)
        #options['user_ids']

    def handle(self, *args, **options):
        ind = BaseResourceIndex()
        propensity = defaultdict(int)
        ownership = defaultdict(int)
        user_usernames = set()
        users_own_resources = {}

        if len(options['user_ids']) == 0:
                print("Please provide a user name")
                return
        target_user = options['user_ids'][0]
        print("target user: " + target_user)
        
        print("-------- build up ownership  ---------")
        ownership_start_time = time.time()
        for user in User.objects.all():
            if user is not None and \
               user.username != 'test' and user.username != 'demo':
                user_usernames.add(user.username)
                users_own_resources[user.username] = BaseResource.objects.filter(Q(r2urp__user=user) |
                                        Q(r2grp__group__g2ugp__user=user) | 
                                        Q(r2url__user=user)).distinct()

        print(str(len(user_usernames)) + " users")
        private_r = set()
        public_r = set()
        for res in users_own_resources[target_user]:
            #if res.short_id == "27d34fc967be4ee6bc1f1ae92657bf2b":
            #    print("~~~~~~~~~~ found  ~~~~~~~~~~~~")
            #    return
            if res.raccess.public or res.raccess.discoverable:
                public_r.add(res.short_id)
            else:
                if not res.raccess.published:
                    private_r.add(res.short_id)
                
        print("target owns: " + str(len(users_own_resources[target_user])) + " public: " + str(len(public_r)) + " private: " + str(len(private_r)))

        '''
        print("~~~~~~~~~~~~   target user resources access  ~~~~~~~~~~~~~~~~~~~~")
        tu = user_from_id(target_user)
        if tu is not None:
            user_group_res = BaseResource.objects.filter(Q(r2urp__user=tu)).distinct()
            for ugr in user_group_res:
                if ugr.short_id == "886398b201e948b2bb5e1df83ccb9e2f":
                    print("~~~~~~~~~~ found  ~~~~~~~~~~~~")
                else:
                    print(ugr.short_id)
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")        
        '''


        for user, resources in users_own_resources.iteritems():
            for res in resources:
                if (user, res.short_id) not in ownership:
                    ownership[(user, res.short_id)] = 1

        ownership_elapsed_time = time.time() - ownership_start_time

        print("ownership data access time cost: " + str(ownership_elapsed_time))
        #pprint(users_own_resources[target_user])
       
        print("----------- build up propensity -----------")
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

        propensity_elapsed_time = time.time() - propensity_start_time
        print("propensity data access time cost: " + str(propensity_elapsed_time))

        tp_counter = 0
        tpd_counter = 0
        op_counter = 0
        pp_counter = 0
        for k, v in propensity.iteritems():
            if k[0] == target_user:
                print(str(k[1]) + ":"  + str(v)) 
                tp_counter += v
                tpd_counter += 1
                if k in ownership:
                    op_counter += 1
                if k[1] in private_r:
                    print("private " + str(k[1]) + ":"  + str(v))
                    pp_counter += 1
        print("target user perform: " + str(tp_counter) + ", distinct res: " + str(tpd_counter) + ", in his/her owned resources: " + str(op_counter) + " private: " + str(pp_counter))
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

        print("------ build up matrices ------")
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

        print(str(len(resource_ids)) + ", " + str(len(public_discoverable_resource_ids)))
        print("subjects length")
        print(str(len(all_subjects)) + ", " + str(len(public_discoverable_all_subjects)))
        
        print("--- building propensity m_ur matrix ---")
        m_ur = pd.DataFrame(0, index=list(user_usernames), columns=list(resource_ids))
        for k, v in propensity.iteritems():
            if k[0] in m_ur.index and k[1] in m_ur.columns:
                m_ur.at[k[0], k[1]] = v

        print("+++++++++++")
        pprint(m_ur.loc[target_user].nonzero())
        print("+++++++++++")

        row_normalized_m_ur = m_ur.divide(m_ur.sum(axis=1), axis=0).fillna(0)
        print("++++++++++++++")
        target_row = m_ur.loc[target_user]
        for i in target_row.nonzero():
            print(target_row.iloc[i])
        print("normalized")
        target_normalized_row = row_normalized_m_ur.loc[target_user]
        for i in target_normalized_row.nonzero():
            print(target_normalized_row.iloc[i])
        print("+++++++++++++++++")
        
        print("--- building ownership m_or matrix ---")
        m_or = pd.DataFrame(0, index=list(user_usernames), columns=list(resource_ids))
        for k, v in ownership.iteritems():
            if k[0] in m_or.index and k[1] in m_or.columns:
                m_or.at[k[0], k[1]] = 1

        print("--- building resource genres m_rg matrix ---")
        m_rg = pd.DataFrame(0, index=list(resource_ids), columns=list(all_subjects))
        for k, subjects in resource_to_subjects.iteritems():
            for sub in subjects:
                if k in m_rg.index and sub in m_rg.columns:
                    m_rg.at[[k], [sub]] = 1

        print("~~~~~~~~~ user propensity genres ~~~~~~~~~~")
        for k, v in propensity.iteritems():
            if (k[0] == target_user):
                res_id = str(k[1])
                if res_id in m_rg.index:
                    res_genres = m_rg.loc[res_id]
                    print("id: " + res_id)
                    for j in res_genres.nonzero():
                        print(res_genres.iloc[j])
        print("~~~~~~~~~~~~")

        print("---- building user propensity genres m_ug and user ownership genres m_og ----")
        #pprint(m_rg.index)
        #pprint(m_ur.values)
        #pprint(m_rg.values)

        nm_ur_values = row_normalized_m_ur.values
        m_or_values = m_or.values
        m_rg_values = m_rg.values

        m_ug_values = np.matmul(nm_ur_values, m_rg_values)
        m_og_values = np.matmul(m_or_values, m_rg_values)

        #pprint(m_ug_values.shape)
        #pprint(m_og_values.shape)

        m_ug = pd.DataFrame(m_ug_values, index=list(user_usernames), columns=list(all_subjects))
        nm_ug = m_ug.divide(m_ug.sum(axis=1), axis=0).fillna(0)

        '''
        #sns.heatmap(nm_ug, cmap='RdYlGn_r', linewidths=0.5, annot=True)
        plt.pcolor(nm_ug)
        plt.yticks(np.arange(0.5, len(nm_ug.index), 1), nm_ug.index)
        plt.xticks(np.arange(0.5, len(nm_ug.columns), 1), nm_ug.columns)
        plt.show()
        '''

        m_og = pd.DataFrame(m_og_values, index=list(user_usernames), columns=list(all_subjects))
        m_og[m_og != 0] = 1

        print("---- build user-group m_uh, group-resource m_hr, user-group-resource m_uhr, user-group-genres m_uhg ----")
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

        m_uhr_values = np.matmul(m_uh_values, m_hr_values)
        m_uhr = pd.DataFrame(m_uhr_values, index=list(user_usernames), columns=list(resource_ids))
        
        #pprint(m_urg_values.shape)

        m_uhg_values = np.matmul(m_uhr_values, m_rg_values)
        m_uhg = pd.DataFrame(m_uhg_values, index=list(user_usernames), columns=list(all_subjects))
        m_uhg[m_uhg != 0] = 1

        print("--- building public_discoverable_m_rg ---")
        public_discoverable_m_rg = pd.DataFrame(0, index=list(public_discoverable_resource_ids), columns=list(all_subjects))
        for k, subjects in public_discoverable_resource_to_subjects.iteritems():
            for sub in subjects:
                if k in public_discoverable_m_rg.index and sub in public_discoverable_m_rg.columns:
                    public_discoverable_m_rg.at[[k], [sub]] = 1

        matrices_elapsed_time = time.time() - matrices_start_time
        print("time for building all matrices: " + str(matrices_elapsed_time))

        print("========== Make recommendations =============")
        similarity_start_time = time.time()

        target_ug_row = nm_ug.loc[target_user]
        print(type(target_ug_row))
        print("==== target user nonzero cells ====")
        target_user_row_df = pd.DataFrame({target_user : target_ug_row})
                
        print(type(target_user_row_df)) 
        sorted_target_df = target_user_row_df.sort_values(by=target_user, ascending=False).transpose()
       
        print(sorted_target_df.transpose().to_string())
        #target_user_nonzero_entries = []
        #pprint(target_ug_row.nonzero())
        #sorted_target_df_t = sorted_target_df.transpose()
        sorted_target_row = sorted_target_df.loc[target_user]
        '''
        for i in sorted_target_row.nonzero():
            print(sorted_target_row.iloc[i])
            #target_user_nonzero_entries.append(target_ug_row.iloc[i])
        
        target_user_nonzero_entries.sort(reverse=True)
        
        sorted_row = nm_ug.loc[target_user]
        np.argsort(sorted_row)
        for k in sortted_row:
             print(k)
        '''

        print("=======================")

        print("**** target user group nonzero cells *****")
        target_uhg_row = m_uhg.loc[target_user]
        pprint(target_uhg_row.nonzero())
        for i in target_uhg_row.nonzero():
            print(target_uhg_row.iloc[i])

        print("------------ calculate similarities --------------")
        nm_ug_ones = nm_ug.copy()
        nm_ug_avg_thresh_copy = nm_ug.copy()
        nm_ug_avg_thresh = nm_ug_avg_thresh_copy.subtract(nm_ug_avg_thresh_copy.mean(axis=1), axis=0).fillna(0)
        nm_ug_ones[nm_ug_ones != 0] = 1

        nm_ug_avg_thresh[nm_ug_avg_thresh > 0] = 1
        nm_ug_avg_thresh[nm_ug_avg_thresh != 1]  = 0
        #print("*************")
        #print(nm_ug_avg_thresh.loc[target_user])
        
        target_recommends = {}
        target_pref_probs = nm_ug.loc[target_user].values
        target_pref_ones = nm_ug_ones.loc[target_user].values
        target_thresh_ones = nm_ug_avg_thresh.loc[target_user].values
        target_group_ones = m_uhg.loc[target_user].values
        target_og_row = m_og.loc[target_user].values
        target_pref_nonzero_probs_list = []
        target_pref_nonzero_ones_list = []
        target_pref_nonzero_index = nm_ug.loc[target_user].nonzero()
        print(type(target_pref_nonzero_index))
        #nonzero_pref_size = len(target_pref_nonzero_index(0))
        for i in target_pref_nonzero_index:
            target_pref_nonzero_probs_list.append(target_pref_probs[i])
            target_pref_nonzero_ones_list.append(target_pref_ones[i])
        
        target_pref_nonzero_probs_arr = np.array(target_pref_nonzero_probs_list)
        target_pref_nonzero_ones_arr = np.asarray(target_pref_nonzero_ones_list)
        #target_pref_nonzero_ones_arr = np.ones(nonzero_pref_size)
        
        print("++++++++++++++++ ONLY POSSITIVE preferences  +++++++++++++++++++++")
        pprint(target_pref_nonzero_probs_arr)
        pprint(target_pref_nonzero_ones_arr)
        print("list type")
        print(type(target_pref_nonzero_probs_list))
        print("arr type")
        print(type(target_pref_nonzero_probs_arr))
        print("+++++++++++++++")

        target_jaccard_sim = {}
        target_cosine_sim ={}
        target_jaccard_ones_sim = {}
        target_cosine_ones_sim = {}
        target_threshold_jaccard_sim = {}
        target_threshold_cosine_sim = {}

        target_ownership_jaccard_sim = {}
        target_ownership_cosine_sim = {}

        target_group_jaccard_sim = {}
        
        target_nonzero_jaccard_sim = {}
        target_nonzero_cosine_sim = {}
        target_nonzero_jaccard_ones_sim = {}
        target_nonzero_cosine_ones_sim = {}

        target_accessible_resources_ids = set()
        for res in users_own_resources[target_user]:
            target_accessible_resources_ids.add(res.short_id)
        
        print("**** target accessible resources ids ****")
        #pprint(target_accessible_resources_id)
        o_counter = 0
        p_counter = 0
        p_o_counter = 0 
        for index, row in public_discoverable_m_rg.iterrows():
            num_of_genres = np.count_nonzero(row.values)
            if num_of_genres == 0:
                continue
             
            if (target_user, index) in ownership and (target_user, index) in propensity:
                p_o_counter += 1
            if (target_user, index) in ownership:
                #print(str(index) + " in ownership")
                o_counter += 1
                continue     
            if (target_user, index) in propensity:
                print(str(index) + " in propensity")
                p_counter += 1
                continue

            row_corr_target_entries_list = []
            for i in target_pref_nonzero_index:
                row_corr_target_entries_list.append(row.values[i])
            row_corr_target_entries_arr = np.array(row_corr_target_entries_list)
            if not row_corr_target_entries_arr.any():
                continue

            num = 0
            dom = 0
            #print(type(target_pref_probs))
            #print(type(row.values))
            for x, y in zip(target_pref_probs, row.values):
                num += min(x, y)
                dom += max(x, y)
                #print(type(x), type(y))
            js = num/dom

            # Cosine similarity for probabilities
            cs = 1 / (1 + distance.cosine(target_pref_probs, row.values))

            # Jaccard similarity for ones
            jos = jaccard_similarity_score(target_pref_ones, row.values)

            # Cosine similarity for ones
            cos = 1 / (1 + distance.cosine(target_pref_probs, row.values))

            # Jaccrad similarity for threshold
            jts = jaccard_similarity_score(target_thresh_ones, row.values)

            # Cosine similarity for threshold
            cts = 1 / (1 + distance.cosine(target_thresh_ones, row.values))

            # Jaccard similarity for ownership
            jows = jaccard_similarity_score(target_og_row, row.values)

            # Cosine similarity for ownership
            cows = 1 / (1 + distance.cosine(target_og_row, row.values))

            # Group Jaccard similarity 
            jps = jaccard_similarity_score(target_group_ones, row.values)

            target_jaccard_sim[index] = js
            target_cosine_sim[index] = cs
            target_jaccard_ones_sim[index] = jos
            target_cosine_ones_sim[index] = cos
            target_threshold_jaccard_sim[index] = jts
            target_threshold_cosine_sim[index] = cts
            target_ownership_jaccard_sim[index] = jows
            target_ownership_cosine_sim[index] = cows
            target_group_jaccard_sim[index] = jps
            '''
            row_corr_target_entries_list = []
            for i in target_pref_nonzero_index:
                row_corr_target_entries_list.append(row.values[i])
            row_corr_target_entries_arr = np.array(row_corr_target_entries_list)
            '''
            #pprint(row_corr_target_entries_list) 
            #print(len(row_corr_target_entries_list))   
            #pprint(target_pref_nonzero_probs_list)
            #print(len(target_pref_nonzero_probs_list))
            pref_num = 0
            pref_dom = 0
            #print("tesing") 
           
            '''       
            for x in target_pref_nonzero_probs_list:
                print(x)
             
            for y in row_corr_target_entries_list:
                print(y)
            '''
            for x, y in zip(target_pref_nonzero_probs_list[0].tolist(), row_corr_target_entries_list[0].tolist()):
                '''
                print(x, y)
                print("x type")
                print(type(x))
                print("y type")
                print(type(y))
                '''
                pref_num += min(x, y)
                pref_dom += max(x, y)
            jns = pref_num/pref_dom

            # Cosine similarity for probabilities
            cns = 1 / (1 + distance.cosine(target_pref_nonzero_probs_list[0].tolist(), row_corr_target_entries_list[0].tolist()))

            # Jaccard similarity for ones
            jnos = jaccard_similarity_score(target_pref_nonzero_ones_list[0], row_corr_target_entries_list[0])

            # Cosine similarity for ones
            cnos = 1 / (1 + distance.cosine(target_pref_nonzero_ones_list[0].tolist(), row_corr_target_entries_list[0].tolist()))

            target_nonzero_jaccard_sim[index] = jns
            target_nonzero_cosine_sim[index] = cns
            target_nonzero_jaccard_ones_sim[index] = jnos
            target_nonzero_cosine_ones_sim[index] = cnos

        print("+++++++ counters  ++++++++")
        print(str(o_counter) + ", " + str(p_counter) + ", " + str(p_o_counter))
        print("------------ Jaccard similarity for probabilities ---------------")
        rec_index = 1
        for key, value in sorted(target_jaccard_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True)[:15]:
            '''
            recommended_genres = m_rg.loc[key]
            print(rec_index)
            for i in recommended_genres.nonzero():
                print(recommended_genres.iloc[i])
            rec_index += 1
            '''
            print("https://www.hydroshare.org/resource/{}\n{}".format(key, value))
        rec_index = 1
        print("------------ Cosine similarity for probabilities ---------------")
        for key, value in sorted(target_cosine_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True)[:15]:
            '''
            recommended_genres = m_rg.loc[key]
            print(rec_index)
            for i in recommended_genres.nonzero():
                print(recommended_genres.iloc[i])
            rec_index += 1
            '''
            print("https://www.hydroshare.org/resource/{}\n{}".format(key, value))
        rec_index = 1
        print("------------ Jaccard similarity for Ones ---------------")
        for key, value in sorted(target_jaccard_ones_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True)[:15]:
            '''
            recommended_genres = m_rg.loc[key]
            print(rec_index)
            for i in recommended_genres.nonzero():
                print(recommended_genres.iloc[i])
            rec_index += 1
            '''
            print("https://www.hydroshare.org/resource/{}\n{}".format(key, value))
        rec_index = 1
        print("------------ Cosine similarity for Ones ---------------")
        for key, value in sorted(target_cosine_ones_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True)[:15]:
            '''
            recommended_genres = m_rg.loc[key]
            print(rec_index)
            for i in recommended_genres.nonzero():
                print(recommended_genres.iloc[i])
            rec_index += 1
            '''
            print("https://www.hydroshare.org/resource/{}\n{}".format(key, value))
        rec_index = 1
        '''
        print("------------ Jaccard similarity for threshold Ones ---------------")
        for key, value in sorted(target_threshold_jaccard_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True)[:15]:
            print("https://www.hydroshare.org/resource/{}\n{}".format(key, value))

        print("------------ Cosine similarity for threshold Ones ---------------")
        for key, value in sorted(target_threshold_cosine_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True)[:15]:
            print("https://www.hydroshare.org/resource/{}\n{}".format(key, value))
        '''
        print("------------ Jaccard similarity for ownership ---------------")
        for key, value in sorted(target_ownership_jaccard_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True)[:15]:
            print("https://www.hydroshare.org/resource/{}\n{}".format(key, value))

        print("------------ Cosine similarity for ownership ---------------")
        for key, value in sorted(target_ownership_cosine_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True)[:15]:
            print("https://www.hydroshare.org/resource/{}\n{}".format(key, value))

        print("------------ Jaccard similarity for group ---------------")
        for key, value in sorted(target_group_jaccard_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True)[:15]:
            print("https://www.hydroshare.org/resource/{}\n{}".format(key, value))

        print("------------ Jaccard similarity for Nonezero probs ---------------")
        for key, value in sorted(target_nonzero_jaccard_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True)[:15]:
            '''
            recommended_genres = m_rg.loc[key]
            print(rec_index)
            for i in recommended_genres.nonzero():
                print(recommended_genres.iloc[i])
            rec_index += 1
            '''
            print("https://www.hydroshare.org/resource/{}\n{}".format(key, value))
        rec_index = 1

        print("------------ Cosine similarity for Nonezero probs ---------------")
        for key, value in sorted(target_nonzero_cosine_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True)[:15]:
            '''
            recommended_genres = m_rg.loc[key]
            print(rec_index)
            for i in recommended_genres.nonzero():
                print(recommended_genres.iloc[i])
            rec_index += 1
            '''
            print("https://www.hydroshare.org/resource/{}\n{}".format(key, value))
        rec_index = 1

        print("------------ Jaccard similarity for Nonezero ones ---------------")
        for key, value in sorted(target_nonzero_jaccard_ones_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True)[:15]:
            '''
            recommended_genres = m_rg.loc[key]
            print(rec_index)
            for i in recommended_genres.nonzero():
                print(recommended_genres.iloc[i])
            rec_index += 1
            '''
            print("https://www.hydroshare.org/resource/{}\n{}".format(key, value))
        rec_index = 1

        print("------------ Cosine similarity for Nonezero ones ---------------")
        for key, value in sorted(target_nonzero_cosine_ones_sim.iteritems(), key=lambda (k,v): (v,k), reverse=True)[:15]:
            '''
            recommended_genres = m_rg.loc[key]
            print(rec_index)
            for i in recommended_genres.nonzero():
                print(recommended_genres.iloc[i])
            rec_index += 1
            '''
            print("https://www.hydroshare.org/resource/{}\n{}".format(key, value))
        rec_index = 1

        similarity_elapsed_time = time.time() - similarity_start_time
        print("similarities calculation time cost: " + str(similarity_elapsed_time))
