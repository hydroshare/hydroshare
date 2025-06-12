import os
import mimetypes
import base64
import copy
import tempfile
import shutil
import logging
import json
import uuid

from django.urls import reverse
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, SuspiciousFileOperation
from django.core.exceptions import ValidationError as CoreValidationError
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import redirect
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied, NotFound

from django_s3.exceptions import SessionException
from django_s3.storage import S3Storage
from django_s3.utils import bucket_and_name
from django_tus.views import TusUpload
from django_tus.tusfile import TusFile, TusChunk, FilenameGenerator
from django_tus.response import TusResponse
from hs_core import hydroshare
from hs_core.models import AbstractResource
from hs_core.hydroshare.utils import get_resource_by_shortkey, get_resource_types, \
    get_content_types
from hs_core.views import utils as view_utils
from hs_core.views.utils import ACTION_TO_AUTHORIZE
from hs_core.views import serializers
from hs_core.hydroshare.utils import get_file_storage, resource_modified
from hs_core.serialization import GenericResourceMeta, HsDeserializationDependencyException, \
    HsDeserializationException
from hs_core.hydroshare.hs_bagit import create_bag_metadata_files
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.parsers import MultiPartParser


logger = logging.getLogger(__name__)


# Mixins
class ResourceFileToListItemMixin(object):
    # URLs in metadata should be fully qualified.
    # ALWAYS qualify them with www.hydroshare.org, rather than the local server name.
    site_url = hydroshare.utils.current_site_url()

    def resourceFileToListItem(self, f):
        url = self.site_url + f.url
        fsize = f.size
        logical_file_type = f.logical_file_type_name
        file_name = os.path.basename(f.resource_file.name)
        modified_time = f.modified_time
        checksum = f.checksum
        # trailing slash confuses mime guesser
        mimetype = mimetypes.guess_type(url)
        if mimetype[0]:
            ftype = mimetype[0]
        else:
            ftype = repr(None)
        resource_file_info_item = serializers.ResourceFileItem(url=url,
                                                               file_name=file_name,
                                                               size=fsize,
                                                               content_type=ftype,
                                                               logical_file_type=logical_file_type,
                                                               modified_time=modified_time,
                                                               checksum=checksum)
        return resource_file_info_item


class ResourceTypes(generics.ListAPIView):
    # We don't need pagination for a list of resource types
    pagination_class = None

    @swagger_auto_schema(operation_description="List Resource Types",
                         responses={200: serializers.ResourceTypesSerializer})
    def get(self, request):
        return self.list(request)

    def get_queryset(self):
        return [serializers.ResourceType(resource_type=rtype.__name__) for rtype in
                get_resource_types()]

    def get_serializer_class(self):
        return serializers.ResourceTypesSerializer


class ContentTypes(generics.ListAPIView):
    pagination_class = None

    @swagger_auto_schema(operation_description="List Content Types",
                         responses={200: serializers.ContentTypesSerializer})
    def get(self, request):
        return self.list(request)

    def get_queryset(self):
        return [serializers.ContentType(content_type=ctype.__name__) for ctype in
                get_content_types()]

    def get_serializer_class(self):
        return serializers.ContentTypesSerializer


class CheckTaskStatus(generics.RetrieveAPIView):

    # TODO, setup a serializer for in, figure out if redirect is needed...
    tid = openapi.Parameter('task_id', openapi.IN_PATH, description="id of the task", type=openapi.TYPE_STRING)

    @swagger_auto_schema(operation_description="Get the status of an asynchronous task",
                         responses={200: serializers.CheckStatusSerializer}, manual_parameters=[tid])
    def get(self, request, task_id):
        '''
        Get the status of an asynchronous task

        :param request:
        :param task_id: Id of the task
        :return: JSON response to return result from asynchronous task
        '''
        url = reverse('rest_check_task_status', kwargs={'task_id': task_id})
        return HttpResponseRedirect(url)


class ResourceReadUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    # pagination doesn't make sense as there is only one resource
    pagination_class = None

    allowed_methods = ('GET', 'PUT', 'DELETE')

    @swagger_auto_schema(operation_description="Get a resource in zipped BagIt format",
                         responses={200: serializers.TaskStatusSerializer})
    def get(self, request, pk):
        res, _, _ = view_utils.authorize(request, pk,
                                         needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)

        bag_url = reverse('rest_download',
                          kwargs={'path': 'bags/{}.zip'.format(pk)})
        return HttpResponseRedirect(bag_url)

    @swagger_auto_schema(operation_description="Not Implemented")
    def put(self, request, pk):
        # TODO: update resource - involves overwriting a resource from the provided bag file
        raise NotImplementedError()

    def delete(self, request, pk):
        # only resource owners are allowed to delete
        view_utils.authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.DELETE_RESOURCE)
        hydroshare.delete_resource(pk, request_username=request.user.username)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ResourceListCreate(generics.ListCreateAPIView):

    @swagger_auto_schema(request_body=serializers.ResourceCreateRequestValidator,
                         operation_description="Create a resource",
                         responses={201: serializers.ResourceCreatedSerializer})
    def post(self, request):
        return self.create(request)

    # Override the create() method from the CreateAPIView class
    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise NotAuthenticated()

        resource_create_request_validator = serializers.ResourceCreateRequestValidator(
            data=request.data)
        if not resource_create_request_validator.is_valid():
            raise ValidationError(detail=resource_create_request_validator.errors)

        validated_request_data = resource_create_request_validator.validated_data
        resource_type = validated_request_data['resource_type']
        if resource_type in ["RasterResource", "GeographicFeatureResource", "RefTimeSeriesResource",
                             "NetcdfResource", "TimeSeriesResource", "GenericResource"]:
            # force deprecated resource types to composite
            resource_type = "CompositeResource"

        res_title = validated_request_data.get('title', 'Untitled resource')
        keywords = validated_request_data.get('keywords', [])
        abstract = validated_request_data.get('abstract', None)
        metadata = validated_request_data.get('metadata', None)
        extra_metadata = validated_request_data.get('extra_metadata', None)

        num_files = len(request.FILES)
        # TODO: (Couch) reconsider whether multiple file upload should be
        # supported when multipart bug fixed.
        if num_files > 0:
            if num_files > 1:
                raise ValidationError(detail={'file': 'Multiple file upload is not allowed on '
                                                      'resource creation. Add additional files '
                                                      'after the resource is created.'})
            # Place files into format expected by hydroshare.utils.resource_pre_create_actions and
            # hydroshare.create_resource, i.e. a tuple of
            # django.core.files.uploadedfile.TemporaryUploadedFile objects.
            files = [request.FILES['file'], ]
        else:
            files = []

        if metadata is not None:
            metadata = json.loads(metadata)
            _validate_metadata(metadata)

        if extra_metadata is not None:
            extra_metadata = json.loads(extra_metadata)
            # TODO: validate extra metadata here

        try:
            _, res_title, metadata = hydroshare.utils.resource_pre_create_actions(
                resource_type=resource_type, resource_title=res_title,
                page_redirect_url_key=None, files=files, metadata=metadata,
                **kwargs)
        except Exception as ex:
            error_msg = {'resource': "Resource creation failed. %s" % str(ex)}
            raise ValidationError(detail=error_msg)

        try:
            resource = hydroshare.create_resource(
                resource_type=resource_type,
                owner=request.user,
                title=res_title,
                edit_users=validated_request_data.get('edit_users', None),
                view_users=validated_request_data.get('view_users', None),
                edit_groups=validated_request_data.get('edit_groups', None),
                view_groups=validated_request_data.get('view_groups', None),
                keywords=keywords,
                metadata=metadata,
                extra_metadata=extra_metadata,
                files=files
            )
            if abstract:
                resource.metadata.create_element('description', abstract=abstract)
        except Exception as ex:
            error_msg = {'resource': "Resource creation failed. %s" % str(ex)}
            raise ValidationError(detail=error_msg)

        post_creation_error_msg = ''
        try:
            hydroshare.utils.resource_post_create_actions(request=request, resource=resource,
                                                          user=request.user,
                                                          metadata=metadata, **kwargs)
        except (hydroshare.utils.ResourceFileValidationException, Exception) as ex:
            post_creation_error_msg = str(ex)
        response_data = {'resource_type': resource_type, 'resource_id': resource.short_id,
                         'message': post_creation_error_msg}

        return Response(data=response_data, status=status.HTTP_201_CREATED)

    pagination_class = PageNumberPagination
    pagination_class.page_size_query_param = 'count'

    @swagger_auto_schema(query_serializer=serializers.ResourceListRequestValidator,
                         operation_description="List resources")
    def get(self, request):
        return self.list(request)

    # needed for list of resources
    # copied from ResourceList
    def get_queryset(self):
        resource_list_request_validator = serializers.ResourceListRequestValidator(
            data=self.request.query_params)
        if not resource_list_request_validator.is_valid():
            raise ValidationError(detail=resource_list_request_validator.errors)

        filter_parms = resource_list_request_validator.validated_data

        if 'coverage_type' in filter_parms:
            site_url = hydroshare.utils.current_site_url()
            message = f"Spatial query is currently disabled in hsapi. Please use discover: {site_url}/search"
            raise ValidationError(detail=message)
        filter_parms['user'] = (self.request.user if self.request.user.is_authenticated else None)
        if len(filter_parms['type']) == 0:
            filter_parms['type'] = None
        else:
            filter_parms['type'] = list(filter_parms['type'])

        filter_parms['public'] = not self.request.user.is_authenticated

        return hydroshare.get_resource_list(**filter_parms)

    # covers serialization of output from GET request
    def get_serializer_class(self):
        return serializers.ResourceListItemSerializer

    # covers serialization of output from POST request
    def post_serializer_class(self):
        return serializers.ResourceCreatedSerializer


