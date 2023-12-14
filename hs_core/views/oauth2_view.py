from oauth2_provider.views.base import AuthorizationView
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.models import User
from django.shortcuts import redirect


class GroupRequiredMixin(AccessMixin):
    """
    Verify that the current user is in the specified group.
    Redirects to authorization group page if user is not part of the group.
    """

    def dispatch(self, request, *args, **kwargs):
        u = User.objects.get(pk=self.request.user.id)

        if not u.uaccess.my_groups.filter(id=kwargs['group_id']).exists():
            return redirect('group', group_id=kwargs['group_id'])
        return super().dispatch(request, *args, **kwargs)


class GroupAuthorizationView(AuthorizationView, GroupRequiredMixin):
    """
    Extends AuthorizationView with the GroupRequiredMixin
    """
