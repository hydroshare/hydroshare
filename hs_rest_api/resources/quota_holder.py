from rest_framework.decorators import api_view
from django.http import HttpResponse
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE


@api_view(['GET'])
def get_quota_holder_bucket(request, resource_id):
    res, _, _ = authorize(request, resource_id, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
    return HttpResponse(res.quota_holder.userprofile.bucket_name)