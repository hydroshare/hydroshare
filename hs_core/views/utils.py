import errno
import json
import logging
import os
import shutil
import string
from collections import namedtuple
from datetime import datetime
from tempfile import NamedTemporaryFile
from urllib import parse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

import paramiko
from dateutil import parser
from django.apps import apps
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import (ObjectDoesNotExist, PermissionDenied,
                                    SuspiciousFileOperation)
from django.core.files.base import File
from django.core.validators import URLValidator
from django.db.models import BooleanField, Case, Prefetch, Value, When
from django.db.models.query import prefetch_related_objects
from django.http import HttpResponse, QueryDict
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import int_to_base36, urlsafe_base64_encode
from mezzanine.conf import settings
from mezzanine.utils.email import send_mail_template, subject_template
from mezzanine.utils.urls import next_url
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError

from django_s3.exceptions import SessionException
from hs_access_control.models import PrivilegeCodes
from hs_core import hydroshare
from hs_core.enums import RelationTypes
from hs_core.hydroshare import (add_resource_files, check_resource_type,
                                delete_resource_file,
                                validate_resource_file_size)
from hs_core.hydroshare.utils import (QuotaException, check_aggregations,
                                      get_file_mime_type, validate_user_quota)
from hs_core.models import (AbstractMetaDataElement, BaseResource,
                            CoreMetaData, Relation, ResourceFile, get_user)
from hs_core.signals import (post_delete_file_from_resource,
                             pre_metadata_element_create)
from hs_core.tasks import FileOverrideException, create_temp_zip
from hs_file_types.utils import set_logical_file_type
from theme.backends import without_login_date_token_generator

ActionToAuthorize = namedtuple('ActionToAuthorize',
                               'VIEW_METADATA, '
                               'VIEW_RESOURCE, '
                               'EDIT_RESOURCE, '
                               'SET_RESOURCE_FLAG, '
                               'DELETE_RESOURCE, '
                               'CREATE_RESOURCE_VERSION, '
                               'VIEW_RESOURCE_ACCESS, '
                               'EDIT_RESOURCE_ACCESS')
ACTION_TO_AUTHORIZE = ActionToAuthorize(0, 1, 2, 3, 4, 5, 6, 7)
logger = logging.getLogger(__name__)


def json_or_jsonp(r, i, code=200):
    if not isinstance(i, str):
        i = json.dumps(i)

    if 'callback' in r:
        return HttpResponse('{c}({i})'.format(c=r['callback'], i=i),
                            content_type='text/javascript')
    elif 'jsonp' in r:
        return HttpResponse('{c}({i})'.format(c=r['jsonp'], i=i),
                            content_type='text/javascript')
    else:
        return HttpResponse(i, content_type='application/json', status=code)


def validate_url(url):
    """
    Validate URL
    :param url: input url to be validated
    :return: [True, ''] if url is valid,[False, 'error message'] if url is not valid
    """
    # validate url's syntax is valid
    error_message = "The URL that you entered is not valid. Please enter a valid http, https, " \
                    "ftp, or ftps URL."
    try:
        validator = URLValidator(schemes=('http', 'https', 'ftp', 'ftps'))
        validator(url)
    except ValidationError:
        return False, error_message

    # validate url is valid, i.e., can be opened
    try:
        # have to add a User-Agent header and pass in a Request to urlopen to test
        # whether a url can be resolved since some valid website URLs block web
        # spiders/bots, which raises a 403 Forbidden HTTPError
        url_req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        urlopen(url_req)
    except (HTTPError, URLError):
        return False, error_message

    return True, ''


def add_url_file_to_resource(res_id, ref_url, ref_file_name, curr_path):
    """
    Create URL file and add it to resource
    :param res_id: resource id to add url file to
    :param ref_url: referenced url to create the url file
    :param ref_file_name: referenced url file name to be created
    :param curr_path: the folder path in the resource to add url file to
    :return: file object being added into resource if successful, otherwise, return None
    """
    # create URL file
    urltempfile = NamedTemporaryFile()
    urlstring = '[InternetShortcut]\nURL=' + ref_url + '\n'
    urltempfile.write(urlstring.encode())
    urltempfile.flush()  # Make sure all data is written to the file

    # validate file size before adding file to resource
    file_size = os.path.getsize(urltempfile.name)
    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    validate_user_quota(resource.quota_holder, file_size)

    fileobj = File(file=urltempfile, name=ref_file_name)

    filelist = add_resource_files(res_id, fileobj, folder=curr_path)

    if filelist:
        return filelist[0]
    else:
        return None


def add_reference_url_to_resource(user, res_id, ref_url, ref_name, curr_path,
                                  validate_url_flag=True):
    """
    Add a reference URL to a composite resource if URL is valid, otherwise, return error message
    :param user: requesting user
    :param res_id: resource uuid
    :param ref_url: reference url to be added to the resource
    :param ref_name: file name of the referenced url in internet shortcut format
    :param curr_path: the folder path in the resource to add the referenced url to
    :param validate_url_flag: optional with default being True, indicating whether url validation
    needs to be performed or not
    :return: 200 status code, 'success' message, and file_id if it succeeds, otherwise,
    return error status code, error message, and None (for file_id).
    """
    # replace space with underline char
    ref_name = ref_name.strip().lower().replace(' ', '_')
    # strip out non-standard chars from ref_name
    valid_chars_in_file_name = '-_.{}{}'.format(string.ascii_letters, string.digits)
    ref_name = ''.join(c for c in ref_name if c in valid_chars_in_file_name)

    if not ref_name.endswith('.url'):
        ref_name += '.url'

    if validate_url_flag:
        is_valid, err_msg = validate_url(ref_url)
        if not is_valid:
            return status.HTTP_400_BAD_REQUEST, err_msg, None

    res = hydroshare.utils.get_resource_by_shortkey(res_id)
    if res.raccess.published and not user.is_superuser:
        err_msg = "Only admin can add file to a published resource"
        return status.HTTP_400_BAD_REQUEST, err_msg, None
    try:
        f = add_url_file_to_resource(res_id, ref_url, ref_name, curr_path)
        if not f:
            return status.HTTP_500_INTERNAL_SERVER_ERROR, 'New url file failed to be added to the ' \
                                                          'resource', None
    except QuotaException as ex:
        return status.HTTP_400_BAD_REQUEST, str(ex), None

    # make sure the new file has logical file set and is single file aggregation
    try:
        # set 'SingleFile' logical file type to this .url file
        res = hydroshare.utils.get_resource_by_shortkey(res_id)
        set_logical_file_type(res, user, f.id, 'SingleFile', extra_data={'url': ref_url})
        hydroshare.utils.resource_modified(res, user, overwrite_bag=False)
    except Exception as ex:
        return status.HTTP_500_INTERNAL_SERVER_ERROR, str(ex), None

    return status.HTTP_200_OK, 'success', f.id


def edit_reference_url_in_resource(user, res, new_ref_url, curr_path, url_filename,
                                   validate_url_flag=True):
    """
    edit the referenced url in an url file
    :param user: requesting user
    :param res: resource object that includes the url file
    :param new_ref_url: new url to replace the old url
    :param curr_path: the folder path of the url file in the resource
    :param url_filename: the url file name in the resource
    :return: 200 status code and 'success' message if it succeeds, otherwise, return error status
    code and error message
    """
    if res.raccess.published and not user.is_superuser:
        return status.HTTP_400_BAD_REQUEST, "url file can be edited by admin only for a published resource"

    ref_name = url_filename.lower()
    if not ref_name.endswith('.url'):
        return status.HTTP_400_BAD_REQUEST, 'url_filename in the request must have .url extension'

    if validate_url_flag:
        is_valid, err_msg = validate_url(new_ref_url)
        if not is_valid:
            return status.HTTP_400_BAD_REQUEST, err_msg

    istorage = res.get_s3_storage()
    # temp path to hold updated url file to be written to S3
    temp_path = istorage.getUniqueTmpPath

    prefix_path = 'data/contents'
    if curr_path == prefix_path:
        folder = ''
    elif curr_path.startswith(prefix_path):
        folder = curr_path[len(prefix_path) + 1:]
    else:
        folder = curr_path

    # update url in extra_data in url file's logical file object
    try:
        f = ResourceFile.get(resource=res, file=url_filename, folder=folder)
    except ObjectDoesNotExist as ex:
        return status.HTTP_500_INTERNAL_SERVER_ERROR, str(ex)
    extra_data = f.logical_file.extra_data
    extra_data['url'] = new_ref_url
    f.logical_file.extra_data = extra_data
    f.logical_file.save()

    try:
        os.makedirs(temp_path)
    except OSError as ex:
        if ex.errno == errno.EEXIST:
            shutil.rmtree(temp_path)
            os.makedirs(temp_path)
        else:
            return status.HTTP_500_INTERNAL_SERVER_ERROR, str(ex)

    # update url file in S3
    urlstring = '[InternetShortcut]\nURL=' + new_ref_url + '\n'
    from_file_name = os.path.join(temp_path, ref_name)
    with open(from_file_name, 'w') as out:
        out.write(urlstring)
    target_s3_file_path = os.path.join(res.root_path, curr_path, ref_name)
    try:
        istorage.saveFile(from_file_name, target_s3_file_path)
        shutil.rmtree(temp_path)
        hydroshare.utils.resource_modified(res, user, overwrite_bag=False)
    except SessionException as ex:
        shutil.rmtree(temp_path)
        return status.HTTP_500_INTERNAL_SERVER_ERROR, ex.stderr

    return status.HTTP_200_OK, 'success'


