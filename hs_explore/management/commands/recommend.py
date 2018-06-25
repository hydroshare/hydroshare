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

class Command(BaseCommand):
    def handle(self, *args, **options):
        ratings = defaultdict(int)
        records = Features.resource_owners()
        for user, res in records:
             if (user, res) not in ratings:
                 ratings[(user, res)] = 1
        print("resources owned")    
        edits = Features.resource_editors() 
        for user, res in edits:
            if (user, res) not in ratings:
                ratings[(user, res)] = 1
            else:
                ratings[(user, res)] += 1
        print("resources edited")
        views = Features.visited_resources(datetime(2017, 11, 01, 0, 0, 0, 0), datetime(2017, 12, 31, 0, 0, 0, 0))
        for user, res_set in views.iteritems():
            #print(user + " visied")
            for res in res_set:
                if (user, res) not in ratings:
                    ratings[(user, res)] = 1
                else:
                    ratings[(user, res)] += 1
        print("resources viewed")
        downloads = Features.user_downloads(datetime(2017, 11, 01, 0, 0, 0, 0), datetime(2017, 12, 31, 0, 0, 0, 0))
        for user, res_set in downloads.iteritems():
            for res in res_set:
                if (user, res) not in ratings:
                    ratings[(user, res)] = 1
                else:
                    ratings[(user, res)] += 1
        print("resources downloads")
        apps = Features.user_apps(datetime(2017, 11, 01, 0, 0, 0, 0), datetime(2017, 12, 31, 0, 0, 0, 0))
        for user, res_set in apps.iteritems():
            for res in res_set:
                if (user, res) not in ratings:
                    ratings[(user, res)] = 1
                else:
                    ratings[(user, res)] += 1
        print("resources apped")
        favors = Features.user_favorites()      
        for user, res_set in favors.iteritems():
            for res in res_set:
                if (user, res) not in ratings:
                    ratings[(user, res)] = 1
                else:
                    ratings[(user, res)] += 1
        print("resources favored")
        #for k, v in ratings.iteritems():
        #    print(k, v)
        user_usernames = set()
        for user in User.objects.all():
            if user is not None and \
               user.username != 'test' and user.username != 'demo':
                user_usernames.add(user.username)
        print(len(user_usernames))
        #for u in user_usernames:
        #    print(u)
        resource_ids = set()
        for res in BaseResource.objects.all():
            resource_ids.add(res.short_id)
        print(len(resource_ids))
        #for r in resource_ids:
        #    print(r)
        print("building rating matrix")
        r_matrix = pd.DataFrame(0, index=list(user_usernames), columns=list(resource_ids))
        #r_matrix[:] = 0
        #print(len(r_matirx[0,0])
        for k, v in ratings.iteritems():
            if k[0] in r_matrix.index and k[1] in r_matrix.columns:
                r_matrix.at[k[0], k[1]] = v
                if k[0] == "dtarb":   
                    print( k[0], k[1],str(v) )
           # else:    
           #     print(k[1] + ":" +  k[0])
        #r_matrix.to_csv("r_matrix.csv", sep='\t', encoding='utf-8')
        #temp = r_matrix.iloc[0:5, 1960:].copy();
        #print(temp.to_string()) 
        print("form sparse matrix")
        #print(r_matrix["dtarb"])
        data_sparse = sparse.csr_matrix(r_matrix.values)
        #data_sparse = r_matrix.to_sparse()
        #data_sparse = r_matrix.to_sparse()
        print("set nmf model")
        model = NMF(n_components=100, init='random', random_state=0)
        print("fit transform")
        #model.fit(r_matrix.values)
       
        W = model.fit_transform(data_sparse);
        H = model.components_;
        nR = np.dot(W,H)
        print("convert to dataframe")
        result_pd = pd.DataFrame(nR, index=list(user_usernames), columns=list(resource_ids))
        print("show sample")
        temp = result_pd.loc["dtarb"].copy();
        print(temp.to_string()) 
        #data_sparse = sparse.csr_matrix(r_matrix.values)
