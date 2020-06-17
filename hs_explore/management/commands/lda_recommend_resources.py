""" This generates a list of recommended resources to each qualified user, who
    selected at least 5 qualified resources in the last 30 days. Resources with more
    than two keywords are considered to be qualified resources.
"""
from collections import defaultdict
from datetime import timedelta, date
from hs_explore import utils
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import user_from_id, get_resource_by_shortkey
from django.core.management.base import BaseCommand
from hs_explore.models import RecommendedResource, PropensityPrefToPair, PropensityPreferences
import string
import gensim
from gensim import corpora
from nltk.stem import WordNetLemmatizer
from operator import itemgetter
from hs_explore.models import LDAWord
from haystack.query import SearchQuerySet, SQ


def get_resource_to_subjects():
    """ :return resource_to_subjects, a dictionary of each resource to its subjects
        :return all_subjects_list, all subjects extracted from available resources
    """
    resource_ids = set()
    all_subjects = set()
    resource_to_subjects = {}
    for res in BaseResource.objects.all():
        if res is None or res.metadata is None or res.metadata.subjects is None:
            continue
        raw_subjects = [subject.value.strip() for subject in res.metadata.subjects.all()
                                .exclude(value__isnull=True)]
        subjects = [sub.lower().replace(" ", "_") for sub in raw_subjects]
        all_subjects.update(subjects)
        resource_ids.add(res.short_id)
        resource_to_subjects[res.short_id] = set(subjects)
    all_subjects_list = list(all_subjects)
    return resource_to_subjects, all_subjects_list


def get_resource_to_abstract():
    """ return a map of each resource to its abstract
    """
    resource_ids = set()
    resource_to_abstract = {}
    for res in BaseResource.objects.all():
        if res is None or res.metadata is None or res.metadata.description is None or \
           res.metadata.description.abstract is None:
            continue
        abstract = res.metadata.description.abstract.lstrip()

        resource_ids.add(res.short_id)
        resource_to_abstract[res.short_id] = abstract

    return resource_to_abstract


def get_resource_to_published():
    """ map each resource to its availability
    """
    resource_to_published = {}
    for res in BaseResource.objects.all():
        if res.raccess.published or res.raccess.public or res.raccess.discoverable:
            resource_to_published[res.short_id] = True
        else:
            resource_to_published[res.short_id] = False
    return resource_to_published


def get_users_interacted_resources(beginning, today):
    """ map each user to resources selected by the user during a given
        time period. And all active users' usernames in this time period
        :param beginning (date type), the start date of the time period
        :param today (date type), the end date of the time period
        :return user_to_resources, map each user to resources selected by the user
        :return usernames, a set of all active users' usernames
    """
    all_usernames = set()
    user_to_resources_set = defaultdict(set)
    triples = utils.user_resource_matrix(beginning, today)
    for v in triples:
        username = v[0]
        res = v[1]
        all_usernames.add(username)
        user_to_resources_set[username].add(res)
    user_to_resources = defaultdict(list)
    for username, res_ids_set in user_to_resources_set.items():
        res_ids_list = list(res_ids_set)
        user_to_resources[username] = list(res_ids_set)
        res_list = []
        for res_id in res_ids_list:
            try:
                r = get_resource_by_shortkey(res_id)
                res_list.append(r)
            except:
                continue
    return user_to_resources, all_usernames


def filter_go_words(res_id, doc, resource_to_subjects, go_words, stop):
    """
    """
    exclude = set(string.punctuation)
    exclude.remove('_')
    lemmatizer = WordNetLemmatizer()
    doc_words = set()
    doc_list = set()

    for w in doc.split(" "):
        doc_list.add(lemmatizer.lemmatize(w))

    for go_word in go_words:
        if " " in go_word:
            if go_word in doc and go_word not in stop:
                bigram_name = go_word.replace(" ", "_")
                doc_words.add(bigram_name)
        else:
            if go_word in doc_list and go_word not in stop:
                doc_words.add(go_word)

    if res_id in resource_to_subjects:
        res_subjects = resource_to_subjects[res_id]
        for sub in res_subjects:
            if sub not in stop:
                doc_words.add(sub)

    return doc_words


