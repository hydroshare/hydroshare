import json
import logging

from django.core.exceptions import PermissionDenied, ObjectDoesNotExist, ValidationError
from django.contrib.auth.models import User, Group
from django.contrib.gis.geos import Polygon, Point
from django.core.files import File
from django.core.files.uploadedfile import UploadedFile
from django.core import exceptions
from django.db.models import Q

from hs_core.models import BaseResource, Contributor, Creator, Subject, Description, Title, \
    Coverage, Relation
from .utils import user_from_id, group_from_id, get_profile
from theme.models import UserQuota, UserProfile
from hs_dictionary.models import University, UncategorizedTerm

DO_NOT_DISTRIBUTE = 'donotdistribute'
EDIT = 'edit'
VIEW = 'view'
PUBLIC = 'public'

log = logging.getLogger(__name__)


def create_account(
        email, username=None, first_name=None, last_name=None, superuser=None, groups=None,
        password=None, active=True, organization=None, middle_name=None):
    """
    Create a new user within the HydroShare system.

    Returns: The user that was created

    """

    from django.contrib.auth.models import User, Group
    from hs_access_control.models import UserAccess
    from hs_labels.models import UserLabels

    try:
        user = User.objects.get(Q(username__iexact=username))
        raise ValidationError("User with provided username already exists.")
    except User.DoesNotExist:
        pass
    try:
        # we chose to follow current email practices with case insensitive emails
        user = User.objects.get(Q(email__iexact=email))
        raise ValidationError("User with provided email already exists.")
    except User.DoesNotExist:
        pass
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
        u.is_active = False
    u.save()

    u.groups = groups

    # make the user a member of the Hydroshare role group
    u.groups.add(Group.objects.get(name='Hydroshare Author'))

    user_access = UserAccess(user=u)
    user_access.save()
    user_labels = UserLabels(user=u)
    user_labels.save()
    user_profile = get_profile(u)

    if organization:
        user_profile.organization = organization
        user_profile.save()

        dict_items = organization.split(";")

        for dict_item in dict_items:
            # Update Dictionaries
            try:
                University.objects.get(name=dict_item)
            except ObjectDoesNotExist:
                new_term = UncategorizedTerm(name=dict_item)
                new_term.save()

    if middle_name:
        user_profile.middle_name = middle_name
        user_profile.save()

    # create default UserQuota object for the new user
    uq = UserQuota.objects.create(user=u)
    uq.save()
    return u


