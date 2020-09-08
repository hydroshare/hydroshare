from django.contrib.auth.models import User
from hs_core.models import BaseResource
from hs_tracking.models import Variable
from django.db.models import Max
from collections import defaultdict
from hs_core.hydroshare.utils import user_from_id, get_resource_by_shortkey
from hs_explore.models import RecommendedResource, UserPreferences, Status
import string
from nltk.stem import WordNetLemmatizer
from hs_explore.models import LDAStopWord
from hs_access_control.models import PrivilegeCodes
from hs_csdms.models import CSDMSName
from hs_odm2.models import ODM2Variable


class LDAKeepWords():
    def __iter__(self):
        csdms_names = list(CSDMSName.list_all_names())
        splitted_names = set()
        keep_words_set = set()
        for csdms_name in csdms_names:
            if len(csdms_name) <= 1:
                continue
            tokens = csdms_name.split(" ")
            keep_words_set.add(csdms_name)
            splitted_names.update(tokens)

        for splitted_name in splitted_names:
            if len(splitted_name) <= 1:
                continue
            keep_words_set.add(splitted_name)

        odm2_list = list(ODM2Variable.all())
        for odm2 in odm2_list:
            tokens = odm2.split(' - ')
            new_string = tokens[0]
            if len(tokens) > 1:
                new_string = tokens[1] + ' ' + tokens[0]
            if len(new_string) > 1:
                keep_words_set.add(new_string.lower())

        for i in list(keep_words_set):
            yield i


def resource_owners():
    """ return a dictionary representing resource ownership """
    return resource_privileges(PrivilegeCodes.OWNER)


def resource_editors():
    """ return a dictionary representing resource editable relationship """
    return resource_privileges(PrivilegeCodes.CHANGE)


def resource_privileges(privilege_code):
    """:privilege_code, a specific PriviledgCode to query
       :return user_to_resources, a dictionary of each user to a resources list
       that satifies the given privilege_code
    """
    user_ids = User.objects.all().values_list("pk", flat=True)
    resources = BaseResource.objects.filter(r2urp__user__id__in=user_ids,
                                            r2urp__privilege=privilege_code)
    records = resources.values_list("r2urp__user__username", "short_id")
    sorted_records = records.order_by("r2urp__user")
    user_to_resources = defaultdict(list)
    for record in sorted_records.all():
        username = record[0]
        res_id = record[1]
        user_to_resources[username].append(res_id)
    return user_to_resources


def user_resource_matrix(fromdate, todate):
    """ return a list of (username, resource_id, last_access_timestamp), which
        shows the latest time that a user accessed a resource during the given
        period.
        :param fromdate (date type), the start date of the time period
        :param todate (date, type), the end date of the time period
    """
    user_ids = User.objects.filter(
        visitor__session__variable__timestamp__gte=fromdate,
        visitor__session__variable__timestamp__lte=todate)\
            .distinct().values_list("pk", flat=True)

    res_ids = BaseResource.objects.filter(
            variable__timestamp__gte=fromdate,
            variable__timestamp__lte=todate,
            variable__session__visitor__user__id__in=user_ids).values_list("pk", flat=True)

    latest = Variable.objects.filter(
                            resource__id__in=res_ids,
                            session__visitor__user__id__in=user_ids,
                            timestamp__gte=fromdate,
                            timestamp__lte=todate)
    grouped = latest.values('session__visitor__user__username', 'resource__short_id')
    grouped_with_latest = grouped.annotate(latest=Max('timestamp'))
    return grouped_with_latest.values_list('session__visitor__user__username', 'resource__short_id', 'latest')


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
    user_to_resources = defaultdict(list)
    triples = user_resource_matrix(beginning, today)
    for v in triples:
        username = v[0]
        if username == 'admin' or '-admin' in username:
            continue
        res = v[1]
        all_usernames.add(username)
        user_to_resources[username].append(res)
    return user_to_resources, all_usernames


