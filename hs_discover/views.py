import json

from django.template.defaultfilters import date, time
from haystack.query import SearchQuerySet
from rest_framework.response import Response
from rest_framework.views import APIView


class SearchAPI(APIView):
    """
    Provide resources returned from a lookup in the haystack interface to the index
    """

    def get(self, request, *args, **kwargs):

        sqs = SearchQuerySet().all()
        if request.GET.get('searchtext'):
            searchtext = request.GET.get('searchtext')
            sqs = sqs.filter(content=searchtext).boost('keyword', 2.0)

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

        resources = json.dumps(resources)

        return Response({
            'resources': resources,
        })