class SystemMetadataRetrieve(APIView):

    allowed_methods = ('GET',)

    @swagger_auto_schema(operation_description="Get resource system metadata, as well as URLs to "
                                               "the bag and science metadata",
                         responses={200: serializers.ResourceListItemSerializer})
    def get(self, request, pk):
        res, _, _ = view_utils.authorize(request, pk,
                                         needed_permission=ACTION_TO_AUTHORIZE.VIEW_METADATA)
        ser = self.get_serializer_class()(res)

        return Response(data=ser.data, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        return serializers.ResourceListItemSerializer


class AccessRulesUpdate(APIView):
    """
    Set access rules for a resource

    REST URL: hsapi/resource/{pk}/access
    DEPRECATED: hsapi/resource/accessRules/{pk}
    HTTP method: PUT

    :type pk: str
    :param pk: id of the resource
    :return: No content.  Status code will 200 (OK)
    """
    # TODO: (Couch) Need GET as well.
    allowed_methods = ('PUT',)

    def put(self, request, pk):
        """ Update access rules
        """
        # only resource owners are allowed to change resource flags (e.g., public)
        view_utils.authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.SET_RESOURCE_FLAG)

        access_rules_validator = serializers.AccessRulesRequestValidator(data=request.data)
        if not access_rules_validator.is_valid():
            raise ValidationError(detail=access_rules_validator.errors)

        validated_request_data = access_rules_validator.validated_data
        res = get_resource_by_shortkey(pk)
        try:
            res.set_public(validated_request_data['public'], request.user)
        except CoreValidationError:
            return Response(data={'resource_id': pk}, status=status.HTTP_403_FORBIDDEN)

        return Response(data={'resource_id': pk}, status=status.HTTP_200_OK)


