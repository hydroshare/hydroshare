__author__ = 'jeff'

from django.dispatch import receiver
from hs_core.signals import pre_create_resource
from ref_ts.models import RefTimeSeriesResource

# redirect to render custom create-resource template
@receiver(pre_create_resource, sender=RefTimeSeriesResource)
def ref_time_series_describe_resource_trigger(sender, **kwargs):
    page_url_dict = kwargs['page_url_dict']
    url_key = kwargs['url_key']
    page_url_dict[url_key] = "pages/create-ref-time-series.html"

