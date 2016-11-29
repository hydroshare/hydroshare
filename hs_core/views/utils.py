from __future__ import absolute_import

import json
import os
import string
from collections import namedtuple
import paramiko
import logging

from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import UploadedFile
from django.utils.http import int_to_base36

from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from mezzanine.utils.email import subject_template, default_token_generator, send_mail_template
from mezzanine.utils.urls import next_url
from mezzanine.conf import settings

from ga_resources.utils import get_user

from hs_core import hydroshare
from hs_core.hydroshare import check_resource_type, delete_resource_file
from hs_core.models import AbstractMetaDataElement, GenericResource, Relation, ResourceFile
from hs_core.signals import pre_metadata_element_create, post_delete_file_from_resource, \
    pre_move_or_rename_file_or_folder
from hs_core.hydroshare import FILE_SIZE_LIMIT
from hs_core.hydroshare.utils import raise_file_size_exception, get_file_mime_type
from django_irods.storage import IrodsStorage
from hs_access_control.models import PrivilegeCodes

ActionToAuthorize = namedtuple('ActionToAuthorize',
                               'VIEW_METADATA, '
                               'VIEW_RESOURCE, '
                               'EDIT_RESOURCE, '
                               'SET_RESOURCE_FLAG, '
                               'DELETE_RESOURCE, '
                               'CREATE_RESOURCE_VERSION')
ACTION_TO_AUTHORIZE = ActionToAuthorize(0, 1, 2, 3, 4, 5)


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
        if size > FILE_SIZE_LIMIT:
            raise_file_size_exception()
        tmpFile = irods_storage.download(ifname)
        fname = os.path.basename(ifname.rstrip(os.sep))
        res_files.append(UploadedFile(file=tmpFile, name=fname, size=size))

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


def validate_user_name(user_name):
    if not User.objects.filter(username=user_name).exists():
        raise ValidationError(detail='No user found for user name:%s' % user_name)


def validate_group_name(group_name):
    if not Group.objects.filter(name=group_name).exists():
        raise ValidationError(detail='No group found for group name:%s' % group_name)


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
        self.POST = element_data_dict


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
    # get a list of resources with effective CHANGE privilege
    editable_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
    # remove obsoleted resources from the editable_resources
    editable_resources = editable_resources.exclude(object_id__in=Relation.objects.filter(
        type='isReplacedBy').values('object_id'))
    # get a list of resources with effective VIEW privilege
    viewable_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
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


def link_irods_file_to_django(resource, filename, size=0):
    # link the newly created zip file to Django resource model
    b_add_file = False
    if resource:
        if resource.resource_federation_path:
            if not ResourceFile.objects.filter(object_id=resource.id,
                                               fed_resource_file_name_or_path=filename).exists():
                ResourceFile.objects.create(content_object=resource,
                                            resource_file=None,
                                            fed_resource_file_name_or_path=filename,
                                            fed_resource_file_size=size)
                b_add_file = True

        elif not ResourceFile.objects.filter(object_id=resource.id,
                                             resource_file=filename).exists():
                ResourceFile.objects.create(content_object=resource,
                                            resource_file=filename)
                b_add_file = True

        if b_add_file:
            file_format_type = get_file_mime_type(filename)
            if file_format_type not in [mime.value for mime in resource.metadata.formats.all()]:
                resource.metadata.create_element('format', value=file_format_type)


