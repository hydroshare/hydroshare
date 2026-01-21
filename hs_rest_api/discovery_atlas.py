
from django.conf import settings
from rest_framework.decorators import api_view
from datetime import datetime
from typing import Optional
from pymongo import MongoClient
from pydantic import BaseModel, ValidationInfo, field_validator, model_validator
from drf_yasg.utils import swagger_auto_schema
from django.http import JsonResponse

mongo_connection_url = settings.ATLAS_CONNECTION_URL
hydroshare_atlas_db = MongoClient(mongo_connection_url)["hydroshare"]


class SearchQuery(BaseModel):
    term: Optional[str] = None
    sortBy: Optional[str] = None
    order: Optional[str] = None
    contentType: Optional[list[str]] = []
    providerName: Optional[str] = None
    creatorName: Optional[str] = None
    keyword: Optional[str] = None
    dataCoverageStart: Optional[int] = None
    dataCoverageEnd: Optional[int] = None
    publishedStart: Optional[int] = None
    publishedEnd: Optional[int] = None
    dateCreatedStart: Optional[int] = None
    dateCreatedEnd: Optional[int] = None
    dateModifiedStart: Optional[int] = None
    dateModifiedEnd: Optional[int] = None
    hasPartName: Optional[str] = None
    isPartOfName: Optional[str] = None
    associatedMediaName: Optional[str] = None
    fundingGrantName: Optional[str] = None
    fundingFunderName: Optional[str] = None
    creativeWorkStatus: Optional[list[str]] = []
    pageNumber: int = 1
    pageSize: int = 20
    paginationToken: Optional[str]

    @field_validator('*')
    def empty_str_to_none(cls, v, info: ValidationInfo):
        if info.field_name == 'term' and v:
            return v.strip()

        # Don't convert empty strings to None for list fields like contentType/creativeWorkStatus
        if info.field_name in ['contentType', 'creativeWorkStatus']:
            return v

        if isinstance(v, str) and v.strip() == '':
            return None
        return v

    @field_validator('contentType', 'creativeWorkStatus')
    def validate_list_type_fields(cls, v):
        """Ensure contentType/creativeWorkStatus is always a list and filter out empty strings"""
        if v is None:
            return []
        if isinstance(v, str):
            # Handle single string values
            return [v.strip()] if v.strip() else []
        if isinstance(v, list):
            # Filter out empty strings from list
            return [item.strip() for item in v if isinstance(item, str) and item.strip()]
        return []

    @field_validator('dataCoverageStart', 'dataCoverageEnd', 'publishedStart', 'publishedEnd', 'dateCreatedStart',
                     'dateCreatedEnd', 'dateModifiedStart', 'dateModifiedEnd')
    def validate_year(cls, v, info: ValidationInfo):
        if v is None:
            return v
        try:
            datetime(v, 1, 1)
        except ValueError:
            raise ValueError(f'{info.field_name} is not a valid year')

        return v

    @model_validator(mode='after')
    def validate_date_range(self):
        if self.dataCoverageStart and self.dataCoverageEnd and self.dataCoverageEnd < self.dataCoverageStart:
            raise ValueError('dataCoverageEnd must be greater or equal to dataCoverageStart')
        if self.publishedStart and self.publishedEnd and self.publishedEnd < self.publishedStart:
            raise ValueError('publishedEnd must be greater or equal to publishedStart')
        if self.dateCreatedStart and self.dateCreatedEnd and self.dateCreatedEnd < self.dateCreatedStart:
            raise ValueError('dateCreatedEnd must be greater or equal to dateCreatedStart')
        if self.dateModifiedStart and self.dateModifiedEnd and self.dateModifiedEnd < self.dateModifiedStart:
            raise ValueError('dateModifiedEnd must be greater or equal to dateModifiedStart')

    @field_validator('pageNumber', 'pageSize')
    def validate_page(cls, v, info: ValidationInfo):
        if v <= 0:
            raise ValueError(f'{info.field_name} must be greater than 0')
        return v

    @property
    def _filters(self):
        filters = []

        # filter out aggregation type documents - aggregation types do not have a value for dateCreated
        filters.append({'compound': {'mustNot': [{'equals': {'path': 'dateCreated', 'value': None}}]}})

        # Build all date range filters
        date_filters = []

        # Combine each date range into single filter objects
        for start_field, end_field, path in [
            (self.publishedStart, self.publishedEnd, 'datePublished'),
            (self.dateCreatedStart, self.dateCreatedEnd, 'dateCreated'),
            (self.dateModifiedStart, self.dateModifiedEnd, 'dateModified'),
        ]:
            if start_field or end_field:
                range_filter = {'path': path}
                if start_field:
                    range_filter['gte'] = datetime(start_field, 1, 1)
                if end_field:
                    range_filter['lt'] = datetime(end_field + 1, 1, 1)
                date_filters.append({'range': range_filter})

        if self.dataCoverageStart:
            date_filters.append(
                {'range': {'path': 'temporalCoverage.startDate', 'gte': datetime(self.dataCoverageStart, 1, 1)}}
            )
        if self.dataCoverageEnd:
            date_filters.append(
                {'range': {'path': 'temporalCoverage.endDate', 'lt': datetime(self.dataCoverageEnd + 1, 1, 1)}}
            )

        filters.extend(date_filters)
        filters.append({'term': {'path': 'type', 'query': "ScientificDataset"}})

        return filters

    @property
    def _should(self):
        search_paths = ['name', 'description', 'keywords']
        should = [{'autocomplete': {'query': self.term, 'path': key, 'fuzzy': {'maxEdits': 1}}} for key in search_paths]
        return should

    @property
    def _must(self):
        must = []
        if self.contentType and len(self.contentType) > 0:
            # Use exact term matching for each content type to ensure precise filtering
            # Check both 'additionalType' (single value) and 'content_types' (array) fields.
            if len(self.contentType) == 1:
                # Single content type - match either path exactly. Use compound should for OR.
                must.append({
                    'compound': {
                        'should': [
                            {'term': {'path': 'additionalType', 'query': self.contentType[0]}},
                            {'term': {'path': 'content_types', 'query': self.contentType[0]}}
                        ]
                    }
                })
            else:
                # Multiple content types - match any of the specified types appearing in either path.
                # Create a single compound 'should' that includes term matches for each
                # requested content type against both 'additionalType' and 'content_types'.
                content_type_conditions = []
                for content_type in self.contentType:
                    content_type_conditions.append({'term': {'path': 'additionalType', 'query': content_type}})
                    content_type_conditions.append({'term': {'path': 'content_types', 'query': content_type}})
                must.append({'compound': {'should': content_type_conditions}})
        if self.creatorName:
            must.append({'text': {'path': ['creator.name', 'contributor.name'], 'query': self.creatorName}})
        if self.keyword:
            must.append({'text': {'path': 'keywords', 'query': self.keyword}})
        if self.providerName:
            must.append({'text': {'path': 'provider.name', 'query': self.providerName}})
        if self.hasPartName:
            must.append({'text': {'path': 'hasPart.name', 'query': self.hasPartName}})
        if self.isPartOfName:
            must.append({'text': {'path': 'isPartOf.name', 'query': self.isPartOfName}})
        if self.associatedMediaName:
            must.append({'text': {'path': 'associatedMedia.name', 'query': self.associatedMediaName}})
        if self.fundingGrantName:
            must.append({'text': {'path': 'funding.name', 'query': self.fundingGrantName}})
        if self.fundingFunderName:
            must.append({'text': {'path': 'funding.funder.name', 'query': self.fundingFunderName}})
        if self.creativeWorkStatus and len(self.creativeWorkStatus) > 0:
            # Use exact term matching for each creative work status to ensure precise filtering
            if len(self.creativeWorkStatus) == 1:
                # Single creative work status - use term for exact match on both possible paths
                must.append({
                    'compound': {
                        'should': [
                            {'term': {'path': 'creativeWorkStatus', 'query': self.creativeWorkStatus[0]}},
                            {'term': {'path': 'creativeWorkStatus.name', 'query': self.creativeWorkStatus[0]}}
                        ]
                    }
                })
            else:
                # Multiple creative work statuses - use compound OR with exact term matches
                status_conditions = []
                for status in self.creativeWorkStatus:
                    status_conditions.append({
                        'compound': {
                            'should': [
                                {'term': {'path': 'creativeWorkStatus', 'query': status}},
                                {'term': {'path': 'creativeWorkStatus.name', 'query': status}}
                            ]
                        }
                    })
                must.append({'compound': {'should': status_conditions}})
        return must

    @property
    def stages(self):
        highlightPaths = ['name', 'description', 'keywords', 'creator.name']
        stages = []
        compound = {'filter': self._filters, 'must': self._must, 'should': []}

        # The term is searched for in name, description, keywords and creator name
        # TODO: should the term be searched for in all fields?
        if self.term:
            compound['should'] = [
                # https://www.mongodb.com/docs/atlas/atlas-search/score/modify-score/#std-label-scoring-boost
                {'autocomplete': {'query': self.term, 'path': 'name', 'fuzzy': {'maxEdits': 1},
                                  'score': {"boost": {"value": 5}}}},
                {'autocomplete': {'query': self.term, 'path': 'description', 'fuzzy': {'maxEdits': 1},
                                  'score': {"boost": {"value": 3}}}},
                {'autocomplete': {'query': self.term, 'path': 'keywords', 'fuzzy': {'maxEdits': 1},
                                  'score': {"boost": {"value": 3}}}},
                {'autocomplete': {'query': self.term, 'path': 'creator.name', 'fuzzy': {'maxEdits': 1},
                                  'score': {"boost": {"value": 5}}}},
                {'autocomplete': {'query': self.term, 'path': 'first_creator.name', 'fuzzy': {'maxEdits': 1},
                                  'score': {"boost": {"value": 5}}}},
                {'autocomplete': {'query': self.term, 'path': 'contributor.name', 'fuzzy': {'maxEdits': 1},
                                  'score': {"boost": {"value": 5}}}},
            ]

        # Dedicated input filters boost the score further if matched.

        if self.creatorName:
            # Matching `creator.name` has a slightly higher score than matching `contributor.name`
            compound['should'].append({'autocomplete': {'query': self.creatorName, 'path': 'creator.name',
                                                        'fuzzy': {'maxEdits': 1},
                                                        'score': {"boost": {"value": 5}}}})
            compound['should'].append({'autocomplete': {'query': self.creatorName, 'path': 'first_creator.name',
                                                        'fuzzy': {'maxEdits': 1},
                                                        'score': {"boost": {"value": 5}}}})
            compound['should'].append({'autocomplete': {'query': self.creatorName, 'path': 'contributor.name',
                                                        'fuzzy': {'maxEdits': 1},
                                                        'score': {"boost": {"value": 4}}}})

        if self.keyword:
            compound['should'].append({'autocomplete': {'query': self.keyword, 'path': 'keywords',
                                                        'fuzzy': {'maxEdits': 1},
                                                        'score': {"boost": {"value": 3}}}})

        if self.fundingFunderName:
            compound['should'].append({'autocomplete': {'query': self.fundingFunderName, 'path': 'funding.funder.name',
                                                        'fuzzy': {'maxEdits': 1},
                                                        'score': {"boost": {"value": 3}}}})

        search_stage = {
            '$search': {
                'index': 'fuzzy_search',
                'compound': compound,
                'highlight': {'path': highlightPaths},
                "concurrent": True,
                "returnStoredSource": True
            }
        }

        if self.paginationToken:
            search_stage["$search"]['searchAfter'] = self.paginationToken

        order = 1 if self.order == "asc" else -1

        # These sorts can occur inside the $search stage
        if self.sortBy == "name":
            search_stage["$search"]['sort'] = {"name": order}
        elif self.sortBy == "dateCreated":
            search_stage["$search"]['sort'] = {"dateCreated": order}
        elif self.sortBy == "lastModified":
            search_stage["$search"]['sort'] = {"dateModified": order}
        elif self.sortBy == "creatorName":
            search_stage["$search"]['sort'] = {"first_creator.name": order}

        stages.append(search_stage)

        set_stage = {'$set': {
            'score': {'$meta': 'searchScore'},
            'highlights': {'$meta': 'searchHighlights'}
        }}

        set_stage['$set']['paginationToken'] = {"$meta" : "searchSequenceToken"}

        stages.append(set_stage)

        if self.term or self.creatorName or self.keyword:
            # get only results which meet minimum relevance score threshold
            stages.append({'$match': {'score': {'$gt': settings.SEARCH_RELEVANCE_SCORE_THRESHOLD}}})

        return stages


