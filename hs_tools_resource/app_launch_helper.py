from hs_core.models import get_user
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
from hs_tools_resource.models import SupportedResTypeChoices, ToolResource
from hs_tools_resource.utils import parse_app_url_template


def resource_level_tool_urls(resource_obj, request_obj):

    res_type_str = resource_obj.resource_type

    relevant_tools = []

    for choice_obj in SupportedResTypeChoices.objects.filter(description__iexact=res_type_str):
        for supported_res_types_obj in choice_obj.associated_with.all():
            tool_res_obj = ToolResource.objects.get(object_id=supported_res_types_obj.object_id)

            if _check_user_can_view_resource(request_obj, resource_obj) and \
               _check_user_can_view_app(request_obj, tool_res_obj) and \
               _check_app_supports_resource_sharing_status(resource_obj, tool_res_obj):

                tool_url = tool_res_obj.metadata.url_base.value \
                           if tool_res_obj.metadata.url_base else None
                tool_icon_url = tool_res_obj.metadata.app_icon.data_url \
                    if tool_res_obj.metadata.app_icon else "raise-img-error"
                hs_term_dict_user = {}
                hs_term_dict_user["HS_USR_NAME"] = request_obj.user.username if \
                    request_obj.user.is_authenticated() \
                    else "anonymous"
                tool_url_new = parse_app_url_template(
                        tool_url, [resource_obj.get_hs_term_dict(), hs_term_dict_user])
                if tool_url_new is not None:
                        tl = {'title': str(tool_res_obj.metadata.title.value),
                              'icon_url': tool_icon_url,
                              'url': tool_url_new,
                              'openwithlist': True if
                              _check_webapp_in_user_open_with_list(tool_res_obj, request_obj) or
                              _check_webapp_is_approved(tool_res_obj)
                              else False
                              }
                        relevant_tools.append(tl)
    return relevant_tools


def _check_user_can_view_app(request_obj, tool_res_obj):

    _, user_can_view_app, _ = authorize(
                request_obj, tool_res_obj.short_id,
                needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE,
                raises_exception=False)
    return user_can_view_app


def _check_webapp_in_user_open_with_list(tool_res_obj, request_obj):

    user_obj = get_user(request_obj)
    return tool_res_obj.rlabels.is_open_with_app(user_obj)


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
    supported_sharing_status_obj = tool_res_obj.metadata.\
        supported_sharing_status
    if supported_sharing_status_obj is not None:
        supported_sharing_status_str = supported_sharing_status_obj.\
                                      get_sharing_status_str()
        if len(supported_sharing_status_str) > 0:
                res_sharing_status = resource_obj.raccess.sharing_status
                if supported_sharing_status_str.lower().\
                        find(res_sharing_status.lower()) != -1:
                    sharing_status_supported = True
    else:
        # backward compatible: webapp without supported_sharing_status metadata
        # is considered to support all sharing status
        sharing_status_supported = True

    return sharing_status_supported
