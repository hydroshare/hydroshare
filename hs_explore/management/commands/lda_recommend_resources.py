from collections import defaultdict
from datetime import date, timedelta
from hs_tracking.models import Variable
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import user_from_id, get_resource_by_shortkey
from django.core.management.base import BaseCommand
from hs_explore.models import ResourcePreferences, UserPreferences, OwnershipPreferences
from hs_explore.models import RecommendedResource, RecommendedUser, RecommendedGroup, \
    GroupPreferences, GroupPrefToPair, PropensityPrefToPair, PropensityPreferences, \
    UserInteractedResources, UserNeighbors
from nltk.corpus import stopwords
import string
import gensim
from gensim import corpora
from nltk.stem import PorterStemmer
from gensim.models import CoherenceModel
from operator import itemgetter
from hs_explore.models import LDAWord


def get_resource_to_subjects():
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
    resource_to_published = {}
    for res in BaseResource.objects.all():
        if res.raccess.published or res.raccess.public or res.raccess.discoverable:
            resource_to_published[res.short_id] = True
        else:
            resource_to_published[res.short_id] = False
    return resource_to_published


def get_users_interacted_resources(beginning, today):
    all_usernames = set()
    user_to_resources_set = defaultdict(set)
    triples = Variable.user_resource_matrix(beginning, today)
    for v in triples:
        username = v[0]
        res = v[1]
        all_usernames.add(username)
        user_to_resources_set[username].add(res)
    user_to_resources = defaultdict(list)
    for username, res_ids_set in user_to_resources_set.items():
        res_ids_list = list(res_ids_set)
        user_to_resources[username] = list(res_ids_set)
        user = user_from_id(username)
        res_list = []
        for res_id in res_ids_list:
            try:
                r = get_resource_by_shortkey(res_id)
                res_list.append(r)
            except:
                continue
        UserInteractedResources.interact(user, res_list)
    return user_to_resources, all_usernames


def filter_go_words(res_id, doc, resource_to_subjects, go_words, stop):
    exclude = set(string.punctuation)
    exclude.remove('_')
    ps = PorterStemmer()
    doc_words = set()
    doc_list = set()

    for w in doc.split(" "):
        doc_list.add(ps.stem(w))

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


def jaccard_sim(res_subs1, res_subs2):
    inter = len(res_subs1.intersection(res_subs2))
    union = len(res_subs1.union(res_subs2))
    if union == 0:
        return 0
    else:
        jac_sim = inter / float(union)
        return jac_sim


def store_user_preferences(user_to_go_words_freq):
    for username, go_word_to_freq in user_to_go_words_freq.items():
        user = user_from_id(username)
        prop_pref_subjects = []
        for go_word, freq in go_word_to_freq.items():
            prop_pref_subjects.append(('subject', go_word, freq))
        PropensityPreferences.prefer(user, 'Resource', prop_pref_subjects)
        PropensityPreferences.prefer(user, 'User', prop_pref_subjects)
        PropensityPreferences.prefer(user, 'Group', prop_pref_subjects)


def store_recommended_resources(user_to_recommended_resources_list, resource_to_go_words):
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
            recommended_go_words = resource_to_go_words[res_id]
            common_subjects = set.intersection(user_res_preferences_set,
                                                set(recommended_go_words))
            for cs in common_subjects:
                raw_cs = cs.replace("_", " ")
                r.relate('subject', raw_cs, user_res_pref_to_weight[cs])


def main():
    resource_to_abstract = get_resource_to_abstract()
    resource_to_subjects, all_subjects_list = get_resource_to_subjects()
    end_date = date(2018, 5, 31)
    start_date = end_date - timedelta(days=30)
    user_to_resources, all_usernames = get_users_interacted_resources(start_date, end_date)
    resource_to_published = get_resource_to_published()
    user_to_abstract_list = {}
    print("resource_to_go_words")
    resource_to_go_words = get_resource_to_go_words(resource_to_subjects, resource_to_abstract)

    print("user interacted at least 5 resources")
    for username, res_ids in user_to_resources.items():
        abstract_list = []
        for res_id in res_ids:
            if res_id in resource_to_abstract:
                abstract_list.append((res_id, resource_to_abstract[res_id]))
        if len(abstract_list) >= 5:
            user_to_abstract_list[username] = abstract_list

    user_to_filtered_abstracts = {}
    user_to_go_words_freq = {}
    for username, res_abstract_tuple_list in user_to_abstract_list.items():
        filtered_abstracts = []
        go_words_freq = {}
        for res_id, doc in res_abstract_tuple_list:
            if res_id not in resource_to_go_words:
                continue
            doc_words = resource_to_go_words[res_id]
            filtered_abstracts.append(list(doc_words))
            for doc_word in doc_words:
                if doc_word not in go_words_freq:
                    go_words_freq[doc_word] = 1
                else:
                    go_words_freq[doc_word] += 1
        user_to_filtered_abstracts[username] = filtered_abstracts
        user_to_go_words_freq[username] = go_words_freq

    print("store user preferences")
    store_user_preferences(user_to_go_words_freq)
    lda_users_recommendations = {}
    user_to_lda_cv = {}
    print("lda process")
    for username, filtered_abstracts in user_to_filtered_abstracts.items():
        user_to_recommend = {}
        if len(filtered_abstracts) > 5:
            dictionary = corpora.Dictionary(filtered_abstracts)
            doc_term_matrix = [dictionary.doc2bow(doc) for doc in filtered_abstracts]
            Lda = gensim.models.ldamodel.LdaModel
            ldamodel = Lda(doc_term_matrix, num_topics=5, id2word=dictionary, passes=50)
            x = ldamodel.show_topics(num_topics=5, num_words=10, formatted=False)
            coherence_model_lda = CoherenceModel(model=ldamodel, texts=filtered_abstracts,
                                                 dictionary=dictionary, coherence='c_v')
            coherence_lda = coherence_model_lda.get_coherence()
            user_to_lda_cv[username] = coherence_lda
            topics_words = [(tp[0], [wd[0] for wd in tp[1]]) for tp in x]
            user_resources = user_to_resources[username]

            for res_id, doc_words in resource_to_go_words.items():
                if resource_to_published[res_id]:
                    if res_id in user_resources:
                        continue
                    r = get_resource_by_shortkey(res_id)
                    if len(doc_words) < 3:
                        continue
                    doc_words_list = list(doc_words)
                    bow = dictionary.doc2bow(doc_words_list)
                    t = ldamodel.get_document_topics(bow)
                    topic_prob_dict = dict((x, y) for x, y in t)
                    for topic, words in topics_words:
                        topic_words_set = set(words)
                        topic_prob = 0
                        if topic in topic_prob_dict:
                            topic_prob = topic_prob_dict[topic]
                        jac_sim = jaccard_sim(doc_words, topic_words_set)
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
    ResourcePreferences.clear()
    UserPreferences.clear()
    GroupPreferences.clear()
    PropensityPreferences.clear()
    OwnershipPreferences.clear()
    UserInteractedResources.clear()
    UserNeighbors.clear()
    RecommendedResource.clear()
    RecommendedUser.clear()
    RecommendedGroup.clear()


class Command(BaseCommand):
    help = "Make recommendations using LDA algorithms."

    def handle(self, *args, **options):
        clear_old_data()
        main()
