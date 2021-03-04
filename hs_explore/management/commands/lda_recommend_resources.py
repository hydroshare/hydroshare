""" This generates a list of recommended resources to each qualified user, who
    selected at least 5 qualified resources in the last 30 days. Resources with more
    than two keywords are considered to be qualified resources.
"""
from datetime import timedelta, date
from hs_explore.utils import get_resource_to_subjects, get_resource_to_abstract,\
    get_resource_to_published, get_users_interacted_resources, get_resource_to_keep_words,\
    jaccard_sim, store_user_preferences, store_recommended_resources, clear_old_data,\
    resource_owners, resource_editors
from collections import defaultdict
from django.core.management.base import BaseCommand
import gensim
from gensim import corpora
from operator import itemgetter
from haystack.query import SearchQuerySet, SQ


def make_recommendations():
    """ The main function for running the LDA recommendation process
    """
    resource_to_abstract = get_resource_to_abstract()
    resource_to_subjects, all_subjects_list = get_resource_to_subjects()
    end_date = date(2018, 5, 31)
    start_date = end_date - timedelta(days=30)
    user_to_resources, all_usernames = get_users_interacted_resources(start_date, end_date)
    resource_to_published = get_resource_to_published()
    owner_to_resources = resource_owners()
    editor_to_resources = resource_editors()
    print("resource_to_keep_words")
    resource_to_keep_words = get_resource_to_keep_words(resource_to_subjects, resource_to_abstract)

    # filter qualfied users to resources selected by each of them
    qualified_user_to_resources = {}
    for username, res_ids in user_to_resources.items():
        qualified_resources_list = []
        for res_id in res_ids:
            if res_id in resource_to_keep_words:
                qualified_resources_list.append(res_id)
        if len(qualified_resources_list) >= 5:
            qualified_user_to_resources[username] = qualified_resources_list

    user_to_res_keep_words_list = {}
    user_to_keep_words_set = {}
    user_to_keep_words_freq = {}
    # build user to keep words frequency dictionary
    for username, qualified_resources_list in qualified_user_to_resources.items():
        res_keep_words_list = []
        keep_words_set = set()
        keep_words_freq = {}
        for res_id in qualified_resources_list:
            res_keep_words = resource_to_keep_words[res_id]
            keep_words_set = keep_words_set.union(res_keep_words)
            res_keep_words_list.append(list(res_keep_words))
            for keep_word in res_keep_words:
                if keep_word not in keep_words_freq:
                    keep_words_freq[keep_word] = 1
                else:
                    keep_words_freq[keep_word] += 1
        # this dictionary is used for training each qualified user's LDA model
        user_to_res_keep_words_list[username] = res_keep_words_list
        # this dictionary is used for doing SOLR pre-filtering
        user_to_keep_words_set[username] = keep_words_set
        # this dictionary is used for storing each user's preference to each keep
        # word selected by the user
        user_to_keep_words_freq[username] = keep_words_freq

    print("store user preferences")
    store_user_preferences(user_to_keep_words_freq)
    lda_users_recommendations = {}
    print("lda process")
    for username, keep_words_list in user_to_res_keep_words_list.items():
        user_to_recommend = {}
        if len(keep_words_list) >= 5:
            dictionary = corpora.Dictionary(keep_words_list)
            corpus = [dictionary.doc2bow(doc) for doc in keep_words_list]
            Lda = gensim.models.ldamodel.LdaModel
            ldamodel = Lda(corpus, num_topics=5, id2word=dictionary, passes=50)
            x = ldamodel.show_topics(num_topics=5, num_words=10, formatted=False)
            topics_words = [(tp[0], [wd[0] for wd in tp[1]]) for tp in x]
            # Find topics in which the user interests
            user_probable_topics_set = set()
            for c in corpus:
                for topic, prob in ldamodel[c]:
                    if prob - 0.2 > 0.001:
                        user_probable_topics_set.add(topic)
            user_resources = []
            user_selected_resources = user_to_resources[username]
            user_resources += user_selected_resources
            if username in owner_to_resources:
                user_owned_resources = owner_to_resources[username]
                user_resources += user_owned_resources
            if username in editor_to_resources:
                user_editable_resources = editor_to_resources[username]
                user_resources += user_editable_resources

            # pre-filter by SOLR
            out = SearchQuerySet()
            out = out.exclude(short_id__in=user_resources)
            filter_sq = None
            user_out = out
            user_keep_words_set = user_to_keep_words_set[username]
            for keep_word in user_keep_words_set:
                if filter_sq is None:
                    filter_sq = SQ(subject__contains=keep_word)
                else:
                    filter_sq.add(SQ(subject__contains=keep_word), SQ.OR)

            if filter_sq is not None:
                user_out = out.filter(filter_sq)

            # If no unselected resource contains any keyword in which the user interests,
            # skip the user
            if user_out.count() == 0:
                continue

            # for res_id, doc_words in resource_to_keep_words.items():
            for candidate in user_out:
                res_id = candidate.short_id
                if res_id not in resource_to_keep_words:
                    continue
                res_keep_words = resource_to_keep_words[res_id]
                if resource_to_published[res_id]:
                    if len(res_keep_words) < 3:
                        continue
                    res_keep_words_list = list(res_keep_words)
                    bow = dictionary.doc2bow(res_keep_words_list)
                    t = ldamodel.get_document_topics(bow)
                    topic_prob_dict = dict((x, y) for x, y in t)
                    # Skip resources without any probable topics.
                    # A probable topic is defined as any topic with probablity over (1/#topics),
                    # which is 0.2 in our case
                    if max(topic_prob_dict.values()) - 0.2 < 0.001:
                        continue
                    res_probable_topics = set()
                    for topic, prob in topic_prob_dict.items():
                        if prob - 0.2 > 0.001:
                            res_probable_topics.add(topic)
                    common_topics = set.intersection(user_probable_topics_set, res_probable_topics)
                    # If the resource has no topics in common with the user's prbable topics set,
                    # Skip it.
                    if len(common_topics) == 0:
                        continue

                    for topic, words in topics_words:
                        if topic not in common_topics:
                            continue
                        topic_words_set = set(words)
                        topic_prob = 0
                        if topic in topic_prob_dict:
                            topic_prob = topic_prob_dict[topic]
                        jac_sim = jaccard_sim(res_keep_words, topic_words_set)
                        if jac_sim == 0.0:
                            continue
                        scaled_jac_sim = topic_prob * jac_sim
                        if res_id not in user_to_recommend:
                            user_to_recommend[res_id] = scaled_jac_sim
                        else:
                            user_to_recommend[res_id] += scaled_jac_sim

            lda_users_recommendations[username] = user_to_recommend
    user_to_recommended_resources_list = defaultdict(list)
    for username, user_to_recommend in lda_users_recommendations.items():
        lda_top_10_recommendations = sorted(user_to_recommend.items(), key=itemgetter(1), reverse=True)[:10]
        for lda_res_id, lda_value in lda_top_10_recommendations:
            if lda_res_id not in resource_to_abstract or lda_res_id not in resource_to_keep_words:
                continue
            user_to_recommended_resources_list[username].append((lda_res_id, lda_value))
    print("store recommended resources")
    store_recommended_resources(user_to_recommended_resources_list, resource_to_keep_words)


class Command(BaseCommand):
    help = "Make recommendations using LDA algorithms."

    def handle(self, *args, **options):
        clear_old_data()
        make_recommendations()
