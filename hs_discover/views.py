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
                "contributor": list value, js will parse JSON as Array
                "author_link":
                "owner": list value, js will parse JSON as Array
                "abstract":
                "subject": list value, js will parse JSON as Array
                "created":
                "modified":
                "start_date":
                "end_date":
                "coverage_type": list point, period, ...

        """

        if request.GET.get('geo'):
            geo = request.GET.get('geo')
            geodata = []
            sqs = SearchQuerySet().all()
            for result in sqs:
                # TODO validation and client error handling
                # TODO getter for SearchResult Abstract / Interface?
                if filter == 'subject':
                    filteritem += result.subject
                elif filter == 'abstract':
                    filteritem.append(result.abstract)
                elif filter == 'author':
                    filteritem.append(result.author)
                elif filter == 'contributor':
                    filteritem.append(result.creator)
                elif filter == 'owner':
                    filteritem += result.owner

                # TODO order by count as indicator of usefulness in autocomplete
                # TODO can integrate with Alva future Recommendations work here

            return Response({
                'filter': json.dumps(list(set(filteritem))),
            })

        if request.GET.get('filter'):
            filter = request.GET.get('filter')
            filteritem = []
            sqs = SearchQuerySet().all()
            for result in sqs:
                # TODO validation and client error handling
                # TODO getter for SearchResult Abstract / Interface?
                if filter == 'subject':
                    filteritem += result.subject
                elif filter == 'abstract':
                    filteritem.append(result.abstract)
                elif filter == 'author':
                    filteritem.append(result.author)
                elif filter == 'contributor':
                    filteritem.append(result.creator)
                elif filter == 'owner':
                    filteritem += result.owner

                # TODO order by count as indicator of usefulness in autocomplete
                # TODO can integrate with Alva future Recommendations work here

            return Response({
                'filter': json.dumps(list(set(filteritem))),
            })

        filtering = None
        if request.GET.get('filtering'):
            filtering = request.GET.get('filtering')

        cat = None
        if request.GET.get('cat'):
            cat = request.GET.get('cat')

        asc = '-1'
        if request.GET.get('asc'):
            asc = request.GET.get('asc')

        sort = 'modified'
        if request.GET.get('sort'):
            sort = request.GET.get('sort')
        sort = sort if asc == '1' else '-{}'.format(sort)

        sqs = SearchQuerySet().all().order_by(sort)

        if request.GET.get('q'):
            q = request.GET.get('q')
            sqs = sqs.filter(content=q).order_by(sort)  # .boost('keyword', 2.0)

        resources = []

        pagelim = 40
            # pagelim = max(len(sqs), 1)

        p = Paginator(sqs, pagelim)

        for result in p.page(1):
            try:
                start_date = result.start_date.isoformat()
                end_date = result.end_date.isoformat()
            except:
                start_date = ''
                end_date = ''

            contributor = 'None'  # contributor is actually a list and can have multiple values
            owner = 'None'  # owner is actually a list and can have multiple values
            author_link = None  # Send None to avoid anchor render

            if result.author:
                author_link = result.author_url

            if result.creator is not None:
                try:
                    contributor = result.creator
                except:
                    print("Missing contributor: {}".format(result.short_id))

            if result.owner is not None:
                try:
                    owner = result.owner
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
                "start_date": start_date,
                "end_date": end_date,
                "short_id": result.short_id
            })

        return Response({
            'resources': json.dumps(resources),
        })
