from django.shortcuts import render
from django.urls import reverse
from django.views import View
from pymongo.errors import PyMongoError

from .forms import (
    CONTENT_TYPE_CHOICES,
    CURRENT_YEAR,
    DISCOVERY_MIN_YEAR,
    STATUS_CHOICES,
    TEMPORAL_MIN_YEAR,
    DiscoverySearchForm,
)
from .services import AtlasSearchService
from .services.query_mapper import SORT_MAP, build_search_query_from_form
from .services.result_mapper import DiscoverySearchResults


def _querystring_from_request(request, **extra):
    query = request.GET.copy()
    query.pop("paginationToken", None)
    for key, value in extra.items():
        query.pop(key, None)
        if value is None or value == "":
            continue
        if isinstance(value, (list, tuple)):
            query.setlist(key, list(value))
        else:
            query[key] = value
    return query.urlencode()


def _querystring_without(request, key=None, value=None, remove_keys=None):
    query = request.GET.copy()
    query.pop("paginationToken", None)

    for remove_key in remove_keys or []:
        query.pop(remove_key, None)

    if key:
        if value is None:
            query.pop(key, None)
        else:
            existing_values = query.getlist(key)
            remaining_values = [item for item in existing_values if item != str(value)]
            query.pop(key, None)
            if remaining_values:
                query.setlist(key, remaining_values)

    return query.urlencode()


def _range_label(start, end):
    if start and end:
        return f"{start} to {end}"
    return str(start or end or "")


def _build_active_filters(form, request, search_url):
    cleaned = form.cleaned_data
    active = []
    data_coverage_enabled = cleaned.get("enableDataCoverage")
    date_created_enabled = cleaned.get("enableDateCreated")
    published_enabled = cleaned.get("enablePublished")
    content_type_enabled = cleaned.get("enableContentType")
    availability_enabled = cleaned.get("enableAvailability")

    def _build_filter_chip(label, value, remove_key=None, remove_value=None, remove_keys=None):
        remove_querystring = _querystring_without(
            request,
            key=remove_key,
            value=remove_value,
            remove_keys=remove_keys,
        )
        remove_url = f"{search_url}?{remove_querystring}" if remove_querystring else search_url
        remove_keys_list = remove_keys or ([remove_key] if remove_key else [])
        return {
            "label": label,
            "value": value,
            "remove_url": remove_url,
            "remove_querystring": remove_querystring,
            "remove_key": remove_key or "",
            "remove_value": str(remove_value) if remove_value is not None else "",
            "remove_keys": remove_keys_list,
            "remove_keys_csv": ",".join(remove_keys_list),
        }

    if cleaned.get("term"):
        active.append(_build_filter_chip("Search", cleaned["term"], remove_key="term"))
    if cleaned.get("creatorName"):
        active.append(_build_filter_chip("Author", cleaned["creatorName"], remove_key="creatorName"))
    if cleaned.get("keyword"):
        active.append(_build_filter_chip("Keyword", cleaned["keyword"], remove_key="keyword"))
    if cleaned.get("fundingFunderName"):
        active.append(_build_filter_chip("Funder", cleaned["fundingFunderName"], remove_key="fundingFunderName"))
    if data_coverage_enabled and (cleaned.get("dataCoverageStart") or cleaned.get("dataCoverageEnd")):
        active.append(
            _build_filter_chip(
                "Temporal coverage",
                _range_label(cleaned.get("dataCoverageStart"), cleaned.get("dataCoverageEnd")),
                remove_keys=["dataCoverageStart", "dataCoverageEnd", "enableDataCoverage"],
            )
        )
    if date_created_enabled and (cleaned.get("dateCreatedStart") or cleaned.get("dateCreatedEnd")):
        active.append(
            _build_filter_chip(
                "Date created",
                _range_label(cleaned.get("dateCreatedStart"), cleaned.get("dateCreatedEnd")),
                remove_keys=["dateCreatedStart", "dateCreatedEnd", "enableDateCreated"],
            )
        )
    if published_enabled and (cleaned.get("publishedStart") or cleaned.get("publishedEnd")):
        active.append(
            _build_filter_chip(
                "Publication year",
                _range_label(cleaned.get("publishedStart"), cleaned.get("publishedEnd")),
                remove_keys=["publishedStart", "publishedEnd", "enablePublished"],
            )
        )

    content_type_labels = dict(CONTENT_TYPE_CHOICES)
    selected_content_types = cleaned.get("contentType") or []
    if content_type_enabled:
        for content_type in selected_content_types:
            active.append(
                _build_filter_chip(
                    "Content type",
                    content_type_labels.get(content_type, content_type),
                    remove_key="contentType",
                    remove_value=content_type,
                )
            )

    status_labels = dict(STATUS_CHOICES)
    selected_statuses = cleaned.get("creativeWorkStatus") or []
    if availability_enabled:
        for status in selected_statuses:
            active.append(
                _build_filter_chip(
                    "Availability",
                    status_labels.get(status, status),
                    remove_key="creativeWorkStatus",
                    remove_value=status,
                )
            )
    return active


