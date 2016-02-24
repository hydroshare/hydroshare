import os
import zipfile
import shutil
import logging

import requests

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError
from django.db import transaction
from django.conf import settings
from rest_framework import status

from mezzanine.generic.models import Keyword, AssignedKeyword

from hs_core.hydroshare import hs_bagit
from hs_core.models import ResourceFile
from hs_core import signals
from hs_core.hydroshare import utils
from hs_access_control.models import ResourceAccess, UserResourcePrivilege, PrivilegeCodes
from hs_labels.models import ResourceLabels


FILE_SIZE_LIMIT = 10*(1024 ** 3)
FILE_SIZE_LIMIT_FOR_DISPLAY = '10G'
METADATA_STATUS_SUFFICIENT = 'Sufficient to publish or make public'
METADATA_STATUS_INSUFFICIENT = 'Insufficient to publish or make public'

logger = logging.getLogger(__name__)

def get_resource(pk):
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
    """

    # 1. Look up the resource by ID
    # 2. Check to see if a bagit file exists on IRODS for that resource
    # 3.T.1. Return the bagit file
    # 3.T.1. Return the bagit file
    # 3.F.1. look up the resource serialization (tastypie) class in the resource type map
    # 3.F.2. Serialize the resource to disk using TastyPie.
    # 3.F.3. Create a bagit file from the serialized resource.
    # 3.F.4. Return the bagit file
    return utils.get_resource_by_shortkey(pk).baseresource.bags.first()


def get_science_metadata(pk):
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
    res = utils.get_resource_by_shortkey(pk)
    return res.metadata.get_xml()


# TODO: Incorrect implementation. Needs fixing if we ever need this api
def get_system_metadata(pk):
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
    return utils.get_resource_by_shortkey(pk)


# TODO: Incorrect implementation. Needs fixing if we ever need this api
def get_resource_map(pk):
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
    return utils.get_resource_by_shortkey(pk)


def get_capabilities(pk):
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
    Exceptions.NotFound - The resource identified does not exist or the file identified by filename does not exist
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
    Exceptions.NotFound - The resource identified does not exist or the file identified by filename does not exist
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


# TODO: incorrect implementation. Needs fixing if we ever need this api
def get_revisions(pk):
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
    return utils.get_resource_by_shortkey(pk).bags.all()


def get_related(pk):
    """
    Returns a list of pids for resources that are related to the resource identified by the specified pid.

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
    Returns a checksum for the specified resource using the MD5 algorithm. The result is used to determine if two
    instances referenced by a pid are identical.

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
    Returns:  the resource type class matching the resource type string; if no match is found, returns None
    """
    for tp in utils.get_resource_types():
        if resource_type == tp.__name__:
            res_cls = tp
            break
    else:
        raise NotImplementedError("Type {resource_type} does not exist".format(resource_type=resource_type))
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
    tmp_dir = getattr(settings, 'HYDROSHARE_SHARED_TEMP', '/shared_temp')
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
        keywords=(), metadata=None, content=None,
        files=(), res_type_cls=None, resource=None, unpack_file=False, **kwargs):
    """
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

    Implementation notes:

    1. pid is called short_id.  This is because pid is a UNIX term for Process ID and could be confusing.

    2. return type is an instance of a subclass of hs_core.models.AbstractResource.  This is for efficiency in the
       native API.  The native API should return actual instance rather than IDs wherever possible to avoid repeated
       lookups in the database when they are unnecessary.

    3. resource_type is a string: see parameter list

    :param resource_type: string. the classname of the resource type, such as GenericResource
    :param owner: email address, username, or User instance. The owner of the resource
    :param title: string. the title of the resource
    :param edit_users: list of email addresses, usernames, or User instances who will be given edit permissions
    :param view_users: list of email addresses, usernames, or User instances who will be given view permissions
    :param edit_groups: list of group names or Group instances who will be given edit permissions
    :param view_groups: list of group names or Group instances who will be given view permissions
    :param keywords: string list. list of keywords to add to the resource
    :param metadata: list of dicts containing keys (element names) and corresponding values as dicts { 'creator': {'name':'John Smith'}}.
    :param files: list of Django File or UploadedFile objects to be attached to the resource
    :param unpack_file: boolean.  If files contains a single zip file, and unpack_file is True,
    the unpacked contents of the zip file will be added to the resource instead of the zip file.
    :param kwargs: extra arguments to fill in required values in AbstractResource subclasses

    :return: a new resource which is an instance of resource_type.
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
        #resource.content_model = "baseresource"
        resource.set_slug('resource{0}{1}'.format('/', resource.short_id))
        resource.save()

        if not metadata:
            metadata = []

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
            add_resource_files(resource.short_id, *files)

        # by default resource is private
        resource_access = ResourceAccess(resource=resource)
        resource_access.save()
        UserResourcePrivilege(resource=resource, grantor=owner, user=owner,
                              privilege=PrivilegeCodes.OWNER).save()

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

        # prepare default metadata
        utils.prepare_resource_default_metadata(resource=resource, metadata=metadata, res_title=title)

        for element in metadata:
            # here k is the name of the element
            # v is a dict of all element attributes/field names and field values
            k, v = element.items()[0]
            resource.metadata.create_element(k, **v)

        for keyword in keywords:
            resource.metadata.create_element('subject', value=keyword)

        hs_bagit.create_bag(resource)

    return resource