class ScienceMetadataRetrieveUpdate(APIView):
    """
    Retrieve resource science metadata

    REST URL: hsapi/scimeta/{pk}
    HTTP method: GET

    :type pk: str
    :param pk: id of the resource
    :return: science metadata as XML document
    :rtype: str
    :raises:
    NotFound: return json format: {'detail': 'No resource was found for resource id:pk'}
    PermissionDenied: return json format: {'detail': 'You do not have permission to perform
    this action.'}

    REST URL: hsapi/scimeta/{pk}
    HTTP method: PUT

    :type pk: str
    :param pk: id of the resource
    :type metadata: json
    :param metadata: resource metadata
    :return: resource id
    :rtype: json of the format: {'resource_id':pk}
    :raises:
    NotFound: return json format: {'detail': 'No resource was found for resource id':pk}
    PermissionDenied: return json format: {'detail': 'You do not have permission to perform
    this action.'}
    ValidationError: return json format: {parameter-1': ['error message-1'],
    'parameter-2': ['error message-2'], .. }
    """
    ACCEPT_FORMATS = ('application/xml', 'application/rdf+xml')

    allowed_methods = ('GET', 'PUT')

    def get(self, request, pk):
        view_utils.authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_METADATA)

        scimeta_url = AbstractResource.scimeta_url(pk)
        return redirect(scimeta_url)

    def put(self, request, pk):
        # Update science metadata based on resourcemetadata.xml uploaded
        resource, authorized, user = view_utils.authorize(
            request, pk,
            needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
            raises_exception=False)
        if not authorized:
            raise PermissionDenied()

        files = list(request.FILES.values())
        if len(files) == 0:
            error_msg = {'file': 'No resourcemetadata.xml file was found to update resource '
                                 'metadata.'}
            raise ValidationError(detail=error_msg)
        elif len(files) > 1:
            error_msg = {'file': ('More than one file was found. Only one file, named '
                                  'resourcemetadata.xml, '
                                  'can be used to update resource metadata.')}
            raise ValidationError(detail=error_msg)

        scimeta = files[0]
        if scimeta.content_type not in self.ACCEPT_FORMATS:
            error_msg = {'file': ("Uploaded file has content type {t}, "
                                  "but only these types are accepted: {e}.").format(
                t=scimeta.content_type, e=",".join(self.ACCEPT_FORMATS))}
            raise ValidationError(detail=error_msg)
        expect = 'resourcemetadata.xml'
        if scimeta.name != expect:
            error_msg = {'file': "Uploaded file has name {n}, but expected {e}.".format(
                n=scimeta.name, e=expect)}
            raise ValidationError(detail=error_msg)

        # Temp directory to store resourcemetadata.xml
        tmp_dir = tempfile.mkdtemp()
        try:
            # Fake the bag structure so that GenericResourceMeta.read_metadata_from_resource_bag
            # can read and validate the system and science metadata for us.
            bag_data_path = os.path.join(tmp_dir, 'data')
            os.mkdir(bag_data_path)
            # Copy new science metadata to bag data path
            scimeta_path = os.path.join(bag_data_path, 'resourcemetadata.xml')
            shutil.copy(scimeta.temporary_file_path(), scimeta_path)
            # Copy existing resource map to bag data path
            # (use a file-like object as the file may be in S3, so we can't
            #  just copy it to a local path)
            resmeta_path = os.path.join(bag_data_path, 'resourcemap.xml')
            with open(resmeta_path, 'wb') as resmeta:
                storage = get_file_storage()
                resmeta_s3 = storage.open(AbstractResource.sysmeta_path(pk))
                shutil.copyfileobj(resmeta_s3, resmeta)

            resmeta_s3.close()
            resmeta.close()

            try:
                # Read resource system and science metadata
                domain = Site.objects.get_current().domain
                rm = GenericResourceMeta.read_metadata_from_resource_bag(tmp_dir,
                                                                         hydroshare_host=domain)
                # Update resource metadata
                rm.write_metadata_to_resource(resource, update_title=True, update_keywords=True)
                create_bag_metadata_files(resource)
            except HsDeserializationDependencyException as e:
                msg = ("HsDeserializationDependencyException encountered when updating "
                       "science metadata for resource {pk}; depedent resource was {dep}.")
                msg = msg.format(pk=pk, dep=e.dependency_resource_id)
                logger.error(msg)
                raise ValidationError(detail=msg)
            except HsDeserializationException as e:
                raise ValidationError(detail=str(e))

            resource_modified(resource, request.user, overwrite_bag=False)
            return Response(data={'resource_id': pk}, status=status.HTTP_202_ACCEPTED)
        finally:
            shutil.rmtree(tmp_dir)


class ResourceMapRetrieve(APIView):
    """
    Retrieve resource map

    REST URL: hsapi/resource/{pk}/map
    HTTP method: GET

    :type pk: str
    :param pk: id of the resource
    :return: resource map as XML document
    :rtype: str
    :raises:
    NotFound: return json format: {'detail': 'No resource was found for resource id:pk'}
    PermissionDenied: return json format: {'detail': 'You do not have permission to perform
    this action.'}
    """
    allowed_methods = ('GET',)

    def get(self, request, pk):
        view_utils.authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_METADATA)

        resmap_url = AbstractResource.resmap_url(pk)
        return redirect(resmap_url)


