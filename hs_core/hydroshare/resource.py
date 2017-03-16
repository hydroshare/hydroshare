import os
import zipfile
import shutil
import logging
import string
import requests

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction

from rest_framework import status

from hs_core.hydroshare import hs_bagit
from hs_core.models import ResourceFile
from hs_core import signals
from hs_core.hydroshare import utils
from hs_access_control.models import ResourceAccess, UserResourcePrivilege, PrivilegeCodes
from hs_labels.models import ResourceLabels


FILE_SIZE_LIMIT = 1*(1024 ** 3)
FILE_SIZE_LIMIT_FOR_DISPLAY = '1G'
METADATA_STATUS_SUFFICIENT = 'Sufficient to publish or make public'
METADATA_STATUS_INSUFFICIENT = 'Insufficient to publish or make public'

logger = logging.getLogger(__name__)


def get_resource(pk):
    """
    Retrieve an instance of type Bags associated with the resource identified by **pk**

    Parameters:    pk - Unique HydroShare identifier for the resource to be retrieved.

    Returns:    An instance of type Bags.

    Raises:
    Exceptions.NotFound - The resource identified by pid does not exist
    """

    return utils.get_resource_by_shortkey(pk).baseresource.bags.first()


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
    for f in ResourceFile.objects.filter(object_id=resource.id):
        if os.path.basename(f.resource_file.name) == filename:
            return f.resource_file
    else:
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
    resource = utils.get_resource_by_shortkey(pk)
    for rf in ResourceFile.objects.filter(object_id=resource.id):
        if os.path.basename(rf.resource_file.name) == filename:
            rf.resource_file.delete()
            rf.resource_file = File(f) if not isinstance(f, UploadedFile) else f
            rf.save()
            return rf
    else:
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
    raise NotImplemented()


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
    the supported maximal size limit

    Parameters:
    files - list of Django File or UploadedFile objects to be attached to the resource
    Returns:    True if files are supported; otherwise, returns False
    """
    for file in files:
        if not isinstance(file, UploadedFile):
            # if file is already on the server, e.g., a file transferred directly from iRODS,
            # the file should not be subject to file size check since the file size check is
            # only prompted by file upload limit
            continue
        if hasattr(file, '_size'):
            if file._size > FILE_SIZE_LIMIT:
                # file is greater than FILE_SIZE_LIMIT, which is not allowed
                return False
        else:
            if os.stat(file).st_size > FILE_SIZE_LIMIT:
                # file is greater than FILE_SIZE_LIMIT, which is not allowed
                return False
    return True


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
        files=(), fed_res_file_names='', fed_res_path='', fed_copy_or_move=None,
        create_metadata=True,
        create_bag=True, unpack_file=False, **kwargs):
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

    :param resource_type: string. the type of the resource such as GenericResource
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
    :param fed_res_file_names: the file names separated by comma from a federated zone to be
                               used to create the resource in the federated zone, default is empty
                               string
    :param fed_res_path: the federated zone path in the format of
    /federation_zone/home/localHydroProxy that indicate where the resource is stored, default is
    empty string
    :param fed_copy_or_move: a string value of 'copy' or 'move' indicating whether the content files
                             should be copied or moved to localHydroProxy space. default is None
    :param create_bag: whether to create a bag for the newly created resource or not. By default,
    the bag is created.
    :param unpack_file: boolean.  If files contains a single zip file, and unpack_file is True,
                        the unpacked contents of the zip file will be added to the resource instead
                        of the zip file.
    :param kwargs: extra arguments to fill in required values in AbstractResource subclasses

    :return: a new resource which is an instance of BaseResource with specificed resource_type.
    """
    with transaction.atomic():
        cls = check_resource_type(resource_type)
        owner = utils.user_from_id(owner)

        # create the resource
        resource = cls.objects.create(
            resource_type=resource_type,
            user=owner,
            creator=owner,
            title=title,
            last_changed_by=owner,
            in_menus=[],
            **kwargs
        )

        resource.resource_type = resource_type

        # by default make resource private
        resource.set_slug('resource{0}{1}'.format('/', resource.short_id))
        resource.save()

        if not metadata:
            metadata = []

        if extra_metadata is not None:
            resource.extra_metadata = extra_metadata
            resource.save()

        fed_zone_home_path = ''
        if fed_res_path:
            fed_zone_home_path = fed_res_path
            resource.resource_federation_path = fed_res_path
            resource.save()
        elif fed_res_file_names:
            fed_zone_home_path = utils.get_federated_zone_home_path(fed_res_file_names[0])
            resource.resource_federation_path = fed_zone_home_path
            resource.save()

        if len(files) == 1 and unpack_file and zipfile.is_zipfile(files[0]):
            # Add contents of zipfile as resource files asynchronously
            # Note: this is done asynchronously as unzipping may take
            # a long time (~15 seconds to many minutes).
            add_zip_file_contents_to_resource_async(resource, files[0])
        else:
            # Add resource file(s) now
            # Note: this is done synchronously as it should only take a
            # few seconds.  We may want to add the option to do this
            # asynchronously if the file size is large and would take
            # more than ~15 seconds to complete.
            add_resource_files(resource.short_id, *files, fed_res_file_names=fed_res_file_names,
                               fed_copy_or_move=fed_copy_or_move,
                               fed_zone_home_path=fed_zone_home_path)

        # by default resource is private
        resource_access = ResourceAccess(resource=resource)
        resource_access.save()
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

        if create_metadata:
            # prepare default metadata
            utils.prepare_resource_default_metadata(resource=resource, metadata=metadata,
                                                    res_title=title)

            for element in metadata:
                # here k is the name of the element
                # v is a dict of all element attributes/field names and field values
                k, v = element.items()[0]
                resource.metadata.create_element(k, **v)

            for keyword in keywords:
                resource.metadata.create_element('subject', value=keyword)

            resource.title = resource.metadata.title.value
            resource.save()
        if create_bag:
            hs_bagit.create_bag(resource, fed_zone_home_path=fed_zone_home_path)
    return resource


