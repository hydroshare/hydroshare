from __future__ import absolute_import

import json
import os
import string
from collections import namedtuple
import paramiko
import logging
from dateutil import parser

from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.base import File
from django.utils.http import int_to_base36
from django.http import HttpResponse, QueryDict

from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from mezzanine.utils.email import subject_template, default_token_generator, send_mail_template
from mezzanine.utils.urls import next_url
from mezzanine.conf import settings

from hs_core import hydroshare
from hs_core.hydroshare import check_resource_type, delete_resource_file
from hs_core.models import AbstractMetaDataElement, BaseResource, GenericResource, Relation, \
    ResourceFile, get_user
from hs_core.signals import pre_metadata_element_create, post_delete_file_from_resource
from hs_core.hydroshare.utils import get_file_mime_type
from django_irods.storage import IrodsStorage
from hs_access_control.models import PrivilegeCodes

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


def json_or_jsonp(r, i, code=200):
    if not isinstance(i, basestring):
        i = json.dumps(i)

    if 'callback' in r.REQUEST:
        return HttpResponse('{c}({i})'.format(c=r.REQUEST['callback'], i=i),
                            content_type='text/javascript')
    elif 'jsonp' in r.REQUEST:
        return HttpResponse('{c}({i})'.format(c=r.REQUEST['jsonp'], i=i),
                            content_type='text/javascript')
    else:
        return HttpResponse(i, content_type='application/json', status=code)


# Since an SessionException will be raised for all irods-related operations from django_irods
# module, there is no need to raise iRODS SessionException from within this function
def upload_from_irods(username, password, host, port, zone, irods_fnames, res_files):
    """
    use iget to transfer selected data object from irods zone to local as a NamedTemporaryFile
    :param username: iRODS login account username used to download irods data object for uploading
    :param password: iRODS login account password used to download irods data object for uploading
    :param host: iRODS login host used to download irods data object for uploading
    :param port: iRODS login port used to download irods data object for uploading
    :param zone: iRODS login zone used to download irods data object for uploading
    :param irods_fnames: the data object file name to download to local for uploading
    :param res_files: list of files for uploading to create resources
    :raises SessionException(proc.returncode, stdout, stderr) defined in django_irods/icommands.py
            to capture iRODS exceptions raised from iRODS icommand subprocess run triggered from
            any method calls from IrodsStorage() if an error or exception ever occurs
    :return: None, but the downloaded file from the iRODS will be appended to res_files list for
    uploading
    """
    irods_storage = IrodsStorage()
    irods_storage.set_user_session(username=username, password=password, host=host, port=port,
                                   zone=zone)
    ifnames = string.split(irods_fnames, ',')
    for ifname in ifnames:
        size = irods_storage.size(ifname)
        tmpFile = irods_storage.download(ifname)
        fname = os.path.basename(ifname.rstrip(os.sep))
        fileobj = File(file=tmpFile, name=fname)
        fileobj.size = size
        res_files.append(fileobj)

    # delete the user session after iRODS file operations are done
    irods_storage.delete_user_session()


def run_ssh_command(host, uname, pwd, exec_cmd):
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
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=uname, password=pwd)
    transport = ssh.get_transport()
    session = transport.open_session()
    session.set_combine_stderr(True)
    session.get_pty()
    session.exec_command(exec_cmd)
    stdin = session.makefile('wb', -1)
    stdout = session.makefile('rb', -1)
    stdin.write("{cmd}\n".format(cmd=pwd))
    stdin.flush()
    logger = logging.getLogger('django')
    output = stdout.readlines()
    if output:
        logger.debug(output)
        return '.'.join(output)
    else:
        return ''


# run the update script on hyrax server via ssh session for netCDF resources on demand
# when private netCDF resources are made public so that all links of data services
# provided by Hyrax service are instantaneously available on demand
def run_script_to_update_hyrax_input_files(shortkey):
    run_ssh_command(host=settings.HYRAX_SSH_HOST, uname=settings.HYRAX_SSH_PROXY_USER,
                    pwd=settings.HYRAX_SSH_PROXY_USER_PWD,
                    exec_cmd=settings.HYRAX_SCRIPT_RUN_COMMAND + ' ' + shortkey)


def can_user_copy_resource(res, user):
    """
    Check whether resource copy is permitted or not
    :param res: resource object to check for whether copy is allowed
    :param user: the requesting user to check for whether copy is allowed
    :return: return True if the resource can be copied; otherwise, return False
    """
    if not user.is_authenticated():
        return False

    if not user.uaccess.owns_resource(res) and \
            (res.metadata.rights.statement == "This resource is shared under the Creative "
                                              "Commons Attribution-NoDerivs CC BY-ND." or
             res.metadata.rights.statement == "This resource is shared under the Creative "
                                              "Commons Attribution-NoCommercial-NoDerivs "
                                              "CC BY-NC-ND."):
        return False

    return True