# TODO: This is not used anywhere except in a skipped unit test - if need to be used then new access rules need to apply
def update_resource(
        pk,
        edit_users=None, view_users=None, edit_groups=None, view_groups=None,
        keywords=(), metadata=None,
        *files, **kwargs):
    """
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
    """
    resource = utils.get_resource_by_shortkey(pk)

    if files:
        ResourceFile.objects.filter(object_id=resource.id).delete()
        for file in files:
            ResourceFile.objects.create(
                content_object=resource,
                resource_file=File(file) if not isinstance(file, UploadedFile) else file
            )

    if 'owner' in kwargs:
        owner = utils.user_from_id(kwargs['owner'])
        resource.owners.add(owner)

    if edit_users:
        resource.edit_users.clear()
        for user in edit_users:
            user = utils.user_from_id(user)
            resource.edit_users.add(user)
            resource.view_users.add(user)

    if view_users:
        resource.view_users.clear()
        for user in view_users:
            user = utils.user_from_id(user)
            resource.view_users.add(user)

    if edit_groups:
        resource.edit_groups.clear()
        for group in edit_groups:
            group = utils.group_from_id(group)
            resource.edit_groups.add(group)
            resource.view_groups.add(group)

    if view_groups:
        resource.edit_groups.clear()
        for group in view_groups:
            group = utils.group_from_id(group)
            resource.view_groups.add(group)

    if keywords:
        AssignedKeyword.objects.filter(object_pk=resource.id).delete()
        ks = [Keyword.objects.get_or_create(title=k) for k in keywords]
        ks = zip(*ks)[0]  # ignore whether something was created or not.  zip is its own inverse

        for k in ks:
            AssignedKeyword.objects.create(content_object=resource, keyword=k)

    # for creating metadata elements based on the new metadata implementation
    if metadata:
        resource.metadata.update(metadata)

    return resource


def add_resource_files(pk, *files):
    """
    Called by clients to update a resource in HydroShare by adding a single file.

    REST URL:  PUT /resource/{pid}/files/{file}

    Parameters:
    pid - Unique HydroShare identifier for the resource that is to be updated.
    files - A list of file-like objects representing files that will be added
    to the existing resource identified by pid

    Returns:    The pid assigned to the updated resource

    Return Type:    pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.InvalidContent - The content of the file is invalid
    Exception.ServiceFailure - The service is unable to process the request

    Notes:
    For mutable resources (resources not formally published), the update adds the file that is passed
    to this method to the resource. For immutable resources (formally published resources), this method creates a new
    resource that is a new version of the formally published resource. HydroShare will record the update by storing the
    SystemMetadata.obsoletes and SystemMetadata.obsoletedBy fields for the respective resources in their system metadata
    HydroShare MUST check or set the values of SystemMetadata.obsoletes and SystemMetadata.obsoletedBy so that they
    accurately represent the relationship between the new and old objects. HydroShare MUST also set
    SystemMetadata.dateSysMetadataModified. The modified system metadata entries must then be available in
    HydroShare.listObjects() to ensure that any cataloging systems pick up the changes when filtering on
    SystmeMetadata.dateSysMetadataModified. A formally published resource can only be obsoleted by one newer version.
    Once a resource is obsoleted, no other resources can obsolete it.

    """
    resource = utils.get_resource_by_shortkey(pk)
    ret = []
    for f in files:
        ret.append(utils.add_file_to_resource(resource, f))
    return ret


