from __future__ import absolute_import
import logging
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ParseError

from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
from hs_core.hydroshare import utils as hs_core_utils
from hs_access_control.models import PrivilegeCodes

logger = logging.getLogger(__name__)


class ShareResourceUser(APIView):

    @swagger_auto_schema(operation_description="Set user privileges of a resource")
    def post(self, request, pk, privilege, user_id):
        res, _, user = authorize(request, pk,
                                 needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
        to_user = hs_core_utils.user_from_id(user_id)
        privilege_code = PrivilegeCodes.from_string(privilege)
        if not privilege_code:
            raise ParseError("Bad privilege code")
        if privilege_code == PrivilegeCodes.NONE:
            user.uaccess.unshare_resource_with_user(res, to_user)
        else:
            user.uaccess.share_resource_with_user(res, to_user, privilege_code)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ShareResourceGroup(APIView):

    @swagger_auto_schema(operation_description="Set group privileges of a resource")
    def post(self, request, pk, privilege, group_id):
        res, _, user = authorize(request, pk,
                                 needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
        to_group = hs_core_utils.group_from_id(group_id)
        privilege_code = PrivilegeCodes.from_string(privilege)
        if not privilege_code:
            raise ParseError("Bad privilege code")
        if privilege_code == PrivilegeCodes.NONE:
            user.uaccess.unshare_resource_with_group(res, to_group)
        else:
            user.uaccess.share_resource_with_group(res, to_group, privilege_code)

        return Response(status=status.HTTP_204_NO_CONTENT)