def create_empty_resource(pk, user, action='version'):
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
        resource which is then further populated with metadata and content in a subsequent step
    """
    res = utils.get_resource_by_shortkey(pk)
    if action == 'version':
        if not user.uaccess.owns_resource(res):
            raise PermissionDenied('Only resource owners can create new versions')
    elif action == 'copy':
        # import here to avoid circular import
        from hs_core.views.utils import can_user_copy_resource
        if not user.uaccess.can_view_resource(res):
            raise PermissionDenied('You do not have permission to view this resource')
        allow_copy = can_user_copy_resource(res, user)
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
        fed_res_path=res.resource_federation_path,
        create_bag=False
    )
    return new_resource


def copy_resource(ori_res, new_res):
    """
    Populate metadata and contents from ori_res object to new_res object to make new_res object
    as a copy of the ori_res object
    Args:
        ori_res: the original resource that is to be copied.
        new_res: the new_res to be populated with metadata and content from the original resource
        as a copy of the original resource
    Returns:
        the new resource copied from the original resource
    """

    # add files directly via irods backend file operation
    utils.copy_resource_files_and_AVUs(ori_res.short_id, new_res.short_id, set_to_private=True)

    utils.copy_and_create_metadata(ori_res, new_res)

    hs_identifier = ori_res.metadata.identifiers.all().filter(name="hydroShareIdentifier")[0]
    if hs_identifier:
        new_res.metadata.create_element('source', derived_from=hs_identifier.url)

    if ori_res.resource_type.lower() == "collectionresource":
        # clone contained_res list of original collection and add to new collection
        # note that new collection will not contain "deleted resources"
        new_res.resources = ori_res.resources.all()

    # create bag for the new resource
    hs_bagit.create_bag(new_res, ori_res.resource_federation_path)

    return new_res


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
    # newly created new resource version is private initially
    set_to_private = False
    if ori_res.raccess.public:
        set_to_private = True

    # add files directly via irods backend file operation
    utils.copy_resource_files_and_AVUs(ori_res.short_id, new_res.short_id, set_to_private)

    # copy metadata from source resource to target new-versioned resource except three elements
    utils.copy_and_create_metadata(ori_res, new_res)

    # add or update Relation element to link source and target resources
    hs_identifier = new_res.metadata.identifiers.all().filter(name="hydroShareIdentifier")[0]
    ori_res.metadata.create_element('relation', type='isReplacedBy', value=hs_identifier.url)

    if new_res.metadata.relations.all().filter(type='isVersionOf').exists():
        # the original resource is already a versioned resource, and its isVersionOf relation
        # element is copied over to this new version resource, needs to delete this element so
        # it can be created to link to its original resource correctly
        eid = new_res.metadata.relations.all().filter(type='isVersionOf').first().id
        new_res.metadata.delete_element('relation', eid)

    hs_identifier = ori_res.metadata.identifiers.all().filter(name="hydroShareIdentifier")[0]
    new_res.metadata.create_element('relation', type='isVersionOf', value=hs_identifier.url)

    if ori_res.resource_type.lower() == "collectionresource":
        # clone contained_res list of original collection and add to new collection
        # note that new version collection will not contain "deleted resources"
        new_res.resources = ori_res.resources.all()

    # create bag for the new resource
    hs_bagit.create_bag(new_res, ori_res.resource_federation_path)

    # since an isReplaceBy relation element is added to original resource, needs to call
    # resource_modified() for original resource
    utils.resource_modified(ori_res, user, overwrite_bag=False)
    # if everything goes well up to this point, set original resource to be immutable so that
    # obsoleted resources cannot be modified from REST API
    ori_res.raccess.immutable = True
    ori_res.raccess.save()
    return new_res


def add_resource_files(pk, *files, **kwargs):
    """
    Called by clients to update a resource in HydroShare by adding one or more files.

    REST URL:  PUT /resource/{pid}/files/{file}

    Parameters:
    pk - Unique HydroShare identifier for the resource that is to be updated.
    files - A list of file-like objects representing files that will be added
    to the existing resource identified by pid

    Returns:    A list of ResourceFile objects

    Return Type:    list

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.InvalidContent - The content of the file is invalid
    Exception.ServiceFailure - The service is unable to process the request

    Notes:
    For mutable resources (resources not formally published), the update adds the file that is
    passed to this method to the resource. For immutable resources (formally published resources),
    this method creates a new resource that is a new version of the formally published resource.
    HydroShare will record the update by storing the SystemMetadata.obsoletes and
    SystemMetadata.obsoletedBy fields for the respective resources in their system metadata
    HydroShare MUST check or set the values of SystemMetadata.obsoletes and
    SystemMetadata.obsoletedBy so that they accurately represent the relationship between the new
    and old objects. HydroShare MUST also set SystemMetadata.dateSysMetadataModified. The modified
    system metadata entries must then be available in HydroShare.listObjects() to ensure that any
    cataloging systems pick up the changes when filtering on SystmeMetadata.dateSysMetadataModified.
    A formally published resource can only be obsoleted by one newer version. Once a resource is
    obsoleted, no other resources can obsolete it.

    """
    resource = utils.get_resource_by_shortkey(pk)
    fed_res_file_names = kwargs.pop('fed_res_file_names', '')
    ret = []
    fed_zone_home_path = kwargs.pop('fed_zone_home_path', '')
    # for adding files to existing resources, the default action is copy
    fed_copy_or_move = kwargs.pop('fed_copy_or_move', 'copy')
    folder = kwargs.pop('folder', None)

    for f in files:
        if fed_zone_home_path:
            # user has selected files from a federated iRODS zone, so files uploaded from local disk
            # need to be stored to the federated iRODS zone rather than HydroShare zone as well
            # TODO: why do we allow the federation prefix to vary in this statement?
            ret.append(utils.add_file_to_resource(resource, f, folder=folder,
                                                  fed_res_file_name_or_path=fed_zone_home_path))
        elif resource.resource_federation_path:
            # file needs to be added to a resource in a federated zone
            # TODO: why do we allow the federation prefix to vary in this statement?
            ret.append(utils.add_file_to_resource(
                resource, f, folder=folder,
                fed_res_file_name_or_path=resource.resource_federation_path))
        else:
            ret.append(utils.add_file_to_resource(resource, f, folder=folder))
    if fed_res_file_names:
        if isinstance(fed_res_file_names, basestring):
            ifnames = string.split(fed_res_file_names, ',')
        elif isinstance(fed_res_file_names, list):
            ifnames = fed_res_file_names
        else:
            return ret
        for ifname in ifnames:
            ret.append(utils.add_file_to_resource(resource, None, folder=folder,
                                                  fed_res_file_name_or_path=ifname,
                                                  fed_copy_or_move=fed_copy_or_move))
    if not ret:
        # no file has been added, make sure data/contents directory exists if no file is added
        utils.create_empty_contents_directory(resource)
    return ret


def update_science_metadata(pk, metadata):
    """
    Updates science metadata for a resource

    Args:
        pk: Unique HydroShare identifier for the resource for which science metadata needs to be
        updated.
        metadata: a list of dictionary items containing data for each metadata element that needs to
        be updated
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
            {'source': {'derived_from': 'http://hydroshare.org/resource/0001'}},
            {'subject': {'value': 'sub-1'}},
            {'subject': {'value': 'sub-2'}},
        ]

    Returns:
    """

    resource = utils.get_resource_by_shortkey(pk)
    resource.metadata.update(metadata)


def delete_resource(pk):
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

    Note:  Only HydroShare administrators will be able to delete formally published resour
    """

    res = utils.get_resource_by_shortkey(pk)

    if res.metadata.relations.all().filter(type='isReplacedBy').exists():
        raise ValidationError('An obsoleted resource in the middle of the obsolescence chain '
                              'cannot be deleted.')

    # when the most recent version of a resource in an obsolescence chain is deleted, the previous
    # version in the chain needs to be set as the "active" version by deleting "isReplacedBy"
    # relation element
    if res.metadata.relations.all().filter(type='isVersionOf').exists():
        is_version_of_res_link = \
            res.metadata.relations.all().filter(type='isVersionOf').first().value
        idx = is_version_of_res_link.rindex('/')
        if idx == -1:
            obsolete_res_id = is_version_of_res_link
        else:
            obsolete_res_id = is_version_of_res_link[idx+1:]
        obsolete_res = utils.get_resource_by_shortkey(obsolete_res_id)
        if obsolete_res.metadata.relations.all().filter(type='isReplacedBy').exists():
            eid = obsolete_res.metadata.relations.all().filter(type='isReplacedBy').first().id
            obsolete_res.metadata.delete_element('relation', eid)
            # also make this obsoleted resource editable now that it becomes the latest version
            obsolete_res.raccess.immutable = False
            obsolete_res.raccess.save()
    res.delete()
    return pk


