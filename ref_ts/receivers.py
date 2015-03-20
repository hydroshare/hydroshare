__author__ = 'jeff'


from django.dispatch import receiver
from hs_core.signals import *
from ref_ts.models import RefTimeSeries

@receiver(pre_create_resource, sender=RefTimeSeries)
def ref_time_series_describe_resource_trigger(sender, **kwargs):
    if(sender is RefTimeSeries):
        page_url_dict = kwargs['page_url_dict']
        url_key = kwargs['url_key']
        page_url_dict[url_key] = "pages/create-ref-time-series.html"
        global title
        title = kwargs['title']



