from django.http import HttpResponse
from django.template import loader
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
from hs_access_control.models import PrivilegeCodes


def debug_resource(request, shortkey):
    """ Debug view for resource depicts output of various integrity checking scripts """
    resource, _, _ = authorize(request, shortkey,
                               needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
    irods_issues, irods_errors = resource.check_irods_files(log_errors=False, return_errors=True)

    template = loader.get_template('debug/debug_resource.html')
    context = {
        'shortkey': shortkey,
        'creator': resource.creator,
        'resource': resource,
        'raccess': resource.raccess,
        'owners': resource.raccess.owners,
        'editors': resource.raccess.get_users_with_explicit_access(PrivilegeCodes.CHANGE),
        'viewers': resource.raccess.get_users_with_explicit_access(PrivilegeCodes.VIEW),
        'public_AVU': resource.getAVU('isPublic'),
        'type_AVU': resource.getAVU('resourceType'),
        'modified_AVU': resource.getAVU('bag_modified'),
        'quota_AVU': resource.getAVU('quotaUserName'),
        'irods_issues': irods_issues,
        'irods_errors': irods_errors,
    }
    return HttpResponse(template.render(context, request))
