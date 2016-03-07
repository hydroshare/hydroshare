import simplejson as json
from django.http import HttpResponse
from haystack.query import SearchQuerySet
from django import forms
from haystack.forms import FacetedSearchForm
from haystack.generic_views import FacetedSearchView
from django.core import serializers
from hs_core.discovery_form import DiscoveryForm

class DiscoveryView(FacetedSearchView):
    facet_fields = ['author', 'subjects', 'resource_type', 'public', 'owners_names', 'discoverable']
    form_class=DiscoveryForm

