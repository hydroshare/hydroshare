from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models import Q, F, Max
from django.db import transaction
from django.core.exceptions import PermissionDenied

from hs_core.models import BaseResource

import os

import numpy
from collections import defaultdict
from copy import deepcopy

from surprise import SVD
from surprise import Dataset
from surprise import Reader


######################################
# Explore / Predictions for users
######################################


class Recommend(models.Model):
    """
    Shared methods for Recommendation System/ Prediction of Resources to read
    """
    DEBUG = 0
    USER_DL_FILE = 'input/USER_DL.OUT'
    RESOURCE_DL_FILE = 'input/RESOURCE_DL.OUT'
    SUPRISE_OUTPUT_FILE = 'output/user_resource_rating_1s.txt'

    class Meta:
        abstract = True

    # @classmethod
    # def get_privilege(cls, **kwargs):
    #     return none;

    @classmethod
    def read(filename):
        dict1 = defaultdict(set)
        with open(filename, 'r') as f:
            s = f.read()
            dict1 = eval(s)
        return dict1
        # if 'Elbin' in self.user_resource:
        #     print self.user_resource['Elbin']

    ""

    def clean(user_dl, resource_dl):
        """ We've 2 user files user-set(resource) and resource-set(user)
            :return: We want to return matrix of user-resource with 0's and 1's
        """

        # dict[(user,resource)] = 0 | 1
        user_resource = defaultdict(int)

        # will also keep track of # of users and # of resources via sets
        users = set()
        resources = set()

        for user, set_resources in user_dl.iteritems():
            # print "%s - %s" % (str(user), str(set_resources))
            for resource in set_resources:
                user_resource[(user, resource)] = 1
                users.add(user)
                resources.add(resource)

        for resource, set_users in resource_dl.iteritems():
            # print "%s - %s" % (str(resource), str(set_users))
            for user in set_users:
                user_resource[(user, resource)] = 1
                users.add(user)
                resources.add(resource)

        # print user_resource
        len_users = len(users)
        len_resources = len(resources)
        print "# users %s \tvs # resources %s" % (len_users, len_resources)

        user_resource_orig = deepcopy(user_resource)
        R = [[0 for x in range(len_resources)] for y in range(len_users)]
        for n, user in enumerate(users):
            for m, resource in enumerate(resources):
                R[n][m] = user_resource[(user, resource)]

        R = numpy.array(R)
        return user_resource_orig, user_resource, R

    def write(filename, user_resource_dict):
        target = open(filename, 'a')
        s = ""
        for user_resource, val in user_resource_dict.iteritems():
            s = user_resource[0] + " " + user_resource[1] + " " + str(val) + "\n"
            print s
            target.write(str(s))

    def get_top_n(predictions, n=10):
        '''Return the top-N recommendation for each user from a set of predictions.

        Args:
            predictions(list of Prediction objects): The list of predictions, as
                returned by the test method of an algorithm.
            n(int): The number of recommendation to output for each user. Default
                is 10.

        Returns:
        A dict where keys are user (raw) ids and values are lists of tuples:
            [(raw item id, rating estimation), ...] of size n.
        '''

        # First map the predictions to each user.
        top_n = defaultdict(list)
        for uid, iid, true_r, est, _ in predictions:
            top_n[uid].append((iid, est))

        # Then sort the predictions for each user and retrieve the k highest ones.
        for uid, user_ratings in top_n.items():
            user_ratings.sort(key=lambda x: x[1], reverse=True)
            top_n[uid] = user_ratings[:n]

        return top_n

    user_dl = read(USER_DL_FILE)
    resource_dl = read(RESOURCE_DL_FILE)

    user_resource_orig, user_resource, R = clean(user_dl, resource_dl)

    write(SUPRISE_OUTPUT_FILE, user_resource_orig)

    # First train an SVD algorithm on the custom dataset.
    # Pode botar tb: timestamp
    reader = Reader(line_format='user item rating', sep=' ', skip_lines=0, rating_scale=(1, 5))

    custom_dataset_path = (os.path.dirname(os.path.realpath(__file__)) + '/' + SUPRISE_OUTPUT_FILE)
    print("> Using: " + custom_dataset_path)
    print("> Loading data...")
    data = Dataset.load_from_file(file_path=custom_dataset_path, reader=reader)

    print("Creating trainset...")
    trainset = data.build_full_trainset()

    print("Training...")
    algo = SVD()
    algo.train(trainset)

    # Than predict ratings for all pairs (u, i) that are NOT in the training set.
    print("Predicting...")
    testset = trainset.build_anti_testset()
    # print "len testset=", (len(testset))
    predictions = algo.test(testset)
    # print "len predictions=", (len(predictions))

    top_n = get_top_n(predictions, n=10)
    # print("OK")

    # Print the recommended items for each user
    print("> Results:")
    for uid, user_ratings in top_n.items():
        print(uid, [iid for (iid, _) in user_ratings])