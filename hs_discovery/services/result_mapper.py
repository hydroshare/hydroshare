from dataclasses import dataclass, field
from typing import Optional

from django.utils.html import escape
from django.utils.safestring import mark_safe


@dataclass
class DiscoveryResult:
    id: str
    title: str
    title_html: str
    identifier: str
    authors: list[str] = field(default_factory=list)
    authors_html: str = ""
    contributors: list[str] = field(default_factory=list)
    abstract: str = ""
    abstract_html: str = ""
    keywords: list[str] = field(default_factory=list)
    resource_type: str = ""
    sharing_status: str = ""
    created: Optional[str] = None
    modified: Optional[str] = None
    published: Optional[str] = None
    temporal_coverage: Optional[dict] = None
    highlights: list[dict] = field(default_factory=list)
    spatial_coverage: Optional[dict] = None
    views: Optional[int] = None
    pagination_token: Optional[str] = None


@dataclass
class DiscoverySearchResults:
    items: list[DiscoveryResult]
    next_pagination_token: Optional[str]
    has_more: bool
    total_count: Optional[int] = None


def _get_highlight_hits(highlights: list[dict], paths: list[str]) -> list[str]:
    hits = []
    for highlight in highlights or []:
        if highlight.get("path") not in paths:
            continue
        for text in highlight.get("texts", []):
            if text.get("type") == "hit" and text.get("value"):
                hits.append(text["value"])
    return list(dict.fromkeys(hits))


def highlight_text(value: str, highlights: list[dict], paths: list[str]) -> str:
    if not value:
        return ""

    content = escape(value)
    for hit in _get_highlight_hits(highlights, paths):
        escaped_hit = escape(hit)
        content = content.replace(escaped_hit, f"<mark>{escaped_hit}</mark>")
    return mark_safe(content)


def _stringify_keywords(raw_keywords) -> list[str]:
    keywords = []
    for keyword in raw_keywords or []:
        if isinstance(keyword, str):
            keywords.append(keyword)
        elif isinstance(keyword, dict):
            name = keyword.get("name")
            if name:
                keywords.append(name)
    return keywords


def _get_people(raw_people) -> list[str]:
    people = []
    for person in raw_people or []:
        if isinstance(person, dict):
            name = person.get("name")
            if name:
                people.append(name)
        elif isinstance(person, str):
            people.append(person)
    return people


def map_atlas_result(raw_result: dict) -> DiscoveryResult:
    document = (raw_result.get("document") or [{}])[0]
    highlights = raw_result.get("highlights") or []
    authors = _get_people(document.get("creator"))
    contributors = _get_people(document.get("contributor"))
    title = document.get("name") or "Untitled resource"
    abstract = document.get("description") or ""
    keywords = _stringify_keywords(document.get("keywords"))
    sharing_status = document.get("creativeWorkStatus")
    if isinstance(sharing_status, dict):
        sharing_status = sharing_status.get("name", "")

    identifier = ""
    identifiers = document.get("identifier") or []
    if identifiers:
        identifier = identifiers[0]
    elif document.get("url"):
        identifier = document["url"]

    first_author = authors[0] if authors else ""

    return DiscoveryResult(
        id=str(raw_result.get("_id", "")),
        title=title,
        title_html=highlight_text(title, highlights, ["name"]),
        identifier=identifier,
        authors=authors,
        authors_html=highlight_text(first_author, highlights, ["creator.name", "first_creator.name"]),
        contributors=contributors,
        abstract=abstract,
        abstract_html=highlight_text(abstract, highlights, ["description"]),
        keywords=keywords,
        resource_type=document.get("additionalType") or "",
        sharing_status=sharing_status or "",
        created=document.get("dateCreated"),
        modified=document.get("dateModified"),
        published=document.get("datePublished"),
        temporal_coverage=document.get("temporalCoverage"),
        highlights=highlights,
        spatial_coverage=(document.get("spatialCoverage") or {}).get("geo"),
        views=document.get("viewCount"),
        pagination_token=raw_result.get("paginationToken"),
    )


def map_atlas_results(raw_results: list[dict], has_more: bool) -> DiscoverySearchResults:
    items = [map_atlas_result(result) for result in raw_results]
    next_token = items[-1].pagination_token if items and has_more else None
    return DiscoverySearchResults(items=items, next_pagination_token=next_token, has_more=has_more)