class ResourceFileCRUD(APIView):
    """
    Retrieve, add, update or delete a resource file

    REST URL: hsapi/resource/{pk}/files/{filename}
    HTTP method: GET

    :type pk: str
    :type filename: str
    :param pk: resource id
    :param filename: name of the file to retrieve/download
    :return: resource file data
    :rtype: file data bytes

    REST URL: POST hsapi/resource/{pk}/files/
    UNUSED: See ResourceFileListCreate for details.
    HTTP method: POST

    Request post data: file data (required)
    :type pk: str
    :param pk: resource id
    :return: id of the resource and name of the file added
    :rtype: json string of format: {'resource_id':pk, 'file_name': name of the file added}

    REST URL: hsapi/resource/{pk}/files/{filename}
    HTTP method: PUT

    :type pk: str
    :type filename: str
    :param pk: resource id
    :param filename: name of the file to update
    :return: id of the resource and name of the file
    :rtype: json string of format: {'resource_id':pk, 'file_name': name of the file updates}

    REST URL: hsapi/resource/{pk}/files/{filename}
    HTTP method: DELETE

    :type pk: str
    :type filename: str
    :param pk: resource id
    :param filename: name of the file to delete
    :return: id of the resource and name of the file
    :rtype: json string of format: {'resource_id':pk, 'file_name': name of the file deleted}

    :raises:
    NotFound: return json format: {'detail': 'No resource was found for resource id':pk}
    PermissionDenied: return json format: {'detail': 'You do not have permission to perform
    this action.'}
    ValidationError: return json format: {'parameter-1':['error message-1'],
    'parameter-2': ['error message-2'], .. }
    """
    allowed_methods = ('GET', 'POST', 'PUT', 'DELETE')
    parser_classes = (MultiPartParser,)

    def initialize_request(self, request, *args, **kwargs):
        """
        Hack to work around the following issue in django-rest-framework:

        https://github.com/tomchristie/django-rest-framework/issues/3951

        Couch: This issue was recently closed (10/12/2016, 2 days before this writing)
        and is slated to be incorporated in the Django REST API 3.5.0 release.
        At that time, we should remove this hack.

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if not isinstance(request, Request):
            # Don't deep copy the file data as it may contain an open file handle
            old_file_data = copy.copy(request.FILES)
            old_post_data = copy.deepcopy(request.POST)
            request = super(ResourceFileCRUD, self).initialize_request(request, *args, **kwargs)
            request.POST._mutable = True
            request.POST.update(old_post_data)
            request.FILES.update(old_file_data)
        return request

    def get(self, request, pk, pathname):
        resource, _, _ = view_utils.authorize(
            request, pk,
            needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)

        if not resource.supports_folders and '/' in pathname:
            return Response("Resource type does not support folders", status.HTTP_403_FORBIDDEN)

        try:
            view_utils.s3_path_is_allowed(pathname)
        except (ValidationError, SuspiciousFileOperation) as ex:
            return Response(str(ex), status_code=status.HTTP_400_BAD_REQUEST)

        try:
            f = hydroshare.get_resource_file(pk, pathname).resource_file
        except ObjectDoesNotExist:
            err_msg = 'File with file name {file_name} does not exist for resource with ' \
                      'resource id {res_id}'.format(file_name=pathname, res_id=pk)
            raise NotFound(detail=err_msg)

        # redirects to django_s3/views.download function
        # use new internal url for rest call
        # TODO: (Couch) Migrate model (with a "data migration") so that this hack is not needed.
        redirect_url = f.url.replace('django_s3/download/', 'django_s3/rest_download/')
        return HttpResponseRedirect(redirect_url)

    @swagger_auto_schema(request_body=serializers.ResourceFileValidator)
    def post(self, request, pk, pathname):
        """
        Add a file to a resource.
        :param request:
        :param pk: Primary key of the resource (i.e. resource short ID)
        :param pathname: the path to the containing folder in the folder hierarchy
        :return:

        Leaving out pathname in the URI calls a different class function in ResourceFileListCreate
        that stores in the root directory instead.
        """
        resource, _, _ = view_utils.authorize(request, pk,
                                              needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

        resource_files = list(request.FILES.values())
        if len(resource_files) == 0:
            error_msg = {'file': 'No file was found to add to the resource.'}
            raise ValidationError(detail=error_msg)
        elif len(resource_files) > 1:
            error_msg = {'file': 'More than one file was found. Only one file can be '
                                 'added at a time.'}
            raise ValidationError(detail=error_msg)

        # TODO: (Brian) I know there has been some discussion when to validate a file
        # I agree that we should not validate and extract metadata as part of the file add api
        # Once we have a decision, I will change this implementation accordingly. In that case
        # we have to implement additional rest endpoints for file validation and extraction.
        try:
            hydroshare.utils.resource_file_add_pre_process(resource=resource,
                                                           files=[resource_files[0]],
                                                           folder=pathname,
                                                           user=request.user, extract_metadata=True)

        except (hydroshare.utils.ResourceFileSizeException,
                hydroshare.utils.ResourceFileValidationException, Exception) as ex:
            error_msg = {'file': 'Adding file to resource failed. %s' % str(ex)}
            raise ValidationError(detail=error_msg)

        try:
            res_file_objects = hydroshare.utils.resource_file_add_process(resource=resource,
                                                                          files=[resource_files[0]],
                                                                          folder=pathname,
                                                                          user=request.user,
                                                                          extract_metadata=True)

        except (hydroshare.utils.ResourceFileValidationException, Exception) as ex:
            error_msg = {'file': 'Adding file to resource failed. %s' % str(ex)}
            raise ValidationError(detail=error_msg)

        # prepare response data
        file_name = os.path.basename(res_file_objects[0].resource_file.name)
        file_path = res_file_objects[0].resource_file.name.split('/data/contents/')[1]
        response_data = {'resource_id': pk, 'file_name': file_name, 'file_path': file_path}
        resource_modified(resource, request.user, overwrite_bag=False)
        return Response(data=response_data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk, pathname):
        resource, _, user = view_utils.authorize(
            request, pk, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

        if not resource.supports_folders and '/' in pathname:
            return Response("Resource type does not support folders", status.HTTP_403_FORBIDDEN)

        try:
            view_utils.s3_path_is_allowed(pathname)  # check for hacking attempts
        except (ValidationError, SuspiciousFileOperation) as ex:
            return Response(str(ex), status=status.HTTP_400_BAD_REQUEST)

        try:
            hydroshare.delete_resource_file(pk, pathname, user)
        except ObjectDoesNotExist as ex:    # matching file not found
            raise NotFound(detail=str(ex))

        # prepare response data
        response_data = {'resource_id': pk, 'file_name': pathname}
        resource_modified(resource, request.user, overwrite_bag=False)
        return Response(data=response_data, status=status.HTTP_200_OK)

    @swagger_auto_schema(auto_schema=None)
    def put(self, request, pk, pathname):
        # TODO: (Brian) Currently we do not have this action for the front end. Will implement
        # in the next iteration. Implement only after we have a decision on when to validate a file
        raise NotImplementedError()


class ResourceFileListCreate(ResourceFileToListItemMixin, generics.ListCreateAPIView):
    """
    Create a resource file or retrieve a list of resource files

    REST URL: hsapi/resource/{pk}/files/
    DEPRECATED: hsapi/resource/{pk}/file_list/
    HTTP method: GET

    :type pk: str
    :type filename: str
    :param pk: resource id
    :param filename: name of the file to retrieve/download
    :return: JSON representation of list of files of the form:

    REST URL: POST hsapi/resource/{pk}/files/
    HTTP method: POST

    Request post data: file data (required)
    :type pk: str
    :param pk: resource id
    :return: id of the resource and name of the file added
    :rtype: json string of format: {'resource_id':pk, 'file_name': name of the file added}

    {
        "count": 2,
        "next": null,
        "previous": null,
        "results": [
            {
                "url": "http://mill24.cep.unc.edu/django_s3/
                download/bd88d2a152894134928c587d38cf0272/data/contents/
                mytest_resource/text_file.txt",
                "size": 21,
                "content_type": "text/plain",
                "modified_time": "2020-02-25T08:28:14",
                "checksum": "7265548b8f345605113bd9539313b4e7"
            },
            {
                "url": "http://mill24.cep.unc.edu/django_s3/download/
                bd88d2a152894134928c587d38cf0272/data/contents/mytest_resource/a_directory/cea.tif",
                "size": 270993,
                "content_type": "image/tiff",
                "modified_time": "2020-02-25T08:28:14",
                "checksum": "ed06b456c22f7123d20888d16bcd181d"
            }
        ]
    }

    :raises:
    NotFound: return json format: {'detail': 'No resource was found for resource id':pk}
    PermissionDenied: return json format: {'detail': 'You do not have permission to perform
    this action.'}

    """
    allowed_methods = ('GET', 'POST')

    def initialize_request(self, request, *args, **kwargs):
        """
        Hack to work around the following issue in django-rest-framework:

        https://github.com/tomchristie/django-rest-framework/issues/3951

        Couch: This issue was recently closed (10/12/2016, 2 days before this writing)
        and is slated to be incorporated in the Django REST API 3.5.0 release.
        At that time, we should remove this hack.

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if not isinstance(request, Request):
            # Don't deep copy the file data as it may contain an open file handle
            old_file_data = copy.copy(request.FILES)
            old_post_data = copy.deepcopy(request.POST)
            request = super(ResourceFileListCreate, self).initialize_request(
                request, *args, **kwargs)
            request.POST._mutable = True
            request.POST.update(old_post_data)
            request.FILES.update(old_file_data)
        return request

    def get(self, request, pk):
        """
        Get a listing of files within a resource.
        :param request:
        :param pk: Primary key of the resource (i.e. resource short ID)
        :return:
        """
        return self.list(request)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            resource_file_info_list = []
            for f in page:
                try:
                    resource_file_info_list.append(self.resourceFileToListItem(f))
                except SessionException as err:
                    logger.error(f"Error for file {f.storage_path} from S3: {err.stderr}")
                except CoreValidationError as err:
                    # primarily this exception will be raised if the file is not found in S3
                    logger.error(f"Error for file {f.storage_path} from S3: {str(err)}")

            serializer = self.get_serializer(resource_file_info_list, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        resource, _, _ = view_utils.authorize(self.request, self.kwargs['pk'],
                                              needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)

        # exclude files with size 0 as they are missing from S3
        return resource.files.exclude(_size=0).all()

    def get_serializer_class(self):
        return serializers.ResourceFileSerializer

    def post(self, request, pk):
        """
        Add a file to a resource.
        :param request:
        :param pk: Primary key of the resource (i.e. resource short ID)
        :return:
        """
        resource, _, _ = view_utils.authorize(request, pk,
                                              needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
        resource_files = list(request.FILES.values())
        if len(resource_files) == 0:
            error_msg = {'file': 'No file was found to add to the resource.'}
            raise ValidationError(detail=error_msg)
        elif len(resource_files) > 1:
            error_msg = {'file': 'More than one file was found. Only one file can be '
                                 'added at a time.'}
            raise ValidationError(detail=error_msg)

        # TODO: (Brian) I know there has been some discussion when to validate a file
        # I agree that we should not validate and extract metadata as part of the file add api
        # Once we have a decision, I will change this implementation accordingly. In that case
        # we have to implement additional rest endpoints for file validation and extraction.
        folder = request.POST.get('folder', '')
        try:
            hydroshare.utils.resource_file_add_pre_process(resource=resource,
                                                           files=[resource_files[0]],
                                                           user=request.user,
                                                           folder=folder,
                                                           extract_metadata=True)

        except (hydroshare.utils.ResourceFileSizeException,
                hydroshare.utils.ResourceFileValidationException, Exception) as ex:
            error_msg = {'file': 'Adding file to resource failed. %s' % str(ex)}
            raise ValidationError(detail=error_msg)

        try:
            res_file_objects = hydroshare.utils.resource_file_add_process(resource=resource,
                                                                          files=[resource_files[0]],
                                                                          user=request.user,
                                                                          folder=folder,
                                                                          extract_metadata=True)

        except (hydroshare.utils.ResourceFileValidationException, Exception) as ex:
            error_msg = {'file': 'Adding file to resource failed. %s' % str(ex)}
            raise ValidationError(detail=error_msg)

        if len(res_file_objects) == 0:
            # metadata ingestion
            response_data = {'resource_id': pk}
        else:
            file_name = os.path.basename(res_file_objects[0].resource_file.name)
            file_path = res_file_objects[0].resource_file.name.split('/data/contents/')[1]
            response_data = {'resource_id': pk, 'file_name': file_name, 'file_path': file_path}
        resource_modified(resource, request.user, overwrite_bag=False)
        return Response(data=response_data, status=status.HTTP_201_CREATED)


def _validate_metadata(metadata_list):
    """
    Make sure the metadata_list does not have data for the following
    core metadata elements. Exception is raised if any of the following elements is present
    in metadata_list:

    title - (endpoint has a title parameter which should be used for specifying resource title)
    subject (keyword) - (endpoint has a keywords parameter which should be used for specifying
    resource keywords)
    description (abstract)- (endpoint has a abstract parameter which should be used for specifying
    resource abstract)
    publisher - this element is created upon resource publication
    format - this element is created by the system based on the resource content files
    date - this element is created by the system
    type - this element is created by the system

    :param metadata_list: list of dicts each representing data for a specific metadata element
    :return:
    """

    err_message = "Metadata validation failed. Metadata element '{}' was found in value passed " \
                  "for parameter 'metadata'. Though it's a valid element it can't be passed " \
                  "as part of 'metadata' parameter."
    for element in metadata_list:
        # here k is the name of the element
        # v is a dict of all element attributes/field names and field values
        k, v = list(element.items())[0]
        if k.lower() in ('title', 'subject', 'description', 'publisher', 'format', 'date', 'type'):
            err_message = err_message.format(k.lower())
            raise ValidationError(detail=err_message)


class CustomTusFile(TusFile):
    # extend TusFile to allow it to write to s3 storage instead of local disk
    # https://github.com/alican/django-tus/blob/2aac2e7c0e6bac79a1cb07721947a48d9cc40ec8/django_tus/tusfile.py#L52

    def __init__(self, resource_id):
        self.storage = S3Storage()
        self.resource_id = resource_id
        self.filename = cache.get("tus-uploads/{}/filename".format(resource_id))
        self.file_size = int(cache.get("tus-uploads/{}/file_size".format(resource_id)))
        self.metadata = cache.get("tus-uploads/{}/metadata".format(resource_id))
        self.offset = cache.get("tus-uploads/{}/offset".format(resource_id))
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
        tus_file.write_init_file()
        return tus_file

    def get_path(self):
        hs_res_id = self.metadata.get('hs_res_id')
        return f"{hs_res_id}/data/contents/{self.resource_id}"
        # return self.resource_id

    def get_path_and_name(self):
        hs_res_id = self.metadata.get('hs_res_id')
        return f"{hs_res_id}/data/contents/{self.filename}"

    @staticmethod
    def check_existing_file(path):
        return S3Storage().exists(path)

    def is_valid(self):
        return self.filename is not None and self.storage.exists(self.get_path())

    def _write_file(self, path, offset, content):
        self.storage.connection.Bucket(self.bucket).put_object(Key=path, Body=content)

    def write_init_file(self):
        try:
            self._write_file(self.get_path(), self.file_size, b"\0")
        except Exception as e:
            error_message = "Unable to create file: {}".format(e)
            logger.error(error_message, exc_info=True)
            return TusResponse(status=500, reason=error_message)

    def write_chunk(self, chunk):
        try:
            self._write_file(self.get_path(), chunk.offset, chunk.content)
            self.offset = cache.incr("tus-uploads/{}/offset".format(self.resource_id), chunk.chunk_size)

        except IOError:
            logger.error("patch", extra={'request': chunk.META, 'tus': {
                "resource_id": self.resource_id,
                "filename": self.filename,
                "file_size": self.file_size,
                "metadata": self.metadata,
                "offset": self.offset,
                "upload_file_path": self.get_path(),
            }})
            return TusResponse(status=500)

    def rename(self):

        setting = settings.TUS_FILE_NAME_FORMAT

        if setting == 'keep':
            if self.check_existing_file(self.filename):
                return TusResponse(status=409, reason="File with same name already exists")
        elif setting == 'random':
            self.filename = FilenameGenerator(self.filename).create_random_name()
        elif setting == 'random-suffix':
            self.filename = FilenameGenerator(self.filename).create_random_suffix_name()
        elif setting == 'increment':
            self.filename = FilenameGenerator(self.filename).create_incremented_name()
        else:
            return ValueError()

        # move the object in s3
        self.storage.moveFile(self.get_path(), self.get_path_and_name())


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
        username_from_client = metadata.get('username')

        if not self.request.user.is_authenticated:
            sessionid = self.request.headers.get('HS-SID', None)
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

        # check that the user has permission to upload a file to the resource
        try:
            _, _, user = view_utils.authorize(self.request, hs_res_id,
                                              needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
            # ensure that the username is the same as the request user
            assert (user.username == username_from_client)
        except (DjangoPermissionDenied, AssertionError):
            return HttpResponseForbidden()

        return super(CustomTusUpload, self).dispatch(*args, **kwargs)

    def patch(self, request, resource_id, *args, **kwargs):

        # tus_file = CustomTusFile.get_tusfile_or_404(str(resource_id))
        tus_file = CustomTusFile(str(resource_id))

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

        tus_file.write_chunk(chunk=chunk)

        # https://github.com/alican/django-tus/blob/2aac2e7c0e6bac79a1cb07721947a48d9cc40ec8/django_tus/tusfile.py#L151-L152
        # here we modify from django_tus to allow for the file to be marked as complete
        if tus_file.is_complete():
            # file transfer complete, rename from resource id to actual filename
            tus_file.rename()
            tus_file.clean()

            # TODO: 5686 any additional cleanup required?
            # self.send_signal(tus_file)
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

        path = f"{metadata.get('hs_res_id')}/{metadata.get('filename', False)}"
        existing = CustomTusFile.check_existing_file(path)

        if settings.TUS_EXISTING_FILE == 'error' and settings.TUS_FILE_NAME_FORMAT == 'keep' and existing:
            return TusResponse(status=409, reason="File = with same name already exists")

        # set the filesize from HTTP header if it exists, otherwise set it from the metadata
        file_size = int(request.META.get("HTTP_UPLOAD_LENGTH", "0"))
        meta_file_size = metadata.get("file_size", None)
        if meta_file_size and meta_file_size != 'null':
            file_size = meta_file_size

        tus_file = CustomTusFile.create_initial_file(metadata, file_size)

        return TusResponse(
            status=201,
            extra_headers={'Location': '{}{}'.format(request.build_absolute_uri(), tus_file.resource_id)})
