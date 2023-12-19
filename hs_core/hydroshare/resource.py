import os
import zipfile
import shutil
import logging
import requests
import datetime
from dateutil import tz

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.contrib.auth.models import User

from rest_framework import status

from hs_core.hydroshare import hs_bagit
from hs_core.models import ResourceFile
from hs_core import signals
from hs_core.hydroshare import utils
from hs_access_control.models import ResourceAccess, UserResourcePrivilege, PrivilegeCodes
from hs_labels.models import ResourceLabels
from theme.models import UserQuota
from django_irods.icommands import SessionException
from django_irods.storage import IrodsStorage


FILE_SIZE_LIMIT = 1 * (1024 ** 3)
FILE_SIZE_LIMIT_FOR_DISPLAY = '1G'
METADATA_STATUS_SUFFICIENT = 'Sufficient to publish or make public'
METADATA_STATUS_INSUFFICIENT = 'Insufficient to publish or make public'

logger = logging.getLogger(__name__)


def get_quota_usage_from_irods(username):
    """
    Query iRODS AVU to get quota usage for a user reported in iRODS quota microservices
    :param username: the user name to get quota usage for.
    :return: the combined quota usage from iRODS data zone and user zone; raise ValidationError
    if quota usage cannot be retrieved from iRODS
    """
    attname = username + '-usage'
    istorage = IrodsStorage()
    # get quota size for user in iRODS data zone by retrieving AVU set on irods bagit path
    # collection
    try:
        uqDataZoneSize = istorage.getAVU(settings.IRODS_BAGIT_PATH, attname)
        if uqDataZoneSize is None:
            # user may not have resources in data zone, so corresponding quota size AVU may not
            # exist for this user
            uqDataZoneSize = -1
        else:
            uqDataZoneSize = float(uqDataZoneSize)
    except SessionException:
        # user may not have resources in data zone, so corresponding quota size AVU may not exist
        # for this user
        uqDataZoneSize = -1

    # get quota size for the user in iRODS user zone
    try:
        uz_bagit_path = os.path.join('/', settings.HS_USER_IRODS_ZONE, 'home',
                                     settings.HS_IRODS_PROXY_USER_IN_USER_ZONE,
                                     settings.IRODS_BAGIT_PATH)
        uqUserZoneSize = istorage.getAVU(uz_bagit_path, attname)
        if uqUserZoneSize is None:
            # user may not have resources in user zone, so corresponding quota size AVU may not
            # exist for this user
            uqUserZoneSize = -1
        else:
            uqUserZoneSize = float(uqUserZoneSize)
    except SessionException:
        # user may not have resources in user zone, so corresponding quota size AVU may not exist
        # for this user
        uqUserZoneSize = -1

    if uqDataZoneSize < 0 and uqUserZoneSize < 0:
        err_msg = 'no quota size AVU in data zone and user zone for user {}'.format(username)
        logger.error(err_msg)
        raise ValidationError(err_msg)
    elif uqUserZoneSize < 0:
        used_val = uqDataZoneSize
    elif uqDataZoneSize < 0:
        used_val = uqUserZoneSize
    else:
        used_val = uqDataZoneSize + uqUserZoneSize
    return used_val


def update_quota_usage(username):
    """
    update quota usage by checking iRODS AVU to get the updated quota usage for the user. Note iRODS micro-service
    quota update only happens on HydroShare iRODS data zone and user zone independently, so the aggregation of usage
    in both zones need to be accounted for in this function to update Django DB as an aggregated usage for hydroshare
    internal zone.
    :param
    username: the name of the user that needs to update quota usage for.
    :return: raise ValidationError if quota cannot be updated.
    """
    hs_internal_zone = "hydroshare"
    uq = UserQuota.objects.filter(user__username=username, zone=hs_internal_zone).first()
    # tlogger = logging.getLogger("django.timer")
    # tlogger.info(f"Usage before: {uq.used_value}")
    if uq is None:
        # the quota row does not exist in Django
        err_msg = 'quota row does not exist in Django for hydroshare zone for user {}'.format(username)
        logger.error(err_msg)
        raise ValidationError(err_msg)

    used_val = get_quota_usage_from_irods(username)
    uq.update_used_value(used_val)
    # tlogger.info(f"Usage after: {uq.used_value}")


def res_has_web_reference(res):
    """
    Check whether a resource includes web reference url file.
    :param res: resource object
    :return: True if yes, False otherwise
    """
    if res.resource_type != "CompositeResource":
        return False

    for lf in res.get_logical_files('GenericLogicalFile'):
        if 'url' in lf.extra_data:
            return True
    return False


def get_science_metadata(pk):
    """
    Describes the resource identified by the pid by returning the associated science metadata
    object (xml+rdf string). If the resource does not exist, Exceptions.NotFound must be raised.

    REST URL:  GET /scimeta/{pid}

    Parameters:    pk  - Unique HydroShare identifier for the resource whose science metadata is to
    be retrieved.

    Returns:    Science metadata document describing the resource.

    Return Type:    xml+rdf string

    Raises:    Exceptions.NotAuthorized -  The user is not authorized
    Exceptions.NotFound  - The resource identified by pid does not exist
    Exception.ServiceFailure  - The service is unable to process the request
    """
    res = utils.get_resource_by_shortkey(pk)
    return res.metadata.get_xml()


