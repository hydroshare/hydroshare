from __future__ import absolute_import

from django import forms
from django.contrib.auth.models import Group, User
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from mezzanine.generic.models import Keyword
from ga_resources.utils import get_user, json_or_jsonp
from hs_core import hydroshare
from hs_core.api import UserResource, GroupResource
from hs_core.hydroshare.utils import group_from_id, user_from_id
from hs_core.models import GroupOwnership
from hs_core.views import utils
from .utils import authorize, validate_json
from django.views.generic import View
from django.core import exceptions
from django.conf import settings


class SetAccessRules(View):
    """
    Set the access permissions for an object identified by pid. Triggers a change in the system metadata. Successful
    completion of this operation in indicated by a HTTP response of 200. Unsuccessful completion of this operation
    must be indicated by returning an appropriate exception such as NotAuthorized.

    REST URL:  PUT /resource/accessRules/{pid}/?principaltype=({userID}|
    {groupID})&principleID={id}&access=(edit|view|donotdistribute)&allow=(true|false)

    Parameters:
    pid - Unique HydroShare identifier for the resource to be modified
    principalType - The type of principal (user or group)
    principalID - Identifier for the user or group to be granted access
    access - Permission to be assigned to the resource for the principal
    allow - True for granting the permission, False to revoke

    Returns: The pid of the resource that was modified

    Return Type: pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exceptions.NotFound - The principal identified by principalID does not exist
    Exception.ServiceFailure - The service is unable to process the request

    Note:  Do not distribute is an attribute of the resource that is set by a user with Full permissions and only
    applies to users with Edit and View privileges. There is no share privilege in HydroShare. Share permission is
    implicit unless prohibited by the Do not distribute attribute. The only permissions in HydroShare are View, Edit
    and Full.

    As-built notes:  The API had no way to declare a resource publicly viewable, this has been added.
    access parameter can be 'public'.  Using allow=true, that will cause the resource to become publicly viewable

    """
    class SetAccessRulesForm(forms.Form):
        pid = forms.CharField(max_length=32, min_length=1)
        principalType = forms.ChoiceField(choices=(
            ('user', 'user'),
            ('group', 'group')
        ))
        principalID = forms.CharField(max_length=128, min_length=1)
        access = forms.ChoiceField(choices=(
            ('edit', 'edit'),
            ('view', 'view')
        ))
        allow = forms.BooleanField()

    class SetDoNotDistributeForm(forms.Form):
        pid = forms.CharField(max_length=32, min_length=1)
        access = forms.ChoiceField(choices=(
            ('donotdistribute', 'donotdistribute'),
            ('public', 'public')
        ))
        allow = forms.BooleanField()

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(SetAccessRules, self).dispatch(request, *args, **kwargs)

    def get(self, _, pk):
        raise NotImplemented()

    def post(self, _, pk):
        return self.put(_, pk)

    def put(self, _, pk):
        return self.set_access_rules(self.request, pk)

    def set_access_rules(self, request, pk):
        res, _, _ = authorize(request, pk, full=True, superuser=True)

        access_rules_form = utils.create_form(SetAccessRules.SetAccessRulesForm, request)
        if access_rules_form.is_valid():
            r = access_rules_form.cleaned_data

            # get the user or group by ID
            # try username first, then email address, then primary key
            if r['principalType'] == 'user':
                tgt = user_from_id(r['principalID'])
                ret = hydroshare.set_access_rules(user=tgt, pk=res, access=r['access'], allow=r['allow'])
            else:
                tgt = group_from_id(r['principalID'])
                ret = hydroshare.set_access_rules(group=tgt, pk=res, access=r['access'], allow=r['allow'])
        else:
            distribute_form = utils.create_form(SetAccessRules.SetDoNotDistributeForm, request)
            if distribute_form.is_valid():
                r = distribute_form.cleaned_data
                ret = hydroshare.set_access_rules(pk=res, access=r['access'], allow=r['allow'])
            else:
                return HttpResponseBadRequest('Invalid request')

        return HttpResponse(ret, content_type='text/plain')