# TODO: Incorrect implementation. Needs fixing if we ever need this api
def update_system_metadata(pk, **kwargs):
    """

    """
    return update_science_metadata(pk, **kwargs)


def update_science_metadata(pk, metadata):
    """
    Updates science metadata for a resource

    Args:
        pk: Unique HydroShare identifier for the resource for which science metadata needs to be updated.
        metadata: a list of dictionary items containing data for each metadata element that needs to be updated
        example metadata format:
        [
            {'title': {'value': 'Updated Resource Title'}},
            {'description': {'abstract': 'Updated Resource Abstract'}},
            {'date': {'type': 'valid', 'start_date': '1/26/2016', 'end_date': '12/31/2016'}},
            {'creator': {'name': 'John Smith', 'email': 'jsmith@gmail.com'}},
            {'creator': {'name': 'Lisa Molley', 'email': 'lmolley@gmail.com'}},
            {'contributor': {'name': 'Kelvin Marshal', 'email': 'kmarshal@yahoo.com',
                             'organization': 'Utah State University',
                             'profile_links': [{'type': 'yahooProfile', 'url': 'http://yahoo.com/LH001'}]}},
            {'coverage': {'type': 'period', 'value': {'name': 'Name for period coverage', 'start': '1/1/2000',
                                                      'end': '12/12/2012'}}},
            {'coverage': {'type': 'point', 'value': {'name': 'Name for point coverage', 'east': '56.45678',
                                                     'north': '12.6789', 'units': 'decimal deg'}}},
            {'identifier': {'name': 'someIdentifier', 'url': "http://some.org/001"}},
            {'language': {'code': 'fre'}},
            {'relation': {'type': 'isPartOf', 'value': 'http://hydroshare.org/resource/001'}},
            {'rights': {'statement': 'This is the rights statement for this resource', 'url': 'http://rights.ord/001'}},
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
    #utils.get_resource_by_shortkey(pk).delete()
    res = utils.get_resource_by_shortkey(pk)
    res.delete()
    return pk


def delete_resource_file(pk, filename_or_id, user):
    """
    Deletes an individual file from a HydroShare resource. If the file does not exist, the Exceptions.NotFound exception
    is raised.

    REST URL:  DELETE /resource/{pid}/files/{filename}

    Parameters:
    pid - The unique HydroShare identifier for the resource from which the file will be deleted
    filename - Name of the file to be deleted from the resource

    Returns:    The pid of the resource from which the file was deleted

    Return Type:    pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist or the file identified by file does not exist
    Exception.ServiceFailure - The service is unable to process the request

    Note:  For mutable resources (resources that have not been formally published), this method modifies the resource by
    deleting the file. For immutable resources (formally published resources), this method creates a new resource that
    is a new version of the formally published resource. HydroShare will record the update by storing the
    SystemMetadata.obsoletes and SystemMetadata.obsoletedBy fields for the respective resources in their system metadata
    HydroShare MUST check or set the values of SystemMetadata.obsoletes and SystemMetadata.obsoletedBy so that they
    accurately represent the relationship between the new and old objects. HydroShare MUST also set
    SystemMetadata.dateSysMetadataModified. The modified system metadata entries must then be available in
    HydroShare.listObjects() to ensure that any cataloging systems pick up the changes when filtering on
    SystmeMetadata.dateSysMetadataModified. A formally published resource can only be obsoleted by one newer
    version. Once a resource is obsoleted, no other resources can obsolete it.
    """
    resource = utils.get_resource_by_shortkey(pk)
    res_cls = resource.__class__

    try:
        file_id = int(filename_or_id)
        filter_condition = lambda fl: fl.id == file_id
    except ValueError:
        filter_condition = lambda fl: os.path.basename(fl.resource_file.name) == filename_or_id

    for f in ResourceFile.objects.filter(object_id=resource.id):
        if filter_condition(f):
            # send signal
            signals.pre_delete_file_from_resource.send(sender=res_cls, file=f, resource=resource)

            file_name = f.resource_file.name
            f.resource_file.delete()
            f.delete()
            delete_file_mime_type = utils.get_file_mime_type(file_name)
            delete_file_extension = os.path.splitext(file_name)[1]

            # if there is no other resource file with the same extension as the
            # file just deleted then delete the matching format metadata element for the resource
            resource_file_extensions = [os.path.splitext(f.resource_file.name)[1] for f in resource.files.all()]
            if delete_file_extension not in resource_file_extensions:
                format_element = resource.metadata.formats.filter(value=delete_file_mime_type).first()
                if format_element:
                    resource.metadata.delete_element(format_element.term, format_element.id)
            break
    else:
        raise ObjectDoesNotExist(filename_or_id)

    if resource.raccess.public or resource.raccess.discoverable:
        if not resource.can_be_public_or_discoverable:
            resource.raccess.public = False
            resource.raccess.discoverable = False
            resource.raccess.save()

    # generate bag
    utils.resource_modified(resource, user)

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
    post_data = {'operation': 'doMDUpload',
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
    Formally publishes a resource in HydroShare. Triggers the creation of a DOI for the resource, and triggers the
    exposure of the resource to the HydroShare DataONE Member Node. The user must be an owner of a resource or an
    adminstrator to perform this action.

    Parameters:
        user - requesting user to publish the resource who must be one of the owners of the resource
        pid - Unique HydroShare identifier for the resource to be formally published.

    Returns:    The pid of the resource that was published

    Return Type:    pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request
    and other general exceptions

    Note:  This is different than just giving public access to a resource via access control rule
    """
    resource = utils.get_resource_by_shortkey(pk)

    if not resource.can_be_public_or_discoverable:
        raise ValidationError("This resource cannot be published since it does not have required metadata or content files.")

    # append pending to the doi field to indicate DOI is not activated yet. Upon successful activation, "pending" will be removed from DOI field
    resource.doi = get_resource_doi(pk, 'pending')
    resource.save()

    response = deposit_res_metadata_with_crossref(resource)
    if not response.status_code == status.HTTP_200_OK:
        # resource metadata deposition failed from CrossRef - set failure flag to be retried in a crontab celery task
        resource.doi = get_resource_doi(pk, 'failure')
        resource.save()

    resource.raccess.public = True
    resource.raccess.immutable = True
    resource.raccess.shareable = False
    resource.raccess.published = True
    resource.raccess.save()

    # change "Publisher" element of science metadata to CUAHSI
    md_args = {'name': 'Consortium of Universities for the Advancement of Hydrologic Science, Inc. (CUAHSI)',
               'url': 'https://www.cuahsi.org'}
    resource.metadata.create_element('Publisher', **md_args)

    # create published date
    resource.metadata.create_element('date', type='published', start_date=resource.updated)

    # add doi to "Identifier" element of science metadata
    md_args = {'name': 'doi',
               'url': get_activated_doi(resource.doi)}
    resource.metadata.create_element('Identifier', **md_args)

    utils.resource_modified(resource, user)

    return pk