def build_discovery_context(request, form, results, error_message=None):
    cleaned = form.cleaned_data
    search_url = reverse("discovery:page")
    active_filters = _build_active_filters(form, request, search_url)
    selected_sort = cleaned.get("sort") or "relevance"
    selected_order = cleaned.get("order") or SORT_MAP.get(selected_sort, {}).get("default_order")

    def sort_querystring(sort_name):
        default_order = SORT_MAP[sort_name]["default_order"]
        if selected_sort == sort_name:
            next_order = "desc" if selected_order == "asc" else "asc"
        else:
            next_order = default_order
        return _querystring_from_request(request, sort=sort_name, order=next_order)

    load_more_querystring = _querystring_from_request(
        request,
        paginationToken=results.next_pagination_token,
    ) if results.has_more and results.next_pagination_token else ""
    sort_labels = dict(form.fields["sort"].choices)
    sort_options = [
        {
            "value": value,
            "label": label,
            "querystring": sort_querystring(value),
            "active": selected_sort == value,
        }
        for value, label in form.fields["sort"].choices
    ]
    return {
        "form": form,
        "results": results,
        "error_message": error_message,
        "active_filters": active_filters,
        "has_active_filters": bool(active_filters),
        "selected_content_types": set(cleaned.get("contentType") or []),
        "selected_statuses": set(cleaned.get("creativeWorkStatus") or []),
        "temporal_min_year": TEMPORAL_MIN_YEAR,
        "temporal_max_year": CURRENT_YEAR,
        "temporal_default_start": cleaned.get("dataCoverageStart") or DISCOVERY_MIN_YEAR,
        "temporal_default_end": cleaned.get("dataCoverageEnd") or CURRENT_YEAR,
        "date_created_min_year": DISCOVERY_MIN_YEAR,
        "date_created_max_year": CURRENT_YEAR,
        "date_created_default_start": cleaned.get("dateCreatedStart") or DISCOVERY_MIN_YEAR,
        "date_created_default_end": cleaned.get("dateCreatedEnd") or CURRENT_YEAR,
        "published_min_year": DISCOVERY_MIN_YEAR,
        "published_max_year": CURRENT_YEAR,
        "published_default_start": cleaned.get("publishedStart") or DISCOVERY_MIN_YEAR,
        "published_default_end": cleaned.get("publishedEnd") or CURRENT_YEAR,
        "enabled_data_coverage": bool(cleaned.get("enableDataCoverage")),
        "enabled_content_type": bool(cleaned.get("enableContentType")),
        "enabled_availability": bool(cleaned.get("enableAvailability")),
        "enabled_date_created": bool(cleaned.get("enableDateCreated")),
        "enabled_published": bool(cleaned.get("enablePublished")),
        "selected_sort": selected_sort,
        "selected_sort_label": sort_labels.get(selected_sort, "Relevance"),
        "sort_options": sort_options,
        "selected_order": selected_order,
        "sort_title_querystring": sort_querystring("title"),
        "sort_first_author_querystring": sort_querystring("first-author"),
        "sort_date_created_querystring": sort_querystring("date-created"),
        "sort_last_modified_querystring": sort_querystring("last-modified"),
        "load_more_querystring": load_more_querystring,
        "search_url": search_url,
        "results_url": reverse("discovery:results"),
        "more_url": reverse("discovery:more"),
        "typeahead_url": reverse("discover-hsapi-typeahead"),
        "page_size": cleaned.get("pageSize") or 20,
        "current_querystring": request.GET.urlencode(),
    }


class _BaseDiscoveryView(View):
    service_class = AtlasSearchService

    def get_form(self, request):
        # Always bind the form to the GET QueryDict, even when it is empty.
        # Passing None creates an unbound form, and unbound Django forms do not
        # populate cleaned_data during is_valid()/full_clean().
        form = DiscoverySearchForm(request.GET)
        form.is_valid()
        return form

    def get_results(self, form):
        search_query = build_search_query_from_form(form.cleaned_data)
        return self.service_class().search(search_query)

    def get_results_with_error_handling(self, form):
        try:
            return self.get_results(form), None
        except PyMongoError as exc:
            return DiscoverySearchResults(items=[], next_pagination_token=None, has_more=False), (
                f"Discovery search is temporarily unavailable because MongoDB Atlas local is not ready: {exc}"
            )


class DiscoverySearchPageView(_BaseDiscoveryView):
    template_name = "hs_discovery/page.html"

    def get(self, request, *args, **kwargs):
        form = self.get_form(request)
        results, error_message = self.get_results_with_error_handling(form)
        context = build_discovery_context(request, form, results, error_message=error_message)
        return render(request, self.template_name, context)


class DiscoverySearchResultsView(_BaseDiscoveryView):
    template_name = "hs_discovery/partials/results_region.html"

    def get(self, request, *args, **kwargs):
        form = self.get_form(request)
        results, error_message = self.get_results_with_error_handling(form)
        context = build_discovery_context(request, form, results, error_message=error_message)
        return render(request, self.template_name, context)


class DiscoverySearchMoreView(_BaseDiscoveryView):
    template_name = "hs_discovery/partials/results_more.html"

    def get(self, request, *args, **kwargs):
        form = self.get_form(request)
        results, error_message = self.get_results_with_error_handling(form)
        context = build_discovery_context(request, form, results, error_message=error_message)
        return render(request, self.template_name, context)