class SetResourceOwner(View):
    """
    Changes ownership of the specified resource to the user specified by a userID.

    REST URL:  PUT /resource/owner/{pid}?user={userID}

    Parameters:
    pid - Unique HydroShare identifier for the resource to be modified
    userID - ID for the user to be set as an owner of the resource identified by pid

    Returns: The pid of the resource that was modified

    Return Type: pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request
    Note:  This can only be done by the resource owner or a HydroShare administrator.

    """
    class SetResourceOwnerForm(forms.Form):
        user = forms.CharField(min_length=1)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(SetResourceOwner, self).dispatch(request, *args, **kwargs)

    def get(self, _, pk):
        raise NotImplemented()

    def post(self, _, pk):
        return self.put(_, pk)

    def put(self, _, pk):
        return self.set_resource_owner(self.request, pk)

    def set_resource_owner(self, request, pk):
        res, _, _ = authorize(request, pk, full=True, superuser=True)
        params = utils.create_form(SetResourceOwner.SetResourceOwnerForm, self.request)
        if params.is_valid():
            r = params.cleaned_data
            tgt = user_from_id(r['user'])
            return HttpResponse(
                hydroshare.set_resource_owner(pk=res, user=tgt),
                content_type='text/plain',
                status='201'
            )
        else:
            raise exceptions.ValidationError("invalid input parameters")


class CreateOrListAccounts(View):
    """
    Create a new user within the HydroShare system.

    REST URL:  POST /accounts

    Parameters: user - An object containing the attributes of the user to be created

    Returns: The userID of the user that was created

    Return Type: userID

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.InvalidContent - The content of the user object is invalid
    Exception.ServiceFailure - The service is unable to process the request

    Note:  This would be done via a JSON object (user) that is in the POST request. Should set a random password, and
    then send an email to make them verify the account. Unverified accounts can't log-in and are automatically deleted
    after a specified time (according to policy).

    ---

    List the users that match search criteria.

    REST URL:  GET /accounts?query={query}[&status={status}&start={start}&count={count}]

    Parameters:
    query - a string specifying the query to perform
    status - (optional) parameter to filter users returned based on status
    start=0 -  (optional) the zero-based index of the first value, relative to the first record of the resultset that
        matches the parameters
    count=100 - (optional) the maximum number of results that should be returned in the response

    Returns: An object containing a list of userIDs that match the query. If none match, an empty list is returned.

    Return Type: userList

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exception.ServiceFailure - The service is unable to process the request

    ### Implementation Notes

    param names are:
        - username
        - first_name
        - last_name
        - email
        - superuser
        - password
        - groups

    Expected POST content is a form response, not a JSON object.  We allow passwords to be set, but accounts must be
    verified before they are considered active.  If username is not specified, it defaults to email address. To create
    an active user and bypass verification, the creator must him or herself be authorized as a superuser. All other
    users must be verified before they are able to login.
    """

    class CreateAccountForm(forms.Form):
        username = forms.CharField(max_length=255, min_length=1)
        first_name = forms.CharField(max_length=255, min_length=1, required=False)
        last_name = forms.CharField(max_length=255, min_length=1, required=False)
        email = forms.CharField(max_length=255, min_length=1)
        superuser = forms.BooleanField(required=False)
        password = forms.CharField(required=False)
        groups = forms.ModelMultipleChoiceField(Group.objects.all(), required=False)

    class ListUsersForm(forms.Form):
        query = forms.CharField(min_length=2, validators=[validate_json], required=False)
        status = forms.ChoiceField(required=False, choices=(
            ('staff', 'staff'),
            ('active', 'active'),
        ))
        start = forms.IntegerField(required=False)
        count = forms.IntegerField(required=False)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(CreateOrListAccounts, self).dispatch(request, *args, **kwargs)

    def get(self, _):
        return self.list_users()

    def post(self, _):
        return self.put(_)

    def put(self, _):
        return self.create_account()

    def create_account(self):
        if not get_user(self.request).is_superuser:
            if settings.DEBUG or ("hydroshare.org" in self.request.META.get('HTTP_REFERER', '')): # fixme insecure vs spoofed header
                active=False
            else:
                raise exceptions.PermissionDenied("user must be superuser to create an account")
        else:
            active=True

        params = utils.create_form(CreateOrListAccounts.CreateAccountForm, self.request)
        if params.is_valid():
            r = params.cleaned_data
            ret = hydroshare.create_account(
                email=r['email'],
                username=r['username'],
                first_name=r['first_name'],
                last_name=r['last_name'],
                superuser=r['superuser'],
                password=r['password'],
                groups=r['groups'],
                active=active
            )

            return HttpResponse(ret, content_type='text/plain')

    def list_users(self):
        params = utils.create_form(CreateOrListAccounts.ListUsersForm, self.request)
        if params.is_valid():
            r = params.cleaned_data
            res = UserResource()
            bundles = []
            for u in hydroshare.list_users(r['query'], r['status'], r['start'], r['count']):
                bundle = res.build_bundle(obj=u, request=self.request)
                bundles.append(res.full_dehydrate(bundle, for_list=True))
            list_json = res.serialize(None, bundles, "application/json")

            return json_or_jsonp(self.request, list_json)
        else:
            raise exceptions.ValidationError('invalid request')


