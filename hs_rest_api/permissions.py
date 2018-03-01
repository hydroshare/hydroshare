from rest_framework import permissions

from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE


class CanViewOrEditResourceMetadata(permissions.BasePermission):
    """
    Global API permission to check basic resource permissions
    """

    def has_permission(self, request, view):
        if request.method == "GET":
            _, authorized, _ = authorize(request, view.kwargs['pk'],
                                         needed_permission=ACTION_TO_AUTHORIZE.VIEW_METADATA)
        else:
            _, authorized, _ = authorize(request, view.kwargs['pk'],
                                         needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
        return authorized


class CanEditResourceMetadata(permissions.BasePermission):
    """
    Global API permission to edit resource metadata
    """

    def has_permission(self, request, view):
        _, authorized, _ = authorize(request, view.kwargs['pk'],
                                     needed_permission=ACTION_TO_AUTHORIZE.SET_RESOURCE_FLAG)

        return authorized