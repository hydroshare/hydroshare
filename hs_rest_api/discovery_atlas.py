
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from django.http import JsonResponse
from drf_yasg import openapi
from pymongo.errors import PyMongoError

from hs_discovery.services import AtlasSearchService, build_search_query_from_request


@swagger_auto_schema(
    method="get",
    operation_description="Search HydroShare with Discovery Atlas",
    responses={200: "Returns the list of resources with jsonld metadata"},
    manual_parameters=[
        openapi.Parameter('term', openapi.IN_QUERY, description="Search term", type=openapi.TYPE_STRING),
        openapi.Parameter('sortBy', openapi.IN_QUERY, description="Field to sort by", type=openapi.TYPE_STRING,
                          enum=["viewCount", "name", "dateCreated", "lastModified", "creatorName"]),
        openapi.Parameter('order', openapi.IN_QUERY, description="Sort order", type=openapi.TYPE_STRING,
                          enum=["asc", "desc"]),
        openapi.Parameter('contentType', openapi.IN_QUERY, description="Content type filter", type=openapi.TYPE_ARRAY,
                          items=openapi.Items(type=openapi.TYPE_STRING)),
        openapi.Parameter('providerName', openapi.IN_QUERY, description="Provider name filter",
                          type=openapi.TYPE_STRING),
        openapi.Parameter('creatorName', openapi.IN_QUERY, description="Creator name filter", type=openapi.TYPE_STRING),
        openapi.Parameter('keyword', openapi.IN_QUERY, description="Keyword filter", type=openapi.TYPE_STRING),
        openapi.Parameter('dataCoverageStart', openapi.IN_QUERY, description="Data coverage start year filter",
                          type=openapi.TYPE_INTEGER),
        openapi.Parameter('dataCoverageEnd', openapi.IN_QUERY, description="Data coverage end year filter",
                          type=openapi.TYPE_INTEGER),
        openapi.Parameter('publishedStart', openapi.IN_QUERY, description="Published start year filter",
                          type=openapi.TYPE_INTEGER),
        openapi.Parameter('publishedEnd', openapi.IN_QUERY, description="Published end year filter",
                          type=openapi.TYPE_INTEGER),
        openapi.Parameter('dateCreatedStart', openapi.IN_QUERY, description="Date created start year filter",
                          type=openapi.TYPE_INTEGER),
        openapi.Parameter('dateCreatedEnd', openapi.IN_QUERY, description="Date created end year filter",
                          type=openapi.TYPE_INTEGER),
        openapi.Parameter('dateModifiedStart', openapi.IN_QUERY, description="Date modified start year filter",
                          type=openapi.TYPE_INTEGER),
        openapi.Parameter('dateModifiedEnd', openapi.IN_QUERY, description="Date modified end year filter",
                          type=openapi.TYPE_INTEGER),
        openapi.Parameter('hasPartName', openapi.IN_QUERY, description="hasPart name filter", type=openapi.TYPE_STRING),
        openapi.Parameter('isPartOfName', openapi.IN_QUERY, description="isPartOf name filter",
                          type=openapi.TYPE_STRING),
        openapi.Parameter('associatedMediaName', openapi.IN_QUERY, description="associatedMedia name filter",
                          type=openapi.TYPE_STRING),
        openapi.Parameter('fundingGrantName', openapi.IN_QUERY, description="Funding grant name filter",
                          type=openapi.TYPE_STRING),
        openapi.Parameter('fundingFunderName', openapi.IN_QUERY, description="Funding funder name filter",
                          type=openapi.TYPE_STRING),
        openapi.Parameter('creativeWorkStatus', openapi.IN_QUERY, description="Creative work status filter",
                          type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
        openapi.Parameter('pageNumber', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
        openapi.Parameter('pageSize', openapi.IN_QUERY, description="Page size", type=openapi.TYPE_INTEGER),
        openapi.Parameter('paginationToken', openapi.IN_QUERY, description="Pagination token from previous response",
                          type=openapi.TYPE_STRING),
    ]
)
@api_view(["GET"])
def search(request):
    try:
        search_query = build_search_query_from_request(request)
        result, _has_more = AtlasSearchService().search_raw(search_query)
        return JsonResponse(result, safe=False)
    except PyMongoError as exc:
        return JsonResponse({"message": f"Discovery Atlas search unavailable: {exc}"}, status=503)


@swagger_auto_schema(
    method="get",
    operation_description="Typeahead endpoint for HydroShare with Discovery Atlas",
    responses={200: "Returns the list of keyword matches"},
    manual_parameters=[
        openapi.Parameter('term', openapi.IN_QUERY, description="Search term", type=openapi.TYPE_STRING),
        openapi.Parameter('field', openapi.IN_QUERY, description="Field to search", type=openapi.TYPE_STRING)
    ]
)
@api_view(["GET"])
def typeahead(request):
    try:
        term = request.GET.get('term', '')
        field = request.GET.get('field', 'term')
        result = AtlasSearchService().typeahead(term=term, field=field)
        return JsonResponse(result, safe=False)
    except PyMongoError as exc:
        return JsonResponse({"message": f"Discovery Atlas typeahead unavailable: {exc}"}, status=503)
