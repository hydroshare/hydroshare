"""
This prints the state of a facet query.
It is used for debugging the faceting system.
"""

from django.core.management.base import BaseCommand
from haystack.query import SearchQuerySet
from django.core.paginator import Paginator
import json
from pprint import pprint


def generate_json(result):
    solr = result.get_stored_fields()

    # assign title and url values to the object
    json_obj['short_id'] = solr['short_id']
    json_obj['title'] = solr['title']
    json_obj['resource_type'] = solr['resource_type']

    json_obj['get_absolute_url'] = solr['absolute_url']
    json_obj['first_author'] = solr['author']

    if solr['author_url']:
        json_obj['first_author_url'] = solr['author_url']

    # iterate over all the coverage values
    if solr['coverage'] is not None:
        for coverage in solr['coverage']:
            json_coverage = json.loads(coverage)
            if 'east' in json_coverage:
                json_obj['coverage_type'] = 'point'
                json_obj['east'] = json_coverage['east']
                json_obj['north'] = json_coverage['north']
            elif 'northlimit' in json_coverage:
                json_obj['coverage_type'] = 'box'
                json_obj['northlimit'] = json_coverage['northlimit']
                json_obj['eastlimit'] = json_coverage['eastlimit']
                json_obj['southlimit'] = json_coverage['southlimit']
                json_obj['westlimit'] = json_coverage['westlimit']
            # else, skip
            else:
                continue

    # encode object to JSON string format
    return json.dumps(json_obj)


# mark the last value to omit trailing JSON comma
def stream_signal_last(sqs):
    iterable = iter(sqs)
    ret_var = next(iterable)
    for val in iterable:
        yield False, ret_var
        ret_var = val
    yield True, ret_var


def stream_sqs(sqs):
    yield "[\n"
    for lastone, s in stream_signal_last(sqs):
        if not lastone:
            yield (generate_json(s) + ',')
        else:
            yield generate_json(s)
    yield "]\n"


def test_stream_query(rid=None):
    # this tests that the stream query is working properly. 
    if rid is not None:
        sqs = SearchQuerySet().all().filter(short_id=rid)
    else:
        sqs = SearchQuerySet().all()

    output = ""
    for result in stream_sqs(sqs):
        output += result

    return output


class Command(BaseCommand):
    help = "Print debugging information about logical files."

    def add_arguments(self, parser):
        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):
        if options['resource_ids']:
            for rid in options['resource_ids']:
                result = test_stream_query(rid)
                print(result)
                print("loading json...")
                json.loads(result)
                print("...done")
        else:
            result = test_stream_query()
            # print(result)
            print("loading json...")
            json.loads(result)
            print("...done")
