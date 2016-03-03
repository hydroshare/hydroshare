__author__ = 'Pabitra'

import os
import mimetypes

from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import redirect

from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.exceptions import *

from hs_core import hydroshare
from hs_core.models import AbstractResource, ResourceManager
from hs_core.hydroshare.utils import get_resource_by_shortkey, get_resource_types
from hs_core.views import utils as view_utils
from hs_core.views.utils import ACTION_TO_AUTHORIZE
from hs_core.views import serializers
from hs_core.views import pagination


# Mixins
class ResourceToListItemMixin(object):
    def resourceToResourceListItem(self, r):
        site_url = hydroshare.utils.current_site_url()
        bag_url = site_url + AbstractResource.bag_url(r.short_id)
        science_metadata_url = site_url + reverse('get_update_science_metadata', args=[r.short_id])
        resource_url = site_url + r.get_absolute_url()
        resource_list_item = serializers.ResourceListItem(resource_type=r.resource_type,
                                                          resource_id=r.short_id,
                                                          resource_title=r.metadata.title.value,
                                                          creator=r.first_creator.name,
                                                          public=r.raccess.public,
                                                          discoverable=r.raccess.discoverable,
                                                          shareable=r.raccess.shareable,
                                                          immutable=r.raccess.immutable,
                                                          published=r.raccess.published,
                                                          date_created=r.created,
                                                          date_last_updated=r.updated,
                                                          bag_url=bag_url,
                                                          science_metadata_url=science_metadata_url,
                                                          resource_url=resource_url)
        return resource_list_item

class ResourceFileToListItemMixin(object):
    def resourceFileToListItem(self, f):
        url = hydroshare.utils.current_site_url() + f.resource_file.url
        fsize = f.resource_file.size
        mimetype = mimetypes.guess_type(url)
        if mimetype[0]:
            ftype = mimetype[0]
        else:
            ftype = repr(None)
        resource_file_info_item = serializers.ResourceFileItem(url=url,
                                                               size=fsize,
                                                               content_type=ftype)
        return resource_file_info_item


class ResourceTypes(generics.ListAPIView):
    """
    Get a list of resource types

    REST URL: hsapi/resourceTypes
    HTTP method: GET

    example return JSON format for GET /hsapi/resourceTypes (note response will consist of only one page):

    [
        {
            "resource_type": "GenericResource"
        },
        {
            "resource_type": "RasterResource"
        },
        {
            "resource_type": "RefTimeSeries"
        },
        {
            "resource_type": "TimeSeriesResource"
        },
        {
            "resource_type": "NetcdfResource"
        },
        {
            "resource_type": "ModelProgramResource"
        },
        {
            "resource_type": "ModelInstanceResource"
        },
        {
            "resource_type": "ToolResource"
        },
        {
            "resource_type": "SWATModelInstanceResource"
        }
    ]
    """
    pagination_class = pagination.SmallDatumPagination

    def get(self, request):
        return self.list(request)

    def get_queryset(self):
        return [serializers.ResourceType(resource_type=rtype.__name__) for rtype in get_resource_types()]

    def get_serializer_class(self):
        return serializers.ResourceTypesSerializer