def get_resource_file_name(f):
    """
    get the file name of a specific ResourceFile object f
    Args:
        f: the ResourceFile object to return name for
    Returns:
        the file name of the ResourceFile object f
    """
    if f.resource_file:
        # file was originally from local disk, and is currently stored in irods hydroshare zone
        res_fname = f.resource_file.name
    elif f.fed_resource_file:
        # file was originally from local disk, but is currently stored in federated irods zone
        res_fname = f.fed_resource_file.name
    else:
        # file was originally from federated irods zone, and is currently stored in the
        # same federated irods zone
        res_fname = f.fed_resource_file_name_or_path
    return res_fname


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
    Returns: file name that has been deleted
    """

    root_path = resource.root_path
    if f.fed_resource_file_name_or_path:
        file_name = os.path.join(root_path, f.fed_resource_file_name_or_path)
        utils.delete_fed_zone_file(file_name)
    elif f.fed_resource_file:
            # file was originally from local disk, but is currently stored in federated irods zone
            file_name = f.fed_resource_file.name
            f.fed_resource_file.delete()
    else:
        # file was originally from local disk, and is currently stored in main irods hydroshare zone
        file_name = f.resource_file.name
        f.resource_file.delete()
    f.delete()
    return file_name


def delete_format_metadata_after_delete_file(resource, file_name):
    """
    delete format metadata as appropriate after a file is deleted.
    :param resource: BaseResource object representing a HydroShare resource
    :param file_name: the file name to be deleted
    :return:
    """
    delete_file_mime_type = utils.get_file_mime_type(file_name)
    delete_file_extension = os.path.splitext(file_name)[1]

    # if there is no other resource file with the same extension as the
    # file just deleted then delete the matching format metadata element for the resource
    resource_file_extensions = [os.path.splitext(get_resource_file_name(f))[1] for f in
                                resource.files.all()]
    if delete_file_extension not in resource_file_extensions:
        format_element = resource.metadata.formats.filter(value=delete_file_mime_type).first()
        if format_element:
            resource.metadata.delete_element(format_element.term, format_element.id)


def filter_condition(filename_or_id, fed_path, fl):
    """
    Converted lambda defintion of filter_condition into def to conform to pep8 E731 rule: do not
    assign a lambda expression, use a def
    :param filename_or_id: passed in filename_or id as the filter
    :param fed_path: resource federation path
    :param fl: the ResourceFile object to filter against
    :return: boolean indicating whether fl conforms to filename_or_id
    """
    try:
        file_id = int(filename_or_id)
        return fl.id == file_id
    except ValueError:
        if fed_path:
            return os.path.basename(fl.fed_resource_file_name_or_path) == filename_or_id \
                if fl.fed_resource_file_name_or_path else \
                os.path.basename(fl.fed_resource_file.name) == filename_or_id \
                if fl.fed_resource_file else False
        else:
            return os.path.basename(fl.resource_file.name) == filename_or_id


def delete_resource_file(pk, filename_or_id, user, delete_logical_file=True):
    """
    Deletes an individual file from a HydroShare resource. If the file does not exist,
    the Exceptions.NotFound exception is raised.

    REST URL:  DELETE /resource/{pid}/files/{filename}

    Parameters:
    pk - The unique HydroShare identifier for the resource from which the file will be deleted
    filename_or_id - Name of the file or id of the file to be deleted from the resource
    user - requesting user
    delete_logical_file - If True then the ResourceFile object to be deleted if it is part of a
    LogicalFile object then the LogicalFile object will be deleted which deletes all associated
    ResourceFile objects and file type metadata objects.

    Returns:    The name or id of the file which was deleted

    Return Type:    string or integer

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist or the file identified by
    file does not exist
    Exception.ServiceFailure - The service is unable to process the request

    Note:  For mutable resources (resources that have not been formally published), this method
    modifies the resource by deleting the file. For immutable resources (formally published
    resources), this method creates a new resource that is a new version of the formally published
    resource. HydroShare will record the update by storing the SystemMetadata.obsoletes and
    SystemMetadata.obsoletedBy fields for the respective resources in their system metadata
    HydroShare MUST check or set the values of SystemMetadata.obsoletes and
    SystemMetadata.obsoletedBy so that they accurately represent the relationship between the new
    and old objects. HydroShare MUST also set SystemMetadata.dateSysMetadataModified.
    The modified system metadata entries must then be available in HydroShare.listObjects() to
    ensure that any cataloging systems pick up the changes when filtering on
    SystmeMetadata.dateSysMetadataModified. A formally published resource can only be obsoleted by
    one newer version. Once a resource is obsoleted, no other resources can obsolete it.
    """
    resource = utils.get_resource_by_shortkey(pk)
    res_cls = resource.__class__
    fed_path = resource.resource_federation_path

    for f in ResourceFile.objects.filter(object_id=resource.id):
        if filter_condition(filename_or_id, fed_path, f):
            if delete_logical_file:
                if f.logical_file is not None:
                    # logical_delete() calls this function (delete_resource_file())
                    # to delete each of its contained ResourceFile objects
                    f.logical_file.logical_delete(user)
                    return filename_or_id
            # send signal
            signals.pre_delete_file_from_resource.send(sender=res_cls, file=f, resource=resource,
                                                       user=user)
            file_name = delete_resource_file_only(resource, f)

            delete_format_metadata_after_delete_file(resource, file_name)
            break
    else:
        raise ObjectDoesNotExist(filename_or_id)

    if resource.raccess.public or resource.raccess.discoverable:
        if not resource.can_be_public_or_discoverable:
            resource.raccess.public = False
            resource.raccess.discoverable = False
            resource.raccess.save()

    signals.post_delete_file_from_resource.send(sender=res_cls, resource=resource)
    # generate bag
    utils.resource_modified(resource, user, overwrite_bag=False)

    return filename_or_id


def get_resource_doi(res_id, flag=''):
    doi_str = "http://dx.doi.org/10.4211/hs.{shortkey}".format(shortkey=res_id)
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
    response = requests.post(post_url, data=post_data, files=files)
    return response


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

    if not resource.can_be_published:
        raise ValidationError("This resource cannot be published since it does not have required "
                              "metadata or content files or this resource type is not allowed "
                              "for publication.")

    # append pending to the doi field to indicate DOI is not activated yet. Upon successful
    # activation, "pending" will be removed from DOI field
    resource.doi = get_resource_doi(pk, 'pending')
    resource.save()

    response = deposit_res_metadata_with_crossref(resource)
    if not response.status_code == status.HTTP_200_OK:
        # resource metadata deposition failed from CrossRef - set failure flag to be retried in a
        # crontab celery task
        resource.doi = get_resource_doi(pk, 'failure')
        resource.save()

    resource.raccess.public = True
    resource.raccess.immutable = True
    resource.raccess.shareable = False
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
