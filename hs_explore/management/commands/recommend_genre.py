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
from sklearn.metrics import jaccard_similarity_score

class Command(BaseCommand):
    def handle(self, *args, **options):
        y_pred = [0.333, 2.121, 1.122, 3.2]
        y_true = [0, 1, 2, 3]
        score = jaccard_similarity_score(y_true, y_pred)
        print(str(score))
