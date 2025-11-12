import base64
import datetime
import json
import logging
import os
import uuid
from uuid import uuid4

from smart_open import open
from django_s3.storage import S3Storage
from django_s3.utils import bucket_and_name
from django_tus.views import TusUpload
from django_tus.tusfile import TusFile, TusChunk
from django_tus.response import TusResponse

from dateutil import tz
from django.conf import settings
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.http import (HttpResponse, HttpResponseRedirect,
                         JsonResponse, HttpResponseForbidden, HttpResponseNotFound)
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view

from hs_core.exceptions import QuotaException
from hs_core.hydroshare.resource import check_resource_type
from hs_core.hydroshare.utils import validate_user_quota, get_resource_by_shortkey, resource_modified
from hs_core.signals import (pre_check_bag_flag, pre_download_file,
                             pre_download_resource)
from hs_core.task_utils import (get_or_create_task_notification,
                                get_resource_bag_task, get_task_notification,
                                get_task_user_id)
from hs_core.tasks import create_bag_by_s3, create_temp_zip, set_resource_files_system_metadata
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

        res.update_download_count()
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
        res.update_download_count()
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
        res.update_download_count()
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


def get_path(metadata):
    hs_res_id = metadata.get('hs_res_id')
    eventual_relative_path = ''
    try:
        # see if there is a path within data/contents that the file should be uploaded to
        existing_path_in_resource = metadata.get('existing_path_in_resource', '')
        existing_path_in_resource = json.loads(existing_path_in_resource).get("path")
        if existing_path_in_resource:
            # in this case, we are uploading to an existing folder in the resource
            # existing_path_in_resource is a list of folder names
            # append them into a path
            for folder in existing_path_in_resource:
                eventual_relative_path += folder + '/'
    except Exception as ex:
        logger.info(f"Existing path in resource not found: {str(ex)}")

    # handle the case that a folder was uploaded instead of a single file
    # use the metadata.relativePath to rebuild the folder structure
    path_within_uploaded_folder = metadata.get('relativePath', '')
    # path_within_resource_contents will include the name of the file, so we need to remove it
    path_within_uploaded_folder = os.path.dirname(path_within_uploaded_folder)
    if path_within_uploaded_folder:
        eventual_relative_path += path_within_uploaded_folder + '/'
    path = f'{hs_res_id}/data/contents/{eventual_relative_path}'
    return path


