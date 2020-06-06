from django.shortcuts import render
import json
from pprint import pprint
from django.shortcuts import render
from django.views.generic import TemplateView
from haystack.query import SearchQuerySet
from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.search_indexes import BaseResourceIndex
from pprint import pprint
from rest_framework.response import Response
import json
from rest_framework.views import APIView
from django.template.defaultfilters import date, time


class SearchView(TemplateView):

    def get(self, request, *args, **kwargs):
        return render(request, 'hs_discover/index.html', {
        })


class SearchAPI(APIView):

    def get(self, request, *args, **kwargs):

        sqs = SearchQuerySet().all()
        # sqs = SearchQuerySet().all().filter(short_id='ff889df950204b6195aeeffbbb7a1e68')
        if request.GET.get('searchtext'):
            searchtext = request.GET.get('searchtext')
            sqs = sqs.filter(content=searchtext).boost('keyword', 2.0)

        vocab = []

        # for result in list(sqs):
        #     print("FETCHING STORED JSON")
        #     stored = result.get_stored_fields()
        #     js = stored['json']
        #     print(js)
        #     print("INTERPRETING STORED JSON")
        #     foo = json.loads(js)
        #     pprint(foo)
        #
        # print('new debug')
        # for result in sqs:
        #     if result.title:
        #         vocab.extend(result.title.split(' '))
        #     if result.subject:
        #         vocab.extend(result.subject)

        vocab = [x for x in vocab if len(x) > 2]
        vocab = list(set(vocab))
        vocab = sorted(vocab)

        resources = []
        for result in sqs:
            resources.append({
                "name": result.title,
                "link": result.absolute_url,
                "availability": result.availability,
                "type": result.resource_type_exact,
                "author": result.author,
                "author_link": result.author_url,
                "abstract": result.abstract,
                "created": date(result.created, "M d, Y") + " at " + time(result.created),
                "modified": date(result.modified, "M d, Y") + " at " + time(result.modified)
            })

        itemcount = len(resources)
        resources = json.dumps(resources)

        if request.GET.get('mode') == 'advanced':
            return render(request, 'hs_discover/advanced_search.html')
        else:
            return Response({
                'resources': resources,
                'vocab': vocab,
            })
