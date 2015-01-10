from __future__ import absolute_import

from hs_core.api import GenericResourceResource
from hs_core.api import v1_api

from .models import HydroProgramResource


class RefTimeSeriesResource(GenericResourceResource):
    class Meta(GenericResourceResource.Meta):
        queryset = HydroProgramResource.objects.all()
        resource_name = 'hydroprogran'

v1_api.register(HydroProgramResource())