class CustomTusFile(TusFile):
    # extend TusFile to allow it to write to s3 storage instead of local disk
    # https://github.com/alican/django-tus/blob/2aac2e7c0e6bac79a1cb07721947a48d9cc40ec8/django_tus/tusfile.py#L52

    def __init__(self, resource_id):
        self.storage = S3Storage()
        self.resource_id = resource_id
        self.filename = cache.get("tus-uploads/{}/filename".format(resource_id))
        self.path = cache.get("tus-uploads/{}/path".format(resource_id))
        try:
            self.file_size = int(cache.get("tus-uploads/{}/file_size".format(resource_id)))
        except (ValueError, TypeError):
            self.file_size = 0
        self.metadata = cache.get("tus-uploads/{}/metadata".format(resource_id))
        self.offset = cache.get("tus-uploads/{}/offset".format(resource_id))
        self.part_number = cache.get("tus-uploads/{}/part_number".format(resource_id))
        self.parts = cache.get("tus-uploads/{}/parts".format(resource_id)) or []
        self.upload_id = cache.get("tus-uploads/{}/upload_id".format(resource_id))
        bucket, _ = bucket_and_name(self.metadata.get("hs_res_id"))
        self.bucket = bucket

    def get_storage(self):
        return self.storage

    @staticmethod
    def create_initial_file(metadata, file_size):
        resource_id = str(uuid.uuid4())
        cache.add("tus-uploads/{}/filename".format(resource_id),
                  "{}".format(metadata.get("filename")), settings.TUS_TIMEOUT)
        cache.add("tus-uploads/{}/file_size".format(resource_id), file_size, settings.TUS_TIMEOUT)
        cache.add("tus-uploads/{}/offset".format(resource_id), 0, settings.TUS_TIMEOUT)
        cache.add("tus-uploads/{}/metadata".format(resource_id), metadata, settings.TUS_TIMEOUT)

        tus_file = CustomTusFile(resource_id)
        tus_file.path = metadata.get("path")
        cache.add("tus-uploads/{}/path".format(resource_id), tus_file.path, settings.TUS_TIMEOUT)
        tus_file.initiate_multipart_upload()
        cache.add("tus-uploads/{}/part_number".format(resource_id), tus_file.part_number, settings.TUS_TIMEOUT)
        cache.add("tus-uploads/{}/parts".format(resource_id), tus_file.parts, settings.TUS_TIMEOUT)
        cache.add("tus-uploads/{}/upload_id".format(resource_id), tus_file.upload_id, settings.TUS_TIMEOUT)
        return tus_file

    @staticmethod
    def check_existing_file(path):
        return S3Storage().exists(path)

    def is_valid(self):
        return self.filename is not None

    def _write_file(self, path, offset, content):
        s3_url = f's3://{self.bucket}/{path}'
        transport_params = {
            'client': self.storage.connection.meta.client
        }
        with open(s3_url, 'wb', transport_params=transport_params) as out_file:
            if offset:
                try:
                    out_file.seek(offset)
                except OSError as e:
                    # https://github.com/piskvorky/smart_open/issues/580
                    logger.error("Error seeking in file for tus upload", exc_info=e)
                    raise IOError("Error seeking in file for tus upload")
            out_file.write(content)

    def initiate_multipart_upload(self):
        try:
            response = self.storage.connection.meta.client.create_multipart_upload(
                Bucket=self.bucket,
                Key=self.path
            )
            self.upload_id = response['UploadId']
            self.part_number = 1
            self.parts = []
        except Exception as e:
            logger.error("Error writing initial file for tus upload", exc_info=e)
            raise IOError("Error writing initial file for tus upload")

    def upload_part(self, chunk):
        try:
            response = self.storage.connection.meta.client.upload_part(
                Bucket=self.bucket,
                Key=self.path,
                PartNumber=self.part_number,
                UploadId=self.upload_id,
                Body=chunk.content
            )
            self.parts.append({'PartNumber': self.part_number, 'ETag': response['ETag']})
            cache.set("tus-uploads/{}/parts".format(self.resource_id), self.parts, settings.TUS_TIMEOUT)
            self.part_number = cache.incr("tus-uploads/{}/part_number".format(self.resource_id))
            self.offset = cache.incr("tus-uploads/{}/offset".format(self.resource_id), chunk.chunk_size)

        except Exception as e:
            logger.error("patch", extra={'request': chunk.META, 'tus': {
                "resource_id": self.resource_id,
                "filename": self.filename,
                "file_size": self.file_size,
                "metadata": self.metadata,
                "offset": self.offset,
                "upload_file_path": self.path,
            }})
            raise e

    def complete_upload(self):
        self.storage.connection.meta.client.complete_multipart_upload(
            Bucket=self.bucket,
            Key=self.path,
            UploadId=self.upload_id,
            MultipartUpload={
                'Parts': self.parts
            }
        )


