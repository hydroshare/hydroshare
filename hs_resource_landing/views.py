import logging
import time
from collections import namedtuple

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from rest_framework.views import APIView

from hs_core.models import GenericResource

logger = logging.getLogger(__name__)

DateRange = namedtuple('DateRange', ['start', 'end'])


class ResourceLandingView(TemplateView):

    def get(self, request, *args, **kwargs):
        maps_key = settings.MAPS_KEY if hasattr(settings, 'MAPS_KEY') else ''
        return render(request, 'hs_resource_landing/index.html', {'maps_key': maps_key})


@method_decorator(login_required, name='dispatch')
class ResourceLandingAPI(APIView):

    def __init__(self, **kwargs):
        super(ResourceLandingAPI, self).__init__(**kwargs)

    def get(self, request, *args, **kwargs):
        """
        Description
        """
        start = time.time()
        # resources = GenericResource.objects.all()
        user = User.objects.get(pk=self.request.user.id)

        grps_member_of = []
        groups = Group.objects.filter(gaccess__active=True).exclude(name="Hydroshare Author")
        # for each group set group dynamic attributes
        for g in groups:
            g.is_user_member = user in g.gaccess.members
            if g.is_user_member:
                grps_member_of.append(g)

        # content_model = page.get_content_model()
        # whether the user has permission to view this resource
        # can_view = content_model.can_view(request)
        # if not can_view:
        #     if user.is_authenticated():
        #         raise PermissionDenied()
        #     return redirect_to_login(request.path)

        # discoverable = content_model.raccess.discoverable
        # validation_error = None
        # resource_is_mine = False
        # if user.is_authenticated():
        #     resource_is_mine = content_model.rlabels.is_mine(user)
        #
        # metadata_status = _get_metadata_status(content_model)
        #
        # belongs_to_collections = content_model.collections.all()
        # discoverable = GenericResource.discoverable_resources.all()
        # public = GenericResource.public_resources.all()

        return JsonResponse({
            'data': 'Sample Test Data',
            'time': (time.time() - start) / 1000
        }, status=200)
