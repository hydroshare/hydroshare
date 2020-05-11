from drf_haystack.serializers import HaystackSerializer
from drf_haystack.viewsets import HaystackViewSet
from hs_core.search_indexes import BaseResourceIndex
from hs_core.models import BaseResource
from drf_haystack.fields import HaystackCharField, HaystackDateField, HaystackMultiValueField, \
    HaystackFloatField
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework import serializers


class DiscoveryResourceSerializer(HaystackSerializer):
    class Meta:
        index_classes = [BaseResourceIndex]
        fields = [
            "text",
            "author",
            "contributor",
            "subject",
            "abstract",
            "resource_type",
            "coverage_type",
            "availability",
            "created",
            "modified",
            "start_date",
            "end_date",
            "east",
            "west",
            "eastlimit",
            "westlimit",
            "northlimit",
            "southlimit"
        ]


class DiscoverResourceValidator(serializers.Serializer):
    text = HaystackCharField(required=False,
                             help_text='Search across all Resource Fields')
    author = HaystackCharField(required=False,
                               help_text='Search by author')
    contributor = HaystackMultiValueField(required=False,
                                          help_text='Search by contributor')
    subject = HaystackMultiValueField(required=False,
                                      help_text='Search within subject keywords')
    abstract = HaystackCharField(required=False,
                                 help_text='Search within the abstract')
    resource_type = HaystackCharField(required=False,
                                      help_text='Search By resource type')
    coverage_type = HaystackMultiValueField(required=False,
                                            help_text='Search by coverage type '
                                                      '(point, box, period)')
    availability = HaystackMultiValueField(required=False,
                                           help_text='Search by availability '
                                                     '(discoverable, public, published)')
    created = HaystackDateField(required=False,
                                help_text='Search by created date')
    modified = HaystackDateField(required=False,
                                 help_text='Search by modified date')
    start_date = HaystackDateField(required=False,
                                   help_text='Search by start date')
    end_date = HaystackDateField(required=False,
                                 help_text='Search by end date')
    east = HaystackFloatField(required=False,
                              help_text='Search by location or box center east longitude')
    north = HaystackFloatField(required=False,
                               help_text='Search by location or box center north latitude')
    eastlimit = HaystackFloatField(required=False,
                                   help_text='Search by east limit longitude')
    westlimit = HaystackFloatField(required=False,
                                   help_text='Search by west limit longitude')
    northlimit = HaystackFloatField(required=False,
                                    help_text='Search by north limit latitude')
    southlimit = HaystackFloatField(required=False,
                                    help_text='Search by south limit latitude')


class DiscoverSearchView(HaystackViewSet):
    index_models = [BaseResource]
    serializer_class = DiscoveryResourceSerializer

    @action(detail=True, methods=['get'])
    @swagger_auto_schema(operation_description="Search HydroShare Resources using solr conventions."
                                               "We use haystack for queries so you can use all of "
                                               "the parameters described here in combination with "
                                               "field lookups "
                                               "https://django-haystack.readthedocs.io/en/latest/"
                                               "searchqueryset_api.html?highlight=lookups#id1",
                         query_serializer=DiscoverResourceValidator)
    def list(self, request):
        return super(DiscoverSearchView, self).list(request)