def run_ssh_command(host, uname, exec_cmd, pwd=None, private_key_file=None):
    """
    run ssh client to ssh to a remote host and run a command on the remote host
    Args:
        host: remote host name to ssh to
        uname: the username on the remote host to ssh to
        pwd: the password of the user on the remote host to ssh to
        exec_cmd: the command to be executed on the remote host via ssh

    Returns:
        None, but raises SSHException from paramiko if there is any error during ssh
        connection and command execution
    """
    if not private_key_file and not pwd:
        raise ValueError("Either Password or .pem is required for ssh connection")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if private_key_file:
        key = paramiko.Ed25519Key.from_private_key_file(private_key_file)
        ssh.connect(host, username=uname, pkey=key)
    else:
        ssh.connect(host, username=uname, password=pwd)

    transport = ssh.get_transport()
    session = transport.open_session()
    session.set_combine_stderr(True)
    session.get_pty()
    session.exec_command(exec_cmd)
    stdin = session.makefile('wb', -1)
    stdout = session.makefile('r', -1)
    stdin.write("{cmd}\n".format(cmd=pwd))
    stdin.flush()
    output = stdout.readlines()
    if output:
        logger.debug(output)
    return output


def rights_allows_copy(res, user):
    """
    Check whether resource copy is permitted or not by checking ownership and rights statement
    :param res: resource object to check for whether copy is allowed
    :param user: the requesting user to check for whether copy is allowed
    :return: return True if the resource can be copied; otherwise, return False
    """
    if not user.is_authenticated:
        return False

    if user.uaccess.owns_resource(res):
        return True

    rights = res.metadata.rights
    if (rights.statement == "This resource is shared under the Creative "
                            "Commons Attribution-NoDerivs CC BY-ND."
        or rights.statement == "This resource is shared under the Creative "
                               "Commons Attribution-NoCommercial-NoDerivs "
                               "CC BY-NC-ND."):
        return False

    return True


def authorize(request, res_id, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE, raises_exception=True):
    """
    This function checks if a user has authorization for resource related actions as outlined
    below. This function doesn't check authorization for user sharing resource with another user.

    How this function should be called for different actions on a resource by a specific user?
    1. User wants to view a resource (both metadata and content files) which includes
       downloading resource bag or resource content files:
       authorize(request, res_id=id_of_resource,
       needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
    2. User wants to view resource metadata only:
       authorize(request, res_id=id_of_resource,
       needed_permission=ACTION_TO_AUTHORIZE.VIEW_METADATA)
    3. User wants to edit a resource which includes:
       a. edit metadata
       b. add file to resource
       c. delete a file from the resource
       authorize(request, res_id=id_of_resource,
       needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    4. User wants to set resource flag (public, published, shareable etc):
       authorize(request, res_id=id_of_resource,
       needed_permission=ACTION_TO_AUTHORIZE.SET_RESOURCE_FLAG)
    5. User wants to delete a resource:
       authorize(request, res_id=id_of_resource,
       needed_permission=ACTION_TO_AUTHORIZE.DELETE_RESOURCE)
    6. User wants to create new version of a resource:
       authorize(request, res_id=id_of_resource,
       needed_permission=ACTION_TO_AUTHORIZE.CREATE_RESOURCE_VERSION)

    Note: resource 'shareable' status has no effect on authorization
    """
    authorized = False
    user = get_user(request)
    if isinstance(res_id, str):
        try:
            res = hydroshare.utils.get_resource_by_shortkey(res_id, or_404=False)
        except ObjectDoesNotExist:
            raise NotFound(detail="No resource was found for resource id:%s" % res_id)
    else:
        res = res_id

    if needed_permission == ACTION_TO_AUTHORIZE.VIEW_METADATA:
        if res.raccess.discoverable or res.raccess.public or res.raccess.allow_private_sharing:
            authorized = True
        elif user.is_authenticated and user.is_active:
            authorized = user.uaccess.can_view_resource(res)
    elif user.is_authenticated and user.is_active:
        if needed_permission == ACTION_TO_AUTHORIZE.VIEW_RESOURCE:
            authorized = user.uaccess.can_view_resource(res)
        elif needed_permission == ACTION_TO_AUTHORIZE.EDIT_RESOURCE:
            authorized = user.uaccess.can_change_resource(res)
        elif needed_permission == ACTION_TO_AUTHORIZE.DELETE_RESOURCE:
            authorized = user.uaccess.can_delete_resource(res)
        elif needed_permission == ACTION_TO_AUTHORIZE.SET_RESOURCE_FLAG:
            authorized = user.uaccess.can_change_resource_flags(res)
        elif needed_permission == ACTION_TO_AUTHORIZE.CREATE_RESOURCE_VERSION:
            authorized = user.uaccess.owns_resource(res)
        elif needed_permission == ACTION_TO_AUTHORIZE.VIEW_RESOURCE_ACCESS:
            authorized = user.uaccess.can_view_resource(res)
        elif needed_permission == ACTION_TO_AUTHORIZE.EDIT_RESOURCE_ACCESS:
            authorized = user.uaccess.can_share_resource(res, PrivilegeCodes.CHANGE)
    elif needed_permission == ACTION_TO_AUTHORIZE.VIEW_RESOURCE:
        authorized = res.raccess.public or res.raccess.allow_private_sharing

    if raises_exception and not authorized:
        raise PermissionDenied
    else:
        return res, authorized, user


def validate_json(js):
    try:
        json.loads(js)
    except ValueError:
        raise ValidationError(detail='Invalid JSON')


def validate_user(user_identifier):
    if not User.objects.filter(username=user_identifier).exists():
        if not User.objects.filter(email=user_identifier).exists():
            raise ValidationError(detail='No user found for user identifier:%s' % user_identifier)


def validate_group(group_identifier):
    if not Group.objects.filter(name=group_identifier).exists():
        try:
            g_id = int(group_identifier)
            if not Group.objects.filter(pk=g_id).exists():
                raise ValidationError(
                    detail='No group found for group identifier:%s' % group_identifier)
        except ValueError:
            raise ValidationError(
                detail='No group found for group identifier:%s' % group_identifier)


def validate_metadata(metadata, resource_type):
    """
    Validate metadata including validation of resource type specific metadata.
    If validation fails, ValidationError exception is raised.

    Note: This validation does not check if a specific element is repeatable or not. If an element
    is not repeatable and the metadata list contains more than one dict for the same element type,
    then exception will be raised when that element is created the 2nd time.

    :param metadata: a list of dicts where each dict defines data for a specific metadata
    element.
    Example: the following list contains 2 dict elements - one for 'Description' element
     and the other one for "Coverage' element.
    [{'description':{'abstract': 'This is a great resource'}},
    {'coverage': {'value':{'type': 'period', 'start': 01/01/2010', 'end': '12/12/2015'}}}]
    :param resource_type: resource type name (e.g., "CollectionResource" or "CollectionResource")
    :return:

    """
    resource_class = check_resource_type(resource_type)

    validation_errors = {'metadata': []}
    for element in metadata:
        # here k is the name of the element
        # v is a dict of all element attributes/field names and field values
        k, v = list(element.items())[0]
        is_core_element = False
        model_type = None
        try:
            model_type = ContentType.objects.get(app_label=resource_class._meta.app_label, model=k)
        except ObjectDoesNotExist:
            try:
                model_type = ContentType.objects.get(app_label='hs_core', model=k)
                is_core_element = True
            except ObjectDoesNotExist:
                validation_errors['metadata'].append("Invalid metadata element name:%s." % k)

        if model_type:
            if not issubclass(model_type.model_class(), AbstractMetaDataElement):
                validation_errors['metadata'].append("Invalid metadata element name:%s." % k)

            element_attribute_names_valid = True
            for attribute_name in v:
                element_class = model_type.model_class()
                if k.lower() == 'coverage' or k.lower() == 'originalcoverage':
                    if attribute_name == 'value':
                        attribute_name = '_value'
                if hasattr(element_class(), attribute_name):
                    if callable(getattr(element_class(), attribute_name)):
                        element_attribute_names_valid = False
                        validation_errors['metadata'].append(
                            "Invalid attribute name:%s found for metadata element name:%s."
                            % (attribute_name, k))
                else:
                    element_attribute_names_valid = False
                    validation_errors['metadata'].append(
                        "Invalid attribute name:%s found for metadata element name:%s."
                        % (attribute_name, k))

            if element_attribute_names_valid:
                if is_core_element:
                    element_resource_class = BaseResource().__class__
                else:
                    element_resource_class = resource_class

                # here we expect element form validation to happen as part of the signal handler
                # in each resource type
                handler_response = pre_metadata_element_create.send(
                    sender=element_resource_class, element_name=k,
                    request=MetadataElementRequest(k, **v))

                for receiver, response in handler_response:
                    if 'is_valid' in response:
                        if not response['is_valid']:
                            validation_errors['metadata'].append(
                                "Invalid data found for metadata element name:%s." % k)
                    else:
                        validation_errors['metadata'].append(
                            "Invalid data found for metadata element name:%s." % k)

    if len(validation_errors['metadata']) > 0:
        raise ValidationError(detail=validation_errors)