def filter_keep_words(res_id, abstract, resource_subjects, keep_words, stop_words):
    """ return a given resource's keep words set
        :param res_id, resource id
        :param abstract, the given resource's abstract
        :param resource_subjects, the given resource subjects set
        :param keep_words, a set of all valid keep words
        :param stop_words, a set of all valid stop words
    """
    exclude = set(string.punctuation)
    exclude.remove('_')
    lemmatizer = WordNetLemmatizer()
    resource_keep_words = set()
    abstract_token_list = set()

    for w in abstract.split(" "):
        abstract_token_list.add(lemmatizer.lemmatize(w))

    for keep_word in keep_words:
        if " " in keep_word:
            if keep_word in abstract and keep_word not in stop_words:
                bigram_name = keep_word.replace(" ", "_")
                resource_keep_words.add(bigram_name)
        else:
            if keep_word in abstract_token_list and keep_word not in stop_words:
                resource_keep_words.add(keep_word)

    if len(resource_subjects) > 0:
        for sub in resource_subjects:
            if sub not in stop_words:
                resource_keep_words.add(sub)

    return resource_keep_words


def get_resource_to_keep_words(resource_to_subjects, resource_to_abstract):
    """ map each resource to its keep words set
        :param resource_to_subjects, a dictionary maps each resource to its subjects
        :param resource_to_abstract, a dictionary maps each resource to its abstract
    """
    resource_to_keep_words = {}
    stop_words = set()
    keep_words = set()
    for word in LDAStopWord.objects.all():
        stop_words.add(word.value)

    lda_keep_words = LDAKeepWords()
    for lda_keep_word in lda_keep_words:
        keep_words.add(lda_keep_word)

    for res_id, res_abs in resource_to_abstract.items():
        resource_subjects = set()
        if res_id in resource_to_subjects:
            resource_subjects = resource_to_subjects[res_id]
        res_keep_words = filter_keep_words(res_id, res_abs, resource_subjects, keep_words, stop_words)
        if len(res_keep_words) < 3:
            continue
        resource_to_keep_words[res_id] = res_keep_words
    return resource_to_keep_words


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
        prop_pref_keywords = {}
        for keep_word, freq in keep_word_to_freq.items():
            prop_pref_keywords[keep_word] = str(freq)
        UserPreferences.prefer(user, 'Resource', prop_pref_keywords)


def store_recommended_resources(user_to_recommended_resources_list, resource_to_keep_words):
    """ store the recommended results for each qualified user
        :param user_to_recommended_resources_list, a dictionary maps each user to a list
         of resources' ids recommended to the user.
        :param resource_to_keep_words, a dictionary maps each resource to its keep words
    """
    for username, recommend_resources_list in user_to_recommended_resources_list.items():
        user = user_from_id(username)
        user_preferences = UserPreferences.objects.get(user=user, pref_for='Resource')
        user_keywords_preferences = user_preferences.preferences
        user_res_preferences_set = set()
        user_res_pref_to_weight = {}
        for keyword, frequency in list(user_keywords_preferences.items()):
            user_res_preferences_set.add(keyword)
            user_res_pref_to_weight[keyword] = frequency

        for res_id, sim in recommend_resources_list:
            recommended_res = get_resource_by_shortkey(res_id)
            recommended_keep_words = resource_to_keep_words[res_id]
            common_subjects = set.intersection(user_res_preferences_set,
                                                set(recommended_keep_words))
            recommended_resource_keep_words = {}
            for cs in common_subjects:
                raw_cs = cs.replace("_", " ")
                recommended_resource_keep_words[raw_cs] = str(user_res_pref_to_weight[cs])

            RecommendedResource.recommend(user,
                                          recommended_res,
                                          'Propensity',
                                          round(sim, 4),
                                          Status.STATUS_NEW,
                                          recommended_resource_keep_words)


def clear_old_data():
    """ clear old recommended data
    """
    print("clear old data")
    UserPreferences.clear()
    RecommendedResource.clear()
