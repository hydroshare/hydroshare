from django import forms
from haystack.forms import FacetedSearchForm
from crispy_forms.layout import *
from crispy_forms.bootstrap import *
import datetime

class MyForm(FacetedSearchForm):

    #faceted_choices = (('author', 'Author'), ('creators', 'Creators'),('subjects', 'Subjects'),
                      # ('public', 'Public'),('discoverable', 'Discoverable'), ('language', 'Language'), ('resource_type', 'Resource Type'))
    #faceted_field = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=faceted_choices)
    faceted_fields = ['author', 'subjects', 'resource_type', 'public', 'owners_names', 'discoverable']
    def search(self):
        sqs = super(MyForm, self).search().filter(discoverable=True)

        if not self.is_valid():
            return self.no_query_found()

        for field in self.faceted_fields:
            sqs = sqs.facet(field)
        #sqs.stats('viewers_count').stats_results()['viewers_count']['max']
        #sqs = sqs.range_facet('viewers_count', start=0.0, end=100.0, gap=20.0)

        #sqs = sqs.date_facet('created', start_date=datetime.date(2015, 01, 01), end_date=datetime.date(2015, 12, 01), gap_by='month')
        #sqs = sqs.date_facet('modified', start_date=datetime.date(2015, 01, 01), end_date=datetime.date(2015, 12, 01), gap_by='month')
        #sqs = sqs.stats('created')
        #sqs = sqs.stats_results()
        return sqs
