from dataclasses import dataclass
from typing import Any

from .atlas_search import SearchQuery
from ..forms import CONTENT_TYPE_VALUE_MAP


SORT_MAP = {
    "relevance": {"sortBy": None, "default_order": None},
    "most-viewed": {"sortBy": "viewCount", "default_order": "desc"},
    "title": {"sortBy": "name", "default_order": "asc"},
    "first-author": {"sortBy": "creatorName", "default_order": "asc"},
    "date-created": {"sortBy": "dateCreated", "default_order": "desc"},
    "last-modified": {"sortBy": "lastModified", "default_order": "desc"},
}


@dataclass
class DiscoveryQueryParams:
    term: str | None = None
    sort: str = "relevance"
    order: str | None = None
    contentType: list[str] | None = None
    creativeWorkStatus: list[str] | None = None
    creatorName: str | None = None
    keyword: str | None = None
    fundingFunderName: str | None = None
    dataCoverageStart: int | None = None
    dataCoverageEnd: int | None = None
    dateCreatedStart: int | None = None
    dateCreatedEnd: int | None = None
    publishedStart: int | None = None
    publishedEnd: int | None = None
    pageSize: int = 20
    paginationToken: str | None = None


def build_query_params(cleaned_data: dict[str, Any]) -> DiscoveryQueryParams:
    enable_content_type = cleaned_data.get("enableContentType")
    enable_availability = cleaned_data.get("enableAvailability")
    enable_data_coverage = cleaned_data.get("enableDataCoverage")
    enable_date_created = cleaned_data.get("enableDateCreated")
    enable_published = cleaned_data.get("enablePublished")

    selected_content_types = (cleaned_data.get("contentType") or []) if enable_content_type else []
    expanded_content_types = []
    for content_type in selected_content_types:
        expanded_content_types.extend(CONTENT_TYPE_VALUE_MAP.get(content_type, [content_type]))
    expanded_content_types = list(dict.fromkeys(expanded_content_types))

    return DiscoveryQueryParams(
        term=cleaned_data.get("term") or None,
        sort=cleaned_data.get("sort") or "relevance",
        order=cleaned_data.get("order") or None,
        contentType=expanded_content_types,
        creativeWorkStatus=(cleaned_data.get("creativeWorkStatus") or []) if enable_availability else [],
        creatorName=cleaned_data.get("creatorName") or None,
        keyword=cleaned_data.get("keyword") or None,
        fundingFunderName=cleaned_data.get("fundingFunderName") or None,
        dataCoverageStart=(cleaned_data.get("dataCoverageStart") or None) if enable_data_coverage else None,
        dataCoverageEnd=(cleaned_data.get("dataCoverageEnd") or None) if enable_data_coverage else None,
        dateCreatedStart=(cleaned_data.get("dateCreatedStart") or None) if enable_date_created else None,
        dateCreatedEnd=(cleaned_data.get("dateCreatedEnd") or None) if enable_date_created else None,
        publishedStart=(cleaned_data.get("publishedStart") or None) if enable_published else None,
        publishedEnd=(cleaned_data.get("publishedEnd") or None) if enable_published else None,
        pageSize=cleaned_data.get("pageSize") or 20,
        paginationToken=cleaned_data.get("paginationToken") or None,
    )


def build_search_query_from_form(cleaned_data: dict[str, Any]) -> SearchQuery:
    params = build_query_params(cleaned_data)
    sort_config = SORT_MAP.get(params.sort, SORT_MAP["relevance"])
    resolved_order = params.order if params.order else sort_config["default_order"]
    return SearchQuery(
        term=params.term,
        sortBy=sort_config["sortBy"],
        order=resolved_order,
        contentType=params.contentType,
        creatorName=params.creatorName,
        keyword=params.keyword,
        fundingFunderName=params.fundingFunderName,
        dataCoverageStart=params.dataCoverageStart,
        dataCoverageEnd=params.dataCoverageEnd,
        dateCreatedStart=params.dateCreatedStart,
        dateCreatedEnd=params.dateCreatedEnd,
        publishedStart=params.publishedStart,
        publishedEnd=params.publishedEnd,
        creativeWorkStatus=params.creativeWorkStatus,
        pageSize=params.pageSize,
        paginationToken=params.paginationToken,
    )
