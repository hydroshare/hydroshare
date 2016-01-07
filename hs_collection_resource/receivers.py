from django.dispatch import receiver

from hs_core.signals import pre_metadata_element_create, pre_metadata_element_update

from hs_collection_resource.models import CollectionResource


@receiver(pre_metadata_element_create, sender=CollectionResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    request = kwargs['request']
    element_name = kwargs['element_name'].lower()
    return validate_form(request, element_name)


@receiver(pre_metadata_element_update, sender=CollectionResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    request = kwargs['request']
    element_name = kwargs['element_name'].lower()
    return validate_form(request, element_name)


def validate_form(request, element_name):
    if element_name == 'collectionitems':
        return {'is_valid': True, 'element_data_dict': {'collection_items': request.POST.getlist("collection_items")}}
    else:
        # TODO: need to return form errors
        return {'is_valid': False, 'element_data_dict': None}