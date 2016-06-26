from django.contrib import messages
from django.http import HttpResponseRedirect

from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE


def update_sqlite_file(request, resource_id, *args, **kwargs):
    res, _, user = authorize(request, resource_id, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    if res.resource_type != "TimeSeriesResource":
        messages.error(request, "This is not a timeseries resource.")
    else:
        try:
            res.metadata.update_sqlite_file()
            messages.success(request, "SQLite file update was successful.")
        except Exception, ex:
            messages.error(request, "Failed to update SQLite file. Error:" + ex.message)

    if 'resource-mode' in request.POST:
        request.session['resource-mode'] = 'edit'

    return HttpResponseRedirect(request.META['HTTP_REFERER'])
