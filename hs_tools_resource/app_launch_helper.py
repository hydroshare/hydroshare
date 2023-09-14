from hs_core.models import get_user
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
from hs_file_types.utils import get_aggregation_types
from hs_tools_resource.app_keys import tool_app_key
from hs_tools_resource.models import ToolResource
from hs_tools_resource.utils import parse_app_url_template, get_SupportedResTypes_choices


def resource_level_tool_urls(resource_obj, request_obj):
    if not _check_user_can_view_resource(request_obj, resource_obj):
        return None

    tool_list = []
    tool_res_id_list = []
    resource_level_app_counter = 0

    supported_res_types = [res_type[0] for res_type in get_SupportedResTypes_choices()]
    if resource_obj.resource_type in supported_res_types and tool_app_key in resource_obj.extra_metadata:
        # check matching appkey with web app tool resources
        appkey_dict = {tool_app_key: resource_obj.extra_metadata[tool_app_key]}
        for tool_res_obj in ToolResource.objects.filter(extra_metadata__contains=appkey_dict):
            # tool_res_obj has the same appkey-value pair so needs to associate with the resource
            if _check_user_can_view_app(request_obj, tool_res_obj) and \
                    _check_app_supports_resource_sharing_status(resource_obj, tool_res_obj):
                tl = _get_app_tool_info(request_obj, resource_obj, tool_res_obj, open_with=True)
                if tl:
                    tool_list.append(tl)
                    tool_res_id_list.append(tl['res_id'])
                    if tl['url']:
                        resource_level_app_counter += 1

    for tool_res_obj in ToolResource.objects.exclude(short_id__in=tool_res_id_list):
        tool_metadata = tool_res_obj.metadata
        if not tool_metadata.supported_resource_types:
            continue
        if tool_metadata.supported_resource_types.supported_res_types.filter(
                description__iexact=resource_obj.resource_type).exists():
            if _check_user_can_view_app(request_obj, tool_res_obj) and \
                    _check_app_supports_resource_sharing_status(resource_obj, tool_res_obj):

                tl = _get_app_tool_info(request_obj, resource_obj, tool_res_obj)
                if tl:
                    tool_list.append(tl)
                    if tl['url']:
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
                      if open_with is True, e.g., appkey additional metadata name-value pair
                      exists that associated this resource with the web app resource, no check
                      is needed, and this web app tool resource will show on this resource's
                      open with list
    :return: an info dict of web tool resource
    """
    is_open_with_app = True if open_with else _check_open_with_app(tool_res_obj, request_obj)
    is_approved_app = False
    if not is_open_with_app:
        is_approved_app = _check_webapp_is_approved(tool_res_obj)
    if not is_approved_app and not is_open_with_app:
        return {}

    tool_metadata = tool_res_obj.metadata
    tool_url_resource = tool_metadata.url_base.value \
        if tool_metadata.url_base else None
    tool_url_aggregation = tool_metadata.url_base_aggregation.value \
        if tool_metadata.url_base_aggregation else None
    tool_url_file = tool_metadata.url_base_file.value \
        if tool_metadata.url_base_file else None
    tool_icon_url = tool_metadata.app_icon.data_url \
        if tool_metadata.app_icon else "raise-img-error"

    url_key_values = get_app_dict(request_obj.user, resource_obj, tool_res_obj)
    tool_url_resource_new = None
    if tool_app_key in resource_obj.extra_metadata and tool_app_key in tool_res_obj.extra_metadata:
        if resource_obj.extra_metadata[tool_app_key] == tool_res_obj.extra_metadata[tool_app_key]:
            tool_url_resource_new = parse_app_url_template(tool_url_resource, url_key_values)
    elif tool_app_key not in tool_res_obj.extra_metadata:
        tool_url_resource_new = parse_app_url_template(tool_url_resource, url_key_values)

    tool_url_agg_new = parse_app_url_template(tool_url_aggregation, url_key_values)
    tool_url_file_new = parse_app_url_template(tool_url_file, url_key_values)

    agg_types = ""
    file_extensions = ""
    tool_appkey = ""
    supported_aggr_types = tool_metadata.supported_aggregation_types
    if supported_aggr_types is not None:
        agg_types = supported_aggr_types.get_supported_agg_types_str()
        tool_appkey = tool_res_obj.extra_metadata.get(tool_app_key, '')

    if tool_url_agg_new is not None and not agg_types:
        # make the tool available for all aggregation types
        agg_type_cls_names = [agg_type.__name__ for agg_type in get_aggregation_types()]
        agg_types = ",".join(agg_type_cls_names)

    supported_file_extensions = tool_metadata.supported_file_extensions
    if supported_file_extensions:
        file_extensions = supported_file_extensions.value

    if any([tool_url_resource_new is not None, tool_url_agg_new is not None, tool_url_file_new is not None]):
        tl = {'title': str(tool_res_obj.metadata.title.value),
              'res_id': tool_res_obj.short_id,
              'icon_url': tool_icon_url,
              'url': tool_url_resource_new,
              'url_aggregation': tool_url_agg_new,
              'url_file': tool_url_file_new,
              'agg_types': agg_types,
              'tool_appkey': tool_appkey,
              'file_extensions': file_extensions,
              }

        return tl
    else:
        return {}


def get_app_dict(user, resource, web_app_resource):
    hs_term_dict_user = {}
    hs_term_dict_user["HS_USR_NAME"] = user.username if user.is_authenticated else "anonymous"
    hs_term_dict_file = {}
    # HS_JS_AGG_KEY and HS_JS_FILE_KEY are overwritten by jquery to launch the url specific to each
    # file
    hs_term_dict_file["HS_AGG_PATH"] = "HS_JS_AGG_KEY"
    hs_term_dict_file["HS_FILE_PATH"] = "HS_JS_FILE_KEY"
    hs_term_dict_file["HS_MAIN_FILE"] = "HS_JS_MAIN_FILE_KEY"
    default_resource_term_dict = web_app_resource.extra_metadata.copy()
    default_resource_term_dict.update(resource.get_hs_term_dict())
    return [default_resource_term_dict, hs_term_dict_user, hs_term_dict_file]


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
    if request_obj.user.is_authenticated:
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