def get_resource_to_go_words(resource_to_subjects, resource_to_abstract):
    resource_to_go_words = {}
    stop_words = set()
    go_words = set()
    for word in LDAWord.objects.all():
        if word.word_type == 'stop':
            stop_words.add(word.value)
        else:
            go_words.add(word.value)

    for res_id, res_abs in resource_to_abstract.items():
        res_go_words = filter_go_words(res_id, res_abs, resource_to_subjects, go_words, stop_words)
        if len(res_go_words) < 3:
            continue
        resource_to_go_words[res_id] = res_go_words
    return resource_to_go_words


def jaccard_sim(keywords_set1, keywords_set2):
    """ calculate the Jaccard similarity between two sets of keywords
        :param keywords_set1, a set of keywords
        :param keywords_set2, another set of keywords
    """
    inter = len(keywords_set1.intersection(keywords_set2))
    union = len(keywords_set1.union(keywords_set2))
    # if both keyword sets are empty, i.e., their union is empty
    # return 0
    if union == 0:
        return 0
    else:
        jac_sim = inter / float(union)
        return jac_sim


def store_user_preferences(user_to_keep_words_freq):
    """ store each user's preference to each keep word selected by the user
        :param user_To_keep_words_freq, a nested dictionary. It maps each username
        to a dictionary that maps each keep word selected by the user to its
        selected frequency
    """
    for username, keep_word_to_freq in user_to_keep_words_freq.items():
        user = user_from_id(username)
        prop_pref_subjects = []
        for keep_word, freq in keep_word_to_freq.items():
            prop_pref_subjects.append(('subject', keep_word, freq))
        PropensityPreferences.prefer(user, 'Resource', prop_pref_subjects)


def store_recommended_resources(user_to_recommended_resources_list, resource_to_keep_words):
    """ store the recommended results for each qualified user
        :param user_to_recommended_resources_list, a dictionary maps each user to a list
         of resources' ids recommended to the user.
        :param resource_to_keep_words, a dictionary maps each resource to its keep words
    """
    for username, recommend_resources_list in user_to_recommended_resources_list.items():
        user = user_from_id(username)
        user_preferences = PropensityPreferences.objects.get(user=user)
        user_preferences_pairs = user_preferences.preferences.all()
        user_resources_preferences = PropensityPrefToPair.objects.\
                                                filter(prop_pref=user_preferences,
                                                       pair__in=user_preferences_pairs,
                                                       state='Seen',
                                                       pref_for='Resource')
        user_res_preferences_set = set()
        user_res_pref_to_weight = {}
        for p in user_resources_preferences:
            if p.pair.key == 'subject':
                user_res_preferences_set.add(p.pair.value)
                user_res_pref_to_weight[p.pair.value] = p.weight

        for res_id, sim in recommend_resources_list:
            recommended_res = get_resource_by_shortkey(res_id)
            r = RecommendedResource.recommend(user,
                                              recommended_res,
                                              'Propensity',
                                              round(sim, 4))
            recommended_keep_words = resource_to_keep_words[res_id]
            common_subjects = set.intersection(user_res_preferences_set,
                                                set(recommended_keep_words))
            for cs in common_subjects:
                raw_cs = cs.replace("_", " ")
                r.relate('subject', raw_cs, user_res_pref_to_weight[cs])


