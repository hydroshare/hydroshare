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
    stored = result.get_stored_fields()
    try:
        start_date = stored['start_date'].isoformat()
        end_date = stored['end_date'].isoformat()
    except:
        start_date = ''
        end_date = ''

    creator = 'none'
    if 'creator_exact' in stored and stored['creator_exact'] is not None:
        try:
            creator = stored['creator_exact'][0]
        except:
            pass

    owner = 'none'
    if 'owner' in stored and stored['owner'] is not None:
        try:
            owner = stored['owner'][0]
        except:
            pass

    return json.dumps({
        "title": stored['title'],
        "link": stored['absolute_url'],
        "availability": stored['availability'],
        "availabilityurl": "/static/img/{}.png".format(stored['availability'][0]),
        "type": stored['resource_type'],
        "author": str(stored['author']),
        "creator": creator,
        "author_link": stored['author_url'],
        "owner": owner,
        "abstract": stored['abstract'],
        "subject": stored['subject'],
        "created": stored['created'].isoformat(),
        "modified": stored['modified'].isoformat(),
        "shareable": stored['shareable'],
        "start_date": start_date,
        "end_date": end_date,
        "short_id": stored['short_id']
    })


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