def authorize(request, res_id, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE,
              raises_exception=True):
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

    try:
        res = hydroshare.utils.get_resource_by_shortkey(res_id, or_404=False)
    except ObjectDoesNotExist:
        raise NotFound(detail="No resource was found for resource id:%s" % res_id)

    if needed_permission == ACTION_TO_AUTHORIZE.VIEW_METADATA:
        if res.raccess.discoverable or res.raccess.public:
            authorized = True
        elif user.is_authenticated() and user.is_active:
            authorized = user.uaccess.can_view_resource(res)
    elif user.is_authenticated() and user.is_active:
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
            authorized = user.uaccess.can_share_resource(res, 2)
    elif needed_permission == ACTION_TO_AUTHORIZE.VIEW_RESOURCE:
        authorized = res.raccess.public

    if raises_exception and not authorized:
        raise PermissionDenied()
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
    :param resource_type: resource type name (e.g., "GenericResource" or "TimeSeriesResource")
    :return:

    """
    resource_class = check_resource_type(resource_type)

    validation_errors = {'metadata': []}
    for element in metadata:
        # here k is the name of the element
        # v is a dict of all element attributes/field names and field values
        k, v = element.items()[0]
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
                    element_resource_class = GenericResource().__class__
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
        params = formclass(data=request.REQUEST)

    return params


def get_my_resources_list(request):
    user = request.user
    # get a list of resources with effective OWNER privilege
    owned_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)
    # remove obsoleted resources from the owned_resources
    owned_resources = owned_resources.exclude(object_id__in=Relation.objects.filter(
        type='isReplacedBy').values('object_id'))

    # get a list of resources with effective CHANGE privilege (should include resources that the
    # user has access to via group
    editable_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE,
                                                                         via_group=True)
    # remove obsoleted resources from the editable_resources
    editable_resources = editable_resources.exclude(object_id__in=Relation.objects.filter(
        type='isReplacedBy').values('object_id'))

    # get a list of resources with effective VIEW privilege (should include resources that the
    # user has access via group
    viewable_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW,
                                                                         via_group=True)
    # remove obsoleted resources from the viewable_resources
    viewable_resources = viewable_resources.exclude(object_id__in=Relation.objects.filter(
        type='isReplacedBy').values('object_id'))

    owned_resources = list(owned_resources)
    editable_resources = list(editable_resources)
    viewable_resources = list(viewable_resources)
    favorite_resources = list(user.ulabels.favorited_resources)
    labeled_resources = list(user.ulabels.labeled_resources)
    discovered_resources = list(user.ulabels.my_resources)

    for res in owned_resources:
        res.owned = True

    for res in editable_resources:
        res.editable = True

    for res in viewable_resources:
        res.viewable = True

    for res in discovered_resources:
        res.discovered = True

    for res in (owned_resources + editable_resources + viewable_resources + discovered_resources):
        res.is_favorite = False
        if res in favorite_resources:
            res.is_favorite = True
        if res in labeled_resources:
            res.labels = res.rlabels.get_labels(user)

    resource_collection = (owned_resources + editable_resources + viewable_resources +
                           discovered_resources)

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
    email_to = kwargs.get('group_owner', user)
    context = {'request': request, 'user': user}
    if action_type == 'group_membership':
        membership_request = kwargs['membership_request']
        action_url = reverse(action_type, kwargs={
            "uidb36": int_to_base36(email_to.id),
            "token": default_token_generator.make_token(email_to),
            "membership_request_id": membership_request.id
        }) + "?next=" + (next_url(request) or "/")

        context['group'] = kwargs.pop('group')
    elif action_type == 'group_auto_membership':
        context['group'] = kwargs.pop('group')
        action_url = ''
    else:
        action_url = reverse(action_type, kwargs={
            "uidb36": int_to_base36(email_to.id),
            "token": default_token_generator.make_token(email_to)
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
    Return True if number of "hasPart" < number of all relation metadata
    :param res_obj:  resource object
    :return: Bool
    """

    all_relation_count = res_obj.metadata.relations.count()
    has_part_count = res_obj.metadata.relations.filter(type="hasPart").count()
    if all_relation_count > has_part_count:
        return True
    return False


