from datetime import datetime
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings
from pymongo import MongoClient
from pydantic import BaseModel, ValidationInfo, field_validator, model_validator

from .result_mapper import map_atlas_results


def _normalize_mongo_connection_url(connection_url: str) -> str:
    """
    MongoDB Atlas local in HydroShare dev currently behaves like a single node
    that requires directConnection=true. Production Atlas URLs should be left
    unchanged.
    """
    if not connection_url.startswith("mongodb://"):
        return connection_url

    parts = urlsplit(connection_url)
    hostname = parts.hostname or ""
    if hostname not in {"mongodb", "localhost", "127.0.0.1"}:
        return connection_url

    query_params = dict(parse_qsl(parts.query, keep_blank_values=True))
    query_params.setdefault("directConnection", "true")
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query_params), parts.fragment))


mongo_connection_url = _normalize_mongo_connection_url(settings.ATLAS_CONNECTION_URL)
hydroshare_atlas_db = MongoClient(mongo_connection_url)[settings.ATLAS_DB_NAME]


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
    paginationToken: Optional[str] = None

    @field_validator('*')
    def empty_str_to_none(cls, v, info: ValidationInfo):
        if info.field_name == 'term' and v:
            return v.strip()
        if info.field_name in ['contentType', 'creativeWorkStatus']:
            return v
        if isinstance(v, str) and v.strip() == '':
            return None
        return v

    @field_validator('contentType', 'creativeWorkStatus')
    def validate_list_type_fields(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if isinstance(v, list):
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
        return self

    @field_validator('pageNumber', 'pageSize')
    def validate_page(cls, v, info: ValidationInfo):
        if v <= 0:
            raise ValueError(f'{info.field_name} must be greater than 0')
        return v

    @property
    def _filters(self):
        filters = []
        filters.append({'compound': {'mustNot': [{'equals': {'path': 'dateCreated', 'value': None}}]}})
        date_filters = []
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
            date_filters.append({'range': {'path': 'temporalCoverage.startDate', 'gte': datetime(self.dataCoverageStart, 1, 1)}})
        if self.dataCoverageEnd:
            date_filters.append({'range': {'path': 'temporalCoverage.endDate', 'lt': datetime(self.dataCoverageEnd + 1, 1, 1)}})

        filters.extend(date_filters)
        filters.append({'term': {'path': 'type', 'query': 'ScientificDataset'}})
        return filters

    @property
    def _must(self):
        must = []
        if self.contentType and len(self.contentType) > 0:
            if len(self.contentType) == 1:
                must.append({'compound': {'should': [
                    {'term': {'path': 'additionalType', 'query': self.contentType[0]}},
                    {'term': {'path': 'content_types', 'query': self.contentType[0]}},
                ]}})
            else:
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
            if len(self.creativeWorkStatus) == 1:
                must.append({'compound': {'should': [
                    {'term': {'path': 'creativeWorkStatus', 'query': self.creativeWorkStatus[0]}},
                    {'term': {'path': 'creativeWorkStatus.name', 'query': self.creativeWorkStatus[0]}},
                ]}})
            else:
                status_conditions = []
                for status in self.creativeWorkStatus:
                    status_conditions.append({'compound': {'should': [
                        {'term': {'path': 'creativeWorkStatus', 'query': status}},
                        {'term': {'path': 'creativeWorkStatus.name', 'query': status}},
                    ]}})
                must.append({'compound': {'should': status_conditions}})
        return must

    @property
    def stages(self):
        highlight_paths = ['name', 'description', 'keywords', 'creator.name', 'contributor.name']
        stages = []
        compound = {'filter': self._filters, 'must': self._must, 'should': []}

        if self.term:
            compound['should'] = [
                {'autocomplete': {'query': self.term, 'path': 'name', 'fuzzy': {'maxEdits': 1},
                                  'score': {'boost': {'value': settings.SEARCH_BOOST_NAME}}}},
                {'autocomplete': {'query': self.term, 'path': 'description', 'fuzzy': {'maxEdits': 1},
                                  'score': {'boost': {'value': settings.SEARCH_BOOST_DESCRIPTION}}}},
                {'autocomplete': {'query': self.term, 'path': 'keywords', 'fuzzy': {'maxEdits': 1},
                                  'score': {'boost': {'value': settings.SEARCH_BOOST_KEYWORDS}}}},
                {'autocomplete': {'query': self.term, 'path': 'creator.name', 'fuzzy': {'maxEdits': 1},
                                  'score': {'boost': {'value': settings.SEARCH_BOOST_CREATOR_NAME}}}},
                {'autocomplete': {'query': self.term, 'path': 'first_creator.name', 'fuzzy': {'maxEdits': 1},
                                  'score': {'boost': {'value': settings.SEARCH_BOOST_FIRST_CREATOR_NAME}}}},
                {'autocomplete': {'query': self.term, 'path': 'contributor.name', 'fuzzy': {'maxEdits': 1},
                                  'score': {'boost': {'value': settings.SEARCH_BOOST_CONTRIBUTOR_NAME}}}},
            ]

        if self.creatorName:
            compound['should'].append({'autocomplete': {'query': self.creatorName, 'path': 'creator.name',
                                                        'fuzzy': {'maxEdits': 1},
                                                        'score': {'boost': {'value': settings.SEARCH_BOOST_CREATOR_NAME_FILTER}}}})
            compound['should'].append({'autocomplete': {'query': self.creatorName, 'path': 'first_creator.name',
                                                        'fuzzy': {'maxEdits': 1},
                                                        'score': {'boost': {'value': settings.SEARCH_BOOST_FIRST_CREATOR_NAME_FILTER}}}})
            compound['should'].append({'autocomplete': {'query': self.creatorName, 'path': 'contributor.name',
                                                        'fuzzy': {'maxEdits': 1},
                                                        'score': {'boost': {'value': settings.SEARCH_BOOST_CONTRIBUTOR_NAME_FILTER}}}})

        if self.keyword:
            compound['should'].append({'autocomplete': {'query': self.keyword, 'path': 'keywords',
                                                        'fuzzy': {'maxEdits': 1},
                                                        'score': {'boost': {'value': settings.SEARCH_BOOST_KEYWORD_FILTER}}}})

        if self.fundingFunderName:
            compound['should'].append({'autocomplete': {'query': self.fundingFunderName, 'path': 'funding.funder.name',
                                                        'fuzzy': {'maxEdits': 1},
                                                        'score': {'boost': {'value': settings.SEARCH_BOOST_FUNDING_FUNDER_NAME_FILTER}}}})

        compound['should'].append({'range': {'path': 'datePublished', 'gte': datetime.min,
                                             'score': {'boost': {'value': settings.SEARCH_BOOST_DATE_PUBLISHED}}}})

        search_stage = {'$search': {
            'index': 'fuzzy_search',
            'compound': compound,
            'highlight': {'path': highlight_paths},
            'concurrent': True,
            'returnStoredSource': True,
        }}

        if self.paginationToken:
            search_stage['$search']['searchAfter'] = self.paginationToken

        order = 1 if self.order == 'asc' else -1
        if self.sortBy == 'name':
            search_stage['$search']['sort'] = {'name': order}
        elif self.sortBy == 'dateCreated':
            search_stage['$search']['sort'] = {'dateCreated': order}
        elif self.sortBy == 'lastModified':
            search_stage['$search']['sort'] = {'dateModified': order}
        elif self.sortBy == 'creatorName':
            search_stage['$search']['sort'] = {'first_creator.name': order}
        elif self.sortBy == 'viewCount':
            search_stage['$search']['sort'] = {'viewCount': order}
        elif not self.term and not self.has_filters:
            search_stage['$search']['sort'] = {'dateModified': -1}

        stages.append(search_stage)
        stages.append({'$set': {
            'score': {'$meta': 'searchScore'},
            'highlights': {'$meta': 'searchHighlights'},
            'paginationToken': {'$meta': 'searchSequenceToken'},
        }})

        if self.term or self.creatorName or self.keyword:
            stages.append({'$match': {'score': {'$gt': settings.SEARCH_RELEVANCE_SCORE_THRESHOLD}}})
        return stages

    @property
    def has_filters(self):
        return any([
            self.contentType,
            self.providerName,
            self.creatorName,
            self.keyword,
            self.dataCoverageStart,
            self.dataCoverageEnd,
            self.publishedStart,
            self.publishedEnd,
            self.dateCreatedStart,
            self.dateCreatedEnd,
            self.dateModifiedStart,
            self.dateModifiedEnd,
            self.hasPartName,
            self.isPartOfName,
            self.associatedMediaName,
            self.fundingGrantName,
            self.fundingFunderName,
            self.creativeWorkStatus,
        ])


def build_search_query_from_request(request) -> SearchQuery:
    return SearchQuery(
        term=request.GET.get('term', None),
        sortBy=request.GET.get('sortBy', None),
        order=request.GET.get('order', None),
        contentType=request.GET.getlist('contentType'),
        providerName=request.GET.get('providerName', None),
        creatorName=request.GET.get('creatorName', None),
        keyword=request.GET.get('keyword', None),
        dataCoverageStart=request.GET.get('dataCoverageStart', None),
        dataCoverageEnd=request.GET.get('dataCoverageEnd', None),
        publishedStart=request.GET.get('publishedStart', None),
        publishedEnd=request.GET.get('publishedEnd', None),
        dateCreatedStart=request.GET.get('dateCreatedStart', None),
        dateCreatedEnd=request.GET.get('dateCreatedEnd', None),
        dateModifiedStart=request.GET.get('dateModifiedStart', None),
        dateModifiedEnd=request.GET.get('dateModifiedEnd', None),
        hasPartName=request.GET.get('hasPartName', None),
        isPartOfName=request.GET.get('isPartOfName', None),
        associatedMediaName=request.GET.get('associatedMediaName', None),
        fundingGrantName=request.GET.get('fundingGrantName', None),
        fundingFunderName=request.GET.get('fundingFunderName', None),
        creativeWorkStatus=request.GET.getlist('creativeWorkStatus'),
        pageNumber=int(request.GET.get('pageNumber', 1)),
        pageSize=int(request.GET.get('pageSize', 20)),
        paginationToken=request.GET.get('paginationToken', None),
    )


def convert_objectid(obj):
    if isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    if isinstance(obj, dict):
        return {k: convert_objectid(v) for k, v in obj.items()}
    if str(type(obj)) == "<class 'bson.objectid.ObjectId'>":
        return str(obj)
    return obj


class AtlasSearchService:
    def __init__(self, collection=None):
        self.collection = collection or hydroshare_atlas_db['discovery']

    def search_raw(self, search_query: SearchQuery) -> tuple[list[dict], bool]:
        stages = list(search_query.stages)
        if not search_query.paginationToken:
            stages.append({'$skip': (search_query.pageNumber - 1) * search_query.pageSize})
        stages.append({'$limit': search_query.pageSize + 1})
        stages.append({'$lookup': {'from': 'discovery', 'localField': '_id', 'foreignField': '_id', 'as': 'document'}})
        result = self.collection.aggregate(stages).to_list(None)
        result = convert_objectid(result)
        has_more = len(result) > search_query.pageSize
        if has_more:
            result = result[:search_query.pageSize]
        return result, has_more

    def search(self, search_query: SearchQuery):
        raw_results, has_more = self.search_raw(search_query)
        return map_atlas_results(raw_results, has_more)

    def typeahead(self, term: str, field: str):
        term = (term or '').strip()
        field = (field or 'term').strip()
        search_paths = ['name', 'description', 'keywords', 'creator.name']
        if field == 'creator':
            search_paths = ['creator.name', 'contributor.name']
        elif field == 'subject':
            search_paths = ['keywords']
        elif field == 'funder':
            search_paths = ['funding.funder.name']
        should = [{'autocomplete': {'query': term, 'path': key, 'fuzzy': {'maxEdits': 1}}} for key in search_paths]
        stages = [
            {'$search': {'index': 'fuzzy_search', 'compound': {'should': should},
                         'highlight': {'path': search_paths}, 'concurrent': True, 'returnStoredSource': True}},
            {'$project': {'name': 1, 'description': 1, 'keywords': 1, 'creator': 1, 'contributor': 1,
                          'funding': 1, 'highlights': {'$meta': 'searchHighlights'}, '_id': 0}},
            {'$limit': 20},
            {'$lookup': {'from': 'discovery', 'localField': '_id', 'foreignField': '_id', 'as': 'document'}},
        ]
        result = self.collection.aggregate(stages).to_list(None)
        return convert_objectid(result)
