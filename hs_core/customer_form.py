from django import forms
from haystack.forms import FacetedSearchForm
from crispy_forms.layout import *
from crispy_forms.bootstrap import *

class MyForm(FacetedSearchForm):
    #faceted_choices = (('author', 'Author'), ('creators', 'Creators'),('subjects', 'Subjects'),
                      # ('public', 'Public'),('discoverable', 'Discoverable'), ('language', 'Language'), ('resource_type', 'Resource Type'))
    #faceted_field = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=faceted_choices)
    facted_fields = ['author', 'subjects', 'resource_type', 'public', 'creators', 'discoverable', 'language']
    def search(self):
        sqs = super(MyForm, self).search().filter(discoverable=True)

        if not self.is_valid():
            return self.no_query_found()

        #if self.cleaned_data['faceted_field']:
       # for field in self.cleaned_data['faceted_field']:
        for field in self.facted_fields:
            sqs = sqs.facet(field, mincount=2)

        return sqs