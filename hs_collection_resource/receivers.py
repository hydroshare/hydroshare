from django.dispatch import receiver

from hs_core.signals import pre_add_files_to_resource, pre_check_bag_flag
from hs_core.hydroshare.utils import set_dirty_bag_flag

from hs_collection_resource.models import CollectionResource
from hs_collection_resource.utils import update_collection_list_csv


@receiver(pre_add_files_to_resource, sender=CollectionResource)
def pre_add_files_to_resource_handler(sender, **kwargs):
    validate_files_dict = kwargs['validate_files']
    validate_files_dict['are_files_valid'] = False
    validate_files_dict['message'] = 'Content files are not allowed in Collection resource'


@receiver(pre_check_bag_flag, sender=CollectionResource)
def pre_check_bag_flag_handler(sender, **kwargs):
    resource = kwargs['resource']
    request_obj = kwargs['request_obj']

    flag = request_obj.session.get("update_list_csv", False)
    if not flag:
        update_collection_list_csv(resource)
        set_dirty_bag_flag(resource)
        request_obj.session['update_list_csv'] = True
    else:
        del request_obj.session['update_list_csv']
