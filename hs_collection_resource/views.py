import logging
from dateutil import parser

from django.http import JsonResponse
from django.db import transaction

from hs_core.hydroshare.utils import current_site_url, get_resource_by_shortkey, resource_modified
from hs_core.models import BaseResource
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE

from .utils import add_or_remove_relation_metadata, update_collection_list_csv

logger = logging.getLogger(__name__)
UI_DATETIME_FORMAT = "%m/%d/%Y"


# update collection
def update_collection(request, shortkey, *args, **kwargs):
    """
    Update collection. The POST request should contain a
    list of resource ids and a 'update_type' parameter with value of 'set', 'add' or 'remove',
    which are three differnt mode to update the collection.If no 'update_type' parameter is
    provided, the 'set' will be used by default.
    To add a resource to collection, user should have certain premission on both collection
    and resources being added.
    For collection: user should have at least Edit permission
    For resources being added, one the following criteria should be met:
    1) user has at lest View permission and the resource is Shareable
    2) user is resource owner
    :param shortkey: id of the collection resource to which resources are to be added.
    """

    status = "success"
    msg = ""
    metadata_status = "Insufficient to make public"
    new_coverage_list = []
    hasPart = "hasPart"

    try:
        with transaction.atomic():
            collection_res_obj, is_authorized, user \
                = authorize(request, shortkey,
                            needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

            if collection_res_obj.resource_type.lower() != "collectionresource":
                raise Exception("Resource {0} is not a collection resource.".format(shortkey))

            # get 'resource_id_list' list from POST
            updated_contained_res_id_list = request.POST.getlist("resource_id_list")

            # get optional 'update_type' parameter:
            # 1) "set" (default): set collection content to the list,
            # following code will find out which resources are newly added, removed and unchanged
            # 2) 'add': add resources in the list to collection
            # adding a resource that is already in the collection will raise error
            # 3) 'remove': remove resources in the list from collection
            # removing a resource that is not in collection will raise error
            update_type = request.POST.get("update_type", 'set').lower()

            if update_type not in ["set", "add", "remove"]:
                raise Exception("Invalid value of 'update_type' parameter")

            if len(updated_contained_res_id_list) > len(set(updated_contained_res_id_list)):
                raise Exception("Duplicate resources exist in list 'resource_id_list'")

            for updated_contained_res_id in updated_contained_res_id_list:
                # avoid adding collection itself
                if updated_contained_res_id == shortkey:
                    raise Exception("Can not contain collection itself.")

            # current contained res
            res_id_list_current_collection = \
                [res.short_id for res in collection_res_obj.resources.all()]

            # res to remove
            res_id_list_remove = []
            if update_type == "remove":
                res_id_list_remove = updated_contained_res_id_list
                for res_id_remove in res_id_list_remove:
                    if res_id_remove not in res_id_list_current_collection:
                        raise Exception('Cannot remove resource {0} as it '
                                        'is not currently contained '
                                        'in collection'.format(res_id_remove))
            elif update_type == "set":
                for res_id_remove in res_id_list_current_collection:
                    if res_id_remove not in updated_contained_res_id_list:
                        res_id_list_remove.append(res_id_remove)

            for res_id_remove in res_id_list_remove:
                # user with Edit permission over this collection can remove any resource from it
                res_obj_remove = get_resource_by_shortkey(res_id_remove)
                collection_res_obj.resources.remove(res_obj_remove)

                # change "Relation" metadata in collection
                res_remove = BaseResource.objects.get(short_id=res_id_remove)
                value = current_site_url(res_remove.get_absolute_url())
                add_or_remove_relation_metadata(add=False, target_res_obj=collection_res_obj,
                                                relation_type=hasPart, relation_value=value,
                                                set_res_modified=False)

            # res to add
            res_id_list_add = []
            if update_type == "add":
                res_id_list_add = updated_contained_res_id_list
                for res_id_add in res_id_list_add:
                    if res_id_add in res_id_list_current_collection:
                        raise Exception('Cannot add resource {0} as it '
                                        'is already contained in collection'.format(res_id_add))
            elif update_type == "set":
                for res_id_add in updated_contained_res_id_list:
                    if res_id_add not in res_id_list_current_collection:
                        res_id_list_add.append(res_id_add)
            for res_id_add in res_id_list_add:
                # check authorization for all new resources being added to the collection
                # the requesting user should at least have metadata view permission for each of
                # the new resources to be added to the collection
                res_to_add, _, _ \
                    = authorize(request, res_id_add,
                                needed_permission=ACTION_TO_AUTHORIZE.VIEW_METADATA)

                # the resources being added should be 'Shareable'
                # or is owned by current user
                is_shareable = res_to_add.raccess.shareable
                is_owner = res_to_add.raccess.owners.filter(pk=user.pk).exists()
                if not is_shareable and not is_owner:
                        raise Exception('Only resource owner can add a non-shareable '
                                        'resource to a collection ')

                # add this new res to collection
                res_obj_add = get_resource_by_shortkey(res_id_add)
                collection_res_obj.resources.add(res_obj_add)

                # change "Relation" metadata in collection
                res_remove = BaseResource.objects.get(short_id=res_id_add)
                value = current_site_url(res_remove.get_absolute_url())
                add_or_remove_relation_metadata(add=True, target_res_obj=collection_res_obj,
                                                relation_type=hasPart, relation_value=value,
                                                set_res_modified=False)

            if collection_res_obj.can_be_public_or_discoverable:
                metadata_status = "Sufficient to make public"

            new_coverage_list = _update_collection_coverages(collection_res_obj)

            update_collection_list_csv(collection_res_obj)

            resource_modified(collection_res_obj, user, overwrite_bag=False)

    except Exception as ex:
        err_msg = "update_collection: {0} ; username: {1}; collection_id: {2} ."
        logger.error(err_msg.format(ex.message,
                     request.user.username if request.user.is_authenticated() else "anonymous",
                     shortkey))
        status = "error"
        msg = ex.message
    finally:
        ajax_response_data = \
            {'status': status, 'msg': msg,
             'metadata_status': metadata_status,
             'new_coverage_list': new_coverage_list}
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
        with transaction.atomic():
            collection_res, is_authorized, user \
                = authorize(request, shortkey,
                            needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

            if collection_res.resource_type.lower() != "collectionresource":
                raise Exception("Resource {0} is not a collection resource.".format(shortkey))

            # handle "Relation" metadata
            hasPart = "hasPart"
            for deleted_res_log in collection_res.deleted_resources:
                relation_value = deleted_res_log.resource_url
                add_or_remove_relation_metadata(add=False,
                                                target_res_obj=collection_res,
                                                relation_type=hasPart,
                                                relation_value=relation_value,
                                                set_res_modified=False)

            new_coverage_list = _update_collection_coverages(collection_res)
            ajax_response_data['new_coverage_list'] = new_coverage_list

            # remove all logged deleted resources for the collection
            collection_res.deleted_resources.all().delete()

            update_collection_list_csv(collection_res)

            resource_modified(collection_res, user, overwrite_bag=False)

    except Exception as ex:
        logger.error("Failed to update collection for "
                     "deleted resources.Collection resource ID: {}. "
                     "Error:{} ".format(shortkey, ex.message))
        logger.error(ex)

        ajax_response_data = {'status': "error", 'message': ex.message}
    finally:
        return JsonResponse(ajax_response_data)


def calculate_collection_coverages(request, shortkey, *args, **kwargs):
    """
    Calculate latest coverages of the specified collection resource
    This func is a wrapper of the _calculate_collection_coverages func
    """
    ajax_response_data = {'status': "success"}
    try:
        collection_res, is_authorized, user \
            = authorize(request, shortkey,
                        needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)

        if collection_res.resource_type.lower() != "collectionresource":
            raise Exception("Resource {0} is not a collection resource.".format(shortkey))

        new_coverage_list = _calculate_collection_coverages(collection_res)
        ajax_response_data['new_coverage_list'] = new_coverage_list

    except Exception as ex:
        logger.error("Failed to calculate collection coverages. Collection resource ID: {0}. "
                     "Error:{1} ".format(shortkey, ex.message))

        ajax_response_data = {'status': "error", 'message': ex.message}
    finally:
        return JsonResponse(ajax_response_data)


def _update_collection_coverages(collection_res_obj):
    """
    Update the collection coverages metadata records in db.
    This func always removes all existing coverage metadata instances first,
    and then create new ones if needed.
    The element id of new created coverage metadata instance is stored in key "element_id_str".
    :param collection_res_obj: instance of CollectionResource type
    :return: a list of coverage metadata dict
    """
    new_coverage_list = _calculate_collection_coverages(collection_res_obj)

    with transaction.atomic():
        collection_res_obj.metadata.coverages.all().delete()
        for cvg in new_coverage_list:
            element = collection_res_obj.\
                metadata.create_element('Coverage',
                                        type=cvg['type'],
                                        value=cvg['value'])
            cvg["element_id_str"] = str(element.id)

    return new_coverage_list


def _calculate_collection_coverages(collection_res_obj):
    """
    Calculate the overall coverages of all contained resources
    :param collection_res_obj: instance of CollectionResource type
    :return: a list of coverage metadata dict
    """
    res_id = collection_res_obj.short_id
    new_coverage_list = []

    lon_list = []
    lat_list = []
    time_list = []
    output_spatial_projection_str = "WGS84 EPSG:4326"
    output_spatial_units_str = "Decimal degrees"
    for contained_res_obj in collection_res_obj.resources.all():
        for cvg in contained_res_obj.metadata.coverages.all():
            if cvg.type.lower() == "box":
                lon_list.append(float(cvg.value["eastlimit"]))
                lon_list.append(float(cvg.value["westlimit"]))
                lat_list.append(float(cvg.value["northlimit"]))
                lat_list.append(float(cvg.value["southlimit"]))
            elif cvg.type.lower() == "point":
                lon_list.append(float(cvg.value["east"]))
                lat_list.append(float(cvg.value["north"]))
            elif cvg.type.lower() == "period":
                try:
                    if cvg.value.get("start", None) is not None:
                        start_date = parser.parse(cvg.value["start"])
                        time_list.append(start_date)
                    if cvg.value.get("end", None) is not None:
                        end_date = parser.parse(cvg.value["end"])
                        time_list.append(end_date)
                except ValueError as ex:
                    # skip the res if it has invalid datetime string
                    logger.warning("_calculate_collection_coverages: "
                                   "Ignore unknown datetime string. "
                                   "Collection resource ID: {0}. "
                                   "Contained res ID: {1}"
                                   "Msg: {2} ".
                                   format(res_id,
                                          contained_res_obj.short_id, ex.message))

    # spatial coverage
    if len(lon_list) > 0 and len(lat_list) > 0:
        value_dict = {}
        type_str = 'point'
        lon_min = min(lon_list)
        lon_max = max(lon_list)
        lat_min = min(lat_list)
        lat_max = max(lat_list)
        if lon_min == lon_max and lat_min == lat_max:
            type_str = 'point'
            value_dict['east'] = lon_min
            value_dict['north'] = lat_min
            value_dict['units'] = output_spatial_units_str
        else:
            type_str = 'box'
            value_dict['eastlimit'] = lon_max
            value_dict['westlimit'] = lon_min
            value_dict['northlimit'] = lat_max
            value_dict['southlimit'] = lat_min
            value_dict['units'] = output_spatial_units_str,
            value_dict['projection'] = output_spatial_projection_str

        new_coverage_list.append({'type': type_str,
                                  'value': value_dict, 'element_id_str': "-1"})

    # temporal coverage
    if len(time_list) > 0:
        time_start = min(time_list)
        time_end = max(time_list)
        value_dict = {'start': time_start.strftime(UI_DATETIME_FORMAT),
                      'end': time_end.strftime(UI_DATETIME_FORMAT)}

        new_coverage_list.append({'type': 'period',
                                  'value': value_dict, 'element_id_str': "-1"})

    return new_coverage_list