def resolve_doi(doi):
    """
    Takes as input a DOI and returns the internal HydroShare identifier (pid) for a resource. This method will be used
    to get the HydroShare pid for a resource identified by a doi for further operations using the web service API.

    REST URL:  GET /resolveDOI/{doi}

    Parameters:    doi - A doi assigned to a resource in HydroShare.

    Returns:    The pid of the resource that was published

    Return Type:    pid

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request

    Note:  All HydroShare methods (except this one) will use HydroShare internal identifiers (pids). This method exists
    so that a program can resolve the pid for a DOI.

    """
    return utils.get_resource_by_doi(doi).short_id


def create_metadata_element(resource_short_id, element_model_name, **kwargs):
    """
    Creates a specific type of metadata element for a given resource

    :param resource_short_id: id of the resource for which a metadata element needs to be created
    :param element_model_name: metadata element name (e.g., creator)
    :param kwargs: metadata element attribute name/value pairs for all those attributes that require a value
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
    :param kwargs: metadata element attribute name/value pairs for all those attributes that need update
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


def get_science_metadata_xml(resource_short_id):
    """
    Gets science metadata as an xml string for a specified resource

    :param resource_short_id: id of the resource
    :return: science metadata as an xml string
    """
    res = utils.get_resource_by_shortkey(resource_short_id)
    return res.metadata.get_xml()