def get_capabilities(pk):
    """
    Describes API services exposed for a resource.  If there are extra capabilites for a particular
    resource type over and above the standard Hydroshare API, then this API call will list these

    REST URL: GET /capabilites/{pid}

    Parameters: Unique HydroShare identifier for the resource whose capabilites are to be retrieved.

    Return Type: Capabilites

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request
    """
    res = utils.get_resource_by_shortkey(pk)
    return getattr(res, 'extra_capabilities', lambda: None)()


def get_resource_file(pk, filename):
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
    Exceptions.NotFound - The resource identified does not exist or the file identified by filename
    does not exist
    Exception.ServiceFailure - The service is unable to process the request
    """
    resource = utils.get_resource_by_shortkey(pk)
    filename = filename.strip("/")
    if not filename.startswith("data/contents/"):
        filename = os.path.join("data", "contents", filename)
    for f in ResourceFile.objects.filter(object_id=resource.id):
        if f.resource_file.name.endswith(filename):
            return f
    raise ObjectDoesNotExist(filename)


def update_resource_file(pk, filename, f):
    """
    Called by clients to update an individual file within a HydroShare resource.

    REST URL:  PUT /resource/{pid}/files/{filename}

    Parameters:
    pid - Unique HydroShare identifier for the resource from which the file will be extracted.
    filename - The data bytes of the file that will be extracted from the resource identified by pid
    file - the data bytes of the file to update

    Returns: The bytes of the file extracted from the resource

    Return Type:    pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified does not exist or the file identified by filename
    does not exist
    Exception.ServiceFailure - The service is unable to process the request
    """
    # TODO: does not update metadata; does not check resource state
    resource = utils.get_resource_by_shortkey(pk)
    for rf in ResourceFile.objects.filter(object_id=resource.id):
        if rf.short_path == filename:
            if rf.resource_file:
                # TODO: should use delete_resource_file
                rf.resource_file.delete()
                # TODO: should use add_file_to_resource
                rf.resource_file = File(f) if not isinstance(f, UploadedFile) else f
                rf.save()
            if rf.fed_resource_file:
                # TODO: should use delete_resource_file
                rf.fed_resource_file.delete()
                # TODO: should use add_file_to_resource
                rf.fed_resource_file = File(f) if not isinstance(f, UploadedFile) else f
                rf.save()
            return rf
    raise ObjectDoesNotExist(filename)


def get_related(pk):
    """
    Returns a list of pids for resources that are related to the resource identified by the
    specified pid.

    REST URL:  GET /related/{pid}

    Parameters:
    pid - Unique HydroShare identifier for the resource whose related resources are to be retrieved.

    Returns:    List of pids for resources that are related to the specified resource.

    Return Type:    List of pids

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request


    """
    raise NotImplementedError()


def get_checksum(pk):
    """
    Returns a checksum for the specified resource using the MD5 algorithm. The result is used to
    determine if two instances referenced by a pid are identical.

    REST URL:  GET /checksum/{pid}

    Parameters:
    pid - Unique HydroShare identifier for the resource for which the checksum is to be returned.

    Returns:    Checksum of the resource identified by pid.

    Return Type:    Checksum

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource specified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request
    """
    raise NotImplementedError()


def check_resource_files(files=()):
    """
    internally used method to check whether the uploaded files are within
    the supported maximal size limit. Also returns sum size of all files for
    quota check purpose if all files are within allowed size limit

    Parameters:
    files - list of Django File or UploadedFile objects to be attached to the resource
    Returns: (status, sum_size) tuple where status is True if files are within FILE_SIZE_LIMIT
             and False if not, and sum_size is the size summation over all files if status is
             True, and -1 if status is False
    """
    sum = 0
    for file in files:
        if not isinstance(file, UploadedFile):
            # if file is already on the server, e.g., a file transferred directly from iRODS,
            # the file should not be subject to file size check since the file size check is
            # only prompted by file upload limit
            if hasattr(file, '_size'):
                sum += int(file._size)
            elif hasattr(file, 'size'):
                sum += int(file.size)
            else:
                try:
                    size = os.stat(file).st_size
                except (TypeError, OSError):
                    size = 0
                sum += size
            continue
        if hasattr(file, '_size') and file._size is not None:
            size = int(file._size)
        elif hasattr(file, 'size') and file.size is not None:
            size = int(file.size)
        else:
            try:
                size = int(os.stat(file.name).st_size)
            except (TypeError, OSError):
                size = 0
        sum += size
        if size > FILE_SIZE_LIMIT:
            # file is greater than FILE_SIZE_LIMIT, which is not allowed
            return False, -1

    return True, sum


def check_resource_type(resource_type):
    """
    internally used method to check the resource type

    Parameters:
    resource_type: the resource type string to check
    Returns:  the resource type class matching the resource type string; if no match is found,
    returns None
    """
    for tp in utils.get_resource_types():
        if resource_type == tp.__name__:
            res_cls = tp
            break
    else:
        raise NotImplementedError("Type {resource_type} does not exist".format(
            resource_type=resource_type))
    return res_cls


def add_zip_file_contents_to_resource_async(resource, f):
    """
    Launch asynchronous celery task to add zip file contents to a resource.
    Note: will copy the zip file into a temporary space accessible to both
    the Django server and the Celery worker.
    :param resource: Resource to which file should be added
    :param f: TemporaryUploadedFile object (or object that implements temporary_file_path())
     representing a zip file whose contents are to be added to a resource.
    """
    # Add contents of zipfile asynchronously; wait 30 seconds to be "sure" that resource creation
    # has finished.
    uploaded_filepath = f.temporary_file_path()
    tmp_dir = getattr(settings, 'HYDROSHARE_SHARED_TEMP', '/shared_tmp')
    logger.debug("Copying uploaded file from {0} to {1}".format(uploaded_filepath,
                                                                tmp_dir))
    shutil.copy(uploaded_filepath, tmp_dir)
    zfile_name = os.path.join(tmp_dir, os.path.basename(uploaded_filepath))
    logger.debug("Retained upload as {0}".format(zfile_name))
    # Import here to avoid circular reference
    from hs_core.tasks import add_zip_file_contents_to_resource
    add_zip_file_contents_to_resource.apply_async((resource.short_id, zfile_name),
                                                  countdown=30)
    resource.file_unpack_status = 'Pending'
    resource.save()


def create_resource(
        resource_type, owner, title,
        edit_users=None, view_users=None, edit_groups=None, view_groups=None,
        keywords=(), metadata=None, extra_metadata=None,
        files=(), create_metadata=True, create_bag=False, unpack_file=False, full_paths={},
        auto_aggregate=True, **kwargs):
    """
    Called by a client to add a new resource to HydroShare. The caller must have authorization to
    write content to HydroShare. The pid for the resource is assigned by HydroShare upon inserting
    the resource.  The create method returns the newly-assigned pid.

    REST URL:  POST /resource

    Parameters:

    Returns:    The newly created resource

    Return Type:    BaseResource resource object

    Note:  The calling user will automatically be set as the owner of the created resource.

    Implementation notes:

    1. pid is called short_id.  This is because pid is a UNIX term for Process ID and could be
    confusing.

    2. return type is an instance of hs_core.models.BaseResource class. This is for efficiency in
    the native API.  The native API should return actual instance rather than IDs wherever possible
    to avoid repeated lookups in the database when they are unnecessary.

    3. resource_type is a string: see parameter list

    :param resource_type: string. the type of the resource such as CompositeResource
    :param owner: email address, username, or User instance. The owner of the resource
    :param title: string. the title of the resource
    :param edit_users: list of email addresses, usernames, or User instances who will be given edit
    permissions
    :param view_users: list of email addresses, usernames, or User instances who will be given view
    permissions
    :param edit_groups: list of group names or Group instances who will be given edit permissions
    :param view_groups: list of group names or Group instances who will be given view permissions
    :param keywords: string list. list of keywords to add to the resource
    :param metadata: list of dicts containing keys (element names) and corresponding values as
    dicts { 'creator': {'name':'John Smith'}}.
    :param extra_metadata: one dict containing keys and corresponding values
         { 'Outlet Point Latitude': '40', 'Outlet Point Longitude': '-110'}.
    :param files: list of Django File or UploadedFile objects to be attached to the resource
    :param create_bag: whether to create a bag for the newly created resource or not.
        By default, the bag is created.
    :param unpack_file: boolean.  If files contains a single zip file, and unpack_file is True,
        the unpacked contents of the zip file will be added to the resource instead of the zip file.
    :param full_paths: Optional.  A map of paths keyed by the correlating resource file.  When
        this parameter is provided, a file will be placed at the path specified in the map.
    :param auto_aggregate: boolean, defaults to True.  Find and create aggregations during
        resource creation.
    :param kwargs: extra arguments to fill in required values in AbstractResource subclasses

    :return: a new resource which is an instance of BaseResource with specified resource_type.
    """

    with transaction.atomic():
        cls = check_resource_type(resource_type)
        owner = utils.user_from_id(owner)

        # get the metadata class specific to resource type to set resource
        # content_object (metadata) attribute
        metadata_class = cls.get_metadata_class()
        metadata_obj = metadata_class()
        metadata_obj.save()

        # create the resource
        resource = cls.objects.create(
            resource_type=resource_type,
            user=owner,
            creator=owner,
            title=title,
            last_changed_by=owner,
            in_menus=[],
            content_object=metadata_obj,
            **kwargs
        )

        resource.resource_type = resource_type

        # by default make resource private
        resource.slug = 'resource{0}{1}'.format('/', resource.short_id)
        resource.save(update_fields=["slug", "resource_type"])

        if not metadata:
            metadata = []

        if extra_metadata is not None:
            resource.extra_metadata = extra_metadata
            resource.save()

        # by default resource is private
        resource_access = ResourceAccess(resource=resource)
        resource_access.save()
        resource.raccess = resource_access
        # use the built-in share routine to set initial provenance.
        UserResourcePrivilege.share(resource=resource, grantor=owner, user=owner,
                                    privilege=PrivilegeCodes.OWNER)

        resource_labels = ResourceLabels(resource=resource)
        resource_labels.save()

        if edit_users:
            for user in edit_users:
                user = utils.user_from_id(user)
                owner.uaccess.share_resource_with_user(resource, user, PrivilegeCodes.CHANGE)

        if view_users:
            for user in view_users:
                user = utils.user_from_id(user)
                owner.uaccess.share_resource_with_user(resource, user, PrivilegeCodes.VIEW)

        if edit_groups:
            for group in edit_groups:
                group = utils.group_from_id(group)
                owner.uaccess.share_resource_with_group(resource, group, PrivilegeCodes.CHANGE)

        if view_groups:
            for group in view_groups:
                group = utils.group_from_id(group)
                owner.uaccess.share_resource_with_group(resource, group, PrivilegeCodes.VIEW)

        # set quota of this resource to this creator
        # quota holder has to be set before the files are added in order for real time iRODS
        # quota micro-services to work
        resource.set_quota_holder(owner, owner)

        if create_metadata:
            # prepare default metadata
            utils.prepare_resource_default_metadata(resource=resource, metadata=metadata,
                                                    res_title=title)

            for element in metadata:
                # here k is the name of the element
                # v is a dict of all element attributes/field names and field values
                k, v = list(element.items())[0]
                resource.metadata.create_element(k, **v)

            for keyword in keywords:
                resource.metadata.create_element('subject', value=keyword)

            resource.title = resource.metadata.title.value
            resource.save(update_fields=["title"])

        if len(files) == 1 and unpack_file and zipfile.is_zipfile(files[0]):
            # Add contents of zipfile as resource files asynchronously
            # Note: this is done asynchronously as unzipping may take
            # a long time (~15 seconds to many minutes).
            add_zip_file_contents_to_resource_async(resource, files[0])
        elif len(files) > 0:
            # Add resource file(s) now
            # Note: this is done synchronously as it should only take a
            # few seconds.  We may want to add the option to do this
            # asynchronously if the file size is large and would take
            # more than ~15 seconds to complete.
            add_resource_files(resource.short_id, *files, full_paths=full_paths,
                               auto_aggregate=auto_aggregate, resource=resource)
        else:
            utils.create_empty_contents_directory(resource)

        if create_bag:
            hs_bagit.create_bag(resource)

    # set the resource to private
    resource.setAVU('isPublic', resource.raccess.public)

    # set the resource type (which is immutable)
    resource.setAVU("resourceType", resource._meta.object_name)

    return resource


def create_empty_resource(pk, user_or_username, action='version'):
    """
    Create a resource with empty content and empty metadata for resource versioning or copying.
    This empty resource object is then used to create metadata and content from its original
    resource. This separate routine is needed to return a new resource object to the calling
    view so that if an exception is raised, this empty resource object can be deleted for clean-up.
    Args:
        pk: the unique HydroShare identifier for the resource that is to be versioned or copied.
        user: the user who requests to create a new version for the resource or copy the resource.
        action: "version" or "copy" with default action being "version"
    Returns:
        the empty new resource that is created as an initial new version or copy for the original
        resource which is then further populated with metadata and content in a subsequent step.
    """
    res = utils.get_resource_by_shortkey(pk)
    if isinstance(user_or_username, User):
        user = user_or_username
    else:
        user = User.objects.get(username=user_or_username)
    if action == 'version':
        if not user.uaccess.owns_resource(res):
            raise PermissionDenied('Only resource owners can create new versions')
    elif action == 'copy':
        # import here to avoid circular import
        from hs_core.views.utils import rights_allows_copy
        if not user.uaccess.can_view_resource(res):
            raise PermissionDenied('You do not have permission to view this resource')
        allow_copy = rights_allows_copy(res, user)
        if not allow_copy:
            raise PermissionDenied('The license for this resource does not permit copying')
    else:
        raise ValidationError('Input parameter error: action needs to be version or copy')

    # create the resource without files and without creating bags first
    new_resource = create_resource(
        resource_type=res.resource_type,
        owner=user,
        title=res.metadata.title.value,
        create_metadata=False,
        create_bag=False
    )
    return new_resource


def copy_resource(ori_res, new_res, user=None):
    """
    Populate metadata and contents from ori_res object to new_res object to make new_res object
    as a copy of the ori_res object
    Args:
        ori_res: the original resource that is to be copied.
        new_res: the new_res to be populated with metadata and content from the original resource
        as a copy of the original resource.
        user: requesting user for the copy action. It is optional, if being passed in, quota is
        counted toward the user; otherwise, quota is not counted toward that user
    Returns:
        the new resource copied from the original resource
    """

    from hs_core.tasks import copy_resource_task
    if user:
        copy_resource_task(ori_res.short_id, new_res.short_id, request_username=user.username)
    else:
        copy_resource_task(ori_res.short_id, new_res.short_id)
    # cannot directly return the new_res object being passed in, but rather return the new resource object being copied
    return utils.get_resource_by_shortkey(new_res.short_id)


def create_new_version_resource(ori_res, new_res, user):
    """
    Populate metadata and contents from ori_res object to new_res object to make new_res object as
    a new version of the ori_res object
    Args:
        ori_res: the original resource that is to be versioned.
        new_res: the new_res to be populated with metadata and content from the original resource
        to make it a new version
        user: the requesting user
    Returns:
        the new versioned resource for the original resource and thus obsolete the original resource

    """
    from hs_core.tasks import create_new_version_resource_task
    if ori_res.locked_time:
        # cannot create new version for this resource since the resource is locked by another user
        raise utils.ResourceVersioningException('Failed to create a new version for this resource '
                                                'since another user is creating a new version for '
                                                'this resource synchronously.')
    # lock the resource to prevent concurrent new version creation since only one new version for an
    # obsoleted resource is allowed
    ori_res.locked_time = datetime.datetime.now(tz.UTC)
    ori_res.save()
    create_new_version_resource_task(ori_res.short_id, user.username, new_res_id=new_res.short_id)
    # cannot directly return the new_res object being passed in, but rather return the new versioned resource object
    return utils.get_resource_by_shortkey(new_res.short_id)


def add_resource_files(pk, *files, **kwargs):
    """
    Called by clients to update a resource in HydroShare by adding one or more files.

    REST URL:  PUT /resource/{pid}/files/{file}

    Parameters:
    pk - Unique HydroShare identifier for the resource that is to be updated.
    files - A list of file-like objects representing files that will be added
    to the existing resource identified by pid

    Returns:    A list of ResourceFile objects added to the resource

    Return Type:    list

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.InvalidContent - The content of the file is invalid
    Exception.ServiceFailure - The service is unable to process the request

    Notes:
    This does **not** handle mutability; changes to immutable resources should be denied elsewhere.

    """
    from hs_core.tasks import set_resource_files_system_metadata

    resource = kwargs.pop("resource", None)
    if resource is None:
        resource = utils.get_resource_by_shortkey(pk)
    uploaded_res_files = []
    source_names = kwargs.pop('source_names', [])
    full_paths = kwargs.pop('full_paths', {})
    auto_aggregate = kwargs.pop('auto_aggregate', True)

    if __debug__:
        assert (isinstance(source_names, list))

    folder = kwargs.pop('folder', '')
    user = kwargs.pop('user', None)

    if __debug__:  # assure that there are no spurious kwargs left.
        for k in kwargs:
            print("kwargs[{}]".format(k))
        assert len(kwargs) == 0

    if resource.raccess.published:
        if user is None or not user.is_superuser:
            raise ValidationError("Only admin can add files to a published resource")

    prefix_path = 'data/contents'
    if folder == prefix_path:
        base_dir = ""
    elif folder.startswith(prefix_path):
        base_dir = folder[len(prefix_path) + 1:]
    else:
        base_dir = folder
    for f in files:
        full_dir = base_dir
        if f in full_paths:
            # TODO, put this in it's own method?
            full_path = full_paths[f]
            dir_name = os.path.dirname(full_path)
            # Only do join if dir_name is not empty, otherwise, it'd result in a trailing slash
            full_dir = os.path.join(base_dir, dir_name) if dir_name else base_dir
        res_file = utils.add_file_to_resource(resource, f, folder=full_dir, user=user, add_to_aggregation=False,
                                              save_file_system_metadata=False)
        uploaded_res_files.append(res_file)

    for ifname in source_names:
        res_file = utils.add_file_to_resource(resource, None, folder=folder, source_name=ifname, user=user,
                                              add_to_aggregation=False,
                                              save_file_system_metadata=False)
        uploaded_res_files.append(res_file)

    if not uploaded_res_files:
        # no file has been added, make sure data/contents directory exists if no file is added
        utils.create_empty_contents_directory(resource)
    else:
        if resource.resource_type == "CompositeResource":
            upload_to_folder = base_dir
            if upload_to_folder:
                aggregations = list(resource.logical_files)
                # check if there is folder based model program or model instance aggregation in the upload path
                aggregation = resource.get_model_aggregation_in_path(upload_to_folder, aggregations=aggregations)
                if aggregation is None:
                    # check if there is a fileset aggregation in the upload path
                    aggregation = resource.get_fileset_aggregation_in_path(upload_to_folder, aggregations=aggregations)
                if aggregation:
                    # Note: we can't use bulk_update here because we need to update the logical_file_content_object
                    # which is not a concrete field in the ResourceFile model
                    for res_file in uploaded_res_files:
                        aggregation.add_resource_file(res_file, set_metadata_dirty=False)

                    aggregation.set_metadata_dirty()
            if auto_aggregate:
                utils.check_aggregations(resource, uploaded_res_files)

        utils.resource_modified(resource, user, overwrite_bag=False)

        # store file level system metadata in Django DB (async task)
        set_resource_files_system_metadata.apply_async((resource.short_id,))

    return uploaded_res_files


def update_science_metadata(pk, metadata, user):
    """
    Updates science metadata for a resource

    Args:
        pk: Unique HydroShare identifier for the resource for which science metadata needs to be
        updated.
        metadata: a list of dictionary items containing data for each metadata element that needs to
        be updated
        user: user who is updating metadata
        example metadata format:
        [
            {'title': {'value': 'Updated Resource Title'}},
            {'description': {'abstract': 'Updated Resource Abstract'}},
            {'date': {'type': 'valid', 'start_date': '1/26/2016', 'end_date': '12/31/2016'}},
            {'creator': {'name': 'John Smith', 'email': 'jsmith@gmail.com'}},
            {'creator': {'name': 'Lisa Molley', 'email': 'lmolley@gmail.com'}},
            {'contributor': {'name': 'Kelvin Marshal', 'email': 'kmarshal@yahoo.com',
                             'organization': 'Utah State University',
                             'profile_links': [{'type': 'yahooProfile', 'url':
                             'http://yahoo.com/LH001'}]}},
            {'coverage': {'type': 'period', 'value': {'name': 'Name for period coverage',
                                                      'start': '1/1/2000',
                                                      'end': '12/12/2012'}}},
            {'coverage': {'type': 'point', 'value': {'name': 'Name for point coverage', 'east':
                                                     '56.45678',
                                                     'north': '12.6789', 'units': 'decimal deg'}}},
            {'identifier': {'name': 'someIdentifier', 'url': "http://some.org/001"}},
            {'language': {'code': 'fre'}},
            {'relation': {'type': 'isPartOf', 'value': 'http://hydroshare.org/resource/001'}},
            {'rights': {'statement': 'This is the rights statement for this resource',
                        'url': 'http://rights.ord/001'}},
            {'subject': {'value': 'sub-1'}},
            {'subject': {'value': 'sub-2'}},
        ]

    Returns:
    """
    resource = utils.get_resource_by_shortkey(pk)
    resource.metadata.update(metadata, user)
    utils.resource_modified(resource, user, overwrite_bag=False)

    # set to private if metadata has become non-compliant
    resource.update_public_and_discoverable()  # set to False if necessary


def delete_resource(pk, request_username=None):
    """
    Deletes a resource managed by HydroShare. The caller must be an owner of the resource or an
    administrator to perform this function. The operation removes the resource from further
    interaction with HydroShare services and interfaces. The implementation may delete the resource
    bytes, and should do so since a delete operation may be in response to a problem with the
    resource (e.g., it contains malicious content, is inappropriate, or is subject to a legal
    request). If the resource does not exist, the Exceptions.NotFound exception is raised.

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

    Note:  Only HydroShare administrators will be able to delete formally published resource
    """
    from hs_core.tasks import delete_resource_task
    resource = utils.get_resource_by_shortkey(pk)
    resource.set_discoverable(False)
    delete_resource_task(pk, request_username)

    return pk


def get_resource_file_name(f):
    """
    get the file name of a specific ResourceFile object f
    Args:
        f: the ResourceFile object to return name for
    Returns:
        the file name of the ResourceFile object f
    """
    return f.storage_path


def delete_resource_file_only(resource, f):
    """
    Delete the single resource file f from the resource without sending signals and
    without deleting related metadata element. This function is called by delete_resource_file()
    function as well as from pre-delete signal handler for specific resource types
    (e.g., netCDF, raster, and feature) where when one resource file is deleted,
    some other resource files needs to be deleted as well.
    Args:
        resource: the resource from which the file f is to be deleted
        f: the ResourceFile object to be deleted
    Returns: unqualified relative path to file that has been deleted
    """
    short_path = f.get_short_path(resource)
    f.delete()
    return short_path


def delete_format_metadata_after_delete_file(resource, file_name):
    """
    delete format metadata as appropriate after a file is deleted.
    :param resource: BaseResource object representing a HydroShare resource
    :param file_name: name of the file that got deleted
    :return:
    """
    delete_file_mime_type = utils.get_file_mime_type(file_name)
    delete_file_extension = os.path.splitext(file_name)[1]

    # if there is no other resource file with the same extension as the
    # file just deleted then delete the matching format metadata element for the resource
    resource_file_extensions = {os.path.splitext(f.get_short_path(resource))[1] for f in
                                resource.files.all()}
    if delete_file_extension not in resource_file_extensions:
        resource.metadata.formats.filter(value=delete_file_mime_type).delete()


# TODO: Remove option for file id, not needed since names are unique.
# TODO: Test that short_path deletes properly.
def delete_resource_file(pk, filename_or_id, user, delete_logical_file=True):
    """
    Deletes an individual file from a HydroShare resource. If the file does not exist,
    the Exceptions.NotFound exception is raised.

    REST URL:  DELETE /resource/{pid}/files/{filename}

    Parameters:
    :param pk: The unique HydroShare identifier for the resource from which the file will be deleted
    :param filename_or_id: Name of the file or id of the file to be deleted from the resource
    :param user: requesting user
    :param delete_logical_file: If True then if the ResourceFile object to be deleted is part of a
    LogicalFile object then the LogicalFile object will be deleted which deletes all associated
    ResourceFile objects and file type metadata objects.

    :returns:    The name or id of the file which was deleted

    Return Type:    string or integer

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist or the file identified by
    file does not exist
    Exception.ServiceFailure - The service is unable to process the request

    Note:  This does not handle immutability as previously intended.
    """
    resource = utils.get_resource_by_shortkey(pk)
    if resource.raccess.published:
        if resource.files.count() == 1:
            raise ValidationError("Resource file delete is not allowed. Published resource must contain at "
                                  "least one file")
        elif not user.is_superuser:
            raise ValidationError("Resource file can be deleted only by admin for a published resource")

    res_cls = resource.__class__
    file_by_id = False
    try:
        int(filename_or_id)
        file_by_id = True
    except ValueError:
        pass

    try:
        if file_by_id:
            f = ResourceFile.objects.get(id=filename_or_id)
        else:
            folder, base = os.path.split(filename_or_id)
            f = ResourceFile.get(resource=resource, file=base, folder=folder)
    except ObjectDoesNotExist:
        raise ObjectDoesNotExist(str.format("resource {}, file {} not found",
                                            resource.short_id, filename_or_id))

    if delete_logical_file and f.has_logical_file:
        logical_file = f.logical_file
        if logical_file.can_be_deleted_on_file_delete():
            # logical_delete() calls this function (delete_resource_file())
            # to delete each of its contained ResourceFile objects
            logical_file.logical_delete(user)
            return filename_or_id
        else:
            logical_file.set_metadata_dirty()

    signals.pre_delete_file_from_resource.send(sender=res_cls, file=f,
                                               resource=resource, user=user)

    file_name = delete_resource_file_only(resource, f)

    # This presumes that the file is no longer in django
    delete_format_metadata_after_delete_file(resource, file_name)

    signals.post_delete_file_from_resource.send(sender=res_cls, resource=resource)

    # set to private if necessary -- AFTER post_delete_file handling
    resource.update_public_and_discoverable()  # set to False if necessary

    # generate bag
    utils.resource_modified(resource, user, overwrite_bag=False)

    return filename_or_id


def get_resource_doi(res_id, flag=''):
    doi_str = "https://doi.org/10.4211/hs.{shortkey}".format(shortkey=res_id)
    if flag:
        return "{doi}{append_flag}".format(doi=doi_str, append_flag=flag)
    else:
        return doi_str


def get_activated_doi(doi):
    """
    Get activated DOI with flags removed. The following two flags are appended
    to the DOI string to indicate publication status for internal use:
    'pending' flag indicates the metadata deposition with CrossRef succeeds, but
     pending activation with CrossRef for DOI to take effect.
    'failure' flag indicates the metadata deposition failed with CrossRef due to
    network or system issues with CrossRef

    Args:
        doi: the DOI string with possible status flags appended

    Returns:
        the activated DOI with all flags removed if any
    """
    idx1 = doi.find('pending')
    idx2 = doi.find('failure')
    if idx1 >= 0:
        return doi[:idx1]
    elif idx2 >= 0:
        return doi[:idx2]
    else:
        return doi


def get_crossref_url():
    main_url = 'https://test.crossref.org/'
    if not settings.USE_CROSSREF_TEST:
        main_url = 'https://doi.crossref.org/'
    return main_url


def deposit_res_metadata_with_crossref(res):
    """
    Deposit resource metadata with CrossRef DOI registration agency.
    Args:
        res: the resource object with its metadata to be deposited for publication

    Returns:
        response returned for the metadata deposition request from CrossRef

    """
    xml_file_name = '{uuid}_deposit_metadata.xml'.format(uuid=res.short_id)
    # using HTTP to POST deposit xml file to crossref
    post_data = {
        'operation': 'doMDUpload',
        'login_id': settings.CROSSREF_LOGIN_ID,
        'login_passwd': settings.CROSSREF_LOGIN_PWD
    }
    files = {'file': (xml_file_name, res.get_crossref_deposit_xml())}
    # exceptions will be raised if POST request fails
    main_url = get_crossref_url()
    post_url = '{MAIN_URL}servlet/deposit'.format(MAIN_URL=main_url)
    # TODO turning off verify for crossref until our ssl dependencies are updated
    response = requests.post(post_url, data=post_data, files=files, verify=False)
    return response


def submit_resource_for_review(request, pk):
    """
    Submits a resource for minimum metadata review, prior to publishing.
    The user must be an owner of a resource or an administrator to perform this action.

    Parameters:
        user - requesting user to publish the resource who must be one of the owners of the resource
        pk - Unique HydroShare identifier for the resource to be formally published.

    Returns:    The id of the resource that was published

    Return Type:    string

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request
    and other general exceptions

    """
    from hs_core.views.utils import get_default_support_user

    resource = utils.get_resource_by_shortkey(pk)
    if resource.raccess.published:
        raise ValidationError("This resource is already published")

    if resource.raccess.review_pending:
        raise ValidationError("Metadata review has already been initiated")

    if not resource.can_be_submitted_for_metadata_review:
        raise ValidationError("This resource cannot be submitted for metadata review since "
                              "it does not have required metadata or content files, or it contains "
                              "reference content, or this resource type is not allowed for publication.")

    user_to = get_default_support_user()
    from hs_core.views.utils import send_action_to_take_email
    send_action_to_take_email(request, user=user_to, user_from=request.user,
                              action_type='metadata_review', resource=resource)

    # create review date -- must be before review_pending = True
    resource.metadata.dates.all().filter(type='reviewStarted').delete()
    resource.metadata.create_element('date', type='reviewStarted', start_date=datetime.datetime.now(tz.UTC))

    resource.raccess.review_pending = True
    resource.raccess.immutable = True
    resource.raccess.save()

    # Repair resource and email support user if there are issues
    from hs_core.tasks import repair_resource_before_publication
    repair_resource_before_publication.apply_async((resource.short_id,))


def publish_resource(user, pk):
    """
    Formally publishes a resource in HydroShare. Triggers the creation of a DOI for the resource,
    and triggers the exposure of the resource to the HydroShare DataONE Member Node. The user must
    be an owner of a resource or an administrator to perform this action.

    Parameters:
        user - requesting user to publish the resource who must be one of the owners of the resource
        pk - Unique HydroShare identifier for the resource to be formally published.

    Returns:    The id of the resource that was published

    Return Type:    string

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request
    and other general exceptions

    Note:  This is different than just giving public access to a resource via access control rule
    """
    resource = utils.get_resource_by_shortkey(pk)
    if resource.raccess.published:
        raise ValidationError("This resource is already published")

    # TODO: whether a resource can be published is not considered in can_be_submitted_for_metadata_review
    # TODO: can_be_submitted_for_metadata_review is currently an alias for can_be_public_or_discoverable
    if not resource.can_be_submitted_for_metadata_review:
        raise ValidationError("This resource cannot be submitted for metadata review since "
                              "it does not have required metadata or content files, or it contains "
                              "reference content, or this resource type is not allowed for publication.")

    # append pending to the doi field to indicate DOI is not activated yet. Upon successful
    # activation, "pending" will be removed from DOI field
    resource.doi = get_resource_doi(pk, 'pending')
    resource.save()

    if not settings.DEBUG:
        # only in production environment submit doi request to crossref
        response = deposit_res_metadata_with_crossref(resource)
        if not response.status_code == status.HTTP_200_OK:
            # resource metadata deposition failed from CrossRef - set failure flag to be retried in a
            # crontab celery task
            logger.error(f"Received a {response.status_code} from Crossref while depositing metadata for res id {pk}")
            resource.doi = get_resource_doi(pk, 'failure')
            resource.save()

    resource.set_public(True)  # also sets discoverable to True
    resource.raccess.published = True
    resource.raccess.save()

    # change "Publisher" element of science metadata to CUAHSI
    md_args = {'name': 'Consortium of Universities for the Advancement of Hydrologic Science, '
                       'Inc. (CUAHSI)',
               'url': 'https://www.cuahsi.org'}
    resource.metadata.create_element('Publisher', **md_args)

    # create published date
    resource.metadata.create_element('date', type='published', start_date=resource.updated)

    # add doi to "Identifier" element of science metadata
    md_args = {'name': 'doi',
               'url': get_activated_doi(resource.doi)}
    resource.metadata.create_element('Identifier', **md_args)

    utils.resource_modified(resource, user, overwrite_bag=False)

    return pk


def resolve_doi(doi):
    """
    Takes as input a DOI and returns the internal HydroShare identifier (pid) for a resource.
    This method will be used to get the HydroShare pid for a resource identified by a doi for
    further operations using the web service API.

    REST URL:  GET /resolveDOI/{doi}

    Parameters:    doi - A doi assigned to a resource in HydroShare.

    Returns:    The pid of the resource that was published

    Return Type:    pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request

    Note:  All HydroShare methods (except this one) will use HydroShare internal identifiers
    (pids). This method exists so that a program can resolve the pid for a DOI.
    """
    return utils.get_resource_by_doi(doi).short_id


def create_metadata_element(resource_short_id, element_model_name, **kwargs):
    """
    Creates a specific type of metadata element for a given resource

    :param resource_short_id: id of the resource for which a metadata element needs to be created
    :param element_model_name: metadata element name (e.g., creator)
    :param kwargs: metadata element attribute name/value pairs for all those attributes that
    require a value
    :return:
    """
    res = utils.get_resource_by_shortkey(resource_short_id)
    res.metadata.create_element(element_model_name, **kwargs)


def update_metadata_element(resource_short_id, element_model_name, element_id, **kwargs):
    """
    Updates the data associated with a metadata element for a specified resource

    :param resource_short_id: id of the resource for which a metadata element needs to be updated
    :param element_model_name: metadata element name (e.g., creator)
    :param element_id: id of the metadata element to be updated
    :param kwargs: metadata element attribute name/value pairs for all those attributes that need
    update
    :return:
    """
    res = utils.get_resource_by_shortkey(resource_short_id)
    res.metadata.update_element(element_model_name, element_id, **kwargs)


def delete_metadata_element(resource_short_id, element_model_name, element_id):
    """
    Deletes a specific type of metadata element for a specified resource

    :param resource_short_id: id of the resource for which metadata element to be deleted
    :param element_model_name: metadata element name (e.g., creator)
    :param element_id: id of the metadata element to be deleted
    :return:
    """
    res = utils.get_resource_by_shortkey(resource_short_id)
    res.metadata.delete_element(element_model_name, element_id)
