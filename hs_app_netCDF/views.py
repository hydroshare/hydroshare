import logging

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.exceptions import ValidationError

from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE


def update_netcdf_file(request, resource_id, *args, **kwargs):
    res, _, user = authorize(request, resource_id,
                             needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    log = logging.getLogger()
    if res.resource_type != "NetcdfResource":
        log.exception("Failed to update NetCDF file. Error:This is not a "
                      "multidimensional (NetCDF) resource. "
                      "Resource ID:{}".format(res.short_id))
        raise ValidationError("The resource is not of type NetCDF. NetCDF file update is "
                              "allowed only for multidimensional (NetCDF) resources.")
    else:
        try:
            res.update_netcdf_file(user)
            messages.success(request, "NetCDF file update was successful.")
            log.info("NetCDF file update was successful for resource ID:{}.".format(res.short_id))
        except Exception as ex:
            messages.error(request, "Failed to update NetCDF file. Error:{}".format(ex.message))
            log.exception("Failed to update NetCDF file. Error:{}".format(ex.message))

    if 'resource-mode' in request.POST:
        request.session['resource-mode'] = 'edit'

    # remove if there exits any previous form validation errors
    if 'validation_error' in request.session:
        del request.session['validation_error']

    return HttpResponseRedirect(request.META['HTTP_REFERER'])
