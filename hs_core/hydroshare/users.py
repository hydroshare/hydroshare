import json

from django.core.exceptions import MultipleObjectsReturned
from django.contrib.auth.models import User, Group
from django.core import exceptions
from django.core import signing

from hs_core.models import GroupOwnership
from .utils import get_resource_by_shortkey, user_from_id, group_from_id, get_resource_types, get_profile


def set_resource_owner(pk, user):
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

    res = get_resource_by_shortkey(pk)
    res.owners = [user]
    res.save()
    return pk


DO_NOT_DISTRIBUTE = 'donotdistribute'
EDIT = 'edit'
VIEW = 'view'
PUBLIC = 'public'


def set_access_rules(pk, user=None, group=None, access=None, allow=False):
    """
    Set the access permissions for an object identified by pid. Triggers a change in the system metadata. Successful
    completion of this operation in indicated by a HTTP response of 200. Unsuccessful completion of this operation must
    be indicated by returning an appropriate exception such as NotAuthorized.

    REST URL:  PUT /resource/accessRules/{pid}/?principaltype=({userID}|{groupID})&principleID={id}&access=
        (edit|view|donotdistribute)&allow=(true|false)

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
    implicit unless prohibited by the Do not distribute attribute. The only permissions in HydroShare are View, Edit and
    Full.

    As-built notes:  TypeError was used as it's a built-in exception Django knows about.  it will result in a
    ServiceFailure if used over the web.

    Also, authorization is not handled in the server-side API.  Server-side API functions run "as root"

    access=public, allow=true will cause the resource to become publicly viewable.

    pid can be a resource instance instead of an identifier (for efficiency)
    """
    access = access.lower()
    if isinstance(pk, basestring):
        res = get_resource_by_shortkey(pk, or_404=False)
    else:
        res = pk  # user passed in the resource instance instead of hte primary key

    if access == DO_NOT_DISTRIBUTE:
        res.do_not_distribute = allow
        res.save()
    elif access == PUBLIC:
        res.public = allow
        res.save()
    elif access == EDIT:
        if user:
            if allow:
                if not res.edit_users.filter(pk=user.pk).exists():
                    res.edit_users.add(user)
            else:
                if res.edit_users.filter(pk=user.pk).exists():
                    res.edit_users.filter(pk=user.pk).delete()
        elif group:
            if allow:
                if not res.edit_groups.filter(pk=group.pk).exists():
                    res.edit_groups.add(group)
            else:
                if res.edit_groups.filter(pk=group.pk).exists():
                    res.edit_groups.filter(pk=group.pk).delete()
        else:
            raise TypeError('Tried to edit access permissions without specifying a user or group')
    elif access == VIEW:
        if user:
            if allow:
                if not res.view_users.filter(pk=user.pk).exists():
                    res.view_users.add(user)
            else:
                if res.view_users.filter(pk=user.pk).exists():
                    res.view_users.filter(pk=user.pk).delete()
        elif group:
            if allow:
                if not res.view_groups.filter(pk=group.pk).exists():
                    res.view_groups.add(group)
            else:
                if res.view_groups.filter(pk=group.pk).exists():
                    res.view_groups.filter(pk=group.pk).delete()
        else:
            raise TypeError('Tried to view access permissions without specifying a user or group')
    else:
        raise TypeError('access was none of {donotdistribute, public, edit, view}  ')

    return res


def create_account(
        email, username=None, first_name=None, last_name=None, superuser=None, groups=None, password=None, active=True
):
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

    """

    from tastypie.models import ApiKey
    from django.contrib.auth.models import User, Group
    from django.contrib.sites.models import Site
    from django.conf import settings

    username = username if username else email

    useirods = getattr(settings,'USE_IRODS', False)
    if useirods:
        from django_irods import account
        iaccount = account.IrodsAccount()
        iaccount.create(username)
        iaccount.setPassward(username, password)

    groups = groups if groups else []
    groups = Group.objects.in_bulk(*groups) if groups and isinstance(groups[0], int) else groups

    if superuser:
        u = User.objects.create_superuser(
            username,
            email,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
    else:
        u = User.objects.create_user(
            username, email,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )

    u.is_staff = False
    if not active:
        u.is_active=False
    u.save()

    u.groups = groups
    ApiKey.objects.get_or_create(user=u)

    try:
        token = signing.dumps('verify_user_email:{0}:{1}'.format(u.pk, u.email))
        u.email_user(
            'Please verify your new Hydroshare account.',
            """