class MetadataElementRequest(object):
    def __init__(self, element_name, **element_data_dict):
        if element_name.lower() == 'coverage' or element_name.lower() == 'originalcoverage':
            cov_type = element_data_dict.get('type', None)
            if 'value' in element_data_dict:
                element_data_dict = element_data_dict['value']
                if cov_type is not None:
                    element_data_dict['type'] = cov_type

        # post data must be a QueryDict
        qdict = QueryDict('', mutable=True)
        if element_name.lower() in ('creator', 'contributor'):
            identifiers = element_data_dict.pop('identifiers', None)
            if identifiers is not None:
                for key in identifiers:
                    identifier = {'identifier_name': key, 'identifier_link': identifiers[key]}
                    qdict.update(identifier)
        if element_data_dict:
            self.POST = qdict.update(element_data_dict)
        self.POST = qdict


def create_form(formclass, request):
    try:
        params = formclass(data=json.loads(request.body))
    except ValueError:
        params = formclass(data=request)

    return params


def get_metadata_contenttypes():
    """Gets a list of all metadata content types"""
    meta_contenttypes = []
    for model in apps.get_models():
        if model == CoreMetaData or issubclass(model, CoreMetaData):
            meta_contenttypes.append(ContentType.objects.get_for_model(model))
    return meta_contenttypes


def get_my_resources_filter_counts(user, **kwargs):
    """
    Gets counts of resources that belong to a given user.
    :param user: an instance of User - user who wants to see his/her resources
    :return: an json object with counts for specific filter cases
    """

    owned_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)
    # remove obsoleted resources from the owned_resources
    owned_resources = owned_resources.exclude(object_id__in=Relation.objects.filter(
        type='isReplacedBy').values('object_id')).exclude(extra_data__to_be_deleted__isnull=False)

    # get a list of resources with effective CHANGE privilege (should include resources that the
    # user has access to via group
    editable_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE, via_group=True)
    # remove obsoleted resources from the editable_resources
    editable_resources = editable_resources.exclude(
        object_id__in=Relation.objects.filter(type='isReplacedBy').values('object_id'))

    # get a list of resources with effective VIEW privilege (should include resources that the
    # user has access via group
    viewable_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW, via_group=True)

    # remove obsoleted resources from the viewable_resources
    viewable_resources = viewable_resources.exclude(
        object_id__in=Relation.objects.filter(type='isReplacedBy').values('object_id'))

    discovered_resources = user.ulabels.my_resources

    favorite_resources = user.ulabels.favorited_resources

    return {
        'favorites': favorite_resources.count(),
        'ownedCount': owned_resources.count(),
        'addedCount': discovered_resources.count(),
        'sharedCount': viewable_resources.count() + editable_resources.count()
    }


def get_my_resources_list(user, annotate=False, filter=None, **kwargs):
    """
    Gets a QuerySet object for listing resources that belong to a given user.
    :param user: an instance of User - user who wants to see his/her resources
    :param annotate: whether to annotate for my resources page listing.
    :param filter: an array containing filters that determine the type of resources fetched
    :return: an instance of QuerySet of resources
    """

    owned_resources = BaseResource.objects.none()
    editable_resources = BaseResource.objects.none()
    viewable_resources = BaseResource.objects.none()
    discovered_resources = BaseResource.objects.none()

    if not filter or 'owned' in filter:
        # get a list of resources with effective OWNER privilege
        owned_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)

    if not filter or 'editable' in filter:
        # get a list of resources with effective CHANGE privilege (should include resources that the
        # user has access to via group
        editable_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE,
                                                                             via_group=True)

    if not filter or 'viewable' in filter:
        # get a list of resources with effective VIEW privilege (should include resources that the
        # user has access via group
        viewable_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW,
                                                                             via_group=True)

    if not filter or 'discovered' in filter:
        discovered_resources = user.ulabels.my_resources

    favorite_resources = user.ulabels.favorited_resources

    # join all queryset objects.
    resource_collection = owned_resources.distinct() | \
        editable_resources.distinct() | \
        viewable_resources.distinct() | \
        discovered_resources.distinct()
    if not filter or 'favorites' in filter:
        resource_collection = resource_collection | favorite_resources.distinct()

    # remove obsoleted resources
    resource_collection = resource_collection.exclude(object_id__in=Relation.objects.filter(
        type='isReplacedBy').values('object_id')).exclude(extra_data__to_be_deleted__isnull=False)

    # When used in the My Resources page, annotate for speed
    if annotate:
        # The annotated field 'has_labels' would allow us to query the DB for labels only if the
        # resource has labels - that means we won't hit the DB for each resource listed on the page
        # to get the list of labels for a resource
        labeled_resources = user.ulabels.labeled_resources
        resource_collection = resource_collection.annotate(has_labels=Case(
            When(short_id__in=labeled_resources.values_list('short_id', flat=True),
                 then=Value(True, BooleanField()))))

        resource_collection = resource_collection.annotate(
            is_favorite=Case(When(short_id__in=favorite_resources.values_list('short_id', flat=True),
                                  then=Value(True, BooleanField()))))

        resource_collection = resource_collection.only('short_id', 'resource_type', 'created', 'content_type')
        # we won't hit the DB for each resource to know if it's status is public/private/discoverable
        # etc
        resource_collection = resource_collection.select_related('raccess', 'rlabels', 'content_type')
        meta_contenttypes = get_metadata_contenttypes()

        for ct in meta_contenttypes:
            # get a list of resources having metadata that is an instance of a specific
            # metadata class (e.g., CoreMetaData) - we have to prefetch by content_type as
            # prefetch works only for the same object type (type of 'content_object' in this case)
            res_list = [res for res in resource_collection if res.content_type == ct]

            # prefetch metadata items - creators, keywords(subjects), dates, and title
            # this will generate 4 queries for the 4 Prefetch + 1 for each resource to retrieve 'content_object'
            if res_list:
                prefetch_related_objects(res_list,
                                         Prefetch('content_object__creators'),
                                         Prefetch('content_object__subjects'),
                                         Prefetch('content_object__dates'),
                                         Prefetch('content_object___title'),
                                         )

    return resource_collection


def send_action_to_take_email(request, user, action_type, **kwargs):
    """
    Sends an email with an action link to a user.
    The actual action takes place when the user clicks on the link

    The ``action_type`` arg is both the name of the urlpattern for
    the action link, as well as the names of the email templates
    to use. Additional context variable needed in the email template can be
    passed using the kwargs

    for action_type == 'group_membership', an instance of GroupMembershipRequest and
    instance of Group are expected to
    be passed into this function
    """
    context = {'request': request, 'user': user, 'explanation': kwargs.get('explanation', None)}
    if action_type == 'group_membership':
        email_to = kwargs.get('group_owner', user)
        membership_request = kwargs['membership_request']
        action_url = reverse(action_type, kwargs={
            "uidb36": int_to_base36(email_to.id),
            "token": without_login_date_token_generator.make_token(email_to),
            "membership_request_id": membership_request.id
        }) + "?next=" + (next_url(request) or "/")

        context['group'] = kwargs.pop('group')
    elif action_type == 'group_auto_membership':
        email_to = kwargs.get('group_owner', user)
        context['group'] = kwargs.pop('group')
        action_url = ''
    elif action_type == 'metadata_review':
        user_from = kwargs.get('user_from', None)
        context['user_from'] = user_from
        email_to = kwargs.get('email_to', user)
        resource = kwargs.pop('resource')
        context['resource'] = resource
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        action_url = reverse(action_type, kwargs={
            "shortkey": resource.short_id,
            "action": "approve",
            "uidb64": uidb64,
            "token": without_login_date_token_generator.make_token(email_to),
        }) + "?next=" + (next_url(request) or "/")
        context['spatial_coverage'] = get_coverage_data_dict(resource)

        context['reject_url'] = action_url.replace("approve", "reject")
        reject_subject = parse.quote("Publication Request Rejected")
        reject_body = parse.quote("Your Publication Request for the following resource was rejected: ")
        href_for_mailto_reject = (
            f"mailto:{user_from.email}?subject={reject_subject}&body={reject_body}"
            f'{request.scheme}://{request.get_host()}/resource/{resource.short_id}'
        )
        context['href_for_mailto_reject'] = href_for_mailto_reject
    elif action_type == 'act_on_quota_request':
        user_from = kwargs.get('user_from', None)
        context['user_from'] = user_from
        email_to = kwargs.get('email_to', user)
        quota_request_form = kwargs.pop('quota_request_form')
        context['quota_request_form'] = quota_request_form
        context['user_quota'] = kwargs.pop('user_quota')
        action_url = reverse(action_type, kwargs={
            "action": "approve",
            "quota_request_id": quota_request_form.id,
            "uidb36": int_to_base36(user.id),
            "token": without_login_date_token_generator.make_token(email_to),
        }) + "?next=" + (next_url(request) or "/")
        context['reject_url'] = action_url.replace("approve", "deny")
        reject_subject = parse.quote("Quota Increase Request Rejected")
        reject_body = parse.quote("Your Quota Increase Request was rejected. ")
        href_for_mailto_reject = (
            f"mailto:{user_from.email}?subject={reject_subject}&body={reject_body}"
            f'{request.scheme}://{request.get_host()}/user/{user_from.id}'
        )
        context['href_for_mailto_reject'] = href_for_mailto_reject
    else:
        email_to = kwargs.get('group_owner', user)
        action_url = reverse(action_type, kwargs={
            "uidb36": int_to_base36(email_to.id),
            "token": without_login_date_token_generator.make_token(email_to)
        }) + "?next=" + (next_url(request) or "/")

    context['action_url'] = action_url
    context.update(kwargs)

    subject_template_name = "email/%s_subject.txt" % action_type
    subject = subject_template(subject_template_name, context)
    send_mail_template(subject, "email/%s" % action_type,
                       settings.DEFAULT_FROM_EMAIL, email_to.email,
                       context=context)


