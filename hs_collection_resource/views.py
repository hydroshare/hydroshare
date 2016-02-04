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


def update_collection(request):

    try:
        collection_obj_resource_id = request.POST["collection_obj_res_id"]
        is_authorized = authorize(request, collection_obj_resource_id, edit=True, raises_exception=True)[1]
        if is_authorized:
            collection_res_obj = hydroshare.get_resource_by_shortkey(collection_obj_resource_id)
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
                COLLECTION_ITEMS=collection_content_res_id_list
                )

            if collection_res_obj.metadata.has_all_required_elements():
                for res in collection_res_obj.metadata.collection_items.first().collection_items.all():
                    all_public = True
                    no_private = True
                    if not res.raccess.public:
                        all_public = False
                        if not res.raccess.discoverable:
                            no_private = False
                            break
                if all_public:
                    metadata_status = "Sufficient to make public or discoverable"
                elif no_private:
                    metadata_status = "Sufficient to make discoverable"
                else:
                    metadata_status = "Insufficient to make public or discoverable"
            else:
                metadata_status = "Insufficient to make public or discoverable"

            ajax_response_data = {'status': 'success', 'element_name': "CollectionItems", 'metadata_status': metadata_status}
            return HttpResponse(json.dumps(ajax_response_data))

    except Exception as ex:
        ajax_response_data = {'status': 'error', 'message': ex.message}
        return HttpResponse(json.dumps(ajax_response_data))


