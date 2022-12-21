from django.dispatch import receiver

from hs_core.signals import pre_add_files_to_resource, pre_check_bag_flag, pre_download_file
from hs_core.hydroshare.utils import set_dirty_bag_flag

from hs_collection_resource.models import CollectionResource
from hs_collection_resource.utils import update_collection_list_csv


@receiver(pre_add_files_to_resource, sender=CollectionResource)
def pre_add_files_to_resource_handler(sender, **kwargs):
    validate_files_dict = kwargs['validate_files']
    validate_files_dict['are_files_valid'] = False
    validate_files_dict['message'] = 'Content files are not allowed in a collection'


@receiver(pre_check_bag_flag, sender=CollectionResource)
def pre_check_bag_flag_handler(sender, **kwargs):

    collection_res_obj = kwargs['resource']
    if collection_res_obj.update_text_file.lower() == 'true':
        update_collection_list_csv(collection_res_obj)
        set_dirty_bag_flag(collection_res_obj)
        collection_res_obj.set_update_text_file(flag='False')


@receiver(pre_download_file, sender=CollectionResource)
def pre_download_file_handler(sender, **kwargs):

    collection_res_obj = kwargs['resource']
    collection_res_obj.set_update_text_file(flag='True')