def show_relations_section(res_obj):
    """
    This func is to determine whether to show 'Relations' section in 'Related Resources' tab.
    Return True if number of "hasPart" + "hasGeneric" < number of all relation metadata
    :param res_obj:  resource object
    :return: Bool
    """

    all_relation_count = res_obj.metadata.relations.count()
    has_part_count = res_obj.metadata.relations.filter(type=RelationTypes.hasPart).count()
    has_inspecific_count = res_obj.metadata.relations.filter(type=RelationTypes.relation).count()
    if all_relation_count > (has_part_count + has_inspecific_count):
        return True
    return False


# TODO: no handling of pre_create or post_create signals
def link_s3_file_to_django(resource, filepath):
    """
    Link a newly created S3 file to Django resource model

    :param filepath: full path to file
    """
    # link the newly created file (**filepath**) to Django resource model
    b_add_file = False
    # TODO: folder is an abstract concept... utilize short_path for whole API
    if resource:
        folder, base = ResourceFile.resource_path_is_acceptable(resource, filepath,
                                                                test_exists=False)
        ret = None
        try:
            ret = ResourceFile.get(resource=resource, file=base, folder=folder)
        except ObjectDoesNotExist:
            # this does not copy the file from anywhere; it must exist already
            b_add_file = True

        if b_add_file:
            ret = ResourceFile.create(resource=resource, file=base, folder=folder)
            file_format_type = get_file_mime_type(filepath)
            if file_format_type not in [mime.value for mime in resource.metadata.formats.all()]:
                resource.metadata.create_element('format', value=file_format_type)
        return ret


def link_s3_folder_to_django(resource, istorage, foldername, auto_aggregate=True):
    res_files = _link_s3_folder_to_django(resource, istorage, foldername)
    if auto_aggregate:
        check_aggregations(resource, res_files)
    return res_files


def listfolders_recursively(istorage, path):
    folders = []
    listing = istorage.listdir(path)
    for folder in listing[0]:
        folder_path = os.path.join(path, folder)
        folders.append(folder_path)
        folders = folders + listfolders_recursively(istorage, folder_path)
    return folders


def _link_s3_folder_to_django(resource, istorage, foldername):
    """
    Recursively Link S3 folder and all files and sub-folders inside the folder to Django
    Database after S3 file and folder operations to get Django and S3 in sync

    :param resource: the BaseResource object representing a HydroShare resource
    :param istorage: REDUNDANT: S3Storage object
    :param foldername: the folder name, as a fully qualified path
    :return: List of ResourceFile of newly linked files
    """
    if __debug__:
        assert (isinstance(resource, BaseResource))
    if istorage is None:
        istorage = resource.get_s3_storage()

    res_files = []
    if foldername:
        store = istorage.listdir(foldername)
        # add files into Django resource model
        for file in store[1]:
            file_path = os.path.join(foldername, file)
            # This assumes that file_path is a full path
            res_files.append(link_s3_file_to_django(resource, file_path))
        # recursively add sub-folders into Django resource model
        for folder in store[0]:
            res_files = res_files + \
                _link_s3_folder_to_django(resource, istorage,
                                          os.path.join(foldername, folder))
    return res_files


def rename_s3_file_or_folder_in_django(resource, src_name, tgt_name):
    """
    Rename file in Django DB after the file/folder is renamed in S3 side
    :param resource: the BaseResource object representing a HydroShare resource
    :param src_name: the file or folder full path name to be renamed
    :param tgt_name: the file or folder full path name to be renamed to
    :return:

    Note: the need to copy and recreate the file object was made unnecessary
    by the ResourceFile.set_storage_path routine, which always sets that
    correctly. Thus it is possible to move without copying. Thus, logical file
    relationships are preserved and no longer need adjustment.
    """
    # checks src_name as a side effect.
    src_folder, base = ResourceFile.resource_path_is_acceptable(resource, src_name,
                                                                test_exists=False)
    tgt_folder, _ = ResourceFile.resource_path_is_acceptable(resource, tgt_name, test_exists=False)
    file_or_folder_move = src_folder != tgt_folder
    composite_file_move = file_or_folder_move and resource.resource_type == 'CompositeResource'
    try:
        res_file_obj = ResourceFile.get(resource=resource, file=base, folder=src_folder)
        # if the source file is part of a FileSet or Model Program/Instance aggregation (based on folder),
        # we need to remove it from that aggregation in the case the file is being moved out of that aggregation
        if composite_file_move:
            resource.remove_aggregation_from_file(res_file_obj, src_folder, tgt_folder)

        # checks tgt_name as a side effect.
        ResourceFile.resource_path_is_acceptable(resource, tgt_name, test_exists=True)
        res_file_obj.set_storage_path(tgt_name)
        if composite_file_move:
            # if the file is getting moved into a folder that represents a FileSet or to a folder
            # inside a fileset folder, then make the file part of that FileSet
            # if the file is moved into a model program aggregation folder or to a folder inside the model program
            # folder, make the file as part of the model program aggregation
            resource.add_file_to_aggregation(res_file_obj)

    except ObjectDoesNotExist:
        # src_name and tgt_name are folder names
        res_file_objs = ResourceFile.list_folder(resource=resource, folder=src_name)
        batch_size = settings.BULK_UPDATE_CREATE_BATCH_SIZE
        is_target_folder_aggregation = False
        if composite_file_move:
            try:
                resource.get_aggregation_by_name(tgt_folder)
                is_target_folder_aggregation = True
            except ObjectDoesNotExist:
                pass
            aggregations = list(resource.logical_files)
            # see the comments above (for the case of moving a single file) for why we need to remove the file from
            # the aggregation
            for fobj in res_file_objs:
                # TODO: this is a case of n+1 query - which can be problematic if the folder being
                #  moved contains a large number of files
                resource.remove_aggregation_from_file(fobj, src_folder, tgt_folder, aggregations=aggregations,
                                                      cleanup=False)
            resource.cleanup_aggregations()

        for fobj in res_file_objs:
            src_path = fobj.get_storage_path(resource=resource)
            # naively replace src_name with tgt_name
            new_path = src_path.replace(src_name, tgt_name, 1)
            folder, _ = fobj.path_is_acceptable(new_path, test_exists=False)
            fobj.file_folder = folder
            fobj.resource_file = new_path

        if res_file_objs:
            ResourceFile.objects.bulk_update(res_file_objs, ['file_folder', 'resource_file'], batch_size=batch_size)

            if is_target_folder_aggregation and composite_file_move:
                res_file_objs = ResourceFile.list_folder(resource=resource, folder=tgt_name)
                aggregations = list(resource.logical_files)
                for fobj in res_file_objs:
                    # see the comments above (for the case of moving a single file) for why we need to add the file to
                    # the aggregation
                    # TODO: this is a case of n+1 query - which can be problematic if the folder being
                    #  moved contains a large number of files
                    resource.add_file_to_aggregation(fobj, aggregations=aggregations)


def remove_s3_folder_in_django(resource, folder_path, user):
    """
    Remove all files inside a folder in Django DB after the folder is removed from S3
    If the folder contains any aggregations, those are also deleted from DB
    :param resource: the BaseResource object representing a HydroShare resource
    :param folder_path: full path (starting with resource id) of the folder that has been removed from S3
    :param user: who initiated the folder delete operation
    :return:
    """

    def get_file_extension(rf):
        _file_name = os.path.basename(rf.get_storage_path(resource=resource))
        _, ext = os.path.splitext(_file_name)
        return ext

    if folder_path.endswith('/'):
        folder_path = folder_path.rstrip('/')

    # we need to delete only the files that are under the folder_path
    rel_folder_path = folder_path[len(resource.file_path) + 1:]
    res_file_set = ResourceFile.objects.filter(object_id=resource.id,
                                               file_folder__startswith=rel_folder_path)

    if resource.resource_type == 'CompositeResource':
        # delete all aggregation objects that are under the folder that got deleted
        aggr_start_path = f"{rel_folder_path}/"
        for lf in resource.logical_files:
            if lf.aggregation_name.startswith(aggr_start_path):
                lf.logical_delete(user, resource=resource, delete_res_files=False, delete_meta_files=False)

        # delete if there is a folder based aggregation matching the folder that got deleted
        for lf in resource.logical_files:
            if lf.aggregation_name == rel_folder_path:
                lf.logical_delete(user, resource=resource, delete_res_files=False, delete_meta_files=False)
                break

    deleted_file_extensions = {get_file_extension(f) for f in res_file_set}

    # delete resource file records from Django DB
    ResourceFile.objects.filter(object_id=resource.id,
                                file_folder__startswith=rel_folder_path).delete()

    resource_file_extensions = {get_file_extension(f) for f in resource.files.all()}
    mime_types = []
    for file_ext in deleted_file_extensions:
        if file_ext not in resource_file_extensions:
            file_name = f"file.{file_ext}"
            delete_file_mime_type = get_file_mime_type(file_name)
            mime_types.append(delete_file_mime_type)

    if mime_types:
        resource.metadata.formats.filter(value__in=mime_types).delete()

    if resource.resource_type == 'CompositeResource':
        resource.cleanup_aggregations()

    # send the post-delete signal
    post_delete_file_from_resource.send(sender=resource.__class__, resource=resource)