def link_irods_folder_to_django(resource, istorage, foldername, exclude=()):
    """
    Recursively Link irods folder and all files and sub-folders inside the folder to Django
    Database after iRODS file and folder operations to get Django and iRODS in sync
    :param resource: the BaseResource object representing a HydroShare resource
    :param istorage: IrodsStorage object
    :param foldername: the folder name
    :param exclude: a tuple that includes file names to be excluded from linking under the folder;
     default is empty meaning nothing is excluded.
    :return:
    """
    if resource and istorage and foldername:
        store = istorage.listdir(foldername)
        # add files into Django resource model
        for file in store[1]:
            if file not in exclude:
                file_path = os.path.join(foldername, file)
                size = istorage.size(file_path)
                link_irods_file_to_django(resource, file_path, size)
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
    """
    if resource.resource_federation_path:
        res_file_obj = ResourceFile.objects.filter(object_id=resource.id,
                                                   fed_resource_file_name_or_path=src_name)
        if res_file_obj.exists():
            # src_name and tgt_name are file names - replace src_name with tgt_name
            res_file_obj[0].fed_resource_file_name_or_path = tgt_name
            res_file_obj[0].mime_type = get_file_mime_type(
                res_file_obj[0].fed_resource_file_name_or_path)
            res_file_obj[0].save()
        else:
            # src_name and tgt_name are folder names
            res_file_objs = \
                ResourceFile.objects.filter(object_id=resource.id,
                                            fed_resource_file_name_or_path__contains=src_name)
            for fobj in res_file_objs:
                old_str = fobj.fed_resource_file_name_or_path
                new_str = old_str.replace(src_name, tgt_name)
                fobj.fed_resource_file_name_or_path = new_str
                fobj.mime_type = get_file_mime_type(fobj.fed_resource_file_name_or_path)
                fobj.save()
    else:
        res_file_obj = ResourceFile.objects.filter(object_id=resource.id,
                                                   resource_file=src_name)
        if res_file_obj.exists():
            # src_name and tgt_name are file names
            # since resource_file is a FileField which cannot be directly renamed,
            # this old ResourceFile object has to be deleted followed by creation of
            # a new ResourceFile with new file associated that replace the old one
            logical_file = res_file_obj[0].logical_file if res_file_obj[0].has_logical_file else None

            res_file_obj[0].delete()
            res_file = ResourceFile.objects.create(content_object=resource, resource_file=tgt_name)
            res_file.mime_type = get_file_mime_type(res_file.resource_file.name)
            if logical_file is not None:
                res_file.logical_file_content_object = logical_file
            res_file.save()

        else:
            # src_name and tgt_name are folder names
            res_file_objs = \
                ResourceFile.objects.filter(object_id=resource.id,
                                            resource_file__contains=src_name)
            for fobj in res_file_objs:
                old_str = fobj.resource_file.name
                new_str = old_str.replace(src_name, tgt_name)
                logical_file = fobj.logical_file if fobj.has_logical_file else None
                fobj.delete()
                res_file = ResourceFile.objects.create(content_object=resource,
                                                       resource_file=new_str)
                res_file.mime_type = get_file_mime_type(res_file.resource_file.name)
                if logical_file is not None:
                    res_file.logical_file_content_object = logical_file
                res_file.save()


def remove_irods_folder_in_django(resource, istorage, foldername, user):
    """
    Remove all files inside a folder in Django DB after the folder is removed from iRODS
    :param resource: the BaseResource object representing a HydroShare resource
    :param istorage: IrodsStorage object
    :param foldername: the folder name that has been removed from iRODS
    :user  user who initiated the folder delete operation
    :return:
    """
    if resource and istorage and foldername:
        if not foldername.endswith('/'):
            foldername += '/'
        if resource.resource_federation_path:
            res_file_set = ResourceFile.objects.filter(
                object_id=resource.id, fed_resource_file_name_or_path__icontains=foldername)
        else:
            res_file_set = ResourceFile.objects.filter(
                object_id=resource.id, resource_file__icontains=foldername)

        # delete all uniqie logicalfiles associated with all resource files to be deleted
        # from django as they need to be deleted differently
        logical_files = list(set([f.logical_file for f in res_file_set if f.has_logical_file]))
        for lf in logical_files:
            lf.logical_delete(user, delete_res_files=False)

        # delete resource file objects
        for f in res_file_set:
            filename = hydroshare.get_resource_file_name(f)
            f.delete()
            hydroshare.delete_format_metadata_after_delete_file(resource, filename)

        # send the signal
        post_delete_file_from_resource.send(sender=resource.__class__, resource=resource)


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
    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    istorage = resource.get_irods_storage()
    if resource.resource_federation_path:
        res_coll_input = os.path.join(resource.resource_federation_path, res_id, input_coll_path)
    else:
        res_coll_input = os.path.join(res_id, input_coll_path)

    content_dir = os.path.dirname(res_coll_input)
    output_zip_full_path = os.path.join(content_dir, output_zip_fname)
    istorage.session.run("ibun", None, '-cDzip', '-f', output_zip_full_path, res_coll_input)
    output_zip_size = istorage.size(output_zip_full_path)

    link_irods_file_to_django(resource, output_zip_full_path, output_zip_size)

    if bool_remove_original:
        for f in ResourceFile.objects.filter(object_id=resource.id):
            full_path_name, basename, _ = \
                hydroshare.utils.get_resource_file_name_and_extension(f)
            if res_coll_input in full_path_name and output_zip_full_path not in full_path_name:
                delete_resource_file(res_id, basename, user)

        # remove empty folder in iRODS
        istorage.delete(res_coll_input)

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
    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    istorage = resource.get_irods_storage()
    if resource.resource_federation_path:
        zip_with_full_path = os.path.join(resource.resource_federation_path, res_id,
                                          zip_with_rel_path)
    else:
        zip_with_full_path = os.path.join(res_id, zip_with_rel_path)

    unzip_path = os.path.dirname(zip_with_full_path)
    zip_fname = os.path.basename(zip_with_rel_path)
    istorage.session.run("ibun", None, '-xDzip', zip_with_full_path, unzip_path)
    link_irods_folder_to_django(resource, istorage, unzip_path, (zip_fname,))

    if bool_remove_original:
        delete_resource_file(res_id, zip_fname, user)

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
    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    istorage = resource.get_irods_storage()
    if resource.resource_federation_path:
        coll_path = os.path.join(resource.resource_federation_path, res_id, folder_path)
    else:
        coll_path = os.path.join(res_id, folder_path)

    # TODO: (Pabitra) handle this in a signal handler in composite resource
    if resource.resource_type == "CompositeResource":
        path_parts = coll_path.split("/")
        # remove the new folder name from the path
        path_parts = path_parts[:-1]
        path_to_check = "/".join(path_parts)
        err_msg = "Folder creation not allowed here."
        if resource.resource_federation_path:
            res_file_objs = resource.files.filter(
                object_id=resource.id,
                fed_resource_file_name_or_path__contains=path_to_check).all()
        else:
            res_file_objs = resource.files.filter(object_id=resource.id,
                                                  resource_file__contains=path_to_check).all()
        for res_file_obj in res_file_objs:
            if not res_file_obj.logical_file.allow_resource_file_rename or \
                    not res_file_obj.logical_file.allow_resource_file_move:
                raise ValidationError(err_msg)

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
    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    istorage = resource.get_irods_storage()
    if resource.resource_federation_path:
        coll_path = os.path.join(resource.resource_federation_path, res_id, folder_path)
    else:
        coll_path = os.path.join(res_id, folder_path)

    istorage.delete(coll_path)

    remove_irods_folder_in_django(resource, istorage, coll_path, user)

    if resource.raccess.public or resource.raccess.discoverable:
        if not resource.can_be_public_or_discoverable:
            resource.raccess.public = False
            resource.raccess.discoverable = False
            resource.raccess.save()

    hydroshare.utils.resource_modified(resource, user, overwrite_bag=False)


def move_or_rename_file_or_folder(user, res_id, src_path, tgt_path, validate_move_rename=True):
    """
    Move or rename a file or folder in hydroshareZone or any federated zone used for HydroShare
    resource backend store.
    :param user: requesting user
    :param res_id: resource uuid
    :param src_path: the relative paths for the source file or folder under res_id collection
    :param tgt_path: the relative paths for the target file or folder under res_id collection
    :param validate_move_rename: if True, then signal is sent for resource type to check if
    move/rename is allowed or not.
    :return:
    """
    resource = hydroshare.utils.get_resource_by_shortkey(res_id)
    istorage = resource.get_irods_storage()
    if resource.resource_federation_path:
        src_full_path = os.path.join(resource.resource_federation_path, res_id, src_path)
        tgt_full_path = os.path.join(resource.resource_federation_path, res_id, tgt_path)
    else:
        src_full_path = os.path.join(res_id, src_path)
        tgt_full_path = os.path.join(res_id, tgt_path)

    tgt_file_name = os.path.basename(tgt_full_path)
    tgt_file_dir = os.path.dirname(tgt_full_path)
    src_file_name = os.path.basename(src_full_path)
    src_file_dir = os.path.dirname(src_full_path)

    # ensure the target_full_path contains the file name to be moved or renamed to
    if src_file_dir != tgt_file_dir and tgt_file_name != src_file_name:
        tgt_full_path = os.path.join(tgt_full_path, src_file_name)

    if validate_move_rename:
        # this must raise ValidationError if move/rename is not allowed by specific resource type
        pre_move_or_rename_file_or_folder.send(sender=resource.__class__, resource=resource,
                                               src_full_path=src_full_path,
                                               tgt_full_path=tgt_full_path)

    istorage.moveFile(src_full_path, tgt_full_path)

    rename_irods_file_or_folder_in_django(resource, src_full_path, tgt_full_path)

    hydroshare.utils.resource_modified(resource, user, overwrite_bag=False)
