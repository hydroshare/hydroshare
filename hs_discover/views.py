import json

from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.generic import TemplateView
from haystack.query import SearchQuerySet
from rest_framework.response import Response
from rest_framework.views import APIView
import time, datetime
from collections import namedtuple

DateRange = namedtuple('DateRange', ['start', 'end'])



def date_overlaps(searchdate):
    """
    Expectation is the user is filtering for dates and looking for any kind of overlap in date
    ranges of interest

    :return:
    """
    resource_temporal = DateRange(start=datetime.date(2010, 1, 1), end=datetime.date(2015, 1, 1))

    overlap = (searchdate.start < resource_temporal.start < searchdate.end) or (resource_temporal.start < searchdate.start < resource_temporal.end)
    return overlap


def queryBuilder():
    """

    :return:
    """


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
        start = time.time()

        #####################
        # TODO sub-endpoints
        #####################
        if request.GET.get('geo'):
            # geo = request.GET.get('geo')
            geodata = []

            sqs = SearchQuerySet().all()
            for result in sqs:
                pt = {}
                pt['short_id'] = result.short_id
                pt['title'] = result.title
                if 'box' in result.coverage_type:
                    pt['coverage_type'] = 'region'
                elif 'point' in result.coverage_type:
                    pt['coverage_type'] = 'point'
                else:
                    pt['coverage_type'] = ''
                if isinstance(result.north, (int, float)):
                    pt['north'] = result.north
                if isinstance(result.east, (int, float)):
                    pt['east'] = result.east
                if isinstance(result.northlimit, (int, float)):
                    pt['northlimit'] = result.northlimit
                if isinstance(result.southlimit, (int, float)):
                    pt['southlimit'] = result.southlimit
                if isinstance(result.eastlimit, (int, float)):
                    pt['eastlimit'] = result.eastlimit
                if isinstance(result.westlimit, (int, float)):
                    pt['westlimit'] = result.westlimit

                geodata.append(pt)
            return Response({
                'time': (time.time() - start),
                'geo': json.dumps(geodata)
            })

        if request.GET.get('datematch'):
            s1 = DateRange(start=datetime.date(2009, 1, 1), end=datetime.date(2013, 1, 1))
            s2 = DateRange(start=datetime.date(2003, 1, 1), end=datetime.date(2004, 1, 1))

        if request.GET.get('filterbuilder'):
            filterlimit = 15

            sqs = SearchQuerySet().facet('author')
            authors = sqs.facet_counts()['fields']['author'][:filterlimit]
            sqs = SearchQuerySet().facet('owner')
            owners = sqs.facet_counts()['fields']['owner'][:filterlimit]
            sqs = SearchQuerySet().facet('subject')
            subjects = sqs.facet_counts()['fields']['subject'][:filterlimit]
            sqs = SearchQuerySet().facet('contributor')
            contributors = sqs.facet_counts()['fields']['contributor'][:filterlimit]
            # sqs = SearchQuerySet().facet('type')
            # types = sqs.facet_counts()['fields']
            sqs = SearchQuerySet().facet('availability')
            availability = sqs.facet_counts()['fields']['availability'][:filterlimit]

            return Response({
                'time': (time.time() - start),
                'filterdata': json.dumps([authors, owners, subjects, contributors, availability])
            })

        #################
        # TODO Main query
        #################
        filtering = None
        if request.GET.get('filtering'):
            filtering = request.GET.get('filtering')

        cat = None
        if request.GET.get('cat'):
            cat = request.GET.get('cat')

        # TODO min/max handling eg exceed max pages
        pnum = 1
        if request.GET.get('pnum'):
            pnum = request.GET.get('pnum')
            pnum = max(1, int(pnum))

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

        if request.GET.get('filterby') and request.GET.get('filtercontent'):
            filterby = request.GET.get('filterby')
            filtercontent = request.GET.get('filtercontent')

            # for result in sqs:
            if filterby == 'subject':
                sqs = sqs.filter(subject=filtercontent)
            elif filterby == 'abstract':
                sqs = sqs.filter(abstract=filtercontent)
            elif filterby == 'author':
                sqs = sqs.filter(author=filtercontent)
            elif filterby == 'contributor':
                sqs = sqs.filter(contributor=filtercontent)
            elif filterby == 'owner':
                sqs = sqs.filter(owner=filtercontent)
            elif filterby == 'type':
                sqs = sqs.filter(type=filtercontent)

        resources = []

        pagelim = 40

        p = Paginator(sqs, pagelim)

        for result in p.page(pnum):
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
            'time': (time.time() - start),
            'resources': json.dumps(resources)
        })
