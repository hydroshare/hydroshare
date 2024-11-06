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
from itertools import groupby
from haystack.query import SearchQuerySet, SQ
from haystack.inputs import Exact
from rest_framework.views import APIView
from hs_core.discovery_parser import ParseSQ

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
        "authors": list value, one for each author.
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

        if request.GET.get('q'):
            q = request.GET.get('q')
            parser = ParseSQ(handle_fields=True, handle_logic=True)
            sq = parser.parse(q)
            sqs = sqs.filter(sq)

        try:
            qs = request.query_params
            filters = json.loads(qs.get('filter'))
            # filter values expect lists, for example discoverapi/?filter={"owner":["Firstname Lastname"]}
            if filters.get('author') and len(filters['author']) > 0:
                for k, authortype in enumerate(filters['author']):
                    if k == 0:
                        phrase = SQ(author=Exact(authortype))
                    else:
                        phrase = phrase | SQ(author=Exact(authortype))
                sqs = sqs.filter(phrase)

            if filters.get('owner') and len(filters['owner']) > 0:
                for k, ownertype in enumerate(filters['owner']):
                    if k == 0:
                        phrase = SQ(owner=Exact(ownertype))
                    else:
                        phrase = phrase | SQ(owner=Exact(ownertype))
                sqs = sqs.filter(phrase)

            if filters.get('subject') and len(filters['subject']) > 0:
                for k, subjtype in enumerate(filters['subject']):
                    if k == 0:
                        phrase = SQ(subject=Exact(subjtype))
                    else:
                        phrase = phrase | SQ(subject=Exact(subjtype))
                sqs = sqs.filter(phrase)

            if filters.get('contributor') and len(filters['contributor']) > 0:
                for k, contribtype in enumerate(filters['contributor']):
                    if k == 0:
                        phrase = SQ(contributor=Exact(contribtype))
                    else:
                        phrase = phrase | SQ(contributor=Exact(contribtype))
                sqs = sqs.filter(phrase)

            if filters.get('type') and len(filters['type']) > 0:
                for k, restype in enumerate(filters['type']):
                    if k == 0:
                        phrase = SQ(content_type=Exact(restype))
                    else:
                        phrase = phrase | SQ(content_type=Exact(restype))
                sqs = sqs.filter(phrase)

            if filters.get('availability') and len(filters['availability']) > 0:
                for k, availtype in enumerate(filters['availability']):
                    if k == 0:
                        phrase = SQ(availability=Exact(availtype))
                    else:
                        phrase = phrase | SQ(availability=Exact(availtype))
                sqs = sqs.filter(phrase)

            if filters.get('geofilter'):
                sqs = sqs.filter(north__range=[-90, 90])  # return resources with geographic data

            if filters.get('date'):
                try:
                    datefilter = DateRange(start=datetime.datetime.strptime(filters['date'][0], '%Y-%m-%d'),
                                           end=datetime.datetime.strptime(filters['date'][1], '%Y-%m-%d'))

                    # restrict to entries with dates
                    sqs = sqs.filter(start_date__gt=datetime.datetime.strptime('1900-01-01', '%Y-%m-%d'))\
                        .filter(end_date__lte=datetime.datetime.strptime(datetime.date.today().isoformat(), '%Y-%m-%d'))

                    # filter out entries that don't fall in specified range
                    sqs = sqs.exclude(start_date__gt=datefilter.end).exclude(end_date__lt=datefilter.start)

                except ValueError as date_ex:
                    return JsonResponse({'message': 'Filter date parsing error expecting String %Y-%m-%d : {}'
                                        .format(str(date_ex)), 'received': request.query_params}, status=400)
                except Exception as gen_date_ex:
                    return JsonResponse({'message': 'Filter date parsing error expecting two date string values : {}'
                                        .format(str(gen_date_ex)), 'received': request.query_params}, status=400)
        except TypeError:
            pass  # no filters passed "the JSON object must be str, bytes or bytearray not NoneType"

        except json.JSONDecodeError as parse_ex:
            return JsonResponse({'message': 'Filter JSON parsing error - {}'.format(str(parse_ex)),
                                 'received': request.query_params}, status=400)

        except Exception as gen_ex:
            logger.warning('hs_discover API - {}: {}'.format(type(gen_ex), str(gen_ex)))
            return JsonResponse({'message': '{}'.format('{}: query error. Contact a server administrator.'
                                                        .format(type(gen_ex)))}, status=520)

        filterdata = []
        if request.GET.get('filterbuilder'):
            authors = sqs.facet('author', limit=self.filterlimit).facet_counts()['fields']['author']
            owners = sqs.facet('owner', limit=self.filterlimit).facet_counts()['fields']['owner']
            subjects = sqs.facet('subject', limit=self.filterlimit).facet_counts()['fields']['subject']
            contributors = sqs.facet('contributor', limit=self.filterlimit).facet_counts()['fields']['contributor']
            types = sqs.facet('content_type', limit=self.filterlimit).facet_counts()['fields']['content_type']
            availability = sqs.facet('availability', limit=self.filterlimit).facet_counts()['fields']['availability']
            # TODO from Alva: to the best of my knowledge, this is invoked on every query and does absolutely nothing.
            if request.GET.get('updatefilters'):
                authors = [x for x in authors if x[1] > 0]
                owners = [x for x in owners if x[1] > 0]
                subjects = [x for x in subjects if x[1] > 0]
                contributors = [x for x in contributors if x[1] > 0]
                types = [x for x in types if x[1] > 0]
                availability = [x for x in availability if x[1] > 0]
            filterdata = [authors, owners, subjects, contributors, types, availability]

        # Filter out the old resources.
        resources_list = list(sqs.all())

        # Group the results by `title`
        grouped_resources = groupby(sorted(resources_list, key=lambda x: x.title), key=lambda x: x.title)

        latest_resources = []
        for title, group in grouped_resources:
            # Get the latest version by picking the one with the latest `created` date
            latest_version = max(group, key=lambda x: x.created)
            latest_resources.append(latest_version)

        # Sort the resources by the requested field or default.
        sort = 'modified'
        if request.GET.get('sort'):
            sort = request.GET.get('sort')
            # protect against ludicrous sort orders
            if sort != 'title' and sort != 'author' and sort != 'modified' and sort != 'created':
                sort = 'modified'
        asc = '-1'
        if request.GET.get('asc'):
            asc = request.GET.get('asc')
        latest_resources = sorted(latest_resources, key=lambda x: getattr(x, sort), reverse=(asc == '-1'))

        # Apply pagination
        p = Paginator(latest_resources, self.perpage)

        if request.GET.get('pnum'):
            pnum = request.GET.get('pnum')
            pnum = int(pnum)
            pnum = min(pnum, p.num_pages)
            if pnum < 1:
                return JsonResponse({
                    'resources': json.dumps([]),
                    'geodata': json.dumps([]),
                    'rescount': 0,
                    'pagecount': 1,
                    'perpage': self.perpage
                }, status=200)
        else:
            pnum = 1  # page number not specified, implies page 1
            pnum = min(pnum, p.num_pages)              

        resources = []
        geodata = []
        for result in p.get_page(pnum).object_list:
            contributor = 'None'  # contributor is actually a list and can have multiple values
            owner = 'None'  # owner is actually a list and can have multiple values
            author_link = None  # Send None to avoid anchor render
            authors = result.creator  # SOLR list
            author = result.author if result.author is not None else 'None'  # SOLR scalar
            author_link = result.author_url if result.author_url is not None else 'None'  # SOLR scalar
            contributor = result.contributor  # SOLR list
            owner = result.owner[0] if result.owner else 'None'  # SOLR list

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
            except: # noqa
                pass  # HydroShare production contains dirty data, this handling is in place, until data cleaned

            resources.append({
                "title": result.title,
                "link": result.absolute_url,
                "availability": result.availability,
                "availabilityurl": f"{settings.STATIC_URL}img/{result.availability[0]}.png",
                "type": result.resource_type,
                "author": author,
                "authors": authors,
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

        return JsonResponse({
            'resources': json.dumps(resources),
            'geodata': json.dumps(geodata),
            'rescount': p.count,
            'pagecount': p.num_pages,
            'perpage': self.perpage,
            'filterdata': json.dumps(filterdata),
            'time': (time.time() - start) / 1000
        }, status=200)
