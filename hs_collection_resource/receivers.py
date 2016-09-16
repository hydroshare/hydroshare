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
    # When user clicks download btn, django_irods.download() first creates bag on-demand.
    # Once bag creation is done, the same django_irods.download() will be called
    # again to retrieve bag stream.
    # If we set bag flag to dirty here for each call, the bag will be created over and over again
    # resulting a dead loop.
    # To avoid dead loop, we monitor a dict 'collection_id_dict' in request.Session to identify
    # consecutive calls on the same collection resource from the same user,
    # and only set bag to dirty in every other call.

    collection_res_obj = kwargs['resource']
    request = kwargs['request_obj']

    collection_id_dict = request.session.get("collection_id_dict", None)
    if collection_id_dict is None or collection_res_obj.short_id not in collection_id_dict:
        update_collection_list_csv(collection_res_obj)
        set_dirty_bag_flag(collection_res_obj)
        if collection_id_dict is None:
            request.session['collection_id_dict'] = {}
        request.session['collection_id_dict'][collection_res_obj.short_id] = "creating bag"

    else:
        del request.session['collection_id_dict'][collection_res_obj.short_id]
        if len(request.session['collection_id_dict']) == 0:
            del request.session['collection_id_dict']
