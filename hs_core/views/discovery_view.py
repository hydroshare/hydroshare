from haystack.generic_views import FacetedSearchView
from haystack.generic_views import FacetedSearchMixin
from hs_core.discovery_form import DiscoveryForm
from haystack.query import SearchQuerySet


class DiscoveryView(FacetedSearchView):
    facet_fields = ['creators', 'subjects', 'resource_type', 'public', 'owners_names', 'discoverable', 'published', 'variable_names', 'sample_mediums' , 'units_names']
    form_class = DiscoveryForm

    def form_valid(self, form):

        self.queryset = form.search()
        query_text = self.request.GET.get('q', '')

        if not self.request.session.get('current_query', None):
            if len(query_text):
                self.request.session['query_changed'] = True
                self.request.session['current_query'] = query_text
            else:
                self.request.session['query_changed'] = False

        else:
            if self.request.session['current_query'] != query_text:
                self.request.session['query_changed'] = True
                self.request.session['current_query'] = query_text
            else:
                self.request.session['query_changed'] = False

        context = self.get_context_data(**{
            self.form_name: form,
            'query': form.cleaned_data.get(self.search_field),
            'object_list': self.queryset
        })
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(FacetedSearchMixin, self).get_context_data(**kwargs)
        
        total_results = SearchQuerySet().all().count()
        # check whether total number of results is set
        if self.request.session.get('total_results', None):
            # if total number of results is not updated
            if total_results == self.request.session['total_results']:
                # if query changed
                if self.request.session.get('query_changed', True):
                    context.update({'facets': self.queryset.facet_counts()})
                    self.request.session['facets_items'] = self.queryset.facet_counts()
                else: # if query not changed
                    # if facets_items is already set
                    if self.request.session.get('facets_items', None):
                        context.update({'facets': self.request.session['facets_items']})
                    else: # initial session variable
                        context.update({'facets': self.queryset.facet_counts()})
                        self.request.session['facets_items'] = self.queryset.facet_counts()
            else: # if total number of results is updated
                self.request.session['total_results'] = total_results
                context.update({'facets': self.queryset.facet_counts()})
                self.request.session['facets_items'] = self.queryset.facet_counts()
        else: # if total number of results is not set yet
            self.request.session['total_results'] = total_results
            context.update({'facets': self.queryset.facet_counts()})
            self.request.session['facets_items'] = self.queryset.facet_counts()

        return context

    def get_queryset(self):
        if len(self.request.GET.get('q', '')):
            qs = super(FacetedSearchMixin, self).get_queryset()
        else:
            qs = SearchQuerySet().all()

        for field in self.facet_fields:
            qs = qs.facet(field)
        return qs