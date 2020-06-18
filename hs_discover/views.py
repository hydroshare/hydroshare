import json

from django.shortcuts import render
from django.template.defaultfilters import date, time
from django.views.generic import TemplateView
from haystack.query import SearchQuerySet
from rest_framework.response import Response
from rest_framework.views import APIView


class SearchView(TemplateView):

    def get(self, request, *args, **kwargs):
        return render(request, 'hs_discover/index.html', {})


class SearchAPI(APIView):

    def get(self, request, *args, **kwargs):

        sqs = SearchQuerySet().all()
        if request.GET.get('searchtext'):
            searchtext = request.GET.get('searchtext')
            sqs = sqs.filter(content=searchtext).boost('keyword', 2.0)

        vocab = []  # will be populated with autocomplete terms from resource
        vocab = [x for x in vocab if len(x) > 2]
        vocab = list(set(vocab))
        vocab = sorted(vocab)

        resources = []

        for result in sqs:
            resources.append({
                "name": result.title,
                "link": result.absolute_url,
                "availability": result.availability,
                "availabilityurl": "/static/img/{}.png".format(result.availability[0]),
                "type": result.resource_type_exact,
                "author": result.author,
                "author_link": result.author_url,
                "abstract": result.abstract,
                "created": date(result.created, "M d, Y") + " at " + time(result.created),
                "modified": date(result.modified, "M d, Y") + " at " + time(result.modified)
            })

        return Response({
            'resources': json.dumps(resources),
            'vocab': vocab,
        })
