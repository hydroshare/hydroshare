from rest_framework import permissions

from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE


class CanViewOrEditResourceMetadata(permissions.BasePermission):
    """
    Global API permission to check basic resource permissions
    """

    def has_permission(self, request, view):
        if request.method == "GET" and 'pk' in view.kwargs:
            _, authorized, _ = authorize(request, view.kwargs['pk'],
                                         needed_permission=ACTION_TO_AUTHORIZE.VIEW_METADATA)
        elif 'pk' in view.kwargs:
            _, authorized, _ = authorize(request, view.kwargs['pk'],
                                         needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
        else:
            # Just to get this to show up in swagger
            authorized = True

        return authorized
