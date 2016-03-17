from haystack.generic_views import FacetedSearchView
from hs_core.discovery_form import DiscoveryForm

class DiscoveryView(FacetedSearchView):
    facet_fields = ['author', 'subjects', 'resource_type', 'public', 'owners_names', 'discoverable']
    form_class = DiscoveryForm