# TODO: no handling of pre_create or post_create signals
def link_irods_file_to_django(resource, filepath):
    """
    Link a newly created irods file to Django resource model

    :param filepath: full path to file
    """
    # link the newly created file (**filepath**) to Django resource model
    b_add_file = False
    # TODO: folder is an abstract concept... utilize short_path for whole API
    if resource:
        folder, base = ResourceFile.resource_path_is_acceptable(resource, filepath,
                                                                test_exists=False)
        try:
            ResourceFile.get(resource=resource, file=base, folder=folder)
        except ObjectDoesNotExist:
            # this does not copy the file from anywhere; it must exist already
            ResourceFile.create(resource=resource, file=base, folder=folder)
            b_add_file = True

        if b_add_file:
            file_format_type = get_file_mime_type(filepath)
            if file_format_type not in [mime.value for mime in resource.metadata.formats.all()]:
                resource.metadata.create_element('format', value=file_format_type)


def link_irods_folder_to_django(resource, istorage, foldername, exclude=()):
    """
    Recursively Link irods folder and all files and sub-folders inside the folder to Django
    Database after iRODS file and folder operations to get Django and iRODS in sync

    :param resource: the BaseResource object representing a HydroShare resource
    :param istorage: REDUNDANT: IrodsStorage object
    :param foldername: the folder name, as a fully qualified path
    :param exclude: UNUSED: a tuple that includes file names to be excluded from
        linking under the folder;
    :return:
    """
    if __debug__:
        assert(isinstance(resource, BaseResource))
    if istorage is None:
        istorage = resource.get_irods_storage()

    if foldername:
        store = istorage.listdir(foldername)
        # add files into Django resource model
        for file in store[1]:
            if file not in exclude:
                file_path = os.path.join(foldername, file)
                # This assumes that file_path is a full path
                link_irods_file_to_django(resource, file_path)
        # recursively add sub-folders into Django resource model
        for folder in store[0]:
            link_irods_folder_to_django(resource,
                                        istorage, os.path.join(foldername, folder), exclude)


