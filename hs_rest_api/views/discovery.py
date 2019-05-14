from drf_haystack.serializers import HaystackSerializer
from drf_haystack.viewsets import HaystackViewSet
from hs_core.search_indexes import BaseResourceIndex
from hs_core.models import BaseResource


class DiscoveryResourceSerializer(HaystackSerializer):
    class Meta:
        index_classes = [BaseResourceIndex]
        fields = [
            "text", "short_id", "doi", "author", "title", "abstract", "creator"
        ]

class DiscoverSearchView(HaystackViewSet):
    index_models = [BaseResource]
    serializer_class = DiscoveryResourceSerializer