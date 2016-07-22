import logging

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.exceptions import ValidationError

from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE


def update_sqlite_file(request, resource_id, *args, **kwargs):
    res, _, user = authorize(request, resource_id,
                             needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    log = logging.getLogger()
    if res.resource_type != "TimeSeriesResource":
        log.exception("Failed to update SQLite file. Error:This is not a timeseries resource. "
                      "Resource ID:{}".format(res.short_id))
        raise ValidationError("The resource is not of type TimeSeries. SQLite file update is "
                              "allowed only for timeseries resources.")
    else:
        try:
            res.metadata.update_sqlite_file()
            messages.success(request, "SQLite file update was successful.")
            log.info("SQLite file update was successful for resource ID:{}.".format(res.short_id))
        except Exception, ex:
            messages.error(request, "Failed to update SQLite file. Error:{}".format(ex.message))
            log.exception("Failed to update SQLite file. Error:{}".format(ex.message))

    if 'resource-mode' in request.POST:
        request.session['resource-mode'] = 'edit'

    return HttpResponseRedirect(request.META['HTTP_REFERER'])