This is an automated email from Hydroshare.org. If you requested a Hydroshare account, please
go to http://{domain}/verify/{token}/ and verify your account.
""".format(
            domain=Site.objects.get_current().domain,
            token=token
        ))
    except:
        pass # FIXME should log this instead of ignoring it.

    u.groups = groups


    return u


def update_account(user, **kwargs):
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

    """
    from django.contrib.auth.models import Group

    groups = kwargs.get('groups', [])
    if groups:
        if len(groups) == 1:
            groups = [(Group.objects.get_or_create(name=groups)
                      if isinstance(groups, basestring) else groups)[0]]
        else:
            groups = zip(
                *(Group.objects.get_or_create(name=g)
                  if isinstance(g, basestring) else g
                  for g in groups))[0]

    if 'password' in kwargs:
        user.set_password(kwargs['password'])

    blacklist = {'username', 'password', 'groups'}  # handled separately or cannot change
    for k in blacklist.intersection(kwargs.keys()):
        del kwargs[k]

    try:
        profile = get_profile(user)
        profile_update = dict()
        update_keys = filter(lambda x: hasattr(profile, str(x)), kwargs.keys())
        for key in update_keys:
            profile_update[key] = kwargs[key]
        for k, v in profile_update.items():
            setattr(profile, k, v)
        profile.save()
    except AttributeError as e:
        raise exceptions.ValidationError(e.message)  # ignore deprecated user profile module when we upgrade to 1.7

    user_update = dict()
    update_keys = filter(lambda x: hasattr(user, str(x)), kwargs.keys())
    for key in update_keys:
            user_update[key] = kwargs[key]
    for k, v in user_update.items():
        setattr(user, k, v)
    user.save()

    user.groups = groups
    return user.username




def get_user_info(user):
    """
    Get the information about a user identified by userID. This would be their profile information, groups they belong.

    REST URL:  GET /accounts/{userID}

    Parameters: userID - ID of the existing user to be modified

    Returns: An object containing the details for the user

    Return Type: user

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The user identified by userID does not exist
    Exception.ServiceFailure - The service is unable to process the request
    """
    from hs_core.api import UserResource

    ur = UserResource()
    ur_bundle = ur.build_bundle(obj=user)
    return json.loads(ur.serialize(None, ur.full_dehydrate(ur_bundle), 'application/json'))


def list_users(query=None, status=None, start=None, count=None):
    """
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

    """
    query = json.loads(query) if isinstance(query, basestring) else query

    qs = User.objects.filter(**query)
    qs = qs.filter(active=True) if status == 'active' else qs
    qs = qs.filter(is_staff=True) if status == 'staff' else qs
    if start and count:
        qs = qs[start:start+count]
    elif start:
        qs = qs[start:]
    elif count:
        qs = qs[:count]

    return qs


def list_groups(query=None, start=None, count=None):
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

    """
    query = json.loads(query) if isinstance(query, basestring) else query
    qs = Group.objects.filter(**query)
    if start and count:
        qs = qs[start:start+count]
    elif start:
        qs = qs[start:]
    elif count:
        qs = qs[:count]

    return qs


def create_group(name, members=None, owners=None):
    """
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
    g = Group.objects.create(name=name)


    if owners:
        owners = [user_from_id(owner) for owner in owners]

        GroupOwnership.objects.bulk_create([
            GroupOwnership(group=g, owner=owner) for owner in owners
        ])

    if members:
        members = [user_from_id(member) for member in members]

        for member in members:
            try:
                member.groups.add(g)
            except MultipleObjectsReturned:
                pass

    return g


def update_group(group, members=None, owners=None):
    """
    Modify details of group identified by groupID or add or remove members to/from the group. Group members can be
    modified only by an owner of the group, otherwise a NotAuthorized exception is thrown. Group members are provided as
    a list of users that replace the group membership.

    REST URL:  PUT /groups/{groupID}

    Parameters:
    groupID - groupID of the existing group to be modified
    group - An object containing the modified attributes of the group to be modified and the modified list of userIDs in
    the group membership

    Returns: The groupID of the group that was modified

    Return Type: groupID

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The group identified by groupID does not exist
    Exceptions.InvalidContent - The content of the group object is invalid
    Exception.ServiceFailure - The service is unable to process the request

    Note:  This would be done via a JSON object (group) that is in the PUT request.
    """

    if owners:
        GroupOwnership.objects.filter(group=group).delete()
        owners = [user_from_id(owner) for owner in owners]

        GroupOwnership.objects.bulk_create([
            GroupOwnership(group=group, owner=owner) for owner in owners
        ])

    if members:
        for u in User.objects.filter(groups=group):
            u.groups.remove(group)

        members = [user_from_id(member) for member in members]

        for member in members:
            try:
                member.groups.add(group)
            except MultipleObjectsReturned:
                pass