class UpdateAccountOrUserInfo(View):
    """
    Update an existing user within the HydroShare system. The user calling this method must have write access to the
    account details.

    REST URL:  PUT /accounts/{userID}

    Parameters: userID - ID of the existing user to be modified

    user - An object containing the modified attributes of the user to be modified

    Returns: The userID of the user that was modified

    Return Type: userID

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The user identified by userID does not exist
    Exceptions.InvalidContent - The content of the user object is invalid
    Exception.ServiceFailure - The service is unable to process the request

    Note:  This would be done via a JSON object (user) that is in the PUT request.

    ---

    Get the information about a user identified by userID. This would be their profile information, groups they belong.

    REST URL:  GET /accounts/{userID}

    Parameters: userID - ID of the existing user to be modified

    Returns: An object containing the details for the user

    Return Type: user

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The user identified by userID does not exist
    Exception.ServiceFailure - The service is unable to process the request

    As Built Notes:
    The GET method returns the results of a Tastypie serialization of a user. See api.py for more details.
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(UpdateAccountOrUserInfo, self).dispatch(request, *args, **kwargs)

    def get(self, _, pk):
        return self.get_user_info(pk)

    def post(self, _, pk):
        return self.put(pk)

    def put(self, _, pk):
        return self.update_account(pk)

    def get_user_info(self, pk):
        return json_or_jsonp(self.request, hydroshare.get_user_info(pk))

    def update_account(self, pk):
        user = get_user(pk)

        originator = get_user(self.request)
        if not originator.is_superuser or originator.pk == user.pk:
            raise exceptions.PermissionDenied("user must be superuser to change an account other than their own")

        kwargs = json.loads(self.request.REQUEST.get('user', self.request.body))
        hydroshare.update_account(user, **kwargs)
        return HttpResponse(pk, content_type='text/plain')


class CreateOrListGroups(View):
    """
    List the groups that match search criteria.

    REST URL:  GET /groups?query={query}[&status={status}&start={start}&count={count}]

    Parameters:
    query - a string specifying the query to perform
    start=0 - (optional) the zero-based index of the first value, relative to the first record of the resultset that
        matches the parameters
    count=100 - (optional) the maximum number of results that should be returned in the response

    Returns: An object containing a list of groupIDs that match the query. If none match, an empty list is returned.

    Return Type: groupList

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exception.ServiceFailure - The service is unable to process the request

    implementation notes: status parameter is unused.  unsure of group status.

    ---

    Create a group within HydroShare. Groups are lists of users that allow all members of the group to be referenced by
    listing solely the name of the group. Group names must be unique within HydroShare. Groups can only be modified by
    users listed as group owners.

    REST URL:  POST /groups

    Parameters: group - An object containing the attributes of the group to be created

    Returns: The groupID of the group that was created
    Return Type: groupID

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.InvalidContent - The content of the group object is invalid
    Exceptions.GroupNameNotUnique - The name of the group already exists in HydroShare
    Exception.ServiceFailure - The service is unable to process the request

    Note:  This would be done via a JSON object (group) that is in the POST request. May want to add an email
    verification step to avoid automated creation of fake groups. The creating user would automatically be set as the
    owner of the created group.

    """

    class ListGroupsForm(forms.Form):
        query = forms.CharField(min_length=2, validators=[validate_json], required=False)
        start = forms.IntegerField(required=False)
        count = forms.IntegerField(required=False)

    class CreateGroupForm(forms.Form):
        name = forms.CharField(min_length=1, required=True)
        members = forms.ModelMultipleChoiceField(queryset=User.objects.all(), required=False)
        owners = forms.ModelMultipleChoiceField(queryset=User.objects.all(), required=False)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(CreateOrListGroups, self).dispatch(request, *args, **kwargs)

    def get(self, _):
        return self.list_groups()

    def post(self, _):
        return self.put(_)

    def put(self, _):
        return self.create_group()

    def create_group(self):
        creator = get_user(self.request)
        if not get_user(self.request).is_authenticated():
            raise exceptions.PermissionDenied("user must be authenticated to create a group.")

        params = utils.create_form(CreateOrListGroups.CreateGroupForm, self.request)
        if params.is_valid():
            r = params.cleaned_data
            r['owners'] = set(r['owners']) if r['owners'] else set()
            r['owners'].add(creator)

            g = hydroshare.create_group(**r)
            return HttpResponse(g.name, content_type='text/plain', status='201')
        else:
            raise exceptions.ValidationError('invalid request')

    def list_groups(self):
        params = utils.create_form(CreateOrListGroups.ListGroupsForm, self.request)
        if params.is_valid():
            r = params.cleaned_data
            res = GroupResource()
            bundles = []
            for g in hydroshare.list_groups(r['query'], r['start'], r['count']):
                bundle = res.build_bundle(obj=g, request=self.request)
                bundles.append(res.full_dehydrate(bundle, for_list=True))
            list_json = res.serialize(None, bundles, "application/json")

            return json_or_jsonp(self.request, list_json)
        else:
            raise exceptions.ValidationError('invalid request')


class ListGroupMembers(View):
    """
    Get the information about a group identified by groupID. For a group this would be its description and membership
    list.

    REST URL:  GET /groups/{groupID}

    Parameters: groupID - ID of the existing user to be modified

    Returns: An object containing the details for the group

    Return Type: group

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The group identified by groupID does not exist
    Exception.ServiceFailure - The service is unable to process the request
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ListGroupMembers, self).dispatch(request, *args, **kwargs)

    def get(self, _, pk):
        return self.list_group_members(pk)

    def list_group_members(self, pk):
        res = UserResource()
        bundles = []
        for u in hydroshare.list_group_members(pk):
            bundle = res.build_bundle(obj=u, request=self.request)
            bundles.append(res.full_dehydrate(bundle, for_list=True))
        list_json = res.serialize(None, bundles, "application/json")

        return json_or_jsonp(self.request, list_json)


