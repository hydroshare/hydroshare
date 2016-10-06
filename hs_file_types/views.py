# coding=utf-8
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError

from hs_core.views.utils import ACTION_TO_AUTHORIZE, authorize
from .utils import raster_extract_metadata

@login_required
def extract_metadata(request, resource_id, hs_file_type, f, **kwargs):
    res, _, _ = authorize(request, resource_id, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    if res.resource_type != "GenericResource":
        err_msg = "File metadata extraction is allowed only for generic resource."
        messages.error(request, err_msg)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    if hs_file_type != "GeoRaster":
        err_msg = "File metadata extraction is allowed only for Geo Raster file type."
        messages.error(request, err_msg)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    try:
        raster_extract_metadata(resource=res, file_name=f)
    except ValidationError as ex:
        messages.error(request, ex.message)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])