# TODO: shouldn't we be able to zip to a different subfolder?  Currently this is not possible.
def zip_folder(user, res_id, input_coll_path, output_zip_fname, bool_remove_original):
    """
    Zip input_coll_path into a zip file in hydroshareZone or any federated zone used for HydroShare
    resource backend store and modify HydroShare Django site accordingly.

    :param user: the requesting user
    :param res_id: resource uuid
    :param input_coll_path: relative sub-collection path under res_id collection to be zipped.
    :param output_zip_fname: file name only with no path of the generated zip file name
    :param bool_remove_original: a boolean indicating whether original files will be deleted
    after zipping.
    :return: output_zip_fname and output_zip_size pair
    """
    if __debug__:
        assert (input_coll_path.startswith("data/contents/"))

    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    if resource.raccess.published:
        raise ValidationError("Folder zipping is not allowed for a published resource")
    istorage = resource.get_s3_storage()
    res_coll_input = os.path.join(resource.root_path, input_coll_path)
    if not istorage.exists(res_coll_input):
        raise ValidationError(f"Specified folder path ({input_coll_path}) doesn't exist.")

    # check resource supports zipping of a folder
    if not resource.supports_zip(res_coll_input):
        raise ValidationError("Zipping of this folder is not supported.")

    # check if resource supports deleting the original folder after zipping
    if bool_remove_original:
        if not resource.supports_delete_folder_on_zip(input_coll_path):
            raise ValidationError("Deleting of original folder is not allowed after "
                                  "zipping of a folder.")

    if not ResourceFile.is_filename_valid(output_zip_fname):
        filename_banned_chars = " ".join(ResourceFile.banned_symbols())
        err_msg = f"Invalid zip filename ({output_zip_fname}). Filename can't have any of these " \
                  f"characters: {filename_banned_chars}"
        raise ValidationError(err_msg)

    content_dir = os.path.dirname(res_coll_input)
    output_zip_full_path = os.path.join(content_dir, output_zip_fname)
    if istorage.exists(output_zip_full_path):
        err_msg = f"Zip filename '{output_zip_fname}' already exists. Provide a different name for the zip file."
        raise ValidationError(err_msg)

    if resource.resource_type == "CompositeResource":
        resource.create_aggregation_meta_files()

    istorage.zipup(res_coll_input, output_zip_full_path)
    output_zip_size = istorage.size(output_zip_full_path)
    zip_res_file = link_s3_file_to_django(resource, output_zip_full_path)
    if resource.resource_type == "CompositeResource":
        # make the newly added zip file part of an aggregation if needed
        resource.add_file_to_aggregation(zip_res_file)

    if bool_remove_original:
        for f in ResourceFile.objects.filter(object_id=resource.id):
            full_path_name = f.storage_path
            if res_coll_input in full_path_name and output_zip_full_path not in full_path_name:
                folder, base = os.path.split(f.short_path)
                try:
                    ResourceFile.get(resource=resource, file=base, folder=folder)
                except ObjectDoesNotExist:
                    # this can happen in case of deleting a file that is part of a logical file group
                    # where deleting one file, deletes all files of the logical file group
                    pass
                else:
                    delete_resource_file(res_id, f.short_path, user)

        # remove empty folder in S3
        istorage.delete(res_coll_input)

    # TODO: should check can_be_public_or_discoverable here

    hydroshare.utils.resource_modified(resource, user, overwrite_bag=False)
    return output_zip_fname, output_zip_size


def zip_by_aggregation_file(user, res_id, aggregation_name, output_zip_fname):
    """
    Zips an aggregation based on aggregation file path (allows zipping of aggregations which are not folder based)
    :param user: user requesting the zipping of an aggregation
    :param res_id: id of the resource that contains the aggregation
    :param aggregation_name: short path (relative to res_id/data/contents/) of the aggregation to be zipped
    :param output_zip_fname: name of the zip file
    :return: zip file path and size of the zip file
    :raises: ValidationError if the aggregation is not found or if the zip file name is invalid
    :raises: QuotaException if the user's quota is exceeded
    """
    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    if resource.resource_type != "CompositeResource":
        raise ValidationError(f"Aggregation zipping is not allowed for resource type:{resource.resource_type}")
    if resource.raccess.published:
        raise ValidationError("Aggregation zipping is not allowed for a published resource")
    istorage = resource.get_s3_storage()
    if aggregation_name.startswith('data/contents/'):
        _, aggregation_name = aggregation_name.split('data/contents/')

    aggr_storage_path = os.path.join(resource.file_path, aggregation_name)
    if not istorage.exists(aggr_storage_path):
        raise ValidationError(f"Specified aggregation path ({aggregation_name}) was not found")

    if not ResourceFile.is_filename_valid(output_zip_fname):
        filename_banned_chars = " ".join(ResourceFile.banned_symbols())
        err_msg = f"Invalid zip filename ({output_zip_fname}). Filename can't have any of " \
                  f"these characters: {filename_banned_chars}"
        raise ValidationError(err_msg)

    if output_zip_fname.lower().endswith('.zip'):
        output_zip_fname = output_zip_fname[:-4]
    aggr_folder_path = os.path.dirname(aggregation_name)
    if aggr_folder_path:
        zip_file_target_full_path = os.path.join(resource.file_path, aggr_folder_path, f"{output_zip_fname}.zip")
    else:
        zip_file_target_full_path = os.path.join(resource.file_path, f"{output_zip_fname}.zip")
    if istorage.exists(zip_file_target_full_path):
        err_msg = f"Zip file ({output_zip_fname}.zip) already exists. Provide a different name for the zip file."
        raise ValidationError(err_msg)

    daily_date = datetime.today().strftime('%Y-%m-%d')
    output_path = f"zips/{daily_date}/{uuid4().hex}/{output_zip_fname}.zip"
    s3_output_path = resource.get_s3_path(output_path, prepend_short_id=False)
    s3_aggr_input_path = os.path.join(resource.file_path, aggregation_name)
    create_temp_zip(resource_id=res_id, input_path=s3_aggr_input_path, output_path=s3_output_path,
                    aggregation_name=aggregation_name)

    # validate the size of the zip file with the user quota
    zip_file_size = istorage.size(s3_output_path)
    validate_user_quota(resource.quota_holder, zip_file_size)

    # move the zip file to the input path
    basepath = os.path.dirname(s3_aggr_input_path)
    zip_file_path = os.path.join(basepath, os.path.basename(s3_output_path))
    istorage.moveFile(s3_output_path, zip_file_path)

    # register the zip file in Django
    zip_res_file = link_s3_file_to_django(resource, zip_file_path)
    output_zip_size = istorage.size(zip_res_file.storage_path)
    # make the newly added zip file part of an aggregation if needed
    resource.add_file_to_aggregation(zip_res_file)

    hydroshare.utils.resource_modified(resource, user, overwrite_bag=False)
    return zip_file_path, output_zip_size


class S3File:
    """Mimics an uploaded file to allow use of the ingestion logic which expects an uploaded file, rather than a file
    on S3."""

    def __init__(self, name, istorage):
        self._name = name
        self._istorage = istorage

    @property
    def name(self):
        return self._name

    def read(self):
        return self._istorage.download(self._name).read()


