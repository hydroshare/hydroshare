# modeling of recommendation queries in SOLR using disjunction and boosts.
from haystack.query import SearchQuerySet, SQ
from pprint import pprint
import re


def find_resources_by_subjects(list):
    """
    Queries the subject field in SOLR without boost factors.

    :param list: an iterable of terms. Can be a QuerySet or Set

    The terms are in an iterable, e.g., a list or set, and represent subjects.  e.g.,
        find_resources_by_subjects([ 'water', 'nitrogen' ])
    says to look for terms "water" and "nitrogen", resulting in the Haystack query:
        SearchQuerySet.filter(SQ(subject='water') | SQ(subject='nitrogen'))
    """
    results = SearchQuerySet()
    # first add query terms
    query = None
    for subject in list:
        # Force exact to work in SOLR by adding trailing space if necessary 
        if query is None:
            query = SQ(subject__exact=subject)
        else:
            query = query | SQ(subject__exact=subject)
    results = results.filter(query)

    # THE FOLLOWING DOESN'T WORK PROPERLY because it asserts unscoped queries
    # -- connected via AND and not OR -- along with the boosts.
    # # now add boost factors
    # for subject in dict:
    #     boost = dict[subject]
    #     results = results.boost(subject, boost)

    return results
