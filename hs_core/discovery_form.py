from django import forms
from haystack.forms import FacetedSearchForm
from crispy_forms.layout import *
from crispy_forms.bootstrap import *


class DiscoveryForm(FacetedSearchForm):

    def search(self):
        sqs = super(DiscoveryForm, self).search().filter(discoverable=True)

        #if not self.is_valid():
        #    return self.no_query_found()

        #for field in self.faceted_fields:
        #    sqs = sqs.facet(field)
        #sqs.stats('viewers_count').stats_results()['viewers_count']['max']
        #sqs = sqs.range_facet('viewers_count', start=0.0, end=100.0, gap=20.0)

        #sqs = sqs.date_facet('created', start_date=datetime.date(2015, 01, 01), end_date=datetime.date(2015, 12, 01), gap_by='month')
        #sqs = sqs.date_facet('modified', start_date=datetime.date(2015, 01, 01), end_date=datetime.date(2015, 12, 01), gap_by='month')
        #sqs = sqs.stats('created')
        #sqs = sqs.stats_results()
        return sqs