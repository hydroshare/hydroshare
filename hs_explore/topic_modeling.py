from collections import defaultdict
import numpy as np
import pandas as pd
from sklearn.decomposition import NMF, LatentDirichletAllocation, TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.metrics.pairwise import cosine_similarity
from scipy import sparse
from random import randint
from hs_explore.models import Recommend


# required for parsing
import datetime


__author__ = 'ara@cs.tufts.edu'


######################################
# Explore / Predictions for users
# Working User-Item recommendation (using surprise library import SVD, Dataset, Reader)
# https://gist.github.com/aramatev/be359ac68fe502a961404027abfc3b72
#
# Working Item-Item cos similarity (using libraries pandas, sklearn.metrics.pairwise.cosine_similarity, scipy.sparse)
# https://gist.github.com/aramatev/161461d666ab7176068c8c3255159245
######################################


class TopicModeling(object):
    def __init__(self):
        # INPUT_DIR = 'input/'
        # USER_RESOURCE_OTHER = ['CF_user_favorites.txt', 'CF_user_my_resources.txt']
        # USER_RESOURCE_DOWNLOADS = ['CF_user_downloads.txt', 'CF_resource_downloads.txt']  # user_dl.out, resource_dl.out
        # GROUP_FILES = [ 'CF_user_owned_groups.txt' , 'CF_user_viewed_groups.txt']
        # ALL_RESOURCES_ALL_FEATURES = INPUT_DIR + 'resource_features.txt'

        # OUTPUT_DIR = 'output/'
        self.USER_RESOURCES_PATH = 'user_resource_ratings_all.txt'

        self.RESOURCES_FEATURES_PATH = 'resource_features_parsed.txt'

        self.NUM_TOPICS = 10
        self.SEPARATOR = "|"
        self.RESOURCES_FEATURES = []

        self.TOP_N_SIMILARITIES = 10

    @staticmethod
    def clean_user_resource(user_with_resources_set):
        """ We've 2 user files user-set(resource) and resource-set(user)
            :return: We want to return matrix of user-resource with 0's and 1's
        """

        # dict[(user,resource)] = 0 | 1
        user_resource = defaultdict(int)

        # will also keep track of # of users and # of resources via sets
        users = set()
        resources = set()

        for user, set_resources in user_with_resources_set.iteritems():
            # print "%s - %s" % (str(user), str(set_resources))
            for resource in set_resources:
                user_resource[(user, resource)] = 1
                users.add(user)
                resources.add(resource)

        # print user_resource - DELETE prints, done in make_m_n_matrix
        len_users = len(users)
        len_resources = len(resources)
        print "%s users and %s resources " % (len_users, len_resources)

        return user_resource, users, resources

    @staticmethod
    def clean_resources_user(user_resource, resources_with_user_set):
        """ We've a file resource-set(user)
            :return: We want to return updated user_resource we pass in
        """
        users = set()
        resources = set()

        for resource, set_users in resources_with_user_set.iteritems():
            # print "%s - %s" % (str(resource), str(set_users))
            for user in set_users:
                user_resource[(user, resource)] = 1
                users.add(user)
                resources.add(resource)

        # print user_resource - DELETE prints, done in make_m_n_matrix
        len_users = len(users)
        len_resources = len(resources)
        print "%s users and %s resources " % (len_users, len_resources)

        return user_resource, users, resources

    @staticmethod
    def write_user_resource(filename, user_resource_dict):
        target = open(filename, 'a')
        count = 0
        for user_resource, val in user_resource_dict.iteritems():
            s = user_resource[0] + " " + user_resource[1] + " " + str(val) + "\n"
            # print s
            target.write(str(s))
            count += 1
        print "%s items" % (count)

    @staticmethod
    def make_user_resource_dict(ratings):
        # dict[(user,resource)] = 0 | 1
        user_resource = defaultdict(lambda: defaultdict(int))

        users = set()
        resources = set()

        for user, resource, rating in ratings:
            user_resource[user][resource] = 1
            users.add(user)
            resources.add(resource)

        # print user_resource
        len_users = len(users)
        len_resources = len(resources)
        print "%s users and %s resources " % (len_users, len_resources)

        # add users to 1st col
        print "len(users)", len(users)
        print "len(resources)", len(resources)

        return users, resources, user_resource

    def dict_arr_to_string_format(self, some_dict):
        s = ""
        resource_uri = '/resource/'
        global RESOURCES_FEATURES
        for feat in RESOURCES_FEATURES:
            feature = some_dict[feat]

            if isinstance(feature, list):
                feature.sort()
                # retval = dict_arr_to_string_format(feature, ARR_SEPARATOR)
                joined = ",".join(feature)
                s += unicode(joined).encode('utf-8')
            elif isinstance(feature, unicode):
                feature = unicode(feature).encode('utf-8')

                # store resource_id
                if resource_uri in feature:
                    s = feature[len(resource_uri):-1] + self.SEPARATOR + s

                s += feature
            else:
                s += str(feature)
            s += self.SEPARATOR

        return s.replace('\r', "").replace('\n', " ")

    def write_resource_features(self, filename, arr):
        """ Array arr has dictionaries which are resources, each dictionary has 53
        'features'. Write them to file each on a separate line.
        The 53 features should be separated by |
        :param filename: file to write | separated features
        :param arr: array of dictionary
        :return:
        """

        target = open(filename, 'a')

        global RESOURCES_FEATURES
        RESOURCES_FEATURES = arr[0].keys()
        features = "resource_id|" + self.SEPARATOR.join(RESOURCES_FEATURES) + self.SEPARATOR
        target.write(str(features))
        target.write(str("\n"))

        count = 0
        for some_dict in arr:
            s = self.dict_arr_to_string_format(some_dict)
            # print s
            target.write(str(s) + "\n")
            count += 1

    @staticmethod
    def split_user_resource_training_test(user_resource_dict):
        test_data = defaultdict(lambda: defaultdict(int))
        train_data = defaultdict(lambda: defaultdict(int))
        for user in user_resource_dict.keys():
            resources = user_resource_dict[user].keys()
            len_resources = len(resources)
            if len_resources > 1:
                test_index = randint(0, len_resources - 1)
                test_resource = resources[test_index]
                test_data[user][test_resource] = user_resource_dict[user][test_resource]
                for index, resource in enumerate(resources):
                    if index != test_index:
                        train_data[user][resource] = user_resource_dict[user][test_resource]

        return train_data, test_data

    @staticmethod
    def test_accuracy(data, similarity_matrix, top_n, train_user_resources, test_user_resources):
        mean_average = 0
        for user in train_user_resources.keys():
            test_resource = test_user_resources[user].keys()[0]
            resources = train_user_resources[user].keys()
            similarities = []
            for resource in resources:
                try:
                    # print (user, resource)
                    series = data.loc[data['resource_id'] == resource, 'abstract']
                    if series.size > 0 and len(series.iloc[0]) > 0:
                        sims_series = similarity_matrix.loc[resource].nlargest(top_n)
                        for resource_id, similarity in sims_series.iteritems():
                            similarities.append((resource_id, similarity))

                except KeyError:
                    # do some exception handling here (or just pass)
                    pass
            match = 0
            total = 0
            precision = 0
            top_n_similarities = sorted(similarities, key=lambda item: item[1])[:top_n]
            # top_n_similarities = similarities
            # print "len(top_n_similarities)", len(similarities)
            for resource_id, similarity in top_n_similarities:
                total += 1
                if resource_id == test_resource:
                    # print (user, resource_id, similarity)
                    match += 1
                    precision += 1.0 * match / total
            if total != 0:
                mean_average += 1.0 * precision / total

        total_users = len(train_user_resources.keys())
        print top_n, "\t", 1.0 * mean_average / total_users * 100

    @staticmethod
    def calculate_similarity(Z, resource_ids):
        """Calculate the column-wise cosine similarity for a sparse
        matrix. Return a new dataframe matrix with similarities.
        """
        data_sparse = sparse.csr_matrix(Z)
        similarities = cosine_similarity(data_sparse)
        sim = pd.DataFrame(data=similarities, index=resource_ids, columns=resource_ids)
        return sim

    @staticmethod
    def populate_user_resource_db(data, similarity_matrix, top_n, user_resource_dict):
        for user in user_resource_dict.keys():
            resources = user_resource_dict[user].keys()
            if len(resources) > 1:
                recommended_resources = []
                for resource in resources:
                    try:
                        # print (user, resource)
                        series = data.loc[data['resource_id'] == resource, 'abstract']
                        if series.size > 0 and len(series.iloc[0]) > 0:
                            sims_series = similarity_matrix.loc[resource].nlargest(top_n)
                            for resource_id, similarity in sims_series.iteritems():
                                recommended_resources.append((resource_id, similarity))
                                Recommend.recommend_ids(user, resource_id, similarity)
                                # print (user, resource_id, similarity)
                    except KeyError:
                        # do some exception handling here (or just pass)
                        pass

                # this is for combined recommendation
                # top_rec_resources = sorted(recommended_resources, key=lambda item: item[1])[-top_n:]
                # for document_id, similarity in top_rec_resources:
                    # call to store Recommend.db(user, document_id, similarity
                    # print (user, document_id, similarity)

    def start(self, all_resource_features, all_resource_abstracts, user_resource_downloads, user_resource_other):
        # not using all_resource_features now, only all_resource_extended/abstracts
        print "len(all_resource_features)", len(all_resource_features)
        print "len(all_resource_abstracts)", len(all_resource_abstracts)
        print "len(user_resource_downloads)", len(user_resource_downloads)
        print "len(user_resource_other)", len(user_resource_other)

        # parse out User- Resource Downloads, and Resource Downloads of Users
        user_resource_dl = user_resource_downloads[0]
        resources_users_dl = user_resource_downloads[1]
        user_resource, users, resources = self.clean_user_resource(user_resource_dl)
        user_resource, users, resources = self.clean_resources_user(user_resource, resources_users_dl)
        open(self.USER_RESOURCES_PATH, 'w').close()
        self.write_user_resource(self.USER_RESOURCES_PATH, user_resource)
        print "User resource downloads: clean & write...\t DONE!"

        # parse out User-Resource info such as favorites and app launches
        for user_resource_dict in user_resource_other:
            user_resource, users, resources = self.clean_user_resource(user_resource_dict)

            self.write_user_resource(self.USER_RESOURCES_PATH, user_resource)
            print "User resource fave/app launches: clean & write ...\t DONE!"

        # ------------------
        # TRANSFORM THE DATASET
        ratings = np.loadtxt(self.USER_RESOURCES_PATH, dtype=str, delimiter=" ")
        users, resources, user_resource_dict = self.make_user_resource_dict(ratings)

        ###########################
        # read all resources' features
        # open(self.RESOURCES_FEATURES_PATH, 'w').close()
        # self.write_resource_features(self.RESOURCES_FEATURES_PATH, all_resource_features)
        #
        # # Important! invalid_raise=False, otherwise we crash and burn here
        # R = np.genfromtxt(self.RESOURCES_FEATURES_PATH, dtype='str', delimiter=self.SEPARATOR, encoding='utf-8', invalid_raise=False,
        #                   filling_values='')
        #
        # # blank out the file and rewrite "R" down to file w/o invalid
        # open(self.RESOURCES_FEATURES_PATH, 'w').close()
        # np.savetxt(self.RESOURCES_FEATURES_PATH, R, fmt="%s", delimiter=self.SEPARATOR, encoding='utf-8')
        # print "All resource features: formatted & invalid cols removed ...\t DONE!"
        #
        # # ------------------
        # # LOAD THE DATASET
        # data = pd.read_csv(self.RESOURCES_FEATURES_PATH, sep=self.SEPARATOR, encoding='utf-8')
        # data = data.replace(np.nan, '', regex=True)
        # data = data.replace('None', '', regex=True)
        # resource_ids = data['resource_id']

        ###########################
        # read resource 'extended' abstracts
        np_arr = np.array(all_resource_abstracts)
        resource_ids = np_arr[:, 0]
        abstracts = np_arr[:, 1]
        data = pd.DataFrame({'resource_id': resource_ids, 'abstract': abstracts})
        data = data.replace(np.nan, '', regex=True)
        data = data.replace('None', '', regex=True)

        # contents_ravel = data['title'] + " " + data['abstract']
        contents_ravel = abstracts
        vectorizer = CountVectorizer(min_df=5, max_df=0.9,
                                     stop_words='english', lowercase=True,
                                     token_pattern='[a-zA-Z\-][a-zA-Z\-]{2,}')
        data_vectorized = vectorizer.fit_transform(contents_ravel)
        print "CountVectorizer: fit_transform ...\t DONE!"

        # Build a Latent Dirichlet Allocation Model
        lda_model = LatentDirichletAllocation(n_components=self.NUM_TOPICS, max_iter=10,
                                              learning_method='online')
        lda_Z = lda_model.fit_transform(data_vectorized)
        print "LatentDirichletAllocation: fit_transform ...\t DONE!"

        # Build the similarity matrix
        # magnitude = sqrt(x2 + y2 + z2 + ...)
        magnitude = np.sqrt(np.square(lda_Z).sum(axis=1))

        # unitvector = (x / magnitude, y / magnitude, z / magnitude, ...)
        lda_Z_pd = pd.DataFrame(lda_Z)
        lda_Z_pd = lda_Z_pd.divide(magnitude, axis='index')

        similarity_matrix = self.calculate_similarity(lda_Z_pd, resource_ids)
        print "calculate similarity_matrix ...\t DONE!"

        # test accuracy using Mean Average Precision
        # train_user_resources, test_user_resources = self.split_user_resource_training_test(user_resource_dict)
        # print "topN, Mean Average Precision (MAP) %"
        # for top_n in [10, 5, 3, 2, 1]:
        #     self.test_accuracy(data, similarity_matrix, top_n, train_user_resources, test_user_resources)

        self.populate_user_resource_db(data, similarity_matrix, self.TOP_N_SIMILARITIES, user_resource_dict)