class CustomTusUpload(TusUpload):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        # check that the user has permission to upload a file to the resource
        from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
        metadata = self.get_metadata(self.request)
        if not metadata:
            # get the tus resource_id from the request
            tus_resource_id = self.kwargs['resource_id']
            try:
                tus_file = CustomTusFile(str(tus_resource_id))
                # get the resource id from the tus metadata
                metadata = tus_file.metadata
            except Exception as ex:
                err_msg = f"Error in getting metadata for the tus upload: {str(ex)}"
                logger.error(err_msg)
                # https://tus.io/protocols/resumable-upload#head
                # return a 404 not found response
                return HttpResponseNotFound(err_msg)

        # get the hydroshare resource id from the metadata
        hs_res_id = metadata.get('hs_res_id')

        if not self.request.user.is_authenticated:
            sessionid = self.request.headers.get('HS-SID', None)
            authorization_header = self.request.headers.get('Authorization', None)
            # use the cookie to get the django session and user
            if sessionid:
                try:
                    # get the user from the session
                    session = Session.objects.get(session_key=sessionid)
                    user_id = session.get_decoded().get('_auth_user_id')
                    user = User.objects.get(pk=user_id)
                    self.request.user = user
                except Exception as ex:
                    err_msg = f"Error in getting user from session: {str(ex)}"
                    logger.error(err_msg)
                    return HttpResponseForbidden(err_msg)
            elif authorization_header:
                # if the user is not authenticated, but has an authorization header,
                # try to get the user from the token
                try:
                    token = authorization_header.split(' ')[1]
                    username, password = base64.b64decode(token).decode('utf-8').split(':')
                    user = User.objects.get(username=username)
                    if not user.check_password(password):
                        raise DjangoPermissionDenied("Invalid credentials")
                    self.request.user = user
                except Exception as ex:
                    err_msg = f"Error in getting user from token: {str(ex)}"
                    logger.error(err_msg)
                    return HttpResponseForbidden(err_msg)

        # check that the user has permission to upload a file to the resource
        try:
            _, _, user = authorize(self.request, hs_res_id,
                                   needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
            # ensure that the username is the same as the request user
            # username_from_client = metadata.get('username')
            # assert (user.username == username_from_client)
        except (DjangoPermissionDenied, AssertionError):
            return HttpResponseForbidden()

        return super(CustomTusUpload, self).dispatch(*args, **kwargs)

    def patch(self, request, resource_id, *args, **kwargs):
        try:
            tus_file = CustomTusFile(str(resource_id))
        except Exception as ex:
            logger.error(f"Error in getting tus_file during patch request: {str(ex)}")
            return HttpResponseNotFound()

        # when using the google file picker api, the file size is initially set to 0
        http_upload_length = request.META.get('HTTP_UPLOAD_LENGTH', None)
        if tus_file.file_size == 0 and http_upload_length:
            tus_file.file_size = int(http_upload_length)
        chunk = TusChunk(request)

        if not tus_file.is_valid():
            return TusResponse(status=410)

        if chunk.offset != tus_file.offset:
            return TusResponse(status=409)

        if chunk.offset > tus_file.file_size and tus_file.file_size != 0:
            return TusResponse(status=413)
        try:
            tus_file.upload_part(chunk=chunk)
        except Exception as e:
            error_message = f"Unable to write chunk for tus upload: {str(e)}"
            logger.error(error_message, exc_info=True)
            return TusResponse(status=500, reason=error_message)

        # https://github.com/alican/django-tus/blob/2aac2e7c0e6bac79a1cb07721947a48d9cc40ec8/django_tus/tusfile.py#L151-L152
        # here we modify from django_tus to allow for the file to be marked as complete
        if tus_file.is_complete():
            tus_file.complete_upload()

            # complete_upload() handles putting the file together in S3, so no need to rename
            # https://github.com/alican/django-tus/blob/2aac2e7c0e6bac79a1cb07721947a48d9cc40ec8/django_tus/tusfile.py#L93
            # tus_file.rename()

            # clean() handles deleting the cache entries
            # https://github.com/alican/django-tus/blob/2aac2e7c0e6bac79a1cb07721947a48d9cc40ec8/django_tus/tusfile.py#L111
            tus_file.clean()

            user = self.request.user
            resource = get_resource_by_shortkey(tus_file.metadata.get('hs_res_id'))

            resource_modified(resource, user, overwrite_bag=False)

            # store file level system metadata in Django DB (async task)
            set_resource_files_system_metadata.apply_async((resource.short_id,))

            # signal is not consumed at this point, but we keep it for future use
            # https://github.com/alican/django-tus/blob/2aac2e7c0e6bac79a1cb07721947a48d9cc40ec8/django_tus/views.py#L112
            self.send_signal(tus_file)

            self.finished()

        return TusResponse(status=204, extra_headers={'Upload-Offset': tus_file.offset})

    def post(self, request, *args, **kwargs):
        # adapted from django_tus TusUpload.post
        # in order to handle missing HTTP_UPLOAD_LENGTH header
        # https://github.com/alican/django-tus/blob/2aac2e7c0e6bac79a1cb07721947a48d9cc40ec8/django_tus/views.py#L56-L75

        metadata = self.get_metadata(request)

        metadata["filename"] = self.validate_filename(metadata)

        message_id = request.META.get("HTTP_MESSAGE_ID")
        if message_id:
            metadata["message_id"] = base64.b64decode(message_id)

        path = f"{get_path(metadata)}{metadata.get('filename', False)}"
        metadata["path"] = path
        existing = CustomTusFile.check_existing_file(path)

        if settings.TUS_EXISTING_FILE == 'error' and settings.TUS_FILE_NAME_FORMAT == 'keep' and existing:
            return TusResponse(status=409, reason="File with same name already exists")

        # set the filesize from HTTP header if it exists, otherwise set it from the metadata
        file_size = int(request.META.get("HTTP_UPLOAD_LENGTH", "0"))
        meta_file_size = metadata.get("file_size", 0)
        if meta_file_size and meta_file_size != 'null':
            file_size = meta_file_size

        res_id = metadata.get("hs_res_id")
        res = get_resource_by_shortkey(res_id)
        if res.raccess.published:
            return TusResponse(status=403, reason="Cannot upload file to a published resource")
        try:
            res_id = metadata.get("hs_res_id")
            res = get_resource_by_shortkey(res_id)
            validate_user_quota(res.quota_holder, int(file_size))
        except QuotaException as e:
            return TusResponse(status=413, reason=str(e))
        try:
            tus_file = CustomTusFile.create_initial_file(metadata, file_size)
        except Exception as e:
            error_message = f"Unable to create file for tus upload {str(e)}"
            logger.error(error_message, exc_info=True)
            return TusResponse(status=500, reason=error_message)

        return TusResponse(
            status=201,
            extra_headers={'Location': '{}{}'.format(request.build_absolute_uri(), tus_file.resource_id)})
