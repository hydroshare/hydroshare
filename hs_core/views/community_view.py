from __future__ import absolute_import

import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from hs_access_control.management.utilities import user_from_name
from hs_access_control.models.privilege import PrivilegeCodes

logger = logging.getLogger(__name__)


class CommunitiesView(TemplateView):
    template_name = 'pages/communities.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(CommunitiesView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        user_id = User.objects.get(pk=self.request.user.id)
        user = user_from_name(user_id)
        groups_owner = user.uaccess.get_groups_with_explicit_access(PrivilegeCodes.OWNER)
        communities_owner = user.uaccess.get_communities_with_explicit_access(PrivilegeCodes.OWNER)
        return {
            'user_id': user_id,
            'groups_owner': groups_owner,
            'communities_owner': communities_owner,
        }
