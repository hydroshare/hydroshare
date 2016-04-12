import logging

from django.http import JsonResponse
from django.db import transaction

from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
from hs_core.hydroshare.utils import get_resource_by_shortkey, resource_modified

logger = logging.getLogger(__name__)


# update collection
def update_collection(request, shortkey, *args, **kwargs):
    """
    Add resources to a collection. The POST request should contain a
    list of resource ids for those resources to be part of the collection. Any existing resources
    from the collection are removed before adding resources as specified by the list of
    resource ids in the post request. Requesting user must at least have metadata view permission
    for any new resources being added to the collection.

    :param shortkey: id of the collection resource to which resources are to be added.
    """

    status = "success"
    msg = ""
    metadata_status = "Insufficient to make public"
    try:
        with transaction.atomic():
            collection_res_obj, is_authorized, user = authorize(request, shortkey,
                                                                needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

            if collection_res_obj.resource_type.lower() != "collectionresource":
                raise Exception("Resource {0} is not a collection resource.".format(shortkey))

            # get res_id list from POST
            updated_contained_res_id_list = request.POST.getlist("resource_id_list")

            if len(updated_contained_res_id_list) > len(set(updated_contained_res_id_list)):
                raise Exception("Duplicate resources were found for adding to the collection")


            for updated_contained_res_id in updated_contained_res_id_list:
                # avoid adding collection itself
                if updated_contained_res_id == shortkey:
                    raise Exception("Can not add collection itself.")

                # check authorization for all new resources being added to the collection
                # the requesting user should at least have metadata view permission for each of the
                # new resources to be added to the collection
                if not collection_res_obj.resources.filter(short_id=updated_contained_res_id).exists():
                    res_to_add, _, _ = authorize(request, updated_contained_res_id,
                                                 needed_permission=ACTION_TO_AUTHORIZE.VIEW_METADATA)

            # remove all resources from the collection
            collection_res_obj.resources.clear()

            # add resources to the collection
            for updated_contained_res_id in updated_contained_res_id_list:
                updated_contained_res_obj = get_resource_by_shortkey(updated_contained_res_id)
                collection_res_obj.resources.add(updated_contained_res_obj)

            if collection_res_obj.can_be_public_or_discoverable:
                metadata_status = "Sufficient to make public"

            resource_modified(collection_res_obj, user)

    except Exception as ex:
        err_msg = "update_collection: {0} ; username: {1}; collection_id: {2} ."
        logger.error(err_msg.format(ex.message,
                     request.user.username if request.user.is_authenticated() else "anonymous",
                     shortkey))
        status = "error"
        msg = ex.message
    finally:
        ajax_response_data = {'status': status, 'msg': msg, 'metadata_status': metadata_status}
        return JsonResponse(ajax_response_data)


def update_collection_for_deleted_resources(request, shortkey, *args, **kwargs):
    """
    If there are any tracked deleted resource objects for a collection resource
    (identified by shortkey), those are deleted and resource bag is regenerated
    for the collection resource to avoid the possibility of broken links in resource map
    as a result of collection referenced resource being deleted by resource owner.
    """

    ajax_response_data = {'status': "success"}
    try:
        collection_res, is_authorized, user = authorize(request, shortkey,
                                                        needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

        if collection_res.resource_type.lower() != "collectionresource":
            raise Exception("Resource {0} is not a collection resource.".format(shortkey))

        resource_modified(collection_res, user)
        # remove all logged deleted resources for the collection
        collection_res.deleted_resources.all().delete()

    except Exception as ex:
        logger.error("Failed to update collection for deleted resources.Collection resource ID: {}. "
                     "Error:{} ".format(shortkey, ex.message))

        ajax_response_data = {'status': "error", 'message': ex.message}
    finally:
        return JsonResponse(ajax_response_data)

