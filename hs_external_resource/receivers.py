from django.dispatch import receiver

from hs_core.signals import pre_add_files_to_resource, pre_check_bag_flag, pre_download_file
from hs_core.hydroshare.utils import set_dirty_bag_flag

from .models import ExternalResource


@receiver(pre_add_files_to_resource, sender=ExternalResource)
def pre_add_files_to_resource_handler(sender, **kwargs):
    validate_files_dict = kwargs['validate_files']
    validate_files_dict['are_files_valid'] = False
    validate_files_dict['message'] = 'Content files are not allowed in external'


@receiver(pre_check_bag_flag, sender=ExternalResource)
def pre_check_bag_flag_handler(sender, **kwargs):

    external_res_obj = kwargs['resource']
    if external_res_obj.update_text_file.lower() == 'true':
        set_dirty_bag_flag(external_res_obj)