def unzip_file(user, res_id, zip_with_rel_path, bool_remove_original,
               overwrite=False, auto_aggregate=True, ingest_metadata=False, unzip_to_folder=False):
    """
    Unzip the input zip file while preserving folder structures in hydroshareZone or
    any federated zone used for HydroShare resource backend store and keep Django DB in sync.
    :param user: requesting user
    :param res_id: resource uuid
    :param zip_with_rel_path: the zip file name with relative path under res_id collection to
    be unzipped
    :param bool_remove_original: a bool indicating whether original zip file will be deleted
    after unzipping.
    :param bool overwrite: a bool indicating whether to overwrite files on unzip
    :param bool auto_aggregate: a bool indicating whether to check for and aggregate recognized files
    :param bool ingest_metadata: a bool indicating whether to look for and ingest resource/aggregation metadata files
    :param bool unzip_to_folder: a bool indicating whether to unzip to a folder or not
    :return:
    """
    from hs_file_types.utils import identify_metadata_files

    if __debug__:
        assert (zip_with_rel_path.startswith("data/contents/"))

    if ingest_metadata:
        if not auto_aggregate:
            raise ValidationError("auto_aggregate must be on when metadata_ingestion is on.")
        if not overwrite:
            raise ValidationError("overwrite must be on when metadata_ingestion is on.")

    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    if resource.raccess.published:
        raise ValidationError("Unzipping of file is not allowed for a published resource.")
    istorage = resource.get_s3_storage()
    zip_with_full_path = os.path.join(resource.root_path, zip_with_rel_path)
    if not istorage.exists(zip_with_full_path):
        raise ValidationError(f"Zip file ({zip_with_rel_path}) was not found.")

    if not resource.supports_unzip(zip_with_rel_path):
        raise ValidationError("Unzipping of this file is not supported.")

    unzip_to_folder_path = ''
    unzip_path_temp = ''
    unzip_temp_folder = ''
    try:
        # unzip to a temporary folder first to validate contents of the zip file
        relative_path = os.path.dirname(zip_with_rel_path.split('data/contents/')[1])
        unzip_temp_folder = os.path.join("tmp", uuid4().hex, relative_path)
        unzip_path_temp = istorage.unzip(zip_with_full_path, unzipped_folder=unzip_temp_folder)

        # validate files in the zip file - checking for banned characters
        unzipped_files = listfiles_recursively(istorage, unzip_path_temp)
        for file_in_zip in unzipped_files:
            file_in_zip = os.path.basename(file_in_zip)
            if not ResourceFile.is_filename_valid(file_in_zip):
                log_msg = f"Failed to unzip. Zip file ({zip_with_full_path}) has file with name that contains " \
                          f"one or more prohibited characters."
                logger.error(log_msg)
                err_msg = "Zip file has file with name that contains one or more prohibited characters."
                raise SuspiciousFileOperation(err_msg)

        # validate folders in the zip file - checking for banned characters
        unzipped_folder_paths = list_folders_recursively(istorage, unzip_path_temp)
        for folder_in_zip in unzipped_folder_paths:
            folder_in_zip = os.path.basename(folder_in_zip)
            if not ResourceFile.is_folder_name_valid(folder_in_zip):
                log_msg = f"Failed to unzip. Zip file ({zip_with_full_path}) has folder with name that contains " \
                          f"one or more prohibited characters."
                logger.error(log_msg)
                err_msg = "Zip file has folder with name that contains one or more prohibited characters."
                raise SuspiciousFileOperation(err_msg)

        if unzip_to_folder:
            # unzip to the subfolder with zip file base name as the subfolder name. If the subfolder name already
            # exists, a sequential number is appended to the subfolder name to make sure the subfolder name is unique
            def _get_nonexistant_path(istorage, path):
                if not istorage.exists(path):
                    return path
                i = 1
                new_path = "{}-{}".format(path, i)
                while istorage.exists(new_path):
                    i += 1
                    new_path = "{}-{}".format(path, i)
                return new_path
            folder_name = os.path.splitext(os.path.basename(zip_with_full_path))[0].strip()
            unzip_folder = os.path.join(os.path.dirname(zip_with_full_path), folder_name)

            unzip_folder = _get_nonexistant_path(istorage, unzip_folder)
            unzip_to_folder_path = istorage.unzip(zip_with_full_path, unzipped_folder=unzip_folder)
            res_files = link_s3_folder_to_django(resource, istorage, unzip_to_folder_path, auto_aggregate)
            if resource.resource_type == 'CompositeResource':
                # make the newly added files part of an aggregation if needed
                aggregations = list(resource.logical_files)
                for res_file in res_files:
                    resource.add_file_to_aggregation(res_file, aggregations=aggregations)
        else:
            dir_file_list = istorage.listdir(unzip_path_temp)
            unzip_subdir_list = dir_file_list[0]
            override_tgt_paths = []
            for sub_dir_name in unzip_subdir_list:
                dest_sub_path = os.path.join(os.path.dirname(zip_with_full_path), sub_dir_name)
                if istorage.exists(dest_sub_path):
                    override_tgt_paths.append(dest_sub_path)

            res_files = []
            for unzipped_file in unzipped_files:
                res_files.append(S3File(unzipped_file, istorage))
            meta_files = []
            if ingest_metadata:
                res_files, meta_files, map_files = identify_metadata_files(res_files)

            for file in res_files:
                destination_file = _get_destination_filename(file.name, unzip_temp_folder, zip_with_full_path)
                if istorage.exists(destination_file):
                    override_tgt_paths.append(destination_file)

            if not overwrite and override_tgt_paths:
                override_simplified_paths = [tgt_path.split('data/contents/')[1] for tgt_path in override_tgt_paths]
                raise FileOverrideException('move would overwrite {}'.format(', '.join(override_simplified_paths)))

            for override_tgt_path in override_tgt_paths:
                if istorage.exists(override_tgt_path):
                    if resource.resource_type == "CompositeResource":
                        aggregation_object = resource.get_file_aggregation_object(override_tgt_path)
                        if aggregation_object:
                            aggregation_object.logical_delete(user)
                        else:
                            # check if destination override path is a file
                            try:
                                f = ResourceFile.get(resource=resource, file=override_tgt_path)
                                f.delete()
                            except ObjectDoesNotExist:
                                # it should be a folder if not a file, but double check it is indeed a folder
                                files = ResourceFile.objects.filter(
                                    object_id=resource.id,
                                    file_folder=override_tgt_path.rsplit('data/contents/')[1])
                                if files:
                                    # it is indeed a folder
                                    remove_folder(user, resource.short_id,
                                                  override_tgt_path.rsplit(f'{resource.short_id}/')[1])
                                else:
                                    # it is somehow in S3 but not in Django, delete it from S3 to be consistent
                                    istorage.delete(override_tgt_path)
                    else:
                        istorage.delete(override_tgt_path)

            size = validate_resource_file_size(res_files)
            validate_user_quota(resource.quota_holder, size)

            # now move each file to the destination
            for file in res_files:
                destination_file = _get_destination_filename(file.name, unzip_temp_folder, zip_with_full_path)
                istorage.moveFile(file.name, destination_file)
            # and now link them to the resource
            added_resource_files = []
            for file in res_files:
                destination_file = _get_destination_filename(file.name, unzip_temp_folder, zip_with_full_path)
                destination_file = destination_file.replace(res_id + "/", "", 1)
                destination_file = resource.get_s3_path(destination_file)
                res_file = link_s3_file_to_django(resource, destination_file)
                added_resource_files.append(res_file)

            if resource.resource_type == "CompositeResource":
                aggregations = list(resource.logical_files)
                for res_file in added_resource_files:
                    # make the newly added files part of an aggregation if needed
                    resource.add_file_to_aggregation(res_file, aggregations=aggregations)
                    # sets size, checksum, and modified time for the newly added file
                    res_file.set_system_metadata(resource=resource, save=False)

                ResourceFile.objects.bulk_update(added_resource_files, ResourceFile.system_meta_fields(),
                                                 batch_size=settings.BULK_UPDATE_CREATE_BATCH_SIZE)

            if auto_aggregate:
                check_aggregations(resource, added_resource_files)
            if ingest_metadata:
                # delete original zip to prevent from being pulled into an aggregation
                zip_with_rel_path = zip_with_rel_path.split("contents/", 1)[1]
                delete_resource_file(res_id, zip_with_rel_path, user)

                from hs_file_types.utils import ingest_metadata_files
                ingest_metadata_files(resource, meta_files, map_files, unzip_temp_folder)
    except Exception as err:
        logger.exception(f"Failed to unzip file:{zip_with_full_path}. Error:{str(err)}")
        if unzip_to_folder_path and istorage.exists(unzip_to_folder_path):
            istorage.delete(unzip_to_folder_path)
        if not unzip_path_temp:
            unzip_path_temp = os.path.dirname(zip_with_full_path)
            unzip_path_temp = os.path.join(unzip_path_temp, unzip_temp_folder)
        raise
    finally:
        if unzip_path_temp and istorage.exists(unzip_path_temp):
            istorage.delete(unzip_path_temp)

    if bool_remove_original and not ingest_metadata:  # ingest_metadata deletes the zip by default
        zip_with_rel_path = zip_with_rel_path.split("contents/", 1)[1]
        delete_resource_file(res_id, zip_with_rel_path, user)

    # TODO: should check can_be_public_or_discoverable here
    resource.refresh_from_db()
    hydroshare.utils.resource_modified(resource, user, overwrite_bag=False)


