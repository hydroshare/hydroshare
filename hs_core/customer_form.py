from django import forms
from haystack.forms import FacetedSearchForm
from crispy_forms.layout import *
from crispy_forms.bootstrap import *

class MyForm(FacetedSearchForm):
    faceted_choices = (('', 'Select'), ('author', 'Author'), ('creators', 'Creators'),('subjects', 'Subjects'),
                       ('public', 'Public'),('discoverable', 'Discoverable'), ('language', 'Language'), ('resource_type', 'Resource Type'))
    faceted_field = forms.ChoiceField(choices=faceted_choices)
    #start_date = forms.DateField(required=False)
    #end_date = forms.DateField(required=False)

    def search(self):
        # First, store the SearchQuerySet received from other processing.
        sqs = super(MyForm, self).search().filter(discoverable=True)

        if not self.is_valid():
            return self.no_query_found()

        # Check to see if a start_date was chosen.
        #if self.cleaned_data['start_date']:
        #    sqs = sqs.filter(pub_date__gte=self.cleaned_data['start_date'])

        # Check to see if an end_date was chosen.
        #if self.cleaned_data['end_date']:
        #    sqs = sqs.filter(pub_date__lte=self.cleaned_data['end_date'])

        if self.cleaned_data['faceted_field']:
            sqs =sqs.facet(self.cleaned_data['faceted_field'])

        return sqs