class ResourceList(ResourceToListItemMixin, generics.ListAPIView):
    """
    Get a list of resources based on the following filter query parameters

    For an anonymous user, all public resources will be listed.
    For any authenticated user with no other query parameters provided in the request, all resources that are viewable
    by the user will be listed.

    REST URL: hsapi/resourceList/{query parameters}
    HTTP method: GET

    Supported query parameters (all are optional):

    :type   owner: str
    :type   types: list of resource type class names
    :type   from_date:  str (e.g., 2015-04-01)
    :type   to_date:    str (e.g., 2015-05-01)
    :type   edit_permission: bool
    :param  owner: (optional) - to get a list of resources owned by a specified username
    :param  types: (optional) - to get a list of resources of the specified resource types
    :param  from_date: (optional) - to get a list of resources created on or after this date
    :param  to_date: (optional) - to get a list of resources created on or before this date
    :param  edit_permission: (optional) - to get a list of resources for which the authorised user has edit permission
    :rtype:  json string
    :return:  a paginated list of resources with data for resource id, title, resource type, creator, public,
    date created, date last updated, resource bag url path, and science metadata url path

    example return JSON format for GET /hsapi/resourceList:

        {   "count":n
            "next": link to next page
            "previous": link to previous page
            "results":[
                    {"resource_type": resource type, "resource_title": resource title, "resource_id": resource id,
                    "creator": creator name, "date_created": date resource created,
                    "date_last_updated": date resource last updated, "public": true or false,
                    "discoverable": true or false, "shareable": true or false, "immutable": true or false,
                    "published": true or false, "bag_url": link to bag file,
                    "science_metadata_url": link to science metadata,
                    "resource_url": link to resource landing HTML page},
                    {"resource_type": resource type, "resource_title": resource title, "resource_id": resource id,
                    "creator": creator name, "date_created": date resource created,
                    "date_last_updated": date resource last updated, "public": true or false,
                    "discoverable": true or false, "shareable": true or false, "immutable": true or false,
                    "published": true or false, "bag_url": link to bag file,
                    "science_metadata_url": link to science metadata,
                    "resource_url": link to resource landing HTML page},
            ]
        }

    """
    pagination_class = PageNumberPagination

    def get(self, request):
        return self.list(request)

    # needed for list of resources
    def get_queryset(self):
        resource_list_request_validator = serializers.ResourceListRequestValidator(data=self.request.query_params)
        if not resource_list_request_validator.is_valid():
            raise ValidationError(detail=resource_list_request_validator.errors)

        filter_parms = resource_list_request_validator.validated_data
        filter_parms['user'] = (self.request.user if self.request.user.is_authenticated() else None)
        if len(filter_parms['type']) == 0:
            filter_parms['type'] = None
        else:
            filter_parms['type'] = list(filter_parms['type'])

        filter_parms['public'] = not self.request.user.is_authenticated()

        filtered_res_list = []

        for r in hydroshare.get_resource_list(**filter_parms):
            resource_list_item = self.resourceToResourceListItem(r)
            filtered_res_list.append(resource_list_item)

        return filtered_res_list

    def get_serializer_class(self):
        return serializers.ResourceListItemSerializer


