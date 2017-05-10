import os
import mimetypes
import copy
import tempfile
import shutil
import logging
import json

from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist, SuspiciousFileOperation
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.contrib.sites.models import Site

from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied, NotFound

from hs_core import hydroshare
from hs_core.models import AbstractResource
from hs_core.hydroshare.utils import get_resource_by_shortkey, get_resource_types
from hs_core.views import utils as view_utils
from hs_core.views.utils import ACTION_TO_AUTHORIZE
from hs_core.views import serializers
from hs_core.views import pagination
from hs_core.hydroshare.utils import get_file_storage, resource_modified
from hs_core.serialization import GenericResourceMeta, HsDeserializationDependencyException, \
    HsDeserializationException
from hs_core.hydroshare.hs_bagit import create_bag_files


logger = logging.getLogger(__name__)


# Mixins
class ResourceToListItemMixin(object):
    def resourceToResourceListItem(self, r):
        site_url = hydroshare.utils.current_site_url()
        bag_url = site_url + AbstractResource.bag_url(r.short_id)
        science_metadata_url = site_url + reverse('get_update_science_metadata', args=[r.short_id])
        resource_map_url = site_url + reverse('get_resource_map', args=[r.short_id])
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
                                                          resource_map_url=resource_map_url,
                                                          resource_url=resource_url)
        return resource_list_item


class ResourceFileToListItemMixin(object):
    def resourceFileToListItem(self, f):
        site_url = hydroshare.utils.current_site_url()
        url = site_url + f.url
        fsize = f.size
        # trailing slash confuses mime guesser
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

    example return JSON format for GET /hsapi/resourceTypes (note response will consist of only
    one page):

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
        return [serializers.ResourceType(resource_type=rtype.__name__) for rtype in
                get_resource_types()]

    def get_serializer_class(self):
        return serializers.ResourceTypesSerializer