# Convert ObjectId to string recursively
def convert_objectid(obj):
    if isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_objectid(v) for k, v in obj.items()}
    elif str(type(obj)) == "<class 'bson.objectid.ObjectId'>":
        return str(obj)
    else:
        return obj


@swagger_auto_schema(
    method="get",
    operation_description="Search HydroShare with Discovery Atlas",
    responses={200: "Returns the list of resources with jsonld metadata"},
)
@api_view(["GET"])
def search(request, term: Optional[str] = None,
           sortBy: Optional[str] = None,
           order: Optional[str] = None,
           contentType: list[str] = [],
           providerName: Optional[str] = None,
           creatorName: Optional[str] = None,
           keyword: Optional[str] = None,
           dataCoverageStart: Optional[int] = None,
           dataCoverageEnd: Optional[int] = None,
           publishedStart: Optional[int] = None,
           publishedEnd: Optional[int] = None,
           dateCreatedStart: Optional[int] = None,
           dateCreatedEnd: Optional[int] = None,
           dateModifiedStart: Optional[int] = None,
           dateModifiedEnd: Optional[int] = None,
           hasPartName: Optional[str] = None,
           isPartOfName: Optional[str] = None,
           associatedMediaName: Optional[str] = None,
           fundingGrantName: Optional[str] = None,
           fundingFunderName: Optional[str] = None,
           creativeWorkStatus: list[str] = [],
           pageNumber: int = 1,
           pageSize: int = 20,
           paginationToken: Optional[str] = None):
    search_query = SearchQuery(
        term=term,
        sortBy=sortBy,
        order=order,
        contentType=contentType,
        providerName=providerName,
        creatorName=creatorName,
        keyword=keyword,
        dataCoverageStart=dataCoverageStart,
        dataCoverageEnd=dataCoverageEnd,
        publishedStart=publishedStart,
        publishedEnd=publishedEnd,
        dateCreatedStart=dateCreatedStart,
        dateCreatedEnd=dateCreatedEnd,
        dateModifiedStart=dateModifiedStart,
        dateModifiedEnd=dateModifiedEnd,
        hasPartName=hasPartName,
        isPartOfName=isPartOfName,
        associatedMediaName=associatedMediaName,
        fundingGrantName=fundingGrantName,
        fundingFunderName=fundingFunderName,
        creativeWorkStatus=creativeWorkStatus,
        pageNumber=pageNumber,
        pageSize=pageSize,
        paginationToken=paginationToken
    )
    stages = search_query.stages
    if not search_query.paginationToken:
        stages.append({"$skip": (search_query.pageNumber - 1) * search_query.pageSize})
    stages.append({"$limit": search_query.pageSize})
    stages.append({
        "$lookup": {
            "from": "discovery", "localField": "_id", "foreignField": "_id", "as": "document"
        }
    })
    result = hydroshare_atlas_db["discovery"].aggregate(stages).to_list(None)

    result = convert_objectid(result)
    return JsonResponse(result, safe=False)