def ingest_bag(resource, bag_file, user):
    """
    Ingests a zipped bagit archive of a hydroshare resource that has been uploaded to the resource
    :param resource: The CompositeResource to ingest the bag into
    :param bag_file: The ResourceFile of the zipped bag in the resource
    :param user: The HydroShare user object to do the action as
    """
    from hs_file_types.utils import (identify_metadata_files,
                                     ingest_metadata_files)

    istorage = resource.get_s3_storage()
    zip_with_full_path = os.path.join(resource.file_path, bag_file.short_path)

    # unzip to a temporary folder
    tmp_folder = os.path.join("tmp", uuid4().hex)
    unzip_path = istorage.unzip(zip_with_full_path, unzipped_folder=tmp_folder)
    delete_resource_file(resource.short_id, bag_file.id, user)

    # list all files to be moved into the resource
    unzipped_files = listfiles_recursively(istorage, unzip_path)
    unzipped_folders = list_folders_recursively(istorage, unzip_path)
    # check folders in the bag file don't contain prohibited characters in folder name
    for unzipped_folder in unzipped_folders:
        base_folder = os.path.basename(unzipped_folder)
        if not ResourceFile.is_folder_name_valid(base_folder):
            istorage.delete(unzip_path)
            log_msg = f"Failed to ingest bag. Bag file ({zip_with_full_path}) has folder with name that contains " \
                      f"one or more prohibited characters."
            logger.error(log_msg)
            err_msg = f"Bag file has folder ({base_folder}) with name that contains one or more prohibited characters."
            raise SuspiciousFileOperation(err_msg)

    res_files = []
    for unzipped_file in unzipped_files:
        base_file = os.path.basename(unzipped_file)
        # check files in the bag file don't contain prohibited characters in file name
        if not ResourceFile.is_filename_valid(base_file):
            istorage.delete(unzip_path)
            log_msg = f"Failed to ingest bag. Bag file ({zip_with_full_path}) has file with name that contains " \
                      f"one or more prohibited characters."
            logger.error(log_msg)
            err_msg = f"Bag file has file ({base_file}) with name that contains one or more prohibited characters."
            raise SuspiciousFileOperation(err_msg)
        res_files.append(S3File(unzipped_file, istorage))
    res_files, meta_files, map_files = identify_metadata_files(res_files)
    # filter res_files to only files in the data/contents directory
    data_contents_dir = os.path.join("data", "contents")
    res_files = [res_file for res_file in res_files if res_file.name.count(data_contents_dir) > 0]
    # now move each file to the destination

    def destination_filename(resource, file):
        """Parses the temporary filename to the destination filename"""
        return os.path.join(resource.file_path, file.split(data_contents_dir, 1)[1].strip("/"))

    added_resource_files = []
    for file in res_files:
        destination_file = destination_filename(resource, file.name)
        istorage.moveFile(file.name, destination_file)

        s3_path = resource.get_s3_path(destination_file)
        res_file = link_s3_file_to_django(resource, s3_path)
        added_resource_files.append(res_file)

    for res_file in added_resource_files:
        # sets size, checksum, and modified time for the newly added file
        res_file.set_system_metadata(resource=resource, save=False)

    ResourceFile.objects.bulk_update(added_resource_files, ResourceFile.system_meta_fields(),
                                     batch_size=settings.BULK_UPDATE_CREATE_BATCH_SIZE)

    check_aggregations(resource, added_resource_files)

    ingest_metadata_files(resource, meta_files, map_files)

    istorage.delete(unzip_path)

    # In addition to the Date metadataelement with type created, the resource django model created field is used and
    # needs to be updated.
    created = [d for d in resource.metadata.dates.all() if d.type == 'created'][0]
    resource.created = created.start_date
    resource.save()


def _get_destination_filename(file, unzipped_foldername, zip_with_full_path):
    """
    Returns the destination file path by removing the temp unzipped_foldername from the file path.
    Useful for moving files from a temporary unzipped folder to the resource outside of the
    temporary folder.
    :param file: path to a file
    :param unzipped_foldername: the name of the unzipped folder
    :param zip_with_full_path: the full path of the zip file
    :return:
    """
    split = file.split(unzipped_foldername.strip("/"), 1)
    destination_file = os.path.join(split[0], split[1])
    zip_name = os.path.basename(zip_with_full_path)
    destination_file_path = zip_with_full_path.replace(
        zip_name, destination_file.strip("/"))
    return destination_file_path


def listfiles_recursively(istorage, path):
    """Returns a list of all file paths that start with the specified path
    :param  istorage: an instance of Storage class
    :param  path: the directory path for which all file paths are needed
    :returns a list of file paths
    """
    files = []
    listing = istorage.listdir(path)
    for file in listing[1]:
        files.append(os.path.join(path, file))
    for folder in listing[0]:
        files = files + listfiles_recursively(istorage, os.path.join(path, folder))
    return files


def list_folders_recursively(istorage, path):
    """Returns a list of all folder paths that start with the specified path
    :param  istorage: an instance of Storage class
    :param  path: the directory path for which all sub folder paths are needed
    :returns a list of directory paths
    """
    folders = []
    for folder in listfolders(istorage, path):
        folders.append(os.path.join(path, folder))
        folders.extend(list_folders_recursively(istorage, os.path.join(path, folder)))
    return folders


def listfolders(istorage, path):
    """Returns a list of all sub folders of the specified path
    :param  istorage: an instance of Storage class
    :param  path: the directory path for which all sub folders are needed
    :returns a list of folder names
    """
    return istorage.listdir(path)[0]


def create_folder(res_id, folder_path, migrating_resource=False):
    """
    create a sub-folder/sub-collection in hydroshareZone or any federated zone used for HydroShare
    resource backend store.
    :param res_id: resource uuid
    :param folder_path: relative path for the new folder to be created under
    res_id collection/directory
    :param migrating_resource: A flag to indicate if the folder is being created as part of resource migration
    :return:
    """
    if __debug__:
        assert folder_path.startswith("data/contents/")

    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    if resource.raccess.published and not migrating_resource:
        raise ValidationError("Folder creation is not allowed for a published resource")
    istorage = resource.get_s3_storage()
    input_folder_path = folder_path[len("data/contents/"):]
    folder_path = ResourceFile.validate_new_path(new_path=input_folder_path)
    coll_path = os.path.join(resource.file_path, folder_path)
    if not resource.supports_folder_creation(coll_path):
        raise ValidationError("Folder creation is not allowed here. "
                              "The target folder seems to contain aggregation(s)")

    # check for duplicate folder path
    if istorage.exists(coll_path):
        raise ValidationError(f"Folder ({folder_path}) already exists")

    # validate each of the folders in the specified path
    folders = [folder for folder in folder_path.split("/")]
    for folder in folders:
        if not ResourceFile.is_folder_name_valid(folder):
            folder_banned_chars = ResourceFile.banned_symbols().replace('/', '')
            folder_banned_chars = " ".join(folder_banned_chars)
            err_msg = f"Folder name ({folder}) contains one more prohibited characters. "
            err_msg = f"{err_msg}Prohibited characters are: {folder_banned_chars}"
            raise SuspiciousFileOperation(err_msg)

    istorage.create_folder(resource.short_id, coll_path)
    # istorage.session.run("imkdir", None, '-p', coll_path)


def remove_folder(user, res_id, folder_path):
    """
    remove a sub-folder/sub-collection in hydroshareZone or any federated zone used for HydroShare
    resource backend store.
    :param user: requesting user
    :param res_id: resource uuid
    :param folder_path: the relative path for the folder to be removed under res_id collection.
    :return:
    """
    if __debug__:
        assert (folder_path.startswith("data/contents/"))

    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    if resource.raccess.published:
        raise ValidationError("Folder deletion is not allowed for a published resource")
    istorage = resource.get_s3_storage()
    coll_path = os.path.join(resource.root_path, folder_path)
    if not istorage.isDir(coll_path):
        raise ValidationError(f"Specified folder ({coll_path}) was not found")

    # Seems safest to delete from S3 before removing from Django
    # istorage command is the longest-running and most likely to get interrupted
    istorage.remove_folder(resource.short_id, coll_path)
    remove_s3_folder_in_django(resource, coll_path, user)

    resource.update_public_and_discoverable()  # make private if required

    hydroshare.utils.resource_modified(resource, user, overwrite_bag=False)


def list_folder(res_id, folder_path):
    """
    list a sub-folder/sub-collection in hydroshareZone or any federated zone used for HydroShare
    resource backend store.
    :param user: requesting user
    :param res_id: resource uuid
    :param folder_path: the relative path for the folder to be listed under res_id collection.
    :return:
    """
    if __debug__:
        assert (folder_path.startswith("data/contents/"))

    folder_path = folder_path.strip()
    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    istorage = resource.get_s3_storage()
    coll_path = os.path.join(resource.root_path, folder_path)

    return istorage.listdir(coll_path, remove_metadata=True)


# TODO: modify this to take short paths not including data/contents
def move_or_rename_file_or_folder(user, res_id, src_path, tgt_path, validate_move_rename=True):
    """
    Move or rename a file or folder in hydroshareZone or any federated zone used for HydroShare
    resource backend store.
    :param user: requesting user
    :param res_id: resource uuid
    :param src_path: the relative paths for the source file or folder under res_id collection
    :param tgt_path: the relative paths for the target file or folder under res_id collection
    :param validate_move_rename: if True, then only ask resource type to check if this action is
            allowed. Sometimes resource types internally want to take this action but disallow
            this action by a user. In that case resource types set this parameter to False to allow
            this action.
    :return:

    Note: this utilizes partly qualified pathnames data/contents/foo rather than just 'foo'
    """

    _path_move_rename(user=user, res_id=res_id, src_path=src_path, tgt_path=tgt_path,
                      validate_move_rename=validate_move_rename)


# TODO: modify this to take short paths not including data/contents
def rename_file_or_folder(user, res_id, src_path, tgt_path, validate_rename=True):
    """
    Rename a file or folder in hydroshareZone or any federated zone used for HydroShare
    resource backend store.
    :param user: requesting user
    :param res_id: resource uuid
    :param src_path: the relative path for the source file or folder under res_id collection
    :param tgt_path: the relative path for the target file or folder under res_id collection
    :param validate_rename: if True, then only ask resource type to check if this action is
            allowed. Sometimes resource types internally want to take this action but disallow
            this action by a user. In that case resource types set this parameter to False to allow
            this action.
    :return:

    Note: this utilizes partly qualified pathnames data/contents/foo rather than just 'foo'.
    Also, this foregoes extensive antibugging of arguments because that is done in the
    REST API.
    """

    _path_move_rename(user=user, res_id=res_id, src_path=src_path, tgt_path=tgt_path,
                      validate_move_rename=validate_rename)


