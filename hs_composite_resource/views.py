from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from rest_framework import status

from hs_core.views.utils import (ACTION_TO_AUTHORIZE, authorize,
                                 get_coverage_data_dict)


@login_required
def update_resource_coverage(request, resource_id, coverage_type, **kwargs):
    """Updates resource coverage based on the coverages of the contained aggregations
    (file types)
    :param  request: an instance of HttpRequest
    :param  resource_id: id of resource for which coverage needs to be updated
    :param  coverage_type: a value of either temporal or spatial
    :return an instance of JsonResponse type
    """

    return _process_resource_coverage_action(request, resource_id, coverage_type, action='update')


@login_required
def delete_resource_coverage(request, resource_id, coverage_type, **kwargs):
    """Deletes resource coverage
    :param  request: an instance of HttpRequest
    :param  resource_id: id of resource for which coverage needs to be deleted
    :param  coverage_type: a value of either temporal or spatial
    :return an instance of JsonResponse type
    """
    return _process_resource_coverage_action(request, resource_id, coverage_type, action='delete')


def check_aggregation_files_to_sync(request, resource_id, **kwargs):
    """
    Checks if there are files in netcdf or timeseries aggregations that need to be updated due to metadata changes by
    the user
    :param  request: an instance of HttpRequest
    :param  resource_id: id of resource for which files in netcdf or timeseries aggregations need to be checked
    :return an instance of JsonResponse type with data containing the list of files (file paths) that need to be updated
    """

    resource, authorized, _ = authorize(request, resource_id,
                                        needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                        raises_exception=False)
    if not authorized:
        response_data = {"status": "ERROR", "message": "Permission denied"}
        return JsonResponse(response_data, status=status.HTTP_401_UNAUTHORIZED)

    file_paths = {"nc_files": [], "ts_files": []}
    if resource.resource_type != "CompositeResource":
        response_data = {"status": "ERROR", "message": "Resource is not a composite resource"}
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)

    if resource.raccess.published or resource.raccess.review_pending:
        # if resource is published or in review, no need to check for files to sync as the user cannot update the files
        data = {"status": "SUCCESS", "files_to_sync": file_paths}
        return JsonResponse(data)

    # check netcdf aggregations
    nc_file_paths = []
    netcdf_logical_files = resource.get_logical_files('NetCDFLogicalFile')
    for lf in netcdf_logical_files:
        if lf.metadata.is_update_file:
            nc_file_paths.append(lf.aggregation_name)
    file_paths["nc_files"] = nc_file_paths
    # check time series aggregations
    ts_file_paths = []
    timeseries_logical_files = resource.get_logical_files('TimeSeriesLogicalFile')
    for lf in timeseries_logical_files:
        if lf.metadata.is_update_file:
            ts_file_paths.append(lf.aggregation_name)
    file_paths["ts_files"] = ts_file_paths

    data = {"status": "SUCCESS", "files_to_sync": file_paths}
    return JsonResponse(data)


def _process_resource_coverage_action(request, resource_id, coverage_type, action):
    res, authorized, _ = authorize(request, resource_id,
                                   needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                   raises_exception=False)

    response_data = {'status': 'error'}
    if not authorized:
        err_msg = "Permission denied"
        response_data['message'] = err_msg
        return JsonResponse(response_data, status=status.HTTP_401_UNAUTHORIZED)

    if res.resource_type != "CompositeResource":
        err_msg = "Coverage can be {}d only for resource.".format(action)
        response_data['message'] = err_msg
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)

    if coverage_type.lower() not in ('temporal', 'spatial'):
        err_msg = "Invalid coverage type specified."
        response_data['message'] = err_msg
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)

    if coverage_type.lower() == 'spatial':
        if action == 'delete':
            res.delete_coverage(coverage_type='spatial')
        else:
            res.update_spatial_coverage()
    else:
        if action == 'delete':
            res.delete_coverage(coverage_type='temporal')
        else:
            res.update_temporal_coverage()

    msg = "Resource {0} coverage was {1}d successfully.".format(coverage_type.lower(), action)
    response_data['status'] = 'success'
    response_data['message'] = msg
    if coverage_type.lower() == 'spatial':
        spatial_coverage_dict = get_coverage_data_dict(res)
        response_data['spatial_coverage'] = spatial_coverage_dict
    else:
        temporal_coverage_dict = get_coverage_data_dict(res, 'temporal')
        response_data['temporal_coverage'] = temporal_coverage_dict

    return JsonResponse(response_data, status=status.HTTP_200_OK)
