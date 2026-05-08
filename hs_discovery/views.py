from django.shortcuts import render
from django.urls import reverse
from django.views import View
from pymongo.errors import PyMongoError

from .forms import CONTENT_TYPE_CHOICES, STATUS_CHOICES, DiscoverySearchForm
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


def _range_label(start, end):
    if start and end:
        return f"{start} to {end}"
    return str(start or end or "")


def _build_active_filters(form):
    cleaned = form.cleaned_data
    active = []
    if cleaned.get("term"):
        active.append({"label": "Search", "value": cleaned["term"]})
    if cleaned.get("creatorName"):
        active.append({"label": "Author", "value": cleaned["creatorName"]})
    if cleaned.get("keyword"):
        active.append({"label": "Keyword", "value": cleaned["keyword"]})
    if cleaned.get("fundingFunderName"):
        active.append({"label": "Funder", "value": cleaned["fundingFunderName"]})
    if cleaned.get("dataCoverageStart") or cleaned.get("dataCoverageEnd"):
        active.append({"label": "Temporal coverage", "value": _range_label(cleaned.get("dataCoverageStart"), cleaned.get("dataCoverageEnd"))})
    if cleaned.get("dateCreatedStart") or cleaned.get("dateCreatedEnd"):
        active.append({"label": "Date created", "value": _range_label(cleaned.get("dateCreatedStart"), cleaned.get("dateCreatedEnd"))})
    if cleaned.get("publishedStart") or cleaned.get("publishedEnd"):
        active.append({"label": "Publication year", "value": _range_label(cleaned.get("publishedStart"), cleaned.get("publishedEnd"))})

    content_type_labels = dict(CONTENT_TYPE_CHOICES)
    selected_content_types = cleaned.get("contentType") or []
    if selected_content_types:
        active.append({
            "label": "Content type",
            "value": ", ".join(content_type_labels.get(value, value) for value in selected_content_types),
        })

    status_labels = dict(STATUS_CHOICES)
    selected_statuses = cleaned.get("creativeWorkStatus") or []
    if selected_statuses:
        active.append({
            "label": "Availability",
            "value": ", ".join(status_labels.get(value, value) for value in selected_statuses),
        })
    return active


def build_discovery_context(request, form, results, error_message=None):
    cleaned = form.cleaned_data
    active_filters = _build_active_filters(form)
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
    return {
        "form": form,
        "results": results,
        "error_message": error_message,
        "active_filters": active_filters,
        "has_active_filters": bool(active_filters),
        "selected_content_types": set(cleaned.get("contentType") or []),
        "selected_statuses": set(cleaned.get("creativeWorkStatus") or []),
        "selected_sort": selected_sort,
        "selected_order": selected_order,
        "sort_title_querystring": sort_querystring("title"),
        "sort_first_author_querystring": sort_querystring("first-author"),
        "sort_date_created_querystring": sort_querystring("date-created"),
        "sort_last_modified_querystring": sort_querystring("last-modified"),
        "load_more_querystring": load_more_querystring,
        "search_url": reverse("discovery:page"),
        "results_url": reverse("discovery:results"),
        "more_url": reverse("discovery:more"),
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