def update_account(user, **kwargs):
    """
    Update an existing user within the HydroShare system. The user calling this method must have
    write access to the account details.

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
            if k == 'picture':
                profile.picture = File(v) if not isinstance(v, UploadedFile) else v
            elif k == 'cv':
                profile.cv = File(v) if not isinstance(v, UploadedFile) else v
            else:
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

# Pabitra: This one seems to be not used anywhere. Can I delete it?
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


def set_group_active_status(user, group_id, status):
    """
    This sets the group active status to True or False
    :param user: User who wants to set this group status flag
    :param group_id: id of the group for which the active status to be set
    :param status: True or False
    :return:
    """
    group = group_from_id(group_id)
    if user.uaccess.can_change_group_flags(group):
        group.gaccess.active = status
        group.gaccess.save()
    else:
        raise PermissionDenied()


def get_discoverable_groups():
        """
        Get a list of all groups marked discoverable or public.

        :return: List of discoverable groups.

        A user can view owners and abstract for a discoverable group.
        Usage:
        ------
            # fetch information about each discoverable or public group
            groups = GroupAccess.get_discoverable_groups()
            for g in groups:
                owners = g.owners
                # abstract = g.abstract
                if g.public:
                    # expose group list
                    members = g.members.all()
                else:
                    members = [] # can't see them.
        """
        return Group.objects.filter(Q(gaccess__discoverable=True) | Q(gaccess__public=True))


def get_public_groups():
        """
        Get a list of all groups marked public.

        :return: List of public groups.

        All users can list the members of a public group.  Public implies discoverable but not vice-versa.
        Usage:
        ------
            # fetch information about each public group
            groups = GroupAccess.get_public_groups()
            for g in groups:
                owners = g.owners
                # abstract = g.abstract
                members = g.members.all()
                # now display member information
        """
        return Group.objects.filter(gaccess__public=True)


def get_resource_list(creator=None, group=None, user=None, owner=None, from_date=None,
                      to_date=None, start=None, count=None, full_text_search=None,
                      published=False, edit_permission=False, public=False,
                      type=None, author=None, contributor=None, subject=None, coverage_type=None,
                      north=None, south=None, east=None, west=None, include_obsolete=False):
    """
    Return a list of pids for Resources that have been shared with a group identified by groupID.

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

    We may want to modify this method to return more than just the pids for resources so that some
    metadata for the list of resources returned could be displayed without having to call
    HydroShare.getScienceMetadata() and HydroShare.GetSystemMetadata() for every resource in the returned list.

    Implementation notes:  For efficiency's sake, this returns a dictionary of query sets with one
    query set per defined resource type.  At a high level someone could run through this whole list,
    collate the results, and send it back as a single list, but on the server side we don't do this
    because it gets too expensive quickly.

    parameters:
        author = a list of User names or emails
        creator = a User or name
        group = Group or name
        user = User or name
        from_date = datetime object
        to_date = datetime object
        start = int
        count = int
        subject = list of subject
        type = list of resource type names, used for filtering
        coverage_type = geo parameter, one of box or point
        north = north coordinate
        west = west coordinate
        south = south coordinate
        east = east coordinate
    """

    if not any((author, creator, group, user, owner, from_date, to_date, start,
                count, subject, full_text_search, public, type)):
        raise NotImplemented("Returning the full resource list is not supported.")

    q = []

    if type:
        query = Q(resource_type=type[0])
        for t in type[1:]:
            query = query | Q(resource_type=t)
        q.append(query)

    if published:
        q.append(Q(doi__isnull=False))

    if author:
        authors = author.split(',')
        author_parties = (
            (Creator.objects.filter(email__in=authors) | Creator.objects.filter(name__in=authors))
        )

        q.append(Q(object_id__in=author_parties.values_list('object_id', flat=True)))

    if coverage_type in ('box', 'point'):
        if not north or not west or not south or not east: \
            raise ValueError("coverage queries must have north, west, south, and east params")

        coverages = set()
        search_polygon = Polygon.from_bbox((east,south,west,north))

        for coverage in Coverage.objects.filter(type="box"):
            coverage_polygon = Polygon.from_bbox((
                coverage.value.get('eastlimit', None),
                coverage.value.get('southlimit', None),
                coverage.value.get('westlimit', None),
                coverage.value.get('northlimit', None)
            ))

            if search_polygon.intersects(coverage_polygon):
                coverages.add(coverage.id)

        for coverage in Coverage.objects.filter(type="point"):
            try:
                coverage_shape = Point(
                    coverage.value.get('east', None),
                    coverage.value.get('north', None),
                )

                if search_polygon.intersects(coverage_shape):
                    coverages.add(coverage.id)
            except Exception as e:
                log.error("Coverage value invalid for coverage id %d" % coverage.id)

        coverage_hits = (Coverage.objects.filter(id__in=coverages))
        q.append(Q(object_id__in=coverage_hits.values_list('object_id', flat=True)))

    if contributor:
        contributor_parties = (
            (Contributor.objects.filter(email__in=contributor) | Contributor.objects.filter(name__in=contributor))
        )

        q.append(Q(object_id__in=contributor_parties.values_list('object_id', flat=True)))

    if edit_permission:
        if group:
            group = group_from_id(group)
            q.append(Q(short_id__in=group.gaccess.edit_resources.values_list('short_id',
                                                                             flat=True)))

        q = _filter_resources_for_user_and_owner(user=user, owner=owner, is_editable=True, query=q)

    else:
        if creator:
            creator = user_from_id(creator)
            q.append(Q(creator=creator))

        if group:
            group = group_from_id(group)
            q.append(Q(short_id__in=group.gaccess.view_resources.values_list('short_id',
                                                                             flat=True)))

        q = _filter_resources_for_user_and_owner(user=user, owner=owner, is_editable=False, query=q)

    if from_date and to_date:
        q.append(Q(created__range=(from_date, to_date)))
    elif from_date:
        q.append(Q(created__gte=from_date))
    elif to_date:
        q.append(Q(created__lte=to_date))

    if subject:
        subjects = subject.split(',')
        subjects = Subject.objects.filter(value__iregex=r'(' + '|'.join(subjects) + ')')
        q.append(Q(object_id__in=subjects.values_list('object_id', flat=True)))

    flt = BaseResource.objects.all()

    if not include_obsolete:
        flt = flt.exclude(object_id__in=Relation.objects.filter(
            type='isReplacedBy').values('object_id'))
    for q in q:
        flt = flt.filter(q)

        if full_text_search:
            desc_ids = Description.objects.filter(abstract__icontains=full_text_search).values_list('object_id', flat=True)
            title_ids = Title.objects.filter(value__icontains=full_text_search).values_list('object_id', flat=True)

            # Full text search must match within the title or abstract
            if desc_ids:
                flt = flt.filter(object_id__in=desc_ids)
            elif title_ids:
                flt = flt.filter(object_id__in=title_ids)
            else:
                # No matches on title or abstract, so treat as no results of search
                flt = flt.none()

    # TODO The below is legacy pagination... need to find out if anything is using it and delete
    qcnt = 0
    if flt:
        qcnt = len(flt)

    if start is not None and count is not None:
        if qcnt > start:
            if qcnt >= start + count:
                flt = flt[start:start+count]
            else:
                flt = flt[start:qcnt]
    elif start is not None:
        if qcnt >= start:
            flt = flt[start:qcnt]
    elif count is not None:
        if qcnt > count:
            flt = flt[0:count]

    return flt


def _filter_resources_for_user_and_owner(user, owner, is_editable, query):
    if user:
        user = user_from_id(user)
        if owner:
            try:
                owner = user_from_id(owner, raise404=False)
            except User.DoesNotExist:
                pass
            else:
                query.append(Q(pk__in=owner.uaccess.owned_resources))

                if user != owner:
                    if user.is_superuser:
                        # admin user sees all owned resources of owner (another user)
                        pass
                    else:
                        # if some non-admin authenticated user is asking for resources owned by another user then
                        # get other user's owned resources that are public or discoverable, or if requesting user
                        # has access to those private resources
                        query.append(Q(pk__in=user.uaccess.view_resources) | Q(raccess__public=True) |
                                     Q(raccess__discoverable=True))
        else:
            if user.is_superuser:
                # admin sees all resources
                pass
            elif is_editable:
                query.append(Q(pk__in=user.uaccess.edit_resources))
            else:
                query.append(Q(pk__in=user.uaccess.view_resources) | Q(raccess__public=True) |
                             Q(raccess__discoverable=True))
    else:
        query.append(Q(raccess__public=True) | Q(raccess__discoverable=True))

    return query
