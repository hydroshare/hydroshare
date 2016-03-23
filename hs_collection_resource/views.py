import json
import logging

from django.http import HttpResponseRedirect, HttpResponseNotFound, HttpResponse, JsonResponse

from hs_core import hydroshare
from hs_core.views import set_resource_flag
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
from hs_core.hydroshare.utils import user_from_id, resource_modified
from hs_core.models import BaseResource

logger = logging.getLogger(__name__)

# update collection content (member resources)
def update_collection(request, shortkey, *args, **kwargs):

    status = "success"
    msg = ""
    try:
        collection_res_obj, is_authorized, user = authorize(request, shortkey,
                                              needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                              raises_exception=False)
        if not is_authorized:
            raise Exception("User has no Edit permission over collection {0}.".format(shortkey))
        if collection_res_obj.resource_type != "CollectionResource":
            raise Exception("Resource {0} is not a collection resource.".format(shortkey))

        # get res_id list from POST
        updated_contained_res_id_list = []
        for res_id in request.POST.getlist("resource_id_list"):
            updated_contained_res_id_list.append(res_id)

        for updated_contained_res_id in updated_contained_res_id_list:
            updated_contained_res_obj, is_authorized, user = authorize(request, shortkey,
                                              needed_permission=ACTION_TO_AUTHORIZE.View_RESOURCE,
                                              raises_exception=False)
            if updated_contained_res_obj in collection_res_obj.resources:
                # skip resource that is already in collection
                continue
            if is_authorized or updated_contained_res_obj.raccess.discoverable:
               # user has permission or this res is not private
               collection_res_obj.resources.add(updated_contained_res_obj)
            else:
                raise Exception("User has no permission over resource {}.".format(updated_contained_res_id))

    except Exception as ex:
        logger.error("update_collection: {0} ; username: {1}; collection_id: {2} ".
                         format(ex.message,
                                request.user.username if request.user.is_authenticated() else "anonymous",
                                shortkey))
        status = "error"
        msg = ex.message
    finally:
        ajax_response_data = {'status': status, 'msg': msg}
        return JsonResponse(ajax_response_data)

# loop through member resources in collection ("shortkey") to check if the target user ("user_id") has
# at least View permission over them.
def collection_member_permission(request, shortkey, user_id, *args, **kwargs):
    try:
        collection_res_obj, is_authorized, user = authorize(request, shortkey,
                                              needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE,
                                              raises_exception=True)
        no_permission_list = []

        user_to_share_with = user_from_id(user_id)
        if collection_res_obj.metadata.collection:
            for res_in_collection in collection_res_obj.metadata.collection.resources.all():
                if not user_to_share_with.uaccess.can_view_resource(res_in_collection) \
                   and not res_in_collection.raccess.public and not res_in_collection.raccess.discoverable:
                    no_permission_list.append(res_in_collection.short_id)
            status = "success"
            ajax_response_data = {'status': status, 'no_permission_list': no_permission_list}
        else:
            raise Exception("Collection element is not yet initialized.")
    except Exception as ex:
        logger.warning("collection_member_permission: %s" % (ex.message))
        ajax_response_data = {'status': "error", 'message': ex.message}
    finally:
        return JsonResponse(ajax_response_data)