class SetOrDeleteGroupOwner(View):
    """
    Adds ownership of the group identified by groupID to the user specified by userID. This can only be done by a group
    owner or HydroShare administrator.

    REST URL:  PUT /groups/{groupID}/owner/{userID}

    Parameters: groupID - groupID of the existing group to be modified

    userID - userID of the existing user to be set as the owner of the group

    Returns: The groupID of the group that was modified

    Return Type: groupID

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The group identified by groupID does not exist
    Exceptions.NotFound - The user identified by userID does not exist
    Exception.ServiceFailure - The service is unable to process the request

    ---

    Removes a group owner identified by a userID from a group specified by groupID. This can only be done by a group
    owner or HydroShare administrator.

    REST URL:  DELETE /groups/{groupID}/owner/?user={userID}

    Parameters: groupID - groupID of the existing group to be modified

    userID - userID of the existing user to be removed as the owner of the group

    Returns: The groupID of the group that was modified

    Return Type: groupID

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The group identified by groupID does not exist
    Exceptions.NotFound - The user identified by userID does not exist
    Exceptions.InvalidRequest - The request would result in removal of the last remaining owner of the group
    Exception.ServiceFailure - The service is unable to process the request

    Note:  A group must have at least one owner.
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(SetOrDeleteGroupOwner, self).dispatch(request, *args, **kwargs)

    def get(self, _):
        raise NotImplemented()

    def post(self, _, g, u):
        return self.put(_, g, u)

    def put(self, _, g, u):
        return self.set_group_owner(g, u)

    def delete(self, _, g, u):
        return self.delete_group_owner(g, u)

    def delete_group_owner(self, g, u):
        originator = get_user(self.request)
        g = group_from_id(g)

        if not GroupOwnership.objects.filter(group=g, user=originator).exists():
            raise exceptions.PermissionDenied("user must be a group owner to change group ownership.")
        else:
            hydroshare.delete_group_owner(g, u)
            return HttpResponse(g.name, content_type='text/plain', status='204')

    def set_group_owner(self, g, u):
        originator = get_user(self.request)
        g = group_from_id(g)

        if not GroupOwnership.objects.filter(group=g, user=originator).exists():
            raise exceptions.PermissionDenied("user must be a group owner to change group ownership.")
        else:
            hydroshare.set_group_owner(g, u)
            return HttpResponse(g.name, content_type='text/plain', status='204')


class GetResourceList(View):
    """
    Return a list of pids for Resources that have been defined by a query.
    REST URL:  GET /resources?groups__contains={groupID}

    Parameters:
    queryType - string specifying the type of query being performed
    groupID - groupID of the group whose list of shared resources is to be returned

    Returns: A list of pids for resources that have been shared with the group identified by groupID.  If no resources
    have been shared with a group, an empty list is returned.

    Return Type: resourceList

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The group identified by groupID does not exist
    Exception.ServiceFailure - The service is unable to process the request

    Note:  See http://django-tastypie.readthedocs.org/en/latest/resources.html#basic-filtering for implementation
    details and example. We may want to modify this method to return more than just the pids for resources so that some
    metadata for the list of resources returned could be displayed without having to call
    HydroShare.getScienceMetadata() and HydroShare.GetSystemMetadata() for every resource in the returned list.

    Implementation notes:  For efficiency's sake, this returns a dictionary of query sets with one
    query set per defined resource type.  At a high level someone could run through this whole list,
    collate the results, and send it back as a single list, but on the server side we don't do this
    because it gets too expensive quickly.

    parameters:
        group = Group or name
        user = User or name
        from_date = datetime object
        to_date = datetime object
        start = int
        count = int
        keywords = list of keywords
        dc = list of lookups which are dicts following the following specifications:
            { term : dublin core term short name
              qualifier : dublin core term qualifier
              content : content of the dublin core term ("content" can be suffixed by django-style field lookups like
                content__startswith, etc
            }
    """


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

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(GetResourceList, self).dispatch(request, *args, **kwargs)

    def get(self, _):
        return self.get_resource_list()

    def get_resource_list(self):
        params = utils.create_form(GetResourceList.GetResourceListForm, self.request)
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
                for r in filter(lambda x:
                                x.public or
                                x.view_users.filter(pk=originator.pk).exists() or
                                x.view_groups.filter(pk__in=[g.pk for g in originator.groups.all()]), resources):
                    ret.append(r.short_id)

            return json_or_jsonp(self.request, ret)
        else:
            raise exceptions.ValidationError('invalid request')
