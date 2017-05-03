from rest_framework import generics
from rest_framework.generics import mixins
from hs_core.views.serializers import DiscoverySerializer
from haystack.query import EmptySearchQuerySet, SearchQuerySet


class DiscoverySearchAPI(generics.ListAPIView):
    serializer_class = DiscoverySerializer

    def get_queryset(self, *args, **kwargs):
        request = self.request
        queryset = EmptySearchQuerySet()

        if request.GET.get('q') is not None:
            query = request.GET.get('q')
            queryset = SearchQuerySet().filter(content=query)

        return queryset