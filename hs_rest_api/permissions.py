from rest_framework import permissions

from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE


class CanViewOrEditResourceMetadata(permissions.BasePermission):
    """
    Global API permission to check basic resource permissions
    """

    def has_permission(self, request, view):
        if not view.kwargs.get('pk', False):
            return True

        if request.method == "GET":
            _, authorized, _ = authorize(request, view.kwargs.get('pk'),
                                         needed_permission=ACTION_TO_AUTHORIZE.VIEW_METADATA)
        else:
            _, authorized, _ = authorize(request, view.kwargs.get('pk'),
                                         needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
        return authorized