class ResourceReadUpdateDelete(ResourceToListItemMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Create, read, or delete a resource

    REST URL: hsapi/resource/{pk}
    HTTP method: GET
    :return: (on success): The resource in zipped BagIt format.

    REST URL: hsapi/resource/{pk}
    HTTP method: DELETE
    :return: (on success): JSON string of the format: {'resource_id':pk}

    REST URL: hsapi/resource/{pk}
    HTTP method: PUT
    :return: (on success): JSON string of the format: {'resource_id':pk}

    :type   str
    :param  pk: resource id
    :rtype:  JSON string for http methods DELETE and PUT, and resource file data bytes for GET

    :raises:
    NotFound: return JSON format: {'detail': 'No resource was found for resource id':pk}
    PermissionDenied: return JSON format: {'detail': 'You do not have permission to perform this action.'}
    ValidationError: return JSON format: {parameter-1': ['error message-1'], 'parameter-2': ['error message-2'], .. }

    :raises:
    ValidationError: return json format: {'parameter-1':['error message-1'], 'parameter-2': ['error message-2'], .. }
    """
    pagination_class = PageNumberPagination

    allowed_methods = ('GET', 'POST', 'PUT', 'DELETE')

    def get(self, request, pk):
        """ Get resource in zipped BagIt format
        """
        view_utils.authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)

        bag_url = hydroshare.utils.current_site_url() + AbstractResource.bag_url(pk)
        return HttpResponseRedirect(bag_url)

    def put(self, request, pk):
        # TODO: update resource - involves overwriting a resource from the provided bag file
        raise NotImplementedError()

    def delete(self, request, pk):
        # only resource owners are allowed to delete
        view_utils.authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.DELETE_RESOURCE)
        hydroshare.delete_resource(pk)
        # spec says we need return the id of the resource that got deleted - otherwise would have used status code 204
        # and not 200
        return Response(data={'resource_id': pk}, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        return serializers.ResourceListItemSerializer


class ResourceCreate(generics.CreateAPIView):
    """
    Create a new resource

    REST URL: hsapi/resource
    HTTP method: POST

    Request data payload parameters:
    :type   resource_type: str
    :type   title: str
    :type   edit_users: str
    :type   edit_groups: str
    :type   view_users: str
    :type   view_groups: str
    :param  resource_type: resource type name
    :param  title: (optional) title of the resource (default value: 'Untitled resource')
    :param  edit_users: (optional) list of comma separated usernames that should have edit permission for the resource
    :param  edit_groups: (optional) list of comma separated group names that should have edit permission for the resource
    :param  view_users: (optional) list of comma separated usernames that should have view permission for the resource
    :param  view_groups: (optional) list of comma separated group names that should have view permission for the resource
    :return: id and type of the resource created
    :rtype: json string of the format: {'resource-id':id, 'resource_type': resource type}
    :raises:
    NotAuthenticated: return json format: {'detail': 'Authentication credentials were not provided.'}
    ValidationError: return json format: {parameter-1':['error message-1'], 'parameter-2': ['error message-2'], .. }
    """

    def get_serializer_class(self):
        return serializers.ResourceCreateRequestValidator

    def post(self, request):
        return self.create(request)

    # Override the create() method from the CreateAPIView class
    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise NotAuthenticated()

        resource_create_request_validator = serializers.ResourceCreateRequestValidator(data=request.data)
        if not resource_create_request_validator.is_valid():
            raise ValidationError(detail=resource_create_request_validator.errors)

        validated_request_data = resource_create_request_validator.validated_data
        resource_type = validated_request_data['resource_type']

        res_title = validated_request_data.get('title', 'Untitled resource')
        keywords = validated_request_data.get('keywords', None)
        abstract = validated_request_data.get('abstract', None)

        num_files = len(request.FILES)
        if num_files > 0:
            if num_files > 1:
                raise ValidationError(detail={'file': 'Multiple file upload is not allowed on resource creation. Add additional files after the resource is created.'})
            # Place files into format expected by hydroshare.utils.resource_pre_create_actions and
            # hydroshare.create_resource, i.e. a tuple of django.core.files.uploadedfile.TemporaryUploadedFile objects.
            files = [request.FILES['file'],]
        else:
            files = []

        _, res_title, metadata = hydroshare.utils.resource_pre_create_actions(resource_type=resource_type,
                                                                              resource_title=res_title,
                                                                              page_redirect_url_key=None,
                                                                              files=files,
                                                                              metadata=None,  **kwargs)
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
                    files=files
            )
            if abstract:
                resource.metadata.create_element('description', abstract=abstract)
        except Exception as ex:
            error_msg = {'resource': "Resource creation failed. %s" % ex.message}
            raise ValidationError(detail=error_msg)

        response_data = {'resource_type': resource_type, 'resource_id': resource.short_id}
        return Response(data=response_data,  status=status.HTTP_201_CREATED)


class SystemMetadataRetrieve(ResourceToListItemMixin, APIView):
    """
    Retrieve resource science metadata

    REST URL: hsapi/sysmeta/{pk}
    HTTP method: GET

    :type pk: str
    :param pk: id of the resource
    :return: system metadata as JSON string
    :rtype: str
    :raises:
    NotFound: return JSON format: {'detail': 'No resource was found for resource id:pk'}
    PermissionDenied: return JSON format: {'detail': 'You do not have permission to perform this action.'}

    example return JSON format for GET hsapi/sysmeta/<RESOURCE_ID>:

    {
        "resource_type": resource type,
        "resource_title": resource title,
        "resource_id": resource id,
        "creator": creator user name,
        "date_created": date resource created,
        "date_last_updated": date resource last updated,
        "public": true or false,
        "discoverable": true or false,
        "shareable": true or false,
        "immutable": true or false,
        "published": true or false,
        "bag_url": link to bag file,
        "science_metadata_url": link to science metadata
    }
    """
    allowed_methods = ('GET',)

    def get(self, request, pk):
        """ Get resource system metadata, as well as URLs to the bag and science metadata
        """
        view_utils.authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_METADATA)
        res = get_resource_by_shortkey(pk)
        ser = self.get_serializer_class()(self.resourceToResourceListItem(res))

        return Response(data=ser.data, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        return serializers.ResourceListItemSerializer


class AccessRulesUpdate(APIView):
    """
    Set access rules for a resource

    REST URL: hsapi/resource/accessRules/{pk}
    HTTP method: PUT

    :type pk: str
    :param pk: id of the resource
    :return: No content.  Status code will 200 (OK)
    """
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
        res.raccess.public = validated_request_data['public']
        res.raccess.save()

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
    PermissionDenied: return json format: {'detail': 'You do not have permission to perform this action.'}

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
    PermissionDenied: return json format: {'detail': 'You do not have permission to perform this action.'}
    ValidationError: return json format: {parameter-1': ['error message-1'], 'parameter-2': ['error message-2'], .. }
    """
    allowed_methods = ('GET', 'PUT')

    def get(self, request, pk):
        view_utils.authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_METADATA)

        scimeta_url = hydroshare.utils.current_site_url() + AbstractResource.scimeta_url(pk)
        return redirect(scimeta_url)


    def put(self, request, pk):
        # TODO: update science metadata using the metadata json data provided - will do in the next iteration
        # Should this update any extracted metadata? It would be easier to implement if we allow update of
        # any metadata.
        raise NotImplementedError()


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

    REST URL: POST hsapi/resource/{pk}/files
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
    PermissionDenied: return json format: {'detail': 'You do not have permission to perform this action.'}
    ValidationError: return json format: {'parameter-1':['error message-1'], 'parameter-2': ['error message-2'], .. }
    """
    allowed_methods = ('GET', 'POST', 'PUT', 'DELETE')

    def get(self, request, pk, filename):
        view_utils.authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
        try:
            f = hydroshare.get_resource_file(pk, filename)
        except ObjectDoesNotExist:
            err_msg = 'File with file name {file_name} does not exist for resource with resource id ' \
                      '{res_id}'.format(file_name=filename, res_id=pk)
            raise NotFound(detail=err_msg)

        # redirects to django_irods/views.download function
        return HttpResponseRedirect(f.url)

    def post(self, request, pk):
        """
        Add a file to a resource.
        :param request:
        :param pk: Primary key of the resource (i.e. resource short ID)
        :return:
        """
        resource, _, _ = view_utils.authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
        resource_files = request.FILES.values()
        if len(resource_files) == 0:
            error_msg = {'file': 'No file was found to add to the resource.'}
            raise ValidationError(detail=error_msg)
        elif len(resource_files) > 1:
            error_msg = {'file': 'More than one file was found. Only one file can be added at a time.'}
            raise ValidationError(detail=error_msg)

        # TODO: I know there has been some discussion when to validate a file
        # I agree that we should not validate and extract metadata as part of the file add api
        # Once we have a decision, I will change this implementation accordingly. In that case we have
        # to implement additional rest endpoints for file validation and extraction.
        try:
            hydroshare.utils.resource_file_add_pre_process(resource=resource, files=[resource_files[0]],
                                                           user=request.user, extract_metadata=True)

        except (hydroshare.utils.ResourceFileSizeException, hydroshare.utils.ResourceFileValidationException, Exception) as ex:
            error_msg = {'file': 'Adding file to resource failed. %s' % ex.message}
            raise ValidationError(detail=error_msg)

        try:
           res_file_objects = hydroshare.utils.resource_file_add_process(resource=resource, files=[resource_files[0]],
                                                                         user=request.user, extract_metadata=True)

        except (hydroshare.utils.ResourceFileValidationException, Exception) as ex:
            error_msg = {'file': 'Adding file to resource failed. %s' % ex.message}
            raise ValidationError(detail=error_msg)

        # prepare response data
        file_name = os.path.basename(res_file_objects[0].resource_file.name)
        response_data = {'resource_id': pk, 'file_name': file_name}
        return Response(data=response_data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk, filename):
        resource, _, user = view_utils.authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
        try:
            hydroshare.delete_resource_file(pk, filename, user)
        except ObjectDoesNotExist as ex:    # matching file not found
            raise NotFound(detail=ex.message)

        # prepare response data
        response_data = {'resource_id': pk, 'file_name': filename}
        return Response(data=response_data, status=status.HTTP_200_OK)

    def put(self, request, pk, filename):
        # TODO: Currently we do not have this action for the front end. Will implement in the next iteration
        # Implement only after we have a decision when to validate a file
        raise NotImplementedError()


class ResourceFileList(ResourceFileToListItemMixin, generics.ListAPIView):
    """
    Retrieve a list of resource files for a resource

    REST URL: hsapi/resource/{pk}/file_list/
    HTTP method: GET

    :type pk: str
    :type filename: str
    :param pk: resource id
    :param filename: name of the file to retrieve/download
    :return: JSON representation of list of files of the form:

    {
        "count": 2,
        "next": null,
        "previous": null,
        "results": [
            {
                "url": "http://mill24.cep.unc.edu/django_irods/download/bd88d2a152894134928c587d38cf0272/data/contents/mytest_resource/text_file.txt",
                "size": 21,
                "content_type": "text/plain"
            },
            {
                "url": "http://mill24.cep.unc.edu/django_irods/download/bd88d2a152894134928c587d38cf0272/data/contents/mytest_resource/a_directory/cea.tif",
                "size": 270993,
                "content_type": "image/tiff"
            }
        ]
    }

    :raises:
    NotFound: return json format: {'detail': 'No resource was found for resource id':pk}
    PermissionDenied: return json format: {'detail': 'You do not have permission to perform this action.'}
    """
    allowed_methods = ('GET',)

    def get(self, request, pk):
        """
        Get a listing of files within a resource.
        :param request:
        :param pk: Primary key of the resource (i.e. resource short ID)
        :return:
        """
        return self.list(request)

    def get_queryset(self):
        resource, _, _ = view_utils.authorize(self.request, self.kwargs['pk'],
                                              needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
        resource_file_info_list = []
        for f in resource.files.all():
            resource_file_info_list.append(self.resourceFileToListItem(f))
        return resource_file_info_list

    def get_serializer_class(self):
        return serializers.ResourceFileSerializer