class ResourceList(ResourceToListItemMixin, generics.ListAPIView):
    """
    Get a list of resources based on the following filter query parameters
    DEPRECATED: See GET /resource/ in CreateResource

    For an anonymous user, all public resources will be listed.
    For any authenticated user with no other query parameters provided in the request, all
    resources that are viewable by the user will be listed.

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
    :param  edit_permission: (optional) - to get a list of resources for which the authorised user
    has edit permission
    :rtype:  json string
    :return:  a paginated list of resources with data for resource id, title, resource type,
    creator, public, date created, date last updated, resource bag url path, and science
    metadata url path

    example return JSON format for GET /hsapi/resourceList:

        {   "count":n
            "next": link to next page
            "previous": link to previous page
            "results":[
                    {"resource_type": resource type, "resource_title": resource title,
                    "resource_id": resource id,
                    "creator": creator name, "date_created": date resource created,
                    "date_last_updated": date resource last updated, "public": true or false,
                    "discoverable": true or false, "shareable": true or false,
                    "immutable": true or false,
                    "published": true or false, "bag_url": link to bag file,
                    "science_metadata_url": link to science metadata,
                    "resource_url": link to resource landing HTML page},
                    {"resource_type": resource type, "resource_title": resource title,
                    "resource_id": resource id,
                    "creator": creator name, "date_created": date resource created,
                    "date_last_updated": date resource last updated, "public": true or false,
                    "discoverable": true or false, "shareable": true or false,
                    "immutable": true or false,
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
        resource_list_request_validator = serializers.ResourceListRequestValidator(
            data=self.request.query_params)
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


class CheckTaskStatus(generics.RetrieveAPIView):
    def get(self, request, task_id):
        url = reverse('rest_check_task_status', kwargs={'task_id': task_id})
        return HttpResponseRedirect(url)


class ResourceReadUpdateDelete(ResourceToListItemMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Read, update, or delete a resource

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
    PermissionDenied: return JSON format: {'detail': 'You do not have permission to perform
    this action.'}
    ValidationError: return JSON format: {parameter-1': ['error message-1'], 'parameter-2':
    ['error message-2'], .. }

    :raises:
    ValidationError: return json format: {'parameter-1':['error message-1'], 'parameter-2':
    ['error message-2'], .. }
    """
    pagination_class = PageNumberPagination

    allowed_methods = ('GET', 'PUT', 'DELETE')

    def get(self, request, pk):
        """ Get resource in zipped BagIt format
        """
        res, _, _ = view_utils.authorize(request, pk,
                                         needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
        site_url = hydroshare.utils.current_site_url()
        if res.resource_type.lower() == "reftimeseriesresource":

            # if res is RefTimeSeriesResource
            bag_url = site_url + reverse('rest_download_refts_resource_bag',
                                         kwargs={'shortkey': pk})
        else:
            bag_url = site_url + reverse('rest_download',
                                         kwargs={'path': 'bags/{}.zip'.format(pk)})
        return HttpResponseRedirect(bag_url)

    def put(self, request, pk):
        # TODO: update resource - involves overwriting a resource from the provided bag file
        raise NotImplementedError()

    def delete(self, request, pk):
        # only resource owners are allowed to delete
        view_utils.authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.DELETE_RESOURCE)
        hydroshare.delete_resource(pk)
        # spec says we need return the id of the resource that got deleted - otherwise would
        # have used status code 204 and not 200
        return Response(data={'resource_id': pk}, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        return serializers.ResourceListItemSerializer


class ResourceListCreate(ResourceToListItemMixin, generics.ListCreateAPIView):
    """
    Create a new resource or list existing resources

    REST URL: hsapi/resource/
    HTTP method: POST

    Request data payload parameters:
    :type   resource_type: str
    :type   title: str
    :type   subject: str
    :type   edit_users: str
    :type   edit_groups: str
    :type   view_users: str
    :type   view_groups: str
    :param  resource_type: resource type name
    :param  title: (optional) title of the resource (default value: 'Untitled resource')
    :param  edit_users: (optional) list of comma separated usernames that should have edit
    permission for the resource
    :param  edit_groups: (optional) list of comma separated group names that should have edit
    permission for the resource
    :param  view_users: (optional) list of comma separated usernames that should have view
    permission for the resource
    :param  view_groups: (optional) list of comma separated group names that should have view
    permission for the resource
    :param  metadata: (optional) data for any valid metadata element including resource specific
    metadata elements can be passed as json string:
    example (passing data for the 'Coverage' element):
    [{'coverage':{'type': 'period', 'start': '01/01/2000', 'end': '12/12/2010'}}, ...]
    Note: the parameter 'metadata' can't be used for passing data for the following core metadata
    elements:
    Title, Description (abstract), Subject (keyword), Date, Publisher, Type, Format
    :param  extra_metadata: (optional) data for any user-defined key/value pair metadata elements
    of the resource can be passed as json string
    example :
    {'Outlet Point Latitude': '40', 'Outlet Point Longitude': '-110'}
    :return: id and type of the resource created
    :rtype: json string of the format: {'resource-id':id, 'resource_type': resource type}
    :raises:
    NotAuthenticated: return json format: {'detail': 'Authentication credentials were not
    provided.'}
    ValidationError: return json format: {parameter-1':['error message-1'], 'parameter-2':
    ['error message-2'], .. }

    REST URL: hsapi/resource/
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
    :param  edit_permission: (optional) - to get a list of resources for which the authorised user
    has edit permission
    :rtype:  json string
    :return:  a paginated list of resources with data for resource id, title, resource type,
    creator, public, date created, date last updated, resource bag url path, and science
    metadata url path

    example return JSON format for GET /hsapi/resourceList:

        {   "count":n
            "next": link to next page
            "previous": link to previous page
            "results":[
                    {"resource_type": resource type, "resource_title": resource title,
                    "resource_id": resource id,
                    "creator": creator name, "date_created": date resource created,
                    "date_last_updated": date resource last updated, "public": true or false,
                    "discoverable": true or false, "shareable": true or false,
                    "immutable": true or false,
                    "published": true or false, "bag_url": link to bag file,
                    "science_metadata_url": link to science metadata,
                    "resource_url": link to resource landing HTML page},
                    {"resource_type": resource type, "resource_title": resource title,
                    "resource_id": resource id,
                    "creator": creator name, "date_created": date resource created,
                    "date_last_updated": date resource last updated, "public": true or false,
                    "discoverable": true or false, "shareable": true or false,
                    "immutable": true or false,
                    "published": true or false, "bag_url": link to bag file,
                    "science_metadata_url": link to science metadata,
                    "resource_url": link to resource landing HTML page},
            ]
        }
    """
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
            request = super(ResourceListCreate, self).initialize_request(request, *args, **kwargs)
            request.POST.update(old_post_data)
            request.FILES.update(old_file_data)
        return request

    # Couch: This is called explicitly in the overrided create() method and thus this
    # declaration does nothing. Thus, it can be changed to whatever is convenient.
    # Currently, it is convenient to use the listing serializer instead, so that
    # it will be the default output serializer.
    # def get_serializer_class(self):
    #     return serializers.ResourceCreateRequestValidator

    def post(self, request):
        return self.create(request)

    # Override the create() method from the CreateAPIView class
    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise NotAuthenticated()

        resource_create_request_validator = serializers.ResourceCreateRequestValidator(
            data=request.data)
        if not resource_create_request_validator.is_valid():
            raise ValidationError(detail=resource_create_request_validator.errors)

        validated_request_data = resource_create_request_validator.validated_data
        resource_type = validated_request_data['resource_type']

        res_title = validated_request_data.get('title', 'Untitled resource')
        keywords = validated_request_data.get('keywords', None)
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
            _, res_title, metadata, _ = hydroshare.utils.resource_pre_create_actions(
                resource_type=resource_type, resource_title=res_title,
                page_redirect_url_key=None, files=files, metadata=metadata,
                **kwargs)
        except Exception as ex:
            error_msg = {'resource': "Resource creation failed. %s" % ex.message}
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
            error_msg = {'resource': "Resource creation failed. %s" % ex.message}
            raise ValidationError(detail=error_msg)

        post_creation_error_msg = ''
        try:
            hydroshare.utils.resource_post_create_actions(request=request, resource=resource,
                                                          user=request.user,
                                                          metadata=metadata, **kwargs)
        except (hydroshare.utils.ResourceFileValidationException, Exception) as ex:
            post_creation_error_msg = ex.message

        response_data = {'resource_type': resource_type, 'resource_id': resource.short_id,
                         'message': post_creation_error_msg}

        return Response(data=response_data,  status=status.HTTP_201_CREATED)

    pagination_class = PageNumberPagination

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

    # covers serialization of output from GET request
    def get_serializer_class(self):
        return serializers.ResourceListItemSerializer


class SystemMetadataRetrieve(ResourceToListItemMixin, APIView):
    """
    Retrieve resource system metadata

    REST URL: hsapi/sysmeta/{pk}
    HTTP method: GET

    :type pk: str
    :param pk: id of the resource
    :return: system metadata as JSON string
    :rtype: str
    :raises:
    NotFound: return JSON format: {'detail': 'No resource was found for resource id:pk'}
    PermissionDenied: return JSON format: {'detail': 'You do not have permission to
    perform this action.'}

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
        res, _, _ = view_utils.authorize(request, pk,
                                         needed_permission=ACTION_TO_AUTHORIZE.VIEW_METADATA)
        ser = self.get_serializer_class()(self.resourceToResourceListItem(res))

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
        except ValidationError:
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

        scimeta_url = hydroshare.utils.current_site_url() + AbstractResource.scimeta_url(pk)
        return redirect(scimeta_url)

    def put(self, request, pk):
        # Update science metadata based on resourcemetadata.xml uploaded
        resource, authorized, user = view_utils.authorize(
            request, pk,
            needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
            raises_exception=False)
        if not authorized:
            raise PermissionDenied()

        files = request.FILES.values()
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
            # (use a file-like object as the file may be in iRODS, so we can't
            #  just copy it to a local path)
            resmeta_path = os.path.join(bag_data_path, 'resourcemap.xml')
            with open(resmeta_path, 'wb') as resmeta:
                storage = get_file_storage()
                resmeta_irods = storage.open(AbstractResource.sysmeta_path(pk))
                shutil.copyfileobj(resmeta_irods, resmeta)

            resmeta_irods.close()

            try:
                # Read resource system and science metadata
                domain = Site.objects.get_current().domain
                rm = GenericResourceMeta.read_metadata_from_resource_bag(tmp_dir,
                                                                         hydroshare_host=domain)
                # Update resource metadata
                rm.write_metadata_to_resource(resource, update_title=True, update_keywords=True)
                create_bag_files(resource)
            except HsDeserializationDependencyException as e:
                msg = ("HsDeserializationDependencyException encountered when updating "
                       "science metadata for resource {pk}; depedent resource was {dep}.")
                msg = msg.format(pk=pk, dep=e.dependency_resource_id)
                logger.error(msg)
                raise ValidationError(detail=msg)
            except HsDeserializationException as e:
                raise ValidationError(detail=e.message)

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
    allowed_methods = ('GET')

    def get(self, request, pk):
        view_utils.authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_METADATA)

        resmap_url = hydroshare.utils.current_site_url() + AbstractResource.resmap_url(pk)
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
            view_utils.irods_path_is_allowed(pathname)
        except (ValidationError, SuspiciousFileOperation) as ex:
            return Response(ex.message, status_code=status.HTTP_400_BAD_REQUEST)

        try:
            f = hydroshare.get_resource_file(pk, pathname)
        except ObjectDoesNotExist:
            err_msg = 'File with file name {file_name} does not exist for resource with ' \
                      'resource id {res_id}'.format(file_name=pathname, res_id=pk)
            raise NotFound(detail=err_msg)

        # redirects to django_irods/views.download function
        # use new internal url for rest call
        # TODO: (Couch) Migrate model (with a "data migration") so that this hack is not needed.
        redirect_url = f.url.replace('django_irods/download/', 'django_irods/rest_download/')
        return HttpResponseRedirect(redirect_url)

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

        resource_files = request.FILES.values()
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
                                                           user=request.user, extract_metadata=True)

        except (hydroshare.utils.ResourceFileSizeException,
                hydroshare.utils.ResourceFileValidationException, Exception) as ex:
            error_msg = {'file': 'Adding file to resource failed. %s' % ex.message}
            raise ValidationError(detail=error_msg)

        try:
            res_file_objects = hydroshare.utils.resource_file_add_process(resource=resource,
                                                                          files=[resource_files[0]],
                                                                          folder=pathname,
                                                                          user=request.user,
                                                                          extract_metadata=True)

        except (hydroshare.utils.ResourceFileValidationException, Exception) as ex:
            error_msg = {'file': 'Adding file to resource failed. %s' % ex.message}
            raise ValidationError(detail=error_msg)

        # prepare response data
        file_name = os.path.basename(res_file_objects[0].resource_file.name)
        response_data = {'resource_id': pk, 'file_name': file_name}
        resource_modified(resource, request.user, overwrite_bag=False)
        return Response(data=response_data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk, pathname):
        resource, _, user = view_utils.authorize(
            request, pk, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

        if not resource.supports_folders and '/' in pathname:
            return Response("Resource type does not support folders", status.HTTP_403_FORBIDDEN)

        try:
            view_utils.irods_path_is_allowed(pathname)  # check for hacking attempts
        except (ValidationError, SuspiciousFileOperation) as ex:
            return Response(ex.message, status=status.HTTP_400_BAD_REQUEST)

        try:
            hydroshare.delete_resource_file(pk, pathname, user)
        except ObjectDoesNotExist as ex:    # matching file not found
            raise NotFound(detail=ex.message)

        # prepare response data
        response_data = {'resource_id': pk, 'file_name': pathname}
        resource_modified(resource, request.user, overwrite_bag=False)
        return Response(data=response_data, status=status.HTTP_200_OK)

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
                "url": "http://mill24.cep.unc.edu/django_irods/
                download/bd88d2a152894134928c587d38cf0272/data/contents/
                mytest_resource/text_file.txt",
                "size": 21,
                "content_type": "text/plain"
            },
            {
                "url": "http://mill24.cep.unc.edu/django_irods/download/
                bd88d2a152894134928c587d38cf0272/data/contents/mytest_resource/a_directory/cea.tif",
                "size": 270993,
                "content_type": "image/tiff"
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

    def get_queryset(self):
        resource, _, _ = view_utils.authorize(self.request, self.kwargs['pk'],
                                              needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
        resource_file_info_list = []
        for f in resource.files.all():
            resource_file_info_list.append(self.resourceFileToListItem(f))
        return resource_file_info_list

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
        resource_files = request.FILES.values()
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
        folder = request.POST.get('folder', None)
        try:
            hydroshare.utils.resource_file_add_pre_process(resource=resource,
                                                           files=[resource_files[0]],
                                                           user=request.user,
                                                           folder=folder,
                                                           extract_metadata=True)

        except (hydroshare.utils.ResourceFileSizeException,
                hydroshare.utils.ResourceFileValidationException, Exception) as ex:
            error_msg = {'file': 'Adding file to resource failed. %s' % ex.message}
            raise ValidationError(detail=error_msg)

        try:
            res_file_objects = hydroshare.utils.resource_file_add_process(resource=resource,
                                                                          files=[resource_files[0]],
                                                                          user=request.user,
                                                                          folder=folder,
                                                                          extract_metadata=True)

        except (hydroshare.utils.ResourceFileValidationException, Exception) as ex:
            error_msg = {'file': 'Adding file to resource failed. %s' % ex.message}
            raise ValidationError(detail=error_msg)

        # prepare response data
        file_name = os.path.basename(res_file_objects[0].resource_file.name)
        response_data = {'resource_id': pk, 'file_name': file_name}
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
        k, v = element.items()[0]
        if k.lower() in ('title', 'subject', 'description', 'publisher', 'format', 'date', 'type'):
            err_message = err_message.format(k.lower())
            raise ValidationError(detail=err_message)
