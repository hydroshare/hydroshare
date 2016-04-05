from haystack.generic_views import FacetedSearchView
from haystack.generic_views import FacetedSearchMixin
from hs_core.discovery_form import DiscoveryForm

current_query = ""
query_changed = False
facets_items = {}
class DiscoveryView(FacetedSearchView):
    facet_fields = ['author', 'subjects', 'resource_type', 'public', 'owners_names', 'discoverable']
    form_class = DiscoveryForm

    def form_valid(self, form):
        global current_query
        global query_changed
        self.queryset = form.search()
        if current_query == form.cleaned_data.get(self.search_field):
            query_changed = False
        else:
            current_query = form.cleaned_data.get(self.search_field)
            query_changed = True
        context = self.get_context_data(**{
            self.form_name: form,
            'query': form.cleaned_data.get(self.search_field),
            'current_query': current_query,
            'query_changed': query_changed,
            'object_list': self.queryset
        })
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        global current_query
        global query_changed
        global facets_items
        context = super(FacetedSearchMixin, self).get_context_data(**kwargs)
        if query_changed:
            context.update({'facets': self.queryset.facet_counts()})
            facets_items = self.queryset.facet_counts()
        else:
            context.update({'facets': facets_items})
        return context