__author__ = 'jeff'


from django.dispatch import receiver
from hs_core.hydroshare import pre_create_resource, post_create_resource
from hs_core.signals import *
from ref_ts.models import RefTimeSeries


@receiver(pre_describe_resource, sender=RefTimeSeries)
def ref_time_series_describe_resource_trigger(sender, **kwargs):
    if(sender is RefTimeSeries):
        return {"create_resource_page_url": "pages/create-ref-time-series.html"}