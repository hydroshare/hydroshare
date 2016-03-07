from __future__ import absolute_import
import arrow

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import Group, User
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from mezzanine.generic.models import Keyword
from ga_resources.utils import get_user, json_or_jsonp
from hs_core import hydroshare
from hs_core.views import utils
from .utils import authorize, validate_json, ACTION_TO_AUTHORIZE
from django.views.generic import View
from django.core import exceptions

from hs_core.models import AbstractResource, ResourceManager

class ResourceCRUD(View):
    """
    Retrieve a resource identified by the pid from HydroShare. The response must contain the bytes of the indicated
    resource, and the checksum of the bytes retrieved should match the checksum recorded in the system metadata for
    that resource. The bytes of the resource will be encoded as a zipped BagIt archive; this archive will contain
    resource contents as well as science metadata. If the resource does not exist in HydroShare, then
    Exceptions.NotFound must be raised. Resources can be any unit of content within HydroShare that has been assigned a
    pid.

    Parameters:    pk - Unique HydroShare identifier for the resource to be retrieved.

    Returns:    Bytes of the specified resource.

    Return Type:    OctetStream

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request

    Notes:
    All resources and resource versions will have a unique internal HydroShare identifier (pid). A DOI will be
    assigned to all formally published versions of a resource. For this method, passing in a pid (which is a HydroShare
    internal identifer) would return a specific resource version corresponding to the pid. A DOI would have to be
    resolved using HydroShare.resolveDOI() to get the pid for the resource, which could then be used with this method.
    The obsoletion chain will be contained within the system metadata for resources and so it can be traversed by
    calling HydroShare.getSystemMetadata().

    ---

    Called by a client to add a new resource to HydroShare. The caller must have authorization to write content to
    HydroShare. The pid for the resource is assigned by HydroShare upon inserting the resource.  The create method
    returns the newly-assigned pid.

    REST URL:  POST /resource

    Parameters:
    resource - The data bytes of the resource to be added to HydroShare

    Returns:    The pid assigned to the newly created resource

    Return Type:    pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized to write to HydroShare
    Exceptions.InvalidContent - The content of the resource is incomplete
    Exception.ServiceFailure - The service is unable to process the request

    Note:  The calling user will automatically be set as the owner of the created resource.

    ---

     Called by clients to update a resource in HydroShare.

    REST URL:  PUT /resource/{pid}

    Parameters:
    pid - Unique HydroShare identifier for the resource that is to be updated.

    resource - The data bytes of the resource that will update the existing resource identified by pid

    Returns:    The pid assigned to the updated resource

    Return Type:    pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.InvalidContent - The content of the resource is incomplete
    Exception.ServiceFailure - The service is unable to process the request

    Notes:
    For mutable resources (resources that have not been formally published), the update overwrites existing data and
    metadata using the resource that is passed to this method. If a user wants to create a copy or modified version of a
    mutable resource this should be done using HydroShare.createResource().

    For immutable resources (formally published resources), this method creates a new resource that is a new version of
    formally published resource. HydroShare will record the update by storing the SystemMetadata.obsoletes and
    SystemMetadata.obsoletedBy fields for the respective resources in their system metadata.HydroShare MUST check or set
    the values of SystemMetadata.obsoletes and SystemMetadata.obsoletedBy so that they accurately represent the
    relationship between the new and old objects. HydroShare MUST also set SystemMetadata.dateSysMetadataModified. The
    modified system metadata entries must then be available in HydroShare.listObjects() to ensure that any cataloging
    systems pick up the changes when filtering on SystmeMetadata.dateSysMetadataModified. A formally published resource
    can only be obsoleted by one newer version. Once a resource is obsoleted, no other resources can obsolete it.

    ----

    Deletes a resource managed by HydroShare. The caller must be an owner of the resource or an administrator to perform
    this function. The operation removes the resource from further interaction with HydroShare services and interfaces. The
    implementation may delete the resource bytes, and should do so since a delete operation may be in response to a problem
    with the resource (e.g., it contains malicious content, is inappropriate, or is subject to a legal request). If the
    resource does not exist, the Exceptions.NotFound exception is raised.

    REST URL:  DELETE /resource/{pid}

    Parameters:
    pid - The unique HydroShare identifier of the resource to be deleted

    Returns:
    The pid of the resource that was deleted

    Return Type:    pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request

    Note:  Only HydroShare administrators will be able to delete formally published resour

    """

    class UpdateResourceForm(forms.Form):
        title = forms.CharField(required=False)
        keywords = forms.ModelMultipleChoiceField(Keyword.objects.all(), required=False)
        metadata = forms.CharField(validators=[validate_json], required=False)
        edit_users = forms.ModelMultipleChoiceField(User.objects.all(), required=False)
        edit_groups = forms.ModelMultipleChoiceField(Group.objects.all(), required=False)
        view_users = forms.ModelMultipleChoiceField(User.objects.all(), required=False)
        view_groups = forms.ModelMultipleChoiceField(Group.objects.all(), required=False)

    class GetResourceListForm(forms.Form):
        group = forms.ModelChoiceField(Group.objects.all(), required=False)
        user = forms.ModelChoiceField(User.objects.all(), required=False)
        from_date = forms.DateTimeField(required=False)
        to_date = forms.DateTimeField(required=False)
        start = forms.IntegerField(required=False)
        count = forms.IntegerField(required=False)
        keywords = forms.ModelMultipleChoiceField(Keyword)
        dc = forms.CharField(min_length=1, required=False, validators=[validate_json])
        full_text_search = forms.CharField(required=False)

    class CreateResourceForm(UpdateResourceForm):
        resource_type = forms.ChoiceField(
            choices=zip(
                [x.__name__ for x in hydroshare.get_resource_types()],
                [x.__name__ for x in hydroshare.get_resource_types()]
            ))

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ResourceCRUD, self).dispatch(request, *args, **kwargs)

    def get(self, _, pk=None):
        if pk:
            return self.get_resource(pk)
        else:
            return self.get_resource_list()

    def put(self, _, pk):
        return self.update_resource(pk)

    def post(self, _):
        return self.create_resource()

    def delete(self, _, pk):
        return self.delete_resource(pk)

    def get_resource(self, pk):
        authorize(self.request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
        
        bag_url = hydroshare.utils.current_site_url() + AbstractResource.bag_url(pk)
        return HttpResponseRedirect(bag_url)

    def update_resource(self, pk):
        authorize(self.request, pk, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

        params = utils.create_form(ResourceCRUD.UpdateResourceForm, self.request)
        if params.is_valid():
            r = params.cleaned_data
            res = hydroshare.update_resource(
                pk,
                edit_users=r['edit_users'],
                view_users=r['view_users'],
                edit_groups=r['edit_groups'],
                view_groups=r['view_groups'],
                keywords=r['keywords'],
                metadata=json.loads(r['dublin_metadata']) if r['dublin_metadata'] else {},
                **{k: v for k, v in self.request.REQUEST.items() if k not in r}
            )
            return HttpResponse(res.short_id, content_type='text/plain', status='204')
        else:
            raise exceptions.ValidationError(params.errors)

    def delete_resource(self, pk):
        authorize(self.request, pk, needed_permission=ACTION_TO_AUTHORIZE.DELETE_RESOURCE)

        hydroshare.delete_resource(pk)
        return HttpResponse(pk, content_type=None, status=204)

    def create_resource(self):
        if not get_user(self.request).is_authenticated():
            print self.request.user
            raise exceptions.PermissionDenied('user must be logged in.')

        params = utils.create_form(ResourceCRUD.CreateResourceForm, self.request)
        if params.is_valid():
            r = params.cleaned_data
            res = hydroshare.create_resource(
                resource_type=r['resource_type'],
                owner=self.request.user,
                title=r['title'],
                edit_users=r['edit_users'],
                view_users=r['view_users'],
                edit_groups=r['edit_groups'],
                view_groups=r['view_groups'],
                keywords=r['keywords'],
                metadata=json.loads(r['dublin_metadata']) if r['dublin_metadata'] else {},
                files=self.request.FILES.values(),
                **{k: v for k, v in self.request.REQUEST.items() if k not in r}
            )
            return HttpResponse(res.short_id, content_type='text/plain')
        else:
            raise exceptions.ValidationError(params.errors)

    def get_resource_list(self):
        params = utils.create_form(ResourceCRUD.GetResourceListForm, self.request)
        if params.is_valid():
            r = params.cleaned_data
            if r['dc']:
                r['dc'] = json.loads(r['dc'])
            else:
                r['dc'] = {}

            ret = []
            resource_table = hydroshare.get_resource_list(**r)
            originator = get_user(self.request)

            for resources in resource_table:
                for r in filter(lambda x: authorize(self.request, x.short_id,
                                                    needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE),
                                resources):
                    ret.append(r.short_id)

            return json_or_jsonp(self.request, ret)
        else:
            raise exceptions.ValidationError(params.errors)


class GetUpdateScienceMetadata(View):
    """
    Describes the resource identified by the pid by returning the associated science metadata object. If the resource
    does not exist, Exceptions.NotFound must be raised.

    REST URL:  GET /scimeta/{pid}

    Parameters:    pk  - Unique HydroShare identifier for the resource whose science metadata is to be retrieved.

    Returns:    Science metadata document describing the resource.

    Return Type:    ScienceMetadata

    Raises:    Exceptions.NotAuthorized -  The user is not authorized
    Exceptions.NotFound  - The resource identified by pid does not exist
    Exception.ServiceFailure  - The service is unable to process the request
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(GetUpdateScienceMetadata, self).dispatch(request, *args, **kwargs)

    def get(self, _, pk):
        return self.get_science_metadata(pk)

    def put(self, _, pk):
        return self.update_science_metadata(pk)

    def post(self, _, pk):
        return self.put(_, pk)

    def delete(self, _, pk):
        raise NotImplemented()

    def get_science_metadata(self, pk):
        authorize(self.request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_METADATA)

        res = hydroshare.get_science_metadata(pk)
        return json_or_jsonp(
            self.request, hydroshare.utils.serialize_science_metadata(res))

    def update_science_metadata(self, pk):
        authorize(self.request, pk, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

        params = utils.create_form(ResourceCRUD.UpdateResourceForm, self.request)
        if params.is_valid():
            r = params.cleaned_data
            res = hydroshare.update_resource(
                pk,
                edit_users=r['edit_users'],
                view_users=r['view_users'],
                edit_groups=r['edit_groups'],
                view_groups=r['view_groups'],
                keywords=r['keywords'],
                metadata=json.loads(r['dublin_metadata']) if r['dublin_metadata'] else {},
                files=self.request.FILES.values(),
                **{k: v for k, v in self.request.REQUEST.items() if k not in r}
            )
            return HttpResponse(res.short_id, content_type='text/plain')
        else:
            raise exceptions.ValidationError('invalid request')



class GetUpdateSystemMetadata(View):
    """
    Describes the resource identified by the pid by returning the associated system metadata object. If the resource
    does not exist, Exceptions.NotFound must be raised.

    REST URL:  GET /sysmeta/{pid}

    Parameters:    pk - Unique HydroShare identifier for the resource whose system metadata is to be retrieved.

    Returns:    System metadata document describing the resource.

    Return Type:    SystemMetadata

    Raises:
        Exceptions.NotAuthorized - The user is not authorized
        Exceptions.NotFound - The resource identified by pid does not exist
        Exception.ServiceFailure - The service is unable to process the request
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(GetUpdateSystemMetadata, self).dispatch(request, *args, **kwargs)

    def get(self, _, pk):
        return self.get_system_metadata(pk)

    def put(self, _, pk):
        return self.update_system_metadata(pk)

    def post(self, _, pk):
        return self.put(_, pk)

    def delete(self, _, pk):
        raise NotImplemented()

    def get_system_metadata(self, pk):
        authorize(self.request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_METADATA)

        res = hydroshare.get_science_metadata(pk)
        return json_or_jsonp(
            self.request, hydroshare.utils.serialize_system_metadata(res))

    def update_system_metadata(self, pk):
        authorize(self.request, pk, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

        params = utils.create_form(ResourceCRUD.UpdateResourceForm, self.request)
        if params.is_valid():
            r = params.cleaned_data
            res = hydroshare.update_resource(
                pk,
                edit_users = r['edit_users'],
                view_users = r['view_users'],
                edit_groups = r['edit_groups'],
                view_groups = r['view_groups'],
                keywords = r['keywords'],
                metadata=json.loads(r['dublin_metadata']) if r['dublin_metadata'] else {},
                files=self.request.FILES.values(),
                **{k: v for k, v in self.request.REQUEST.items() if k not in r}
            )
            return HttpResponse(res.short_id, content_type='text/plain')
        else:
            raise exceptions.ValidationError('invalid request')



class GetResourceMap(View):
    """
    Describes the resource identified by the pid by returning the associated resource map document. If the resource does
    not exist, Exceptions.NotFound must be raised.

    REST URL:  GET /resourcemap/{pid}

    Parameters:    pid - Unique HydroShare identifier for the resource whose resource map is to be retrieved.

    Returns:    Resource map document describing the resource.

    Return Type:    ResourceMap

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(GetResourceMap, self).dispatch(request, *args, **kwargs)

    def get(self, _, pk):
        return self.get_resource_map(pk)

    def put(self, _, pk):
        raise NotImplemented()

    def post(self, _, pk):
        raise NotImplemented()

    def delete(self, _, pk):
        raise NotImplemented()

    def get_resource_map(self, pk):
        authorize(self.request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)

        res = hydroshare.get_science_metadata(pk)
        return json_or_jsonp(
            self.request, hydroshare.utils.serialize_resource_map(res))


class GetCapabilities(View):
    """
    Describes API services exposed for a resource.  If there are extra capabilites for a particular resource type over
    and above the standard Hydroshare API, then this API call will list these

    REST URL: GET /capabilites/{pid}

    Parameters: Unique HydroShare identifier for the resource whose capabilites are to be retrieved.

    Return Type: Capabilites

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(GetCapabilities, self).dispatch(request, *args, **kwargs)

    def get(self, _, pk):
        return self.get_resource_map(pk)

    def put(self, _, pk):
        raise NotImplemented()

    def post(self, _, pk):
        raise NotImplemented()

    def delete(self, _, pk):
        raise NotImplemented()

    def get_resource_map(self, pk):
        authorize(self.request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)

        res = hydroshare.get_capabilities(pk)
        return json_or_jsonp(self.request, res)


class ResourceFileCRUD(View):
    """
    Called by clients to get an individual file within a HydroShare resource.

    REST URL:  GET /resource/{pid}/files/{filename}

    Parameters:
    pid - Unique HydroShare identifier for the resource from which the file will be extracted.
    filename - The data bytes of the file that will be extracted from the resource identified by pid

    Returns: The bytes of the file extracted from the resource

    Return Type:    pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified does not exist or the file identified by filename does not exist
    Exception.ServiceFailure - The service is unable to process the request
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ResourceFileCRUD, self).dispatch(request, *args, **kwargs)

    def get(self, _, pk, filename):
        return self.get_resource_file(pk, filename)

    def put(self, _, pk, filename):
        return self.update_resource_file(pk, filename)

    def post(self, _, pk, filename=None):
        return self.add_resource_file(pk, filename)

    def delete(self, _, pk, filename):
        return self.delete_resource_file(pk, filename)

    def get_resource_file(self, pk, filename):
        authorize(self.request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
        try:
            f = hydroshare.get_resource_file(pk, filename)
        except ObjectDoesNotExist:
            raise Http404
        return HttpResponseRedirect(f.url, content_type='text/plain')

    def update_resource_file(self, pk, filename):
        authorize(self.request, pk, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

        f = hydroshare.update_resource_file(pk, filename, self.request.FILES.values()[0])
        return HttpResponse(f.url, content_type='text/plain')

    def add_resource_file(self, pk, filename=None):
        authorize(self.request, pk, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

        if filename:
            rf = self.request.FILES.values()[0]
            rf.name = filename
            f = hydroshare.add_resource_files(pk, rf)
            return HttpResponse(f.url, content_type='text/plain')
        else:
            fs = hydroshare.add_resource_files(pk, self.request.FILES.values())
            return json_or_jsonp(self.request, { f.name: f.url for f in fs})

    def delete_resource_file(self, pk, filename):
        authorize(self.request, pk, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
        f = hydroshare.delete_resource_file(pk, filename)
        return HttpResponse(f, content_type='text/plain')


class GetRevisions(View):
    """
    Returns a list of pids for resources that are revisions of the resource identified by the specified pid.

    REST URL:  GET /revisions/{pid}

    Parameters:    pid - Unique HydroShare identifier for the resource whose revisions are to be retrieved.

    Returns: List of pids for resources that are revisions of the specified resource.

    Return Type: List of pids

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The Resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(GetRevisions, self).dispatch(request, *args, **kwargs)

    def get(self, _, pk):
        return self.get_revisions(pk)

    def put(self, _, pk):
        raise NotImplemented()

    def post(self, _, pk):
        raise NotImplemented()

    def delete(self, _, pk):
        raise NotImplemented()

    def get_revisions(self, pk):
        authorize(self.request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)

        js = {arrow.get(bag.timestamp).isoformat(): hydroshare.utils.current_site_url() + AbstractResource.bag_url(pk) for bag in hydroshare.get_revisions(pk) }
        return json_or_jsonp(self.request, js)


class GetRelated(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(GetRelated, self).dispatch(request, *args, **kwargs)

    def get(self, _, pk):
        raise NotImplemented()

    def put(self, _, pk):
        raise NotImplemented()

    def post(self, _, pk):
        raise NotImplemented()

    def delete(self, _, pk):
        raise NotImplemented()


class GetChecksum(View):   
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(GetChecksum, self).dispatch(request, *args, **kwargs)

    def get(self, _, pk):
        raise NotImplemented()

    def put(self, _, pk):
        raise NotImplemented()

    def post(self, _, pk):
        raise NotImplemented()

    def delete(self, _, pk):
        raise NotImplemented()


class PublishResource(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(PublishResource, self).dispatch(request, *args, **kwargs)

    def get(self, _, pk):
        raise NotImplemented()

    def put(self, _, pk):
        return self.publish_resource(pk)

    def post(self, _, pk):
        return self.put(_, pk)

    def delete(self, _, pk):
        raise NotImplemented()

    def publish_resource(self, pk):
        authorize(self.request, pk, needed_permission=ACTION_TO_AUTHORIZE.SET_RESOURCE_FLAG)

        hydroshare.publish_resource(pk)
        return HttpResponse(pk, content_type='text/plain')

class ResolveDOI(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ResolveDOI, self).dispatch(request, *args, **kwargs)

    def get(self, _, doi):
        return self.resolve_doi(doi)

    def put(self, _, doi):
        raise NotImplemented()

    def post(self, _, doi):
        raise NotImplemented()

    def delete(self, _, doi):
        raise NotImplemented()

    def resolve_doi(self, doi):
        return HttpResponse(hydroshare.resolve_doi(doi), content_type='text/plain')