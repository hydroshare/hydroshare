import datetime
import logging
import os
from uuid import uuid4

from dateutil import tz
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import (HttpResponse, HttpResponseRedirect,
                         JsonResponse)
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view

from hs_core.hydroshare.resource import check_resource_type
from hs_core.signals import (pre_check_bag_flag, pre_download_file,
                             pre_download_resource)
from hs_core.task_utils import (get_or_create_task_notification,
                                get_resource_bag_task, get_task_notification,
                                get_task_user_id)
from hs_core.tasks import create_bag_by_s3, create_temp_zip
from hs_core.views.utils import ACTION_TO_AUTHORIZE, authorize, is_ajax
from hs_file_types.enums import AggregationMetaFilePath

logger = logging.getLogger(__name__)


def download(request, path, use_async=True,
             *args, **kwargs):
    """ perform a download request, either asynchronously or synchronously

    :param request: the request object.
    :param path: the path of the thing to be downloaded.
    :param use_async: True means to utilize asynchronous creation of objects to download.

    The following variables are computed:

    * `path` is the public path of the thing to be downloaded.
    * `s3_path` is the location of `path` in S3.
    * `output_path` is the output path to be reported in the response object.
    * `s3_output_path` is the location of `output_path` in S3

    and there are six cases:

    Zipped query param signal the download should be zipped
        - folders are always zipped regardless of this paramter
        - single file aggregations are zipped with the aggregation metadata files

    A path may point to:
    1. a single file
    2. a single-file-aggregation object in a composite resource.
    3. a folder
    3. a metadata object that may need updating.
    4. a bag that needs to be updated and then returned.
    6. a previously zipped file that was zipped asynchronously.

    """
    if not settings.DEBUG:
        logger.debug("request path is {}".format(path))

    split_path_strs = path.split('/')
    while split_path_strs[-1] == '':
        split_path_strs.pop()
    path = '/'.join(split_path_strs)  # no trailing slash

    # initialize case variables
    is_bag_download = False
    is_zip_download = False
    is_zip_request = request.GET.get('zipped', "False").lower() == "true"
    is_aggregation_request = request.GET.get('aggregation', "False").lower() == "true"
    api_request = request.META.get('CSRF_COOKIE', None) is None
    aggregation_name = None
    is_sf_request = False

    if split_path_strs[0] == 'bags':
        is_bag_download = True
        # format is bags/{rid}.zip
        res_id = os.path.splitext(split_path_strs[1])[0]
    elif split_path_strs[0] == 'zips':
        is_zip_download = True
        # zips prefix means that we are following up on an asynchronous download request
        # format is zips/{date}/{zip-uuid}/{public-path}.zip where {public-path} contains the rid
        res_id = split_path_strs[3]
    else:  # regular download request
        res_id = split_path_strs[0]

    if not settings.DEBUG:
        logger.debug("resource id is {}".format(res_id))

    # now we have the resource Id and can authorize the request
    # if the resource does not exist in django, authorized will be false
    res, authorized, _ = authorize(request, res_id,
                                   needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE,
                                   raises_exception=False)
    if not authorized:
        response = HttpResponse(status=401)
        content_msg = "You do not have permission to download this resource!"
        response.content = content_msg
        return response

    istorage = res.get_s3_storage()

    s3_path = res.get_s3_path(path, prepend_short_id=False)

    # in many cases, path and output_path are the same.
    output_path = path
    s3_output_path = s3_path
    # folder requests are automatically zipped
    if not is_bag_download and not is_zip_download:  # path points into resource: should I zip it?
        # check for aggregations
        if is_aggregation_request and res.resource_type == "CompositeResource":
            prefix = res.file_path
            if path.startswith(prefix):
                # +1 to remove trailing slash
                aggregation_name = path[len(prefix) + 1:]
            aggregation = res.get_aggregation_by_aggregation_name(aggregation_name)
            if not is_zip_request:
                download_url = request.GET.get('url_download', 'false').lower()
                if download_url == 'false':
                    # redirect to referenced url in the url file instead
                    if hasattr(aggregation, 'redirect_url'):
                        return HttpResponseRedirect(aggregation.redirect_url)
            # point to the main file path
            path = aggregation.get_main_file.storage_path
            is_zip_request = True
            daily_date = datetime.datetime.today().strftime('%Y-%m-%d')
            output_path = "zips/{}/{}/{}.zip".format(daily_date, uuid4().hex, path)

            s3_path = res.get_s3_path(path, prepend_short_id=False)
            s3_output_path = res.get_s3_path(output_path, prepend_short_id=False)

        store_path = '/'.join(split_path_strs[1:])  # data/contents/{path-to-something}
        if res.is_folder(store_path):  # automatically zip folders
            is_zip_request = True
            daily_date = datetime.datetime.today().strftime('%Y-%m-%d')
            output_path = "zips/{}/{}/{}.zip".format(daily_date, uuid4().hex, path)
            s3_output_path = res.get_s3_path(output_path, prepend_short_id=False)

            if not settings.DEBUG:
                logger.debug("automatically zipping folder {} to {}".format(path, output_path))
        elif istorage.exists(s3_path):
            if not settings.DEBUG:
                logger.debug("request for single file {}".format(path))
            is_sf_request = True

            if is_zip_request:
                daily_date = datetime.datetime.today().strftime('%Y-%m-%d')
                output_path = "tmp/{}/{}/{}.zip".format(daily_date, uuid4().hex, path)
                s3_output_path = res.get_s3_path(output_path, prepend_short_id=False)

    # After this point, we have valid path, s3_path, output_path, and s3_output_path
    # * is_zip_request: signals download should be zipped, folders are always zipped
    # * aggregation: aggregation object if the path matches an aggregation
    # * is_sf_request: path is a single-file
    # flags for download:
    # * is_bag_download: download a bag in format bags/{rid}.zip
    # * is_zip_download: download a zipfile in format zips/{date}/{random guid}/{path}.zip
    # if none of these are set, it's a normal download

    resource_cls = check_resource_type(res.resource_type)

    if is_zip_request:
        download_path = '/django_s3/rest_download/' + output_path
        if use_async:
            user_id = get_task_user_id(request)
            task = create_temp_zip.apply_async((res_id, s3_path, s3_output_path,
                                                aggregation_name, is_sf_request))
            task_id = task.task_id
            if api_request:
                return JsonResponse({
                    'zip_status': 'Not ready',
                    'task_id': task.task_id,
                    'download_path': '/django_s3/rest_download/' + output_path})
            else:
                # return status to the task notification App AJAX call
                task_dict = get_or_create_task_notification(task_id, name='zip download', payload=download_path,
                                                            username=user_id)
                return JsonResponse(task_dict)

        else:  # synchronous creation of download
            ret_status = create_temp_zip(res_id, s3_path, s3_output_path,
                                         aggregation_name=aggregation_name, sf_zip=is_sf_request)
            if not ret_status:
                content_msg = "Zip could not be created."
                response = HttpResponse()
                response.content = content_msg
                return response
            # At this point, output_path presumably exists and contains a zipfile
            # to be streamed below

    elif is_bag_download:
        now = datetime.datetime.now(tz.UTC)
        res.bag_last_downloaded = now
        res.save()
        # Shorten request if it contains extra junk at the end
        bag_file_name = res_id + '.zip'
        output_path = os.path.join('bags', bag_file_name)
        s3_output_path = res.bag_path
        res.update_relation_meta()
        bag_modified = res.getAVU('bag_modified')
        # recreate the bag if it doesn't exist even if bag_modified is "false".
        if not settings.DEBUG:
            logger.debug("s3_output_path is {}".format(s3_output_path))
        if bag_modified is None or not bag_modified:
            if not istorage.exists(s3_output_path):
                bag_modified = True

        # send signal for pre_check_bag_flag
        # this generates metadata other than that generated by create_bag_files.
        pre_check_bag_flag.send(sender=resource_cls, resource=res)
        if bag_modified is None or bag_modified:
            if use_async:
                # task parameter has to be passed in as a tuple or list, hence (res_id,) is needed
                # Note that since we are using JSON for task parameter serialization, no complex
                # object can be passed as parameters to a celery task

                task_id = get_resource_bag_task(res_id)
                user_id = get_task_user_id(request)
                if not task_id:
                    # create the bag
                    task = create_bag_by_s3.apply_async((res_id, ))
                    task_id = task.task_id
                    if api_request:
                        return JsonResponse({
                            'bag_status': 'Not ready',
                            'task_id': task_id,
                            'download_path': "",
                            # status and id are checked by by hs_core.tests.api.rest.test_create_resource.py
                            'status': 'Not ready',
                            'id': task_id})
                    else:
                        task_dict = get_or_create_task_notification(task_id, name='bag download', payload="",
                                                                    username=user_id)
                        return JsonResponse(task_dict)
                else:
                    # bag creation has already started
                    if api_request:
                        return JsonResponse({
                            'bag_status': 'Not ready',
                            'task_id': task_id,
                            'download_path': ""})
                    else:
                        task_dict = get_or_create_task_notification(task_id, name='bag download', payload="",
                                                                    username=user_id)
                        return JsonResponse(task_dict)
            else:
                ret_status = create_bag_by_s3(res_id)
                if not ret_status:
                    content_msg = "Bag cannot be created successfully. Check log for details."
                    response = HttpResponse()
                    response.content = content_msg
                    return response
        elif is_ajax(request):
            task_dict = {
                'id': datetime.datetime.today().isoformat(),
                'name': "bag download",
                'status': "completed",
                'payload': res.bag_url
            }
            return JsonResponse(task_dict)
    else:  # regular file download
        # if fetching main metadata files, then these need to be refreshed.
        if path in [f"{res_id}/data/resourcemap.xml", f"{res_id}/data/resourcemetadata.xml",
                    f"{res_id}/manifest-md5.txt", f"{res_id}/tagmanifest-md5.txt", f"{res_id}/readme.txt",
                    f"{res_id}/bagit.txt"]:
            res.update_relation_meta()
            bag_modified = res.getAVU("bag_modified")
            if bag_modified is None or bag_modified or not istorage.exists(s3_output_path):
                res.setAVU("bag_modified", True)  # ensure bag_modified is set when s3_output_path does not exist
                create_bag_by_s3(res_id, create_zip=False)
        elif any([path.endswith(suffix) for suffix in AggregationMetaFilePath]):
            # download aggregation meta xml/json schema file
            try:
                aggregation = res.get_aggregation_by_meta_file(path)
            except ObjectDoesNotExist:
                aggregation = None

            if aggregation is not None and aggregation.metadata.is_dirty:
                aggregation.create_aggregation_xml_documents()
    # If we get this far,
    # * path and s3_path point to true input
    # * output_path and s3_output_path point to true output.
    # Try to stream the file back to the requester.

    # retrieve file size to set up Content-Length header
    # TODO: standardize this to make it less brittle
    flen = istorage.size(s3_output_path)
    # this logs the download request in the tracking system
    if is_bag_download:
        pre_download_resource.send(sender=resource_cls, resource=res, request=request)
    else:
        download_file_name = split_path_strs[-1]
        # send signal for pre download file
        # TODO: does not contain subdirectory information: duplicate refreshes possible
        pre_download_file.send(sender=resource_cls, resource=res,
                               download_file_name=download_file_name,
                               file_size=flen,
                               request=request)

    # if we get here, none of the above conditions are true
    # if reverse proxy is enabled, then this is because the resource is remote and federated
    # OR the user specifically requested a non-proxied download.
    filename = output_path.split('/')[-1]
    signed_url = istorage.signed_url(s3_output_path, ResponseContentDisposition=f'attachment; filename="{filename}"')
    return HttpResponseRedirect(signed_url)


@swagger_auto_schema(method='get', auto_schema=None)
@api_view(['GET'])
def rest_download(request, path, *args, **kwargs):
    # need to have a separate view function just for REST API call
    return download(request, path, rest_call=True, *args, **kwargs)


@swagger_auto_schema(method='get', auto_schema=None)
@api_view(['GET'])
def rest_check_task_status(request, task_id, *args, **kwargs):
    '''
    A REST view function to tell the client if the asynchronous create_bag_by_s3()
    task is done and the bag file is ready for download.
    Args:
        request: an ajax request to check for download status
    Returns:
        JSON response to return result from asynchronous task create_bag_by_s3
    '''
    if not task_id:
        task_id = request.POST.get('task_id')
    task_notification = get_task_notification(task_id)
    if task_notification:
        n_status = task_notification['status']
        if n_status in ['completed', 'delivered']:
            return JsonResponse({"status": 'true', 'payload': task_notification['payload']})
        if n_status == 'progress':
            return JsonResponse({"status": 'false'})
        if n_status in ['failed', 'aborted']:
            return JsonResponse({"status": 'false'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return JsonResponse({"status": None})