def main():
    """ The main function for running the LDA recommendation process
    """
    resource_to_abstract = get_resource_to_abstract()
    resource_to_subjects, all_subjects_list = get_resource_to_subjects()
    # For testing purpose, import date and uncommnet this line
    end_date = date(2020, 6, 7)
    # end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    user_to_resources, all_usernames = get_users_interacted_resources(start_date, end_date)
    resource_to_published = get_resource_to_published()
    print("resource_to_go_words")
    resource_to_go_words = get_resource_to_go_words(resource_to_subjects, resource_to_abstract)

    # filter qualfied users to resources selected by each of them
    qualified_user_to_resources = {}
    for username, res_ids in user_to_resources.items():
        qualified_resources_list = []
        for res_id in res_ids:
            if res_id in resource_to_go_words:
                qualified_resources_list.append(res_id)
        if len(qualified_resources_list) >= 5:
            qualified_user_to_resources[username] = qualified_resources_list

    user_to_res_go_words_list = {}
    user_to_go_words_set = {}
    user_to_go_words_freq = {}
    # build user to keep words frequency dictionary
    for username, qualified_resources_list in qualified_user_to_resources.items():
        res_go_words_list = []
        go_words_set = set()
        go_words_freq = {}
        for res_id in qualified_resources_list:
            res_go_words = resource_to_go_words[res_id]
            go_words_set = go_words_set.union(res_go_words)
            res_go_words_list.append(list(res_go_words))
            for go_word in res_go_words:
                if go_word not in go_words_freq:
                    go_words_freq[go_word] = 1
                else:
                    go_words_freq[go_word] += 1
        # this dictionary is used for training each qualified user's LDA model
        user_to_res_go_words_list[username] = res_go_words_list
        # this dictionary is used for doing SOLR pre-filtering
        user_to_go_words_set[username] = go_words_set
        # this dictionary is used for storing each user's preference to each keep
        # word selected by the user
        user_to_go_words_freq[username] = go_words_freq

    print("store user preferences")
    store_user_preferences(user_to_go_words_freq)
    lda_users_recommendations = {}
    print("lda process")
    for username, go_words_list in user_to_res_go_words_list.items():
        user_to_recommend = {}
        if len(go_words_list) >= 5:
            dictionary = corpora.Dictionary(go_words_list)
            corpus = [dictionary.doc2bow(doc) for doc in go_words_list]
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
            user_resources = user_to_resources[username]

            # pre-filter by SOLR
            out = SearchQuerySet()
            out = out.exclude(short_id__in=user_resources)
            filter_sq = None
            user_out = out
            user_go_words_set = user_to_go_words_set[username]
            for go_word in user_go_words_set:
                if filter_sq is None:
                    filter_sq = SQ(subject__contains=go_word)
                else:
                    filter_sq.add(SQ(subject__contains=go_word), SQ.OR)

            if filter_sq is not None:
                user_out = out.filter(filter_sq)

            # If no unselected resource contains any keyword in which the user interests,
            # skip the user
            if user_out.count() == 0:
                continue

            # for res_id, doc_words in resource_to_go_words.items():
            for candidate in user_out:
                res_id = candidate.short_id
                if res_id not in resource_to_go_words:
                    continue
                res_go_words = resource_to_go_words[res_id]
                if resource_to_published[res_id]:
                    if len(res_go_words) < 3:
                        continue
                    res_go_words_list = list(res_go_words)
                    bow = dictionary.doc2bow(res_go_words_list)
                    t = ldamodel.get_document_topics(bow)
                    topic_prob_dict = dict((x, y) for x, y in t)
                    # Skip resources without any probable topics.
                    # A dominant topic is defined as any topic with probablity over (1/#topics),
                    # which is 0.2 in our case
                    if max(topic_prob_dict.values()) - 0.2 < 0.001:
                        continue
                    res_dominant_topics = set()
                    for topic, prob in topic_prob_dict.items():
                        if prob - 0.2 > 0.001:
                            res_dominant_topics.add(topic)
                    common_topics = set.intersection(user_probable_topics_set, res_dominant_topics)
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
                        jac_sim = jaccard_sim(res_go_words, topic_words_set)
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
            if lda_res_id not in resource_to_abstract or lda_res_id not in resource_to_go_words:
                continue
            user_to_recommended_resources_list[username].append((lda_res_id, lda_value))
    print("store recommended resources")
    store_recommended_resources(user_to_recommended_resources_list, resource_to_go_words)


def clear_old_data():
    """ clear old recommended data
    """
    PropensityPreferences.clear()
    RecommendedResource.clear()


class Command(BaseCommand):
    help = "Make recommendations using LDA algorithms."

    def handle(self, *args, **options):
        clear_old_data()
        main()