def list_group_members(name):
    """
    Get the information about a group identified by groupID. For a group this would be its description and membership
    list.

    REST URL:  GET /group/{groupID}

    Parameters: groupID - ID of the existing user to be modified

    Returns: An object containing the details for the group

    Return Type: group

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The group identified by groupID does not exist
    Exception.ServiceFailure - The service is unable to process the request
    """
    return User.objects.filter(groups=group_from_id(name))


def set_group_owner(group, user):
    """
    Adds ownership of the group identified by groupID to the user specified by userID. This can only be done by a group
    owner or HydroShare administrator.

    REST URL:  PUT /groups/{groupID}/owner/?user={userID}

    Parameters: groupID - groupID of the existing group to be modified

    userID - userID of the existing user to be set as the owner of the group

    Returns: The groupID of the group that was modified

    Return Type: groupID

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The group identified by groupID does not exist
    Exceptions.NotFound - The user identified by userID does not exist
    Exception.ServiceFailure - The service is unable to process the request
    """
    if not GroupOwnership.objects.filter(group=group, owner=user).exists():
        GroupOwnership.objects.create(group=group, owner=user)


def delete_group_owner(group, user):
    """
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
    GroupOwnership.objects.filter(group=group, owner=user).delete()


def get_resource_list(
        group=None, user=None, owner=None,
        from_date=None, to_date=None,
        start=None, count=None,
        keywords=None, dc=None,
        full_text_search=None,
        published=False,
        edit_permission=False,
        public=False
):
    """
    Return a list of pids for Resources that have been shared with a group identified by groupID.
    REST URL:  GET /resourceList?groups__contains={groupID}

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
    from django.db.models import Q

    if not any((group, user, owner, from_date, to_date, start, count, keywords, dc, full_text_search, public)):
        raise NotImplemented("Returning the full resource list is not supported.")

    resource_types = get_resource_types()
    queries = dict((el, []) for el in resource_types)

    for t, q in queries.items():
        if published:
            queries[t].append(Q(doi__isnull=False))

        if edit_permission:
            if group:
                group = group_from_id(group)
                queries[t].append(Q(edit_groups=group))

            if user:
                user = user_from_id(user)
                queries[t].append(Q(edit_users=user) | Q(owners=user))
        else:
            if group:
                group = group_from_id(group)
                queries[t].append(Q(edit_groups=group) | Q(view_groups=group))

            if user:
                user = user_from_id(user)
                if owner:
                    queries[t].append(Q(owners=user))
                else:
                    queries[t].append(Q(edit_users=user) | Q(view_users=user) | Q(owners=user) | Q(public=True))

        if from_date and to_date:
            queries[t].append(Q(updated__range=(from_date, to_date)))
        elif from_date:
            queries[t].append(Q(updated__ge=from_date))
        elif to_date:
            queries[t].append(Q(updated__le=to_date))

        #if keywords:
        #    queries[t].append(Q(keywords__title__in=keywords))

        #if dc:
        #    for lookup in dc:
        #        queries[t].append(Q(dublin_metadata__term=lookup['term']) & Q(dublin_metadata__content__contains=lookup['content']))

        flt = t.objects.all()
        for q in queries[t]:
            flt = flt.filter(q)

        if public:
            flt = flt.filter(public=True)

        if full_text_search:
            flt = flt.search(full_text_search)

        queries[t] = flt

        if keywords:
            for k in keywords:
                queries[t] = flt.filter(keywords_string__contains=k)

        if dc:
            for metadata in dc:
                if metadata['content']:
                    queries[t] = filter(lambda r: r.dublin_metadata.filter(term=metadata['term']).exists(), queries[t])
                    queries[t] = filter(lambda r: r.dublin_metadata.filter(content=metadata['content']).exists(), queries[t])
        qcnt = 0
        if queries[t]:
            qcnt = queries[t].__len__();

        if start is not None and count is not None:
            if qcnt>start:
                if(qcnt>=start+count):
                    queries[t] = queries[t][start:start+count]
                else:
                    queries[t] = queries[t][start:qcnt]
        elif start is not None:
            if qcnt>=start:
                queries[t] = queries[t][start:qcnt]
        elif count is not None:
            if qcnt>count:
                queries[t] = queries[t][0:count]

    return queries
