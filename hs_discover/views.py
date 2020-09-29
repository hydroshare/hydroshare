import datetime
import json
import logging
import time
from collections import namedtuple

from django.conf import settings
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from haystack.query import SearchQuerySet
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

DateRange = namedtuple('DateRange', ['start', 'end'])


class SearchView(TemplateView):

    def get(self, request, *args, **kwargs):
        maps_key = settings.MAPS_KEY if hasattr(settings, 'MAPS_KEY') else ''
        return render(request, 'hs_discover/index.html', {'maps_key': maps_key})


class SearchAPI(APIView):

    def __init__(self, **kwargs):
        super(SearchAPI, self).__init__(**kwargs)
        self.filterlimit = 20
        self.perpage = 40

    def get(self, request, *args, **kwargs):
        """
        Primary endpoint for retrieving resources via the index
        Values should never be empty string or python None, instead return string "None" with str() call
        "availability": list value, js will parse JSON as Array
        "availabilityurl": single value, pass a string to REST client
        "type": single value, pass a string to REST client
        "author": single value, pass a string to REST client first author
        "creator: authors,
                The reason for the weird name is the DataOne standard. The metadata was designed to be compliant
                with DataOne standards. These standards do not contain an author field. Instead, the creator field
                represents authors.
        "contributor": list value, js will parse JSON as Array
        "owner": list value, js will parse JSON as Array
        "subject": list value, js will parse JSON as Array
        "coverage_type": list point, period, ...
        """
        start = time.time()

        sqs = SearchQuerySet().all()

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
        if request.GET.get('asc', '-1'):
            asc = request.GET.get('asc')

        sort = 'modified'
        if request.GET.get('sort'):
            sort = request.GET.get('sort')
        sort = sort if asc == '1' else '-{}'.format(sort)

        if request.GET.get('q'):
            q = request.GET.get('q')
            sqs = sqs.filter(content=q)  # .boost('keyword', 2.0)

        try:
            qs = request.query_params
            filters = json.loads(qs.get('filter'))
            # filter values expect lists, for example discoverapi/?filter={"owner":["Firstname Lastname"]}
            if filters.get('author'):
                sqs = sqs.filter(author__in=filters['author'])
            if filters.get('owner'):
                sqs = sqs.filter(owner__in=filters['owner'])
            if filters.get('subject'):
                sqs = sqs.filter(subject__in=filters['subject'])
            if filters.get('contributor'):
                sqs = sqs.filter(contributor__in=filters['contributor'])
            if filters.get('type'):
                sqs = sqs.filter(resource_type__in=list(filters['type']))
            if filters.get('availability'):
                sqs = sqs.filter(availability__in=filters['availability'])
            if filters.get('geofilter'):
                sqs = sqs.filter(north__range=[-90, 90])  # return resources with geographic data
            if filters.get('date'):
                try:
                    datefilter = DateRange(start=datetime.datetime.strptime(filters['date'][0], '%Y-%m-%d'),
                                           end=datetime.datetime.strptime(filters['date'][1], '%Y-%m-%d'))

                    # (datefilter.start < start_date < datefilter.end) or (start_date < datefilter.start)
                    sqs = sqs.exclude(start_date__gt=datefilter.end).exclude(end_date__lt=datefilter.start)
                except ValueError as date_ex:
                    return JsonResponse({'message': 'Filter date parsing error expecting String %Y-%m-%d : {}'
                                        .format(str(date_ex)), 'received': request.query_params}, status=400)
                except Exception as gen_date_ex:
                    return JsonResponse({'message': 'Filter date parsing error expecting two date string values : {}'
                                        .format(str(gen_date_ex)), 'received': request.query_params}, status=400)
        except TypeError as type_ex:
            pass  # no filters passed "the JSON object must be str, bytes or bytearray not NoneType"

        except json.JSONDecodeError as parse_ex:
            return JsonResponse({'message': 'Filter JSON parsing error - {}'.format(str(parse_ex)),
                                 'received': request.query_params}, status=400)

        except Exception as gen_ex:
            logger.warning('hs_discover API - {}: {}'.format(type(gen_ex), str(gen_ex)))
            return JsonResponse({'message': '{}'.format('{}: query error. Contact a server administrator.'
                                                        .format(type(gen_ex)))}, status=520)

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
            creator = 'None'

            if result.creator:
                creator = result.creator

            if result.author:
                author_link = result.author_url
                author = str(result.author)
            else:
                if result.authors:
                    author = result.authors[0]
                elif result.organization:
                    author = result.organization
                else:
                    author = 'None'

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
            pt = ''  # pass empty string for the frontend to ensure the attribute exists but can be evaluated for empty
            try:
                if 'box' in result.coverage_type:
                    pt = {'short_id': result.short_id, 'title': result.title, 'coverage_type': 'box'}
                elif 'point' in result.coverage_type:
                    pt = {'short_id': result.short_id, 'title': result.title, 'coverage_type': 'point'}

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
                pass  # HydroShare production contains dirty data, this handling is in place, until data cleaned
            resources.append({
                "title": result.title,
                "link": result.absolute_url,
                "availability": result.availability,
                "availabilityurl": "/static/img/{}.png".format(result.availability[0]),
                "type": result.resource_type_exact,
                "author": author,
                "authors": creator,
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

        if sort == 'title':
            resources = sorted(resources, key=lambda k: k['title'].lower())
        elif sort == '-title':
            resources = sorted(resources, key=lambda k: k['title'].lower(), reverse=True)

        return JsonResponse({
            'time': (time.time() - start),
            'resources': json.dumps(resources),
            'geodata': json.dumps(geodata),
            'rescount': p.count,
            'pagecount': p.num_pages,
            'perpage': self.perpage
        }, status=200)
