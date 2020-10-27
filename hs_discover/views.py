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
from haystack.inputs import Exact
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

        asc = '-1'
        if request.GET.get('asc'):
            asc = request.GET.get('asc')

        sort = 'modified'
        if request.GET.get('sort'):
            sort = request.GET.get('sort')
        sort = sort if asc == '1' else '-{}'.format(sort)

        if request.GET.get('q'):
            q = request.GET.get('q')
            sqs = sqs.filter(content=q)

        if request.GET.get('filter'):
            menufilter = request.GET.get('filter')
            filteritem = []
            sqs = SearchQuerySet().all()
            for result in sqs:
                # TODO validation and client error handling
                # TODO getter for SearchResult Abstract / Interface?
                if menufilter == 'subject':
                    filteritem += result.subject
                elif menufilter == 'abstract':
                    filteritem.append(result.abstract)
                elif menufilter == 'author':
                    filteritem.append(result.author)
                elif menufilter == 'contributor':
                    filteritem.append(result.creator)
                elif menufilter == 'owner':
                    filteritem += result.owner

                # TODO order by count as indicator of usefulness in autocomplete
                # TODO can integrate with Alva future Recommendations work here

            return JsonResponse({
                'time': (time.time() - start),
                'filter': json.dumps(list(set(filteritem)))
            })

        filtering = None
        if request.GET.get('filtering'):
            filtering = request.GET.get('filtering')

        cat = None
        if request.GET.get('cat'):
            cat = request.GET.get('cat')

        try:
            qs = request.query_params
            filters = json.loads(qs.get('filter'))
            # filter values expect lists, for example discoverapi/?filter={"owner":["Firstname Lastname"]}
            if filters.get('author'):
                for k, authortype in enumerate(filters['author']):
                    if k == 0 or k == len(filters['author']):
                        sqs = sqs.filter(author_exact=Exact(authortype))
                    else:
                        sqs = sqs.filter_or(author_exact=Exact(authortype))
            if filters.get('owner'):
                for k, ownertype in enumerate(filters['owner']):
                    if k == 0 or k == len(filters['owner']):
                        sqs = sqs.filter(owner_exact=Exact(ownertype))
                    else:
                        sqs = sqs.filter_or(owner_exact=Exact(ownertype))
            if filters.get('subject'):
                for k, subjtype in enumerate(filters['subject']):
                    if k == 0 or k == len(filters['subject']):
                        sqs = sqs.filter(subject_exact=Exact(subjtype))
                    else:
                        sqs = sqs.filter_or(subject_exact=Exact(subjtype))
            if filters.get('contributor'):
                for k, contribtype in enumerate(filters['contributor']):
                    if k == 0 or k == len(filters['contributor']):
                        sqs = sqs.filter(contributor_exact=Exact(contribtype))
                    else:
                        sqs = sqs.filter_or(contributor_exact=Exact(contribtype))
            if filters.get('type'):
                for k, restype in enumerate(filters['type']):
                    if k == 0 or k == len(filters['type']):
                        sqs = sqs.filter(resource_type_exact=Exact(restype))
                    else:
                        sqs = sqs.filter_or(resource_type_exact=Exact(restype))
            if filters.get('availability'):
                for k, availtype in enumerate(filters['availability']):
                    if k == 0 or k == len(filters['availability']):
                        sqs = sqs.filter(availability_exact=Exact(availtype))
                    else:
                        sqs = sqs.filter_or(availability_exact=Exact(availtype))
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
        except TypeError as type_ex:
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
            authors = sqs.facet('author').facet_counts()['fields']['author']
            owners = sqs.facet('owner').facet_counts()['fields']['owner']
            subjects = sqs.facet('subject').facet_counts()['fields']['subject']
            contributors = sqs.facet('contributor').facet_counts()['fields']['contributor']
            types = sqs.facet('resource_type').facet_counts()['fields']['resource_type']
            availability = sqs.facet('availability').facet_counts()['fields']['availability']
            if request.GET.get('updatefilters'):
                authors = [x for x in authors if x[1] > 0]
                owners = [x for x in owners if x[1] > 0]
                subjects = [x for x in subjects if x[1] > 0]
                contributors = [x for x in contributors if x[1] > 0]
                types = [x for x in types if x[1] > 0]
                availability = [x for x in availability if x[1] > 0]
            filterdata = [authors[:self.filterlimit], owners[:self.filterlimit], subjects[:self.filterlimit],
                          contributors[:self.filterlimit], types[:self.filterlimit], availability[:self.filterlimit]]

        if sort == 'author':
            sqs = sqs.order_by('author_exact')
        elif sort == '-author':
            sqs = sqs.order_by('-author_exact')
        else:
            sqs = sqs.order_by(sort)

        resources = []

        # TODO future release will add title and facilitate order_by title_exact
        # convert sqs to list after facet operations to allow for Python sorting instead of Haystack order_by
        if sort == 'title':
            sqs = sorted(sqs, key=lambda idx: idx.title.lower())
        elif sort == '-title':
            sqs = sorted(sqs, key=lambda idx: idx.title.lower(), reverse=True)

        p = Paginator(sqs, self.perpage)

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

        geodata = []

        for result in p.page(pnum):
            contributor = 'None'  # contributor is actually a list and can have multiple values
            owner = 'None'  # owner is actually a list and can have multiple values
            author_link = None  # Send None to avoid anchor render
            creator = 'None'
            author = 'None'

            if result.creator:
                creator = result.creator

            authors = creator  # there is no concept of authors in DataOne standard
            # authors might be string 'None' here

            if result.author:
                author_link = result.author_url
                author = str(result.author)
                if authors == 'None':
                    authors = author  # author would override creator in
            else:
                if result.organization:
                    if isinstance(result.organization, list):
                        author = str(result.organization[0])
                    else:
                        author = str(result.organization)

                    author = author.replace('"', '')
                    author = author.replace('[', '')
                    author = author.replace(']', '').strip()

                    if authors == 'None':
                        authors = author

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
