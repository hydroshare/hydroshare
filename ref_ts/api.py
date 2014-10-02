from __future__ import absolute_import

from hs_core.api import GenericResourceResource
from hs_core.api import v1_api

from .models import RefTimeSeries


class RefTimeSeriesResource(GenericResourceResource):
    class Meta(GenericResourceResource.Meta):
        queryset = RefTimeSeries.objects.all()
        resource_name = 'reftimeseries'

v1_api.register(RefTimeSeriesResource())

