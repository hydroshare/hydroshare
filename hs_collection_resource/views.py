from __future__ import absolute_import
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.utils.timezone import now
from django import forms
from django.http import HttpResponseRedirect, HttpResponseNotFound, HttpResponse
from mezzanine.pages.page_processors import processor_for
from ga_resources.utils import json_or_jsonp
from hs_core import hydroshare, page_processors
from hs_core.hydroshare.hs_bagit import create_bag
from hs_core.models import ResourceFile
from .models import CollectionResource
import requests
from lxml import etree
import datetime
from django.utils.timezone import now
import os
import json
from hs_core.signals import post_create_resource
import ast
from hs_core.views.utils import authorize
from hs_core.hydroshare.utils import user_from_id
from hs_core.views import _set_resource_sharing_status


def update_collection(request):

    try:
        collection_obj_resource_id = request.POST["collection_obj_res_id"]
        collection_res_obj, is_authorized, user = authorize(request, collection_obj_resource_id, edit=True, raises_exception=True)
        if is_authorized:
            # collection_res_obj = hydroshare.get_resource_by_shortkey(collection_obj_resource_id)
            collection_content_res_id_list = []
            for res_id in request.POST.getlist("collection_items"):
                collection_content_res_id_list.append(res_id)

            if collection_res_obj.metadata.collection_items.first() is not None:
                element_id = collection_res_obj.metadata.collection_items.first().id
                hydroshare.resource.update_metadata_element(collection_res_obj.short_id,
                'CollectionItems',
                collection_items=collection_content_res_id_list,
                element_id = element_id
                )
            else:
                hydroshare.resource.create_metadata_element(collection_res_obj.short_id,
                'CollectionItems',
                collection_items=collection_content_res_id_list
                )

            current_sharing_status = "Private"
            if collection_res_obj.raccess.discoverable:
                current_sharing_status = "Discoverable"
            elif collection_res_obj.raccess.public:
                current_sharing_status = "Public"

            new_sharing_status = ""
            if collection_res_obj.raccess.public or collection_res_obj.raccess.discoverable:
                for checked_res_id in collection_content_res_id_list:
                    res_checked = hydroshare.get_resource_by_shortkey(checked_res_id)
                    if not res_checked.raccess.public and not res_checked.raccess.discoverable:
                        _set_resource_sharing_status(request, user, collection_res_obj, flag_to_set='public', flag_value=False)
                        new_sharing_status = "Private"

            user_permission = "Edit"
            _, is_owner, _ = authorize(request, collection_obj_resource_id, full=True, raises_exception=False)
            if is_owner:
                user_permission = "Own"

            if collection_res_obj.metadata.has_all_required_elements():
                metadata_status = "Sufficient to make public"
            else:
                metadata_status = "Insufficient to make public"

            ajax_response_data = {'status': 'success', 'user_permission': user_permission, 'current_sharing_status': current_sharing_status, 'new_sharing_status': new_sharing_status, 'metadata_status': metadata_status}
            return HttpResponse(json.dumps(ajax_response_data))

    except Exception as ex:
        ajax_response_data = {'status': 'error', 'message': ex.message}
        return HttpResponse(json.dumps(ajax_response_data))


def collection_member_permission(request, shortkey, user_id, *args, **kwargs):
    try:
        collection_res_obj, is_authorized, user = authorize(request, shortkey, view=True, edit=True, \
                                                  full=True, superuser=True, raises_exception=True)
        no_permission_list = []
        if is_authorized:
            user_to_share_with = user_from_id(user_id)
            if collection_res_obj.metadata.collection_items.first() is not None:
                for res_in_collection in collection_res_obj.metadata.collection_items.first().collection_items.all():
                    if not user_to_share_with.uaccess.can_view_resource(res_in_collection):
                        no_permission_list.append(res_in_collection.short_id)
                status = "success"
                ajax_response_data = {'status': status, 'no_permission_list': no_permission_list}
                return HttpResponse(json.dumps(ajax_response_data))
            else:
                raise Exception("Collection member metadata is not yet initialized.")
    except Exception as ex:
        ajax_response_data = {'status': "error", 'message': ex.message}
        return HttpResponse(json.dumps(ajax_response_data))
