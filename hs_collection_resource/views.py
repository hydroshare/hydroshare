import logging
from dateutil import parser

from django.http import JsonResponse
from django.db import transaction

from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
from hs_core.hydroshare.utils import get_resource_by_shortkey, resource_modified

logger = logging.getLogger(__name__)
UI_DATETIME_FORMAT = "%m/%d/%Y"


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
    new_coverage_list = []
    try:
        with transaction.atomic():
            collection_res_obj, is_authorized, user \
                = authorize(request, shortkey,
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
                if not collection_res_obj.\
                        resources.filter(short_id=updated_contained_res_id).exists():
                    res_to_add, _, _ \
                        = authorize(request, updated_contained_res_id,
                                    needed_permission=ACTION_TO_AUTHORIZE.VIEW_METADATA)

            # remove all resources from the collection
            collection_res_obj.resources.clear()

            # add resources to the collection
            for updated_contained_res_id in updated_contained_res_id_list:
                updated_contained_res_obj = get_resource_by_shortkey(updated_contained_res_id)
                collection_res_obj.resources.add(updated_contained_res_obj)

            if collection_res_obj.can_be_public_or_discoverable:
                metadata_status = "Sufficient to make public"

            new_coverage_list = _update_collection_coverages(collection_res_obj)

            resource_modified(collection_res_obj, user)

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
        collection_res, is_authorized, user \
            = authorize(request, shortkey,
                        needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

        if collection_res.resource_type.lower() != "collectionresource":
            raise Exception("Resource {0} is not a collection resource.".format(shortkey))

        new_coverage_list = _update_collection_coverages(collection_res)
        ajax_response_data['new_coverage_list'] = new_coverage_list

        resource_modified(collection_res, user)
        # remove all logged deleted resources for the collection
        collection_res.deleted_resources.all().delete()

    except Exception as ex:
        logger.error("Failed to update collection for "
                     "deleted resources.Collection resource ID: {}. "
                     "Error:{} ".format(shortkey, ex.message))

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
    try:
        with transaction.atomic():
            collection_res_obj.metadata.coverages.all().delete()
            for cvg in new_coverage_list:
                element = collection_res_obj.\
                    metadata.create_element('Coverage',
                                            type=cvg['type'],
                                            value=cvg['value'])
                cvg["element_id_str"] = str(element.id)

            return new_coverage_list
    except Exception as ex:
        raise Exception("Failed to update collection coverages: {0}".format(ex.message))


def _calculate_collection_coverages(collection_res_obj):
    """
    Calculate the overall coverages of all contained resources
    :param collection_res_obj: instance of CollectionResource type
    :return: a list of coverage metadata dict
    """
    res_id = collection_res_obj.short_id
    new_coverage_list = []
    try:
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

    except Exception as ex:
        raise Exception("Failed to calculate collection coverages: {0}".format(ex.message))
