# coding=utf-8
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError

from hs_core.views.utils import ACTION_TO_AUTHORIZE, authorize
from .utils import set_file_to_geo_raster_file_type

@login_required
def set_file_type(request, resource_id, file_id, hs_file_type,  **kwargs):
    res, _, _ = authorize(request, resource_id, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    if res.resource_type != "ComopsiteResource":
        err_msg = "File type can be set only for files in composite resource."
        messages.error(request, err_msg)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    if hs_file_type != "GeoRaster":
        err_msg = "Currently a file can be set to Geo Raster file type."
        messages.error(request, err_msg)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    try:
        set_file_to_geo_raster_file_type(resource=res, file_id=file_id, user=request.user)
        msg = "File was successfully set to Geo Raster file tye." \
              "Raster metadata extraction was successful."
        messages.success(request, msg)
    except ValidationError as ex:
        messages.error(request, ex.message)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])