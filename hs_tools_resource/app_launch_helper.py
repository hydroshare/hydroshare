from django.contrib.contenttypes.models import ContentType

from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
from hs_tools_resource.models import SupportedResTypeChoices, ToolResource, SupportedFileTypeChoices
from hs_tools_resource.utils import parse_app_url_template


def resource_level_tool_urls(resource_obj, request_obj):

    res_type_str = resource_obj.resource_type

    relevant_tools = []

    for choice_obj in SupportedResTypeChoices.objects.filter(description__iexact=res_type_str):
        for supported_res_types_obj in choice_obj.associated_with.all():
            tool_res_obj = ToolResource.objects.get(object_id=supported_res_types_obj.object_id)

            if _check_user_can_view_app(request_obj, tool_res_obj) and \
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
                        tool_url, [tool_res_obj.get_hs_term_dict(), hs_term_dict_user])
                if tool_url_new is not None:
                        tl = {'title': str(tool_res_obj.metadata.title.value),
                              'icon_url': tool_icon_url,
                              'url': tool_url_new}
                        relevant_tools.append(tl)
    return relevant_tools


def filetype_level_app_urls(file_type_str,
                            logical_file_id,
                            res_obj,
                            request_obj
                            ):

    relevant_tools = []
    for choice_obj in SupportedFileTypeChoices.objects.filter(description__iexact=file_type_str):
        for supported_file_types_obj in choice_obj.associated_with.all():
            tool_res_obj = ToolResource.objects.get(object_id=supported_file_types_obj.object_id)

            if _check_user_can_view_app(request_obj, tool_res_obj) and \
               _check_app_supports_resource_sharing_status(res_obj, tool_res_obj):
                tool_url = tool_res_obj.metadata.url_template_file_type.value \
                           if tool_res_obj.metadata.url_template_file_type else None
                tool_icon_url = tool_res_obj.metadata.app_icon.data_url \
                                if tool_res_obj.metadata.app_icon else "raise-img-error"
                hs_term_dict_additional = {}
                hs_term_dict_additional["HS_USR_NAME"] = request_obj.user.username if \
                                                         request_obj.user.is_authenticated() \
                                                         else "anonymous"

                file_type_ctype = ContentType.objects.get(app_label="hs_file_types",
                                                          model=file_type_str.lower())
                file_type_obj = file_type_ctype.get_object_for_this_type(id=logical_file_id)

                tool_url_new = parse_app_url_template(
                        tool_url, [tool_res_obj.get_hs_term_dict(),
                                   hs_term_dict_additional,
                                   file_type_obj.get_hs_term_dict()])
                if tool_url_new is not None:
                    tl = {'title': str(tool_res_obj.metadata.title.value),
                          'icon_url': tool_icon_url,
                          'url': tool_url_new}
                    relevant_tools.append(tl)
    return relevant_tools


def _check_user_can_view_app(request_obj, tool_res_obj):

    user_can_view_app = authorize(
                request_obj, tool_res_obj.short_id,
                needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE,
                raises_exception=False)[1]
    return user_can_view_app


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
