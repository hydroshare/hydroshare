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


class SearchView(TemplateView):

    def get(self, request, *args, **kwargs):
        return render(request, 'hs_discover/index.html', {})


class SearchAPI(APIView):

    def __init__(self, **kwargs):
        super(SearchAPI, self).__init__(**kwargs)
        self.filterlimit = 20
        self.perpage = 35

    def get(self, request, *args, **kwargs):
        """
        Primary endpoint for retrieving resources via the index
        :param request:
        :param args:
        :param kwargs:
        :return:
                Values should never be empty string or None, instead return string "None" with str() call
                "availability": list value, js will parse JSON as Array
                "availabilityurl":
                "type": single value, pass a string to REST client
                "author": single value, pass a string to REST client first author
                "creator: authors,
                "contributor": list value, js will parse JSON as Array
                "owner": list value, js will parse JSON as Array
                "subject": list value, js will parse JSON as Array
                "coverage_type": list point, period, ...

        The reason for the weird name is the DataOne standard. The metadata was designed to be compliant with DataOne
        standards. These standards do not contain an author field. Instead, the creator field represents authors.
        """
        start = time.time()

        sqs = SearchQuerySet().all()

        if request.GET.get('geo'):
            geodata = []

            for result in sqs:
                try:
                    pt = {'short_id': result.short_id, 'title': result.title}
                    if 'box' in result.coverage_type:
                        pt['coverage_type'] = 'region'
                    elif 'point' in result.coverage_type:
                        pt['coverage_type'] = 'point'
                    else:
                        continue
                except TypeError:
                    continue

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

        if request.GET.get('filterbuilder'):
            sqs = SearchQuerySet().facet('author')
            authors = sqs.facet_counts()['fields']['author'][:self.filterlimit]
            sqs = SearchQuerySet().facet('owner')
            owners = sqs.facet_counts()['fields']['owner'][:self.filterlimit]
            sqs = SearchQuerySet().facet('subject')
            subjects = sqs.facet_counts()['fields']['subject'][:self.filterlimit]
            sqs = SearchQuerySet().facet('contributor')
            contributors = sqs.facet_counts()['fields']['contributor'][:self.filterlimit]
            sqs = SearchQuerySet().facet('resource_type')
            types = sqs.facet_counts()['fields']['resource_type'][:self.filterlimit]
            sqs = SearchQuerySet().facet('availability')
            availability = sqs.facet_counts()['fields']['availability'][:self.filterlimit]

            return Response({
                'time': (time.time() - start),
                'filterdata': json.dumps([authors, owners, subjects, contributors, types, availability])
            })

        asc = '-1'
        if request.GET.get('asc'):
            asc = request.GET.get('asc')

        sort = 'modified'
        if request.GET.get('sort'):
            sort = request.GET.get('sort')
        sort = sort if asc == '1' else '-{}'.format(sort)

        if request.GET.get('q'):
            q = request.GET.get('q')
            sqs = sqs.filter(content=q)  # .boost('keyword', 2.0)

        if request.GET.get('filterby'):
            filterby = request.GET.get('filterby')
            try:
                filters = json.loads(filterby)
                if filters['author']:
                    sqs = sqs.filter(author__in=filters['author'])
                if filters['owner']:
                    for owner in filters['owner']:
                        sqs = sqs.filter_or(owner__in=owner)
                if filters['subject']:
                    sqs = sqs.filter(subject__in=filters['subject'])
                if filters['contributor']:
                    sqs = sqs.filter_or(contributor__in=filters['contributor'])
                if filters['type']:
                    sqs = sqs.filter(resource_type__in=list(filters['type']))
                if filters['availability']:
                    sqs = sqs.filter(availability__in=filters['availability'])
                if filters['uid']:
                    sqs = sqs.filter(short_id__in=filters['uid'])
                if filters['geofilter']:
                    sqs = sqs.filter(north__lte='0')
                    sqs = sqs.filter_or(north__gte='0')
                if filters['date']:
                    # (searchdate.start < resource_temporal.start < searchdate.end)
                    # or (resource_temporal.start < searchdate.start < resource_temporal.end)
                    try:
                        datefilter = DateRange(start=datetime.datetime.strptime(filters['date'][0], '%Y-%m-%d'),
                                               end=datetime.datetime.strptime(filters['date'][1], '%Y-%m-%d'))
                        sqs = sqs.filter(start_date__gte=datefilter.start).filter_and(start_date__lte=datefilter.end)

                    except ValueError as e:
                        print('Not all data information provided or invalid value sent - {}'.format(e))

            except Exception as ex:
                print('Invalid filter data {} - {}'.format(filterby, ex))

        sqs = sqs.order_by(sort)

        resources = []

        p = Paginator(sqs, self.perpage)

        pnum = 1
        if request.GET.get('pnum'):
            pnum = request.GET.get('pnum')
            pnum = max(1, int(pnum))
            pnum = min(pnum, p.num_pages)

        geodata = []

        for result in p.page(pnum):
            contributor = 'None'  # contributor is actually a list and can have multiple values
            owner = 'None'  # owner is actually a list and can have multiple values
            author_link = None  # Send None to avoid anchor render

            if result.author:
                author_link = result.author_url

            if result.contributor is not None:
                try:
                    contributor = result.contributor
                except:
                    pass

            if result.owner is not None:
                try:
                    owner = result.owner
                except:
                    pass
            pt = None
            try:
                pt = {'short_id': result.short_id, 'title': result.title}
                if 'box' in result.coverage_type:
                    pt['coverage_type'] = 'region'
                elif 'point' in result.coverage_type:
                    pt['coverage_type'] = 'point'
                else:
                    continue
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
            except:
                pass

            resources.append({
                "title": result.title,
                "link": result.absolute_url,
                "availability": result.availability,
                "availabilityurl": "/static/img/{}.png".format(result.availability[0]),
                "type": result.resource_type_exact,
                "author": str(result.author),
                "authors": result.creator,
                "contributor": contributor,
                "author_link": author_link,
                "owner": owner,
                "abstract": result.abstract,
                "subject": result.subject,
                "created": result.created.isoformat(),
                "modified": result.modified.isoformat(),
                "short_id": result.short_id,
                "geo": pt
            })
        # gids = [x['short_id'] for x in geodata]
        # resources = [x for x in resources if x['short_id'] in gids]

        if sort == 'title':
            resources = sorted(resources, key=lambda k: k['title'].lower())
        elif sort == '-title':
            resources = sorted(resources, key=lambda k: k['title'].lower(), reverse=True)

        return Response({
            'time': (time.time() - start),
            'resources': json.dumps(resources),
            'geodata': json.dumps(geodata),
            'rescount': p.count,
            'pagecount': p.num_pages,
            'perpage': self.perpage
        })
