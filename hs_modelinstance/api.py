from hs_core.api import BaseResourceResource
from hs_core.api import v1_api

from .models import ModelInstanceResource


class ModelInstanceResourceType(GenericResourceResource):
    class Meta(GenericResourceResource.Meta):
        queryset = ModelInstanceResource.objects.all()
        resource_name = 'modelinstance'


v1_api.register(ModelInstanceResourceType())
