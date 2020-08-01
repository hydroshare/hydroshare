import json

from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.generic import TemplateView
from haystack.query import SearchQuerySet
from rest_framework.response import Response
from rest_framework.views import APIView


class SearchView(TemplateView):

    def get(self, request, *args, **kwargs):
        return render(request, 'hs_discover/index.html', {})


class SearchAPI(APIView):

    def get(self, request, *args, **kwargs):
        """
        Primary endpoint for retrieving resources via the index
        :param request:
        :param args:
        :param kwargs:
        :return:
                Values should never be empty string or None, instead return string "None" with str() call
                "title":
                "link":
                "availability": list value, js will parse JSON as Array
                "availabilityurl":
                "type": single value, pass a string to REST client
                "author": single value, pass a string to REST client
                "contributor": single value, pass a string to REST client
                "author_link":
                "owner": single value, pass a string to REST client
                "abstract":
                "subject":
                "created":
                "modified":
                "start_date":
                "end_date":
        """
        sqs = SearchQuerySet().all()

        if request.GET.get('q'):
            q = request.GET.get('q')
            sqs = sqs.filter(content=q)  # .boost('keyword', 2.0)

        # vocab = []  # will be populated with autocomplete terms from resource
        # vocab = [x for x in vocab if len(x) > 2]
        # vocab = list(set(vocab))
        # vocab = sorted(vocab)

        resources = []

        p = Paginator(sqs, max(len(sqs), 1))

        for result in p.page(1):
            try:
                start_date = result.start_date.isoformat()
                end_date = result.end_date.isoformat()
            except:
                start_date = ''
                end_date = ''

            contributor = 'None'
            owner = 'None'
            author_link = None  # Send None to avoid anchor render

            if result.author:
                author_link = result.author_url

            if result.creator is not None:
                try:
                    contributor = result.creator[0]
                except:
                    print("Missing contributor: {}".format(result.short_id))

            if result.owner is not None:
                try:
                    owner = result.owner[0]
                except:
                    print("Missing owner: {}".format(result.short_id))

            resources.append({
                "title": result.title,
                "link": result.absolute_url,
                "availability": result.availability,
                "availabilityurl": "/static/img/{}.png".format(result.availability[0]),
                "type": result.resource_type_exact,
                "author": str(result.author),
                "contributor": contributor,
                "author_link": author_link,
                "owner": owner,
                "abstract": result.abstract,
                "subject": result.subject,
                "created": result.created.isoformat(),
                "modified": result.modified.isoformat(),
                "shareable": True,
                "start_date": start_date,
                "end_date": end_date,
                "short_id": result.short_id
            })

        return Response({
            'resources': json.dumps(resources),
        })
