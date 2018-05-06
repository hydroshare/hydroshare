from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from rest_framework import status

from hs_core.views.utils import ACTION_TO_AUTHORIZE, authorize, get_coverage_data_dict


@login_required
def update_resource_coverage(request, resource_id, coverage_type, **kwargs):
    """Updates resource coverage based on the coverages of the contained aggregations
    (file types)
    :param  request: an instance of HttpRequest
    :param  resource_id: id of resource for which coverage needs to be updated
    :param  coverage_type: a value of either temporal or spatial
    :return an instance of JsonResponse type
    """

    res, authorized, _ = authorize(request, resource_id,
                                   needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                   raises_exception=False)
    response_data = {'status': 'error'}
    if not authorized:
        err_msg = "Permission denied"
        response_data['message'] = err_msg
        return JsonResponse(response_data, status=status.HTTP_401_UNAUTHORIZED)

    if res.resource_type != "CompositeResource":
        err_msg = "Coverage can be updated only for composite resource."
        response_data['message'] = err_msg
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)

    if coverage_type.lower() not in ('temporal', 'spatial'):
        err_msg = "Invalid coverage type specified."
        response_data['message'] = err_msg
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)

    if coverage_type.lower() == 'spatial':
        res.update_spatial_coverage()
    else:
        res.update_temporal_coverage()

    msg = "Resource {} coverage was updated successfully.".format(coverage_type.lower())
    response_data['status'] = 'success'
    response_data['message'] = msg
    if coverage_type.lower() == 'spatial':
        spatial_coverage_dict = get_coverage_data_dict(res)
        response_data['spatial_coverage'] = spatial_coverage_dict
    else:
        temporal_coverage_dict = get_coverage_data_dict(res, 'temporal')
        response_data['temporal_coverage'] = temporal_coverage_dict

    return JsonResponse(response_data, status=status.HTTP_200_OK)
