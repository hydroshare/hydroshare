from hs_core.models import get_user, BaseResource
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
from hs_tools_resource.models import SupportedResTypeChoices, ToolResource
from hs_tools_resource.utils import parse_app_url_template
from hs_tools_resource.app_keys import tool_app_key


def resource_level_tool_urls(resource_obj, request_obj):
    res_type_str = resource_obj.resource_type

    tool_list = []
    tool_res_id_list = []
    resource_level_app_counter = 0

    # associate resources with app tools using extended metadata name-value pair with 'appkey' key
    filterd_res_obj = BaseResource.objects.filter(short_id=resource_obj.short_id,
                                                  extra_metadata__has_key=tool_app_key).first()
    if filterd_res_obj:
        # check appkey matching with web app tool resources
        appkey_dict = {tool_app_key: filterd_res_obj.extra_metadata[tool_app_key]}
        for tool_res_obj in ToolResource.objects.filter(extra_metadata__contains=appkey_dict):
            # tool_res_obj has the same appkey-value pair so needs to associate with the resource
            if _check_user_can_view_resource(request_obj, resource_obj) and \
                    _check_user_can_view_app(request_obj, tool_res_obj) and \
                    _check_app_supports_resource_sharing_status(resource_obj,
                                                                tool_res_obj):
                is_open_with_app, tl = _get_app_tool_info(request_obj, resource_obj,
                                                          tool_res_obj, open_with=True)
                if tl:
                    tool_list.append(tl)
                    tool_res_id_list.append(tl['res_id'])
                    if is_open_with_app and tl['url']:
                        resource_level_app_counter += 1

    for choice_obj in SupportedResTypeChoices.objects.filter(description__iexact=res_type_str):
        for supported_res_types_obj in choice_obj.associated_with.all():
            tool_res_obj = ToolResource.objects.get(object_id=supported_res_types_obj.object_id)
            if tool_res_obj.short_id not in tool_res_id_list and \
                    _check_user_can_view_resource(request_obj, resource_obj) and \
                    _check_user_can_view_app(request_obj, tool_res_obj) and \
                    _check_app_supports_resource_sharing_status(resource_obj, tool_res_obj):

                is_open_with_app, tl = _get_app_tool_info(request_obj, resource_obj, tool_res_obj)
                if tl:
                    tool_list.append(tl)
                    if is_open_with_app and tl['url']:
                        resource_level_app_counter += 1

    if len(tool_list) > 0:
        return {"tool_list": tool_list,
                "resource_level_app_counter": resource_level_app_counter}
    else:
        return None


def _get_app_tool_info(request_obj, resource_obj, tool_res_obj, open_with=False):
    """
    get app tool info.
    :param request_obj: request object
    :param resource_obj: resource object
    :param tool_res_obj: web tool app resource object
    :param open_with: Default is False, meaning check has to be done to see whether
                      the web app resource should show on the resource's open with list;
                      if open_with is True, e.g., appkey extended metadata name-value pair
                      exists that associated this resource with the web app resource, no check
                      is needed, and this web app tool resource will show on this resource's
                      open with list
    :return: an info dict of web tool resource
    """
    tool_url_resource = tool_res_obj.metadata.url_base.value \
        if tool_res_obj.metadata.url_base else None
    tool_url_aggregation = tool_res_obj.metadata.url_base_aggregation.value \
        if tool_res_obj.metadata.url_base_aggregation else None
    tool_url_file = tool_res_obj.metadata.url_base_file.value \
        if tool_res_obj.metadata.url_base_file else None
    tool_icon_url = tool_res_obj.metadata.app_icon.data_url \
        if tool_res_obj.metadata.app_icon else "raise-img-error"

    url_key_values = get_app_dict(request_obj.user, resource_obj)

    tool_url_resource_new = parse_app_url_template(tool_url_resource, url_key_values)
    tool_url_agg_new = parse_app_url_template(tool_url_aggregation, url_key_values)
    tool_url_file_new = parse_app_url_template(tool_url_file, url_key_values)

    is_open_with_app = True if open_with else _check_open_with_app(tool_res_obj, request_obj)
    is_approved_app = _check_webapp_is_approved(tool_res_obj)
    agg_types = ""
    file_extensions = ""
    if (tool_url_agg_new and ("HS_JS_AGG_KEY" in tool_url_agg_new or
                              "HS_JS_FILE_KEY" in tool_url_agg_new)) or \
            (tool_url_file_new and ("HS_JS_AGG_KEY" in tool_url_file_new or
                                    "HS_JS_FILE_KEY" in tool_url_file_new)):
        if tool_res_obj.metadata._supported_agg_types.first():
            agg_types = tool_res_obj.metadata._supported_agg_types.first() \
                .get_supported_agg_types_str()
        if tool_res_obj.metadata.supported_file_extensions:
            file_extensions = tool_res_obj.metadata.supported_file_extensions.value

    if (tool_url_resource_new is not None) or \
            (tool_url_agg_new is not None) or \
            (tool_url_file_new is not None):
        tl = {'title': str(tool_res_obj.metadata.title.value),
              'res_id': tool_res_obj.short_id,
              'icon_url': tool_icon_url,
              'url': tool_url_resource_new,
              'url_aggregation': tool_url_agg_new,
              'url_file': tool_url_file_new,
              'openwithlist': is_open_with_app,
              'approved': is_approved_app,
              'agg_types': agg_types,
              'file_extensions': file_extensions
              }

        return is_open_with_app, tl
    else:
        return False, {}


