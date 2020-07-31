import json

from django.shortcuts import render
from django.views.generic import TemplateView
from haystack.query import SearchQuerySet, SQ
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.paginator import Paginator


class SearchView(TemplateView):

    def get(self, request, *args, **kwargs):

        return render(request, 'hs_discover/index.html', {})


class SearchAPI(APIView):

    def do_clean_data(self):
        """
        Stub function for data validation to be moved elsewhere


        if self.cleaned_data.get('q'):
        The prior code corrected for an failed match of complete words, as documented
        in issue #2308. This version instead uses an advanced query syntax in which
        "word" indicates an exact match and the bare word indicates a stemmed match.
        cdata = self.cleaned_data.get('q')
        """

    def do_assign_haystack(self, NElng, SWlng, NElat, SWlat):
        """

        :return:
        """
        if NElng and SWlng:
            geo_sq = SQ(east__lte=float(NElng))
            geo_sq.add(SQ(east__gte=float(SWlng)), SQ.AND)
        else:
            geo_sq = SQ(east__gte=float(SWlng))
            geo_sq.add(SQ(east__lte=float(180)), SQ.OR)
            geo_sq.add(SQ(east__lte=float(NElng)), SQ.AND)
            geo_sq.add(SQ(east__gte=float(-180)), SQ.AND)

        if NElat and SWlat:
            # latitude might be specified without longitude
            if geo_sq is None:
                geo_sq = SQ(north__lte=float(NElat))
            else:
                geo_sq.add(SQ(north__lte=float(NElat)), SQ.AND)
            geo_sq.add(SQ(north__gte=float(SWlat)), SQ.AND)

    def get(self, request, *args, **kwargs):
        """

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
            sqs = sqs.filter(content=q)#.boost('keyword', 2.0)

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
                "author_link": result.author_url,
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