# TODO: modify this to take short paths not including data/contents
def move_to_folder(user, res_id, src_paths, tgt_path, validate_move=True):
    """
    Move a file or folder to a folder in hydroshareZone or any federated zone used for HydroShare
    resource backend store.
    :param user: requesting user
    :param res_id: resource uuid
    :param src_paths: the relative paths for the source files and/or folders under res_id collection
    :param tgt_path: the relative path for the target folder under res_id collection
    :param validate_move: if True, then only ask resource type to check if this action is
            allowed. Sometimes resource types internally want to take this action but disallow
            this action by a user. In that case resource types set this parameter to False to allow
            this action.
    :return:

    Note: this utilizes partly qualified pathnames data/contents/foo rather than just 'foo'
    Also, this foregoes extensive antibugging of arguments because that is done in the
    REST API.
    """
    if __debug__:
        for s in src_paths:
            assert (s.startswith('data/contents/'))
        assert (tgt_path == 'data/contents' or tgt_path.startswith("data/contents/"))

    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    if resource.raccess.published and not user.is_superuser:
        raise ValidationError("Operations related to file/folder are allowed only for admin for a published resource")
    istorage = resource.get_s3_storage()
    tgt_full_path = os.path.join(resource.root_path, tgt_path)
    if not istorage.exists(tgt_full_path):
        raise ValidationError(f"Target path ({tgt_path}) doesn't exist")

    for src_path in src_paths:
        src_full_path = os.path.join(resource.root_path, src_path)
        if not istorage.exists(src_full_path):
            raise ValidationError(f"Source path ({src_full_path}) doesn't exist")

    if validate_move:
        # this must raise ValidationError if move is not allowed by specific resource type
        for src_path in src_paths:
            src_full_path = os.path.join(resource.root_path, src_path)
            if not resource.supports_rename_path(src_full_path, tgt_full_path):
                raise ValidationError("File/folder move is not allowed. "
                                      "Either the target folder or the source folder represents an aggregation "
                                      "that doesn't permit file move.")

    for src_path in src_paths:
        src_full_path = os.path.join(resource.root_path, src_path)
        src_base_name = os.path.basename(src_path)
        tgt_qual_path = os.path.join(tgt_full_path, src_base_name)

        istorage.moveFile(src_full_path, tgt_qual_path)
        rename_s3_file_or_folder_in_django(resource, src_full_path, tgt_qual_path)
        if resource.resource_type == "CompositeResource":
            resource.set_flag_to_recreate_aggregation_meta_files(orig_path=src_full_path, new_path=tgt_qual_path)

    # TODO: should check can_be_public_or_discoverable here

    hydroshare.utils.resource_modified(resource, user, overwrite_bag=False)


def s3_path_is_allowed(path):
    """ paths containing '/../' are suspicious """
    if path == "":
        raise ValidationError("Empty file paths are not allowed")
    if '/../' in path:
        raise SuspiciousFileOperation("File paths cannot contain '/../'")
    if '/./' in path:
        raise SuspiciousFileOperation("File paths cannot contain '/./'")


def s3_path_is_directory(istorage, path):
    """ return True if the path is a directory. """
    folder, base = os.path.split(path.rstrip('/'))
    listing = istorage.listdir(folder)
    return base in listing[0]


def get_coverage_data_dict(source, coverage_type='spatial'):
    """Get coverage data as a dict for the specified resource
    :param  source: An instance of BaseResource or FileSet aggregation for which coverage data is
    needed
    :param  coverage_type: Type of coverage data needed. Default is spatial otherwise temporal
    :return A dict of coverage data
    """
    if coverage_type.lower() == 'spatial':
        spatial_coverage = source.metadata.spatial_coverage
        spatial_coverage_dict = {}
        if spatial_coverage:
            spatial_coverage_dict['type'] = spatial_coverage.type
            spatial_coverage_dict['name'] = spatial_coverage.value.get('name', "")
            spatial_coverage_dict['element_id'] = spatial_coverage.id
            if spatial_coverage.type == 'point':
                spatial_coverage_dict['east'] = spatial_coverage.value['east']
                spatial_coverage_dict['north'] = spatial_coverage.value['north']
            else:
                # type is box
                spatial_coverage_dict['eastlimit'] = spatial_coverage.value['eastlimit']
                spatial_coverage_dict['northlimit'] = spatial_coverage.value['northlimit']
                spatial_coverage_dict['westlimit'] = spatial_coverage.value['westlimit']
                spatial_coverage_dict['southlimit'] = spatial_coverage.value['southlimit']
        return spatial_coverage_dict
    else:
        temporal_coverage = source.metadata.temporal_coverage
        temporal_coverage_dict = {}
        if temporal_coverage:
            temporal_coverage_dict['element_id'] = temporal_coverage.id
            temporal_coverage_dict['type'] = temporal_coverage.type
            start_date = parser.parse(temporal_coverage.value['start'])
            end_date = parser.parse(temporal_coverage.value['end'])
            temporal_coverage_dict['start'] = start_date.strftime('%m-%d-%Y')
            temporal_coverage_dict['end'] = end_date.strftime('%m-%d-%Y')
        return temporal_coverage_dict


def get_default_admin_user():
    """A helper method to get the default admin user - used in email notification"""

    from hs_core.hydroshare import create_account
    try:
        default_user_from = User.objects.get(email__iexact=settings.DEFAULT_FROM_EMAIL)
    except User.DoesNotExist:
        default_user_from = create_account(
            email=settings.DEFAULT_FROM_EMAIL,
            username=settings.DEFAULT_FROM_EMAIL,
            first_name=settings.DEFAULT_FROM_EMAIL,
            last_name=settings.DEFAULT_FROM_EMAIL,
            superuser=True
        )
    return default_user_from


def get_default_support_user():
    """A helper method to get or create the default support user - used in email notification"""

    from hs_core.hydroshare import create_account
    try:
        support_user = User.objects.get(email__iexact=settings.DEFAULT_SUPPORT_EMAIL)
    except User.DoesNotExist:
        support_user = create_account(
            email=settings.DEFAULT_SUPPORT_EMAIL,
            username=settings.DEFAULT_SUPPORT_EMAIL,
            first_name=settings.DEFAULT_SUPPORT_EMAIL,
            last_name=settings.DEFAULT_SUPPORT_EMAIL,
            superuser=True
        )
    return support_user


def _path_move_rename(user, res_id, src_path, tgt_path, validate_move_rename=True):
    """helper method for moving/renaming file/folder"""

    if __debug__:
        assert (src_path.startswith("data/contents/"))
        assert (tgt_path.startswith("data/contents/"))

    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    if resource.raccess.published and not user.is_superuser:
        raise ValidationError("Operations related to file/folder are allowed only for admin for a published resource")
    istorage = resource.get_s3_storage()
    src_base_name = src_path[len("data/contents/"):]
    src_base_name = ResourceFile.validate_new_path(new_path=src_base_name)
    src_full_path = os.path.join(resource.file_path, src_base_name)
    tgt_base_name = tgt_path[len("data/contents/"):]
    tgt_base_name = ResourceFile.validate_new_path(new_path=tgt_base_name)
    tgt_full_path = os.path.join(resource.file_path, tgt_base_name)

    if src_full_path == tgt_full_path:
        raise ValidationError("File/folder name is not valid.")

    if validate_move_rename:
        # this must raise ValidationError if move/rename is not allowed by specific resource type
        if not resource.supports_rename_path(src_full_path, tgt_full_path):
            raise ValidationError("File/folder move/rename is not allowed.")

    if src_base_name != tgt_base_name:
        if istorage.isFile(src_full_path):
            # renaming a file - need to validate the new file name
            tgt_file_name_new = os.path.basename(tgt_base_name)
            if not ResourceFile.is_filename_valid(tgt_file_name_new):
                filename_banned_chars = " ".join(ResourceFile.banned_symbols())
                err_msg = f"Filename ({tgt_file_name_new}) contains one more prohibited characters. "
                err_msg = f"{err_msg}Prohibited characters are: {filename_banned_chars}"
                raise SuspiciousFileOperation(err_msg)
        else:
            # renaming a folder - need validate the new folder name
            tgt_folder_name_new = os.path.basename(tgt_base_name)
            if not ResourceFile.is_folder_name_valid(tgt_folder_name_new):
                foldername_banned_chars = ResourceFile.banned_symbols().replace('/', '')
                foldername_banned_chars = " ".join(foldername_banned_chars)
                err_msg = f"Folder name ({tgt_folder_name_new}) contains one more prohibited characters. "
                err_msg = f"{err_msg}Prohibited characters are: {foldername_banned_chars}"
                raise SuspiciousFileOperation(err_msg)

    istorage.moveFile(src_full_path, tgt_full_path)
    rename_s3_file_or_folder_in_django(resource, src_full_path, tgt_full_path)
    if resource.resource_type == "CompositeResource":
        resource.set_flag_to_recreate_aggregation_meta_files(orig_path=src_full_path, new_path=tgt_full_path)

    hydroshare.utils.resource_modified(resource, user, overwrite_bag=False)


def user_from_bucket_name(bucket_name: str) -> User:
    """
    Get the user from the bucket name
    :param bucket_name: the name of the bucket
    :return: the user
    :raises: User.DoesNotExist if the user does not exist
    """
    return User.objects.get(userprofile___bucket_name=bucket_name)


def is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'