def rename_irods_file_or_folder_in_django(resource, src_name, tgt_name):
    """
    Rename file in Django DB after the file is renamed in Django side
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
    folder, base = ResourceFile.resource_path_is_acceptable(resource, src_name,
                                                            test_exists=False)
    try:
        res_file_obj = ResourceFile.get(resource=resource, file=base, folder=folder)
        # checks tgt_name as a side effect.
        ResourceFile.resource_path_is_acceptable(resource, tgt_name,
                                                 test_exists=True)
        res_file_obj.set_storage_path(tgt_name)

    except ObjectDoesNotExist:
        # src_name and tgt_name are folder names
        res_file_objs = ResourceFile.list_folder(resource, src_name)

        for fobj in res_file_objs:
            src_path = fobj.storage_path
            # naively replace src_name with tgt_name
            new_path = src_path.replace(src_name, tgt_name, 1)
            fobj.set_storage_path(new_path)


def remove_irods_folder_in_django(resource, istorage, folderpath, user):
    """
    Remove all files inside a folder in Django DB after the folder is removed from iRODS
    :param resource: the BaseResource object representing a HydroShare resource
    :param istorage: IrodsStorage object (redundant; equal to resource.get_irods_storage())
    :param foldername: the folder name that has been removed from iRODS
    :user  user who initiated the folder delete operation
    :return:
    """
    # TODO: Istorage parameter is redundant; derived from resource; can be deleted.
    if resource and istorage and folderpath:
        if not folderpath.endswith('/'):
            folderpath += '/'
        res_file_set = ResourceFile.objects.filter(object_id=resource.id)

        # then delete resource file objects
        for f in res_file_set:
            filename = f.storage_path
            if filename.startswith(folderpath):
                # TODO: integrate deletion of logical file with ResourceFile.delete
                # delete the logical file object if the resource file has one
                if f.has_logical_file:
                    # this should delete the logical file and any associated metadata
                    # but does not delete the resource files that are part of the logical file
                    f.logical_file.logical_delete(user, delete_res_files=False)
                f.delete()
                hydroshare.delete_format_metadata_after_delete_file(resource, filename)

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
        assert(input_coll_path.startswith("data/contents/"))

    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    istorage = resource.get_irods_storage()
    res_coll_input = os.path.join(resource.root_path, input_coll_path)

    # check resource supports zipping of a folder
    if not resource.supports_zip(res_coll_input):
        raise ValidationError("Folder zipping is not supported. "
                              "Folder seems to contain aggregation(s).")

    # check if resource supports deleting the original folder after zipping
    if bool_remove_original:
        if not resource.supports_delete_folder_on_zip(input_coll_path):
            raise ValidationError("Deleting of original folder is not allowed after "
                                  "zipping of a folder.")

    content_dir = os.path.dirname(res_coll_input)
    output_zip_full_path = os.path.join(content_dir, output_zip_fname)
    istorage.session.run("ibun", None, '-cDzip', '-f', output_zip_full_path, res_coll_input)

    output_zip_size = istorage.size(output_zip_full_path)

    link_irods_file_to_django(resource, output_zip_full_path)

    if bool_remove_original:
        for f in ResourceFile.objects.filter(object_id=resource.id):
            full_path_name = f.storage_path
            if res_coll_input in full_path_name and output_zip_full_path not in full_path_name:
                delete_resource_file(res_id, f.short_path, user)

        # remove empty folder in iRODS
        istorage.delete(res_coll_input)

    # TODO: should check can_be_public_or_discoverable here

    hydroshare.utils.resource_modified(resource, user, overwrite_bag=False)
    return output_zip_fname, output_zip_size


def unzip_file(user, res_id, zip_with_rel_path, bool_remove_original):
    """
    Unzip the input zip file while preserving folder structures in hydroshareZone or
    any federated zone used for HydroShare resource backend store and keep Django DB in sync.
    :param user: requesting user
    :param res_id: resource uuid
    :param zip_with_rel_path: the zip file name with relative path under res_id collection to
    be unzipped
    :param bool_remove_original: a bool indicating whether original zip file will be deleted
    after unzipping.
    :return:
    """
    if __debug__:
        assert(zip_with_rel_path.startswith("data/contents/"))

    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    istorage = resource.get_irods_storage()
    zip_with_full_path = os.path.join(resource.root_path, zip_with_rel_path)

    if not resource.supports_unzip(zip_with_rel_path):
        raise ValidationError("Unzipping of this file is not supported.")

    zip_fname = os.path.basename(zip_with_rel_path)
    unzip_path = istorage.unzip(zip_with_full_path)
    link_irods_folder_to_django(resource, istorage, unzip_path)

    if bool_remove_original:
        delete_resource_file(res_id, zip_fname, user)

    # TODO: should check can_be_public_or_discoverable here

    hydroshare.utils.resource_modified(resource, user, overwrite_bag=False)


def create_folder(res_id, folder_path):
    """
    create a sub-folder/sub-collection in hydroshareZone or any federated zone used for HydroShare
    resource backend store.
    :param res_id: resource uuid
    :param folder_path: relative path for the new folder to be created under
    res_id collection/directory
    :return:
    """
    if __debug__:
        assert(folder_path.startswith("data/contents/"))

    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    istorage = resource.get_irods_storage()
    coll_path = os.path.join(resource.root_path, folder_path)

    if not resource.supports_folder_creation(coll_path):
        raise ValidationError("Folder creation is not allowed here. "
                              "The target folder seems to contain aggregation(s)")

    istorage.session.run("imkdir", None, '-p', coll_path)


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
        assert(folder_path.startswith("data/contents/"))

    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    istorage = resource.get_irods_storage()
    coll_path = os.path.join(resource.root_path, folder_path)

    # TODO: Pabitra - resource should check here if folder can be removed
    istorage.delete(coll_path)

    remove_irods_folder_in_django(resource, istorage, coll_path, user)

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
        assert(folder_path.startswith("data/contents/"))

    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    istorage = resource.get_irods_storage()
    coll_path = os.path.join(resource.root_path, folder_path)

    return istorage.listdir(coll_path)


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
    if __debug__:
        assert(src_path.startswith("data/contents/"))
        assert(tgt_path.startswith("data/contents/"))

    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    istorage = resource.get_irods_storage()
    src_full_path = os.path.join(resource.root_path, src_path)
    tgt_full_path = os.path.join(resource.root_path, tgt_path)

    if validate_move_rename:
        # this must raise ValidationError if move/rename is not allowed by specific resource type
        if not resource.supports_rename_path(src_full_path, tgt_full_path):
            raise ValidationError("File/folder move/rename is not allowed.")

    istorage.moveFile(src_full_path, tgt_full_path)
    rename_irods_file_or_folder_in_django(resource, src_full_path, tgt_full_path)
    if resource.resource_type == "CompositeResource":
        org_aggregation_name = src_full_path[len(resource.file_path) + 1:]
        new_aggregation_name = tgt_full_path[len(resource.file_path) + 1:]
        resource.recreate_aggregation_xml_docs(org_aggregation_name, new_aggregation_name)

    hydroshare.utils.resource_modified(resource, user, overwrite_bag=False)


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
    if __debug__:
        assert(src_path.startswith("data/contents/"))
        assert(tgt_path.startswith("data/contents/"))

    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    istorage = resource.get_irods_storage()
    src_full_path = os.path.join(resource.root_path, src_path)
    tgt_full_path = os.path.join(resource.root_path, tgt_path)

    if validate_rename:
        # this must raise ValidationError if move/rename is not allowed by specific resource type
        if not resource.supports_rename_path(src_full_path, tgt_full_path):
            raise ValidationError("File rename is not allowed. "
                                  "File seems to be part of an aggregation")

    istorage.moveFile(src_full_path, tgt_full_path)
    rename_irods_file_or_folder_in_django(resource, src_full_path, tgt_full_path)
    if resource.resource_type == "CompositeResource":
        org_aggregation_name = src_full_path[len(resource.file_path) + 1:]
        new_aggregation_name = tgt_full_path[len(resource.file_path) + 1:]
        resource.recreate_aggregation_xml_docs(org_aggregation_name, new_aggregation_name)
    hydroshare.utils.resource_modified(resource, user, overwrite_bag=False)


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
            assert(s.startswith('data/contents/'))
        assert(tgt_path == 'data/contents' or tgt_path.startswith("data/contents/"))

    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    istorage = resource.get_irods_storage()
    tgt_full_path = os.path.join(resource.root_path, tgt_path)

    if validate_move:
        # this must raise ValidationError if move is not allowed by specific resource type
        for src_path in src_paths:
            src_full_path = os.path.join(resource.root_path, src_path)
            if not resource.supports_rename_path(src_full_path, tgt_full_path):
                raise ValidationError("File/folder move is not allowed. "
                                      "Target folder seems to contain aggregation(s).")

    for src_path in src_paths:
        src_full_path = os.path.join(resource.root_path, src_path)
        src_base_name = os.path.basename(src_path)
        tgt_qual_path = os.path.join(tgt_full_path, src_base_name)
        # logger = logging.getLogger(__name__)
        # logger.info("moving file {} to {}".format(src_full_path, tgt_qual_path))

        istorage.moveFile(src_full_path, tgt_qual_path)
        rename_irods_file_or_folder_in_django(resource, src_full_path, tgt_qual_path)
        if resource.resource_type == "CompositeResource":
            org_aggregation_name = src_full_path[len(resource.file_path) + 1:]
            new_aggregation_name = tgt_qual_path[len(resource.file_path) + 1:]
            resource.recreate_aggregation_xml_docs(org_aggregation_name, new_aggregation_name)

    # TODO: should check can_be_public_or_discoverable here

    hydroshare.utils.resource_modified(resource, user, overwrite_bag=False)


def irods_path_is_allowed(path):
    """ paths containing '/../' are suspicious """
    if path == "":
        raise ValidationError("Empty file paths are not allowed")
    if '/../' in path:
        raise SuspiciousFileOperation("File paths cannot contain '/../'")
    if '/./' in path:
        raise SuspiciousFileOperation("File paths cannot contain '/./'")


def irods_path_is_directory(istorage, path):
    """ return True if the path is a directory. """
    folder, base = os.path.split(path.rstrip('/'))
    listing = istorage.listdir(folder)
    return base in listing[0]


def get_coverage_data_dict(resource, coverage_type='spatial'):
    """Get coverage data as a dict for the specified resource
    :param  resource: An instance of BaseResource for which coverage data is needed
    :param  coverage_type: Type of coverage data needed. Default is spatial otherwise temporal
    :return A dict of coverage data
    """
    if coverage_type.lower() == 'spatial':
        spatial_coverage = resource.metadata.coverages.exclude(type='period').first()
        spatial_coverage_dict = {}
        if spatial_coverage:
            spatial_coverage_dict['type'] = spatial_coverage.type
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
        temporal_coverage = resource.metadata.coverages.filter(type='period').first()
        temporal_coverage_dict = {}
        if temporal_coverage:
            temporal_coverage_dict['element_id'] = temporal_coverage.id
            temporal_coverage_dict['type'] = temporal_coverage.type
            start_date = parser.parse(temporal_coverage.value['start'])
            end_date = parser.parse(temporal_coverage.value['end'])
            temporal_coverage_dict['start'] = start_date.strftime('%m-%d-%Y')
            temporal_coverage_dict['end'] = end_date.strftime('%m-%d-%Y')
        return temporal_coverage_dict