@swagger_auto_schema(
    method="get",
    operation_description="Typeahead endpoint for HydroShare with Discovery Atlas",
    responses={200: "Returns the list of keyword matches"},
)
@api_view(["GET"])
def typeahead(request, term: str, field: str = "term"):
    search_paths = ['name', 'description', 'keywords', "creator.name"]

    if field == "creator":
        search_paths = ["creator.name", "contributor.name"]
    elif field == "subject":
        search_paths = ["keywords"]
    elif field == "funder":
        search_paths = ["funding.funder.name"]

    should = [{'autocomplete': {'query': term, 'path': key, 'fuzzy': {'maxEdits': 1}}} for key in search_paths]

    stages = [
        {
            '$search': {
                'index': 'fuzzy_search',
                'compound': {'should': should},
                'highlight': {'path': search_paths},
                "concurrent": True,
                "returnStoredSource": True
            }
        },
        {
            '$project': {
                'name': 1,
                'description': 1,
                'keywords': 1,
                'creator': 1,
                'contributor': 1,
                'funding': 1,
                'highlights': {'$meta': 'searchHighlights'},
                '_id': 0,
            }
        },
    ]
    stages.append({"$limit": 20})
    stages.append({
        "$lookup": {
            "from": "discovery", "localField": "_id", "foreignField": "_id", "as": "document"
        }
    })
    result = hydroshare_atlas_db["discovery"].aggregate(stages).to_list(None)
    result = convert_objectid(result)
    return JsonResponse(result, safe=False)
