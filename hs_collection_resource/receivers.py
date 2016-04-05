from django.dispatch import receiver

from hs_core.signals import *
from hs_collection_resource.models import CollectionResource


@receiver(pre_add_files_to_resource, sender=CollectionResource)
def pre_add_files_to_resource_handler(sender, **kwargs):
    validate_files_dict = kwargs['validate_files']
    validate_files_dict['are_files_valid'] = False
    validate_files_dict['message'] = 'Content files are not allowed in Collection resource'