def get_app_dict(user, resource):
    hs_term_dict_user = {}
    hs_term_dict_user["HS_USR_NAME"] = user.username if user.is_authenticated() else "anonymous"
    hs_term_dict_file = {}
    # HS_JS_AGG_KEY and HS_JS_FILE_KEY are overwritten by jquery to launch the url specific to each
    # file
    hs_term_dict_file["HS_AGG_PATH"] = "HS_JS_AGG_KEY"
    hs_term_dict_file["HS_FILE_PATH"] = "HS_JS_FILE_KEY"
    hs_term_dict_file["HS_MAIN_FILE"] = "HS_JS_MAIN_FILE_KEY"
    return [resource.get_hs_term_dict(), hs_term_dict_user, hs_term_dict_file]


def _check_user_can_view_app(request_obj, tool_res_obj):
    _, user_can_view_app, _ = authorize(
        request_obj, tool_res_obj.short_id,
        needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE,
        raises_exception=False)
    return user_can_view_app


def _check_open_with_app(tool_res_obj, request_obj):
    return _check_webapp_in_user_open_with_list(tool_res_obj, request_obj) or \
           _check_webapp_is_approved(tool_res_obj)


def _check_webapp_in_user_open_with_list(tool_res_obj, request_obj):
    if request_obj.user.is_authenticated():
        user_obj = get_user(request_obj)
        return tool_res_obj.rlabels.is_open_with_app(user_obj)
    else:
        return False


def _check_webapp_is_approved(tool_res_obj):
    try:
        return tool_res_obj.metadata.approved
    except Exception:
        return False


def _check_user_can_view_resource(request_obj, resource_obj):
    _, user_can_view_res, _ = authorize(
        request_obj, resource_obj.short_id,
        needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE,
        raises_exception=False)
    return user_can_view_res


def _check_app_supports_resource_sharing_status(resource_obj, tool_res_obj):
    sharing_status_supported = False
    supported_sharing_status_obj = tool_res_obj.metadata. \
        supported_sharing_status
    if supported_sharing_status_obj is not None:
        supported_sharing_status_str = supported_sharing_status_obj. \
            get_sharing_status_str()
        if len(supported_sharing_status_str) > 0:
            res_sharing_status = resource_obj.raccess.sharing_status
            if supported_sharing_status_str.lower(). \
                    find(res_sharing_status.lower()) != -1:
                sharing_status_supported = True
    else:
        # backward compatible: webapp without supported_sharing_status metadata
        # is considered to support all sharing status
        sharing_status_supported = True

    return sharing_status_supported
