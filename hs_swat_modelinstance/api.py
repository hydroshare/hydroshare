from hs_core.api import GenericResourceResource
from hs_core.api import v1_api

from .models import SWATModelInstanceResource


class SWATModelInstanceResourceType(GenericResourceResource):
    class Meta(GenericResourceResource.Meta):
        queryset = SWATModelInstanceResource.objects.all()
        resource_name = 'swatmodelinstance'

v1_api.register(SWATModelInstanceResourceType())
