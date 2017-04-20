from __future__ import absolute_import

import mimetypes
import os
import tempfile
import logging
import shutil
import string
import copy
from uuid import uuid4
import errno

from django.apps import apps
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.auth.models import User, Group
from django.core.files import File
from django.core.files.uploadedfile import UploadedFile
from django.core.files.storage import DefaultStorage

from mezzanine.conf import settings

from hs_core.signals import pre_create_resource, post_create_resource, pre_add_files_to_resource, \
    post_add_files_to_resource
from hs_core.models import AbstractResource, BaseResource, ResourceFile
from hs_core.hydroshare.hs_bagit import create_bag_files

from django_irods.icommands import SessionException
from django_irods.storage import IrodsStorage


logger = logging.getLogger(__name__)


class ResourceFileSizeException(Exception):
    pass


class ResourceFileValidationException(Exception):
    pass


def get_resource_types():
    resource_types = []
    for model in apps.get_models():
        if issubclass(model, AbstractResource) and model != BaseResource:
            if not getattr(model, 'archived_model', False):
                resource_types.append(model)
    return resource_types


def get_resource_instance(app, model_name, pk, or_404=True):
    model = apps.get_model(app, model_name)
    if or_404:
        return get_object_or_404(model, pk=pk)
    else:
        return model.objects.get(pk=pk)


def get_resource_by_shortkey(shortkey, or_404=True):
    try:
        res = BaseResource.objects.get(short_id=shortkey)
    except BaseResource.DoesNotExist:
        if or_404:
            raise Http404(shortkey)
        else:
            raise
    content = res.get_content_model()
    assert content, (res, res.content_model)
    return content


def get_resource_by_doi(doi, or_404=True):
    try:
        res = BaseResource.objects.get(doi=doi)
    except BaseResource.DoesNotExist:
        if or_404:
            raise Http404(doi)
        else:
            raise
    content = res.get_content_model()
    assert content, (res, res.content_model)
    return content


def user_from_id(user, raise404=True):
    if isinstance(user, User):
        return user

    try:
        tgt = User.objects.get(username=user)
    except ObjectDoesNotExist:
        try:
            tgt = User.objects.get(email=user)
        except ObjectDoesNotExist:
            try:
                tgt = User.objects.get(pk=int(user))
            except ValueError:
                if raise404:
                    raise Http404('User not found')
                else:
                    raise User.DoesNotExist
            except ObjectDoesNotExist:
                if raise404:
                    raise Http404('User not found')
                else:
                    raise
    return tgt


def group_from_id(grp):
    if isinstance(grp, Group):
        return grp

    try:
        tgt = Group.objects.get(name=grp)
    except ObjectDoesNotExist:
        try:
            tgt = Group.objects.get(pk=int(grp))
        except TypeError:
            raise Http404('Group not found')
        except ObjectDoesNotExist:
            raise Http404('Group not found')
    return tgt


def get_user_zone_status_info(user):
    """
    This function should be called to determine whether the site is in production and whether user
    zone functionality should be enabled or not on the web site front end
    Args:
        user: the requesting user
    Returns:
        in_production, enable_user_zone where both are boolean indicating whether the site is
        in production and whether user zone functionality should be enabled or not on the web site
        front end
    """
    if user is None:
        return None, None
    if not hasattr(user, 'userprofile') or user.userprofile is None:
        return None, None

    in_production = True if settings.IRODS_USERNAME == settings.HS_WWW_IRODS_PROXY_USER else False
    enable_user_zone = user.userprofile.create_irods_user_account
    if not in_production and enable_user_zone:
        # if these settings are not empty, for example, in users' local
        # development environment for testing, user_zone selection is shown
        if (not settings.HS_WWW_IRODS_PROXY_USER_PWD or
                not settings.HS_WWW_IRODS_HOST or not settings.HS_WWW_IRODS_ZONE):
            enable_user_zone = False
    return in_production, enable_user_zone


def is_federated(homepath):
    """
    Check if the selected file via the iRODS browser is from a federated zone or not
    Args:
        homepath: the logical iRODS file name with full logical path, e.g., selected from
                  iRODS browser

    Returns:
    True is the selected file indicated by homepath is from a federated zone, False if otherwise
    """
    homepath = homepath.strip()
    homepath_list = homepath.split('/')
    # homepath is an iRODS logical path in the format of
    # /irods_zone/home/irods_account_username/collection_relative_path, so homepath_list[1]
    # is the irods_zone which we can use to form the fed_proxy_path to check whether
    # fed_proxy_path exists to hold hydroshare resources in a federated zone
    if homepath_list[1]:
        fed_proxy_path = os.path.join(homepath_list[1], 'home',
                                      settings.HS_LOCAL_PROXY_USER_IN_FED_ZONE)
        fed_proxy_path = '/' + fed_proxy_path
    else:
        # the test path input is invalid, return False meaning it is not federated
        return False
    if settings.REMOTE_USE_IRODS:
        irods_storage = IrodsStorage('federated')
    else:
        irods_storage = IrodsStorage()

    # if the iRODS proxy user in hydroshare zone can list homepath and the federation zone proxy
    # user path, it is federated; otherwise, it is not federated
    return irods_storage.exists(homepath) and irods_storage.exists(fed_proxy_path)


def get_federated_zone_home_path(filepath):
    """
    Args:
        filepath: the iRODS data object file path that included zone name in the format of
        /zone_name/home/user_name/file_path

    Returns:
        the zone name extracted from filepath
    """
    if filepath and filepath.startswith('/'):
        split_path_strs = filepath.split('/')
        # the Zone name should follow the first slash
        zone = split_path_strs[1]
        return '/{zone}/home/{local_proxy_user}'.format(
            zone=zone, local_proxy_user=settings.HS_LOCAL_PROXY_USER_IN_FED_ZONE)
    else:
        return ''


# TODO: replace with a cache facility that has automatic cleanup
# TODO: pass a list rather than a string to allow commas in filenames.
def get_fed_zone_files(irods_fnames):
    """
    Get the files from iRODS federated zone to Django server for metadata extraction on-demand
    for specific resource types
    Args:
        irods_fnames: the logical iRODS file names with full logical path separated by comma

    Returns:
    a list of the named temp files which have been copied over to local Django server
    or raise exceptions if input parameter is wrong or iRODS operations fail

    Note: application must delete these files after use.
    """
    ret_file_list = []
    if isinstance(irods_fnames, basestring):
        ifnames = string.split(irods_fnames, ',')
    elif isinstance(irods_fnames, list):
        ifnames = irods_fnames
    else:
        raise ValueError("Input parameter to get_fed_zone_files() must be String or List")
    irods_storage = IrodsStorage('federated')
    for ifname in ifnames:
        fname = os.path.basename(ifname.rstrip(os.sep))
        # TODO: this is statistically unique but not guaranteed to be unique.
        tmpdir = os.path.join(settings.TEMP_FILE_DIR, uuid4().hex)
        tmpfile = os.path.join(tmpdir, fname)
        try:
            os.makedirs(tmpdir)
        except OSError as ex:
            if ex.errno == errno.EEXIST:
                shutil.rmtree(tmpdir)
                os.makedirs(tmpdir)
            else:
                raise Exception(ex.message)
        irods_storage.getFile(ifname, tmpfile)
        ret_file_list.append(tmpfile)
    return ret_file_list


# TODO: make the local cache file (and cleanup) part of ResourceFile state?
def get_file_from_irods(res_file):
    """
    Copy the file (res_file) from iRODS (local or federated zone)
    over to django (temp directory) which is
    necessary for manipulating the file (e.g. metadata extraction).
    Note: The caller is responsible for cleaning the temp directory

    :param res_file: an instance of ResourceFile
    :return: location of the copied file
    """
    res = res_file.resource
    istorage = res.get_irods_storage()
    res_file_path = res_file.storage_path
    file_name = os.path.basename(res_file_path)

    tmpdir = os.path.join(settings.TEMP_FILE_DIR, uuid4().hex)
    tmpfile = os.path.join(tmpdir, file_name)

    # TODO: If collisions occur, really bad things happen.
    # TODO: Directories are never cleaned up when unused. need cache management.
    try:
        os.makedirs(tmpdir)
    except OSError as ex:
        if ex.errno == errno.EEXIST:
            shutil.rmtree(tmpdir)
            os.makedirs(tmpdir)
        else:
            raise Exception(ex.message)

    istorage.getFile(res_file_path, tmpfile)
    copied_file = tmpfile
    return copied_file


# TODO: should be ResourceFile.replace
def replace_resource_file_on_irods(new_file, original_resource_file, user):
    """
    Replaces the specified resource file with file (new_file) by copying to iRODS
    (local or federated zone)
    :param new_file: file path for the file to be copied to iRODS
    :param original_resource_file: an instance of ResourceFile that is to be replaced
    :param user: user who is replacing the resource file.
    :return:
    """
    ori_res = original_resource_file.resource
    istorage = ori_res.get_irods_storage()
    ori_storage_path = original_resource_file.storage_path

    # Note: this doesn't update metadata at all.
    istorage.saveFile(new_file, ori_storage_path, True)

    # do this so that the bag will be regenerated prior to download of the bag
    resource_modified(ori_res, by_user=user, overwrite_bag=False)


# TODO: should be inside ResourceFile, and federation logic should be transparent.
def get_resource_file_name_and_extension(res_file):
    """
    Gets the full file name with path, file base name, and extension of the specified resource file
    :param res_file: an instance of ResourceFile for which file extension to be retrieved
    :return: (full filename with path, full file base name, file extension)
             ex: "/my_path_to/ABC.nc" --> ("/my_path_to/ABC.nc", "ABC.nc", ".nc")
    """
    f_fullname = res_file.storage_path
    f_basename = os.path.basename(f_fullname)
    _, file_ext = os.path.splitext(f_fullname)

    return f_fullname, f_basename, file_ext


# TODO: should be ResourceFile.url
def get_resource_file_url(res_file):
    """
    Gets the download url of the specified resource file
    :param res_file: an instance of ResourceFile for which download url is to be retrieved
    :return: download url for the resource file
    """

    if res_file.resource_file:
        f_url = res_file.resource_file.url
    elif res_file.fed_resource_file:
        f_url = res_file.fed_resource_file.url
    else:
        f_url = ''
    return f_url


# TODO: should be classmethod of ResourceFile
def get_resource_files_by_extension(resource, file_extension):
    matching_files = []
    for res_file in resource.files.all():
        _, _, file_ext = get_resource_file_name_and_extension(res_file)
        if file_ext == file_extension:
            matching_files.append(res_file)
    return matching_files


def get_resource_file_by_name(resource, file_name):
    for res_file in resource.files.all():
        _, fl_name, _ = get_resource_file_name_and_extension(res_file)
        if fl_name == file_name:
            return res_file
    return None


def get_resource_file_by_id(resource, file_id):
    return resource.files.filter(id=file_id).first()


# TODO: This is unnecessary since delete now cascades.
def delete_fed_zone_file(file_name_with_full_path):
    '''
    Args:
        file_name_with_full_path: the absolute full logical path in a federated iRODS zone
    Returns:
        None, but exceptions will be raised if there is an issue with iRODS delete operation
    '''
    istorage = IrodsStorage('federated')
    istorage.delete(file_name_with_full_path)


def replicate_resource_bag_to_user_zone(user, res_id):
    """
    Replicate resource bag to iRODS user zone
    Args:
        user: the requesting user
        res_id: the resource id with its bag to be replicated to iRODS user zone

    Returns:
    None, but exceptions will be raised if there is an issue with iRODS operation
    """
    # do on-demand bag creation
    res = get_resource_by_shortkey(res_id)
    res_coll = res.root_path
    istorage = res.get_irods_storage()
    bag_modified = "false"
    # needs to check whether res_id collection exists before getting/setting AVU on it to
    # accommodate the case where the very same resource gets deleted by another request when
    # it is getting downloaded
    # TODO: why would we want to do anything at all if the resource does not exist???
    if istorage.exists(res_coll):
        bag_modified = istorage.getAVU(res_coll, 'bag_modified')
        if bag_modified.lower() == "true":
            # import here to avoid circular import issue
            from hs_core.tasks import create_bag_by_irods
            create_bag_by_irods(res_id)

        # do replication of the resource bag to irods user zone
        if not res.resource_federation_path:
            istorage.set_fed_zone_session()
        src_file = res.bag_path
        # TODO: allow setting destination path
        tgt_file = '/{userzone}/home/{username}/{resid}.zip'.format(
            userzone=settings.HS_USER_IRODS_ZONE, username=user.username, resid=res_id)
        istorage.copyFiles(src_file, tgt_file)
    else:
        raise ValidationError("Resource {} does not exist in iRODS".format(res.short_id))


def copy_resource_files_and_AVUs(src_res_id, dest_res_id):
    """
    Copy resource files and AVUs from source resource to target resource including both
    on iRODS storage and on Django database
    :param src_res_id: source resource uuid
    :param dest_res_id: target resource uuid
    :return:
    """
    avu_list = ['bag_modified', 'metadata_dirty', 'isPublic', 'resourceType']
    src_res = get_resource_by_shortkey(src_res_id)
    tgt_res = get_resource_by_shortkey(dest_res_id)

    # This makes the assumption that the destination is in the same exact zone.
    # Also, bags and similar attached files are not copied.
    istorage = src_res.get_irods_storage()

    # This makes an exact copy of all physical files.
    src_files = os.path.join(src_res.root_path, 'data')
    # This has to be one segment short of the source because it is a target directory.
    dest_files = tgt_res.root_path
    istorage.copyFiles(src_files, dest_files)

    src_coll = src_res.root_path
    tgt_coll = tgt_res.root_path
    for avu_name in avu_list:
        value = istorage.getAVU(src_coll, avu_name)

        # make formerly public things private
        if avu_name == 'isPublic':
            istorage.setAVU(tgt_coll, avu_name, 'false')

        # bag_modified AVU needs to be set to true for copied resource
        elif avu_name == 'bag_modified':
            istorage.setAVU(tgt_coll, avu_name, 'true')

        # everything else gets copied literally
        else:
            istorage.setAVU(tgt_coll, avu_name, value)

    # link copied resource files to Django resource model
    files = src_res.files.all()

    # if resource files are part of logical files, then logical files also need copying
    src_logical_files = list(set([f.logical_file for f in files if f.has_logical_file]))
    map_logical_files = {}
    for src_logical_file in src_logical_files:
        map_logical_files[src_logical_file] = src_logical_file.get_copy()

    for n, f in enumerate(files):
        folder, base = os.path.split(f.short_path)  # strips object information.
        new_resource_file = ResourceFile.create(tgt_res, base, folder=folder)

        # if the original file is part of a logical file, then
        # add the corresponding new resource file to the copy of that logical file
        if f.has_logical_file:
            tgt_logical_file = map_logical_files[f.logical_file]
            tgt_logical_file.add_resource_file(new_resource_file)

    if src_res.resource_type.lower() == "collectionresource":
        # clone contained_res list of original collection and add to new collection
        # note that new collection resource will not contain "deleted resources"
        tgt_res.resources = src_res.resources.all()


def copy_and_create_metadata(src_res, dest_res):
    """
    Copy metadata from source resource to target resource except identifier, publisher, and date
    which need to be created for the target resource as appropriate. This method is used for
    resource copying and versioning.
    :param src_res: source resource
    :param dest_res: target resource
    :return:
    """
    # copy metadata from source resource to target resource except three elements
    exclude_elements = ['identifier', 'publisher', 'date']
    dest_res.metadata.copy_all_elements_from(src_res.metadata, exclude_elements)

    # create Identifier element that is specific to the new resource
    dest_res.metadata.create_element('identifier', name='hydroShareIdentifier',
                                     url='{0}/resource/{1}'.format(current_site_url(),
                                                                   dest_res.short_id))

    # create date element that is specific to the new resource
    dest_res.metadata.create_element('date', type='created', start_date=dest_res.created)
    dest_res.metadata.create_element('date', type='modified', start_date=dest_res.updated)

    # copy date element to the new resource if exists
    src_res_valid_date_filter = src_res.metadata.dates.all().filter(type='valid')
    if src_res_valid_date_filter:
        res_valid_date = src_res_valid_date_filter[0]
        dest_res.metadata.create_element('date', type='valid', start_date=res_valid_date.start_date,
                                         end_date=res_valid_date.end_date)

    src_res_avail_date_filter = src_res.metadata.dates.all().filter(type='available')
    if src_res_avail_date_filter:
        res_avail_date = src_res_avail_date_filter[0]
        dest_res.metadata.create_element('date', type='available',
                                         start_date=res_avail_date.start_date,
                                         end_date=res_avail_date.end_date)
    # create the key/value metadata
    dest_res.extra_metadata = copy.deepcopy(src_res.extra_metadata)
    dest_res.save()


# TODO: should be BaseResource.mark_as_modified.
def resource_modified(resource, by_user=None, overwrite_bag=True):
    """
    Set an AVU flag that forces the bag to be recreated before fetch.

    This indicates that some content of the bag has been edited.

    """

    resource.last_changed_by = by_user

    resource.updated = now().isoformat()
    # seems this is the best place to sync resource title with metadata title
    resource.title = resource.metadata.title.value
    resource.save()
    if resource.metadata.dates.all().filter(type='modified'):
        res_modified_date = resource.metadata.dates.all().filter(type='modified')[0]
        resource.metadata.update_element('date', res_modified_date.id)

    if overwrite_bag:
        create_bag_files(resource)

    # set bag_modified-true AVU pair for the modified resource in iRODS to indicate
    # the resource is modified for on-demand bagging.
    set_dirty_bag_flag(resource)


# TODO: should be part of BaseResource
def set_dirty_bag_flag(resource):
    """
    Set bag_modified=true AVU pair for the modified resource in iRODS
    to indicate that the resource is modified for on-demand bagging.

    set metadata_dirty (AVU) to 'true' to indicate that metadata has been modified for the
    resource so that xml metadata files need to be generated on-demand

    This is done so that the bag creation can be "lazy", in the sense that the
    bag is recreated only after multiple changes to the bag files, rather than
    after each change. It is created when someone attempts to download it.
    """
    res_coll = resource.root_path

    istorage = resource.get_irods_storage()
    res_coll = resource.root_path
    istorage.setAVU(res_coll, "bag_modified", "true")
    istorage.setAVU(res_coll, "metadata_dirty", "true")


def _validate_email(email):
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def get_profile(user):
    return user.userprofile


def current_site_url():
    """Returns fully qualified URL (no trailing slash) for the current site."""
    from django.contrib.sites.models import Site
    current_site = Site.objects.get_current()
    protocol = getattr(settings, 'MY_SITE_PROTOCOL', 'http')
    port = getattr(settings, 'MY_SITE_PORT', '')
    url = '%s://%s' % (protocol, current_site.domain)
    if port:
        url += ':%s' % port
    return url


def get_file_mime_type(file_name):
    # TODO: looks like the mimetypes module can't find all mime types
    # We may need to user the python magic module instead
    file_format_type = mimetypes.guess_type(file_name)[0]
    if not file_format_type:
        # TODO: this is probably not the right way to get the mime type
        file_format_type = 'application/%s' % os.path.splitext(file_name)[1][1:]

    return file_format_type


def check_file_dict_for_error(file_validation_dict):
    if 'are_files_valid' in file_validation_dict:
        if not file_validation_dict['are_files_valid']:
            error_message = file_validation_dict.get('message',
                                                     "Uploaded file(s) failed validation.")
            raise ResourceFileValidationException(error_message)


def raise_file_size_exception():
    from .resource import FILE_SIZE_LIMIT_FOR_DISPLAY
    error_msg = 'The resource file is larger than the supported size limit: %s.' \
                % FILE_SIZE_LIMIT_FOR_DISPLAY
    raise ResourceFileSizeException(error_msg)


def validate_resource_file_size(resource_files):
    from .resource import check_resource_files
    valid = check_resource_files(resource_files)
    if not valid:
        raise_file_size_exception()


def validate_resource_file_type(resource_cls, files):
    supported_file_types = resource_cls.get_supported_upload_file_types()
    # see if file type checking is needed
    if '.*' in supported_file_types:
        # all file types are supported
        return

    supported_file_types = [x.lower() for x in supported_file_types]
    for f in files:
        file_ext = os.path.splitext(f.name)[1]
        if file_ext.lower() not in supported_file_types:
            err_msg = "{file_name} is not a supported file type for {res_type} resource"
            err_msg = err_msg.format(file_name=f.name, res_type=resource_cls)
            raise ResourceFileValidationException(err_msg)


def validate_resource_file_count(resource_cls, files, resource=None):
    if len(files) > 0:
        if len(resource_cls.get_supported_upload_file_types()) == 0:
            err_msg = "Content files are not allowed in {res_type} resource"
            err_msg = err_msg.format(res_type=resource_cls)
            raise ResourceFileValidationException(err_msg)

        err_msg = "Multiple content files are not supported in {res_type} resource"
        err_msg = err_msg.format(res_type=resource_cls)
        if len(files) > 1:
            if not resource_cls.allow_multiple_file_upload():
                raise ResourceFileValidationException(err_msg)

        if resource is not None and resource.files.all().count() > 0:
            if not resource_cls.can_have_multiple_files():
                raise ResourceFileValidationException(err_msg)


def resource_pre_create_actions(resource_type, resource_title, page_redirect_url_key,
                                files=(), source_names=[], metadata=None,
                                requesting_user=None, **kwargs):
    from.resource import check_resource_type
    from hs_core.views.utils import validate_metadata

    if __debug__:
        assert(isinstance(source_names, list))

    if not resource_title:
        resource_title = 'Untitled resource'
    else:
        resource_title = resource_title.strip()
        if len(resource_title) == 0:
            resource_title = 'Untitled resource'

    resource_cls = check_resource_type(resource_type)
    if len(files) > 0:
        validate_resource_file_size(files)
        validate_resource_file_count(resource_cls, files)
        validate_resource_file_type(resource_cls, files)

    if not metadata:
        metadata = []
    else:
        validate_metadata(metadata, resource_type)

    page_url_dict = {}
    # this is needed since raster and feature resource types allows to upload a zip file,
    # then replace zip file with exploded files. If the zip file is loaded from hydroshare
    # federation zone, the original zip file encoded in source_names gets deleted
    # in this case and fed_res_path is used to keep the federation path, so that the resource
    # will be stored in the federated zone rather than the hydroshare zone
    fed_res_path = []
    # receivers need to change the values of this dict if file validation fails
    file_validation_dict = {'are_files_valid': True, 'message': 'Files are valid'}

    # Send pre-create resource signal - let any other app populate the empty metadata list object
    # also pass title to other apps, and give other apps a chance to populate page_redirect_url
    # if they want to redirect to their own page for resource creation rather than use core
    # resource creation code
    pre_create_resource.send(sender=resource_cls, metadata=metadata, files=files,
                             title=resource_title,
                             url_key=page_redirect_url_key, page_url_dict=page_url_dict,
                             validate_files=file_validation_dict,
                             source_names=source_names,
                             user=requesting_user, fed_res_path=fed_res_path, **kwargs)

    if len(files) > 0:
        check_file_dict_for_error(file_validation_dict)

    return page_url_dict, resource_title,  metadata, fed_res_path


def resource_post_create_actions(resource, user, metadata,  **kwargs):
    # receivers need to change the values of this dict if file validation fails
    file_validation_dict = {'are_files_valid': True, 'message': 'Files are valid'}
    # Send post-create resource signal
    post_create_resource.send(sender=type(resource), resource=resource, user=user,
                              metadata=metadata,
                              validate_files=file_validation_dict, **kwargs)

    check_file_dict_for_error(file_validation_dict)


def prepare_resource_default_metadata(resource, metadata, res_title):
    add_title = True
    for element in metadata:
        if 'title' in element:
            if 'value' in element['title']:
                res_title = element['title']['value']
                add_title = False
            else:
                metadata.remove(element)
            break

    if add_title:
        metadata.append({'title': {'value': res_title}})

    add_language = True
    for element in metadata:
        if 'language' in element:
            if 'code' in element['language']:
                add_language = False
            else:
                metadata.remove(element)
            break

    if add_language:
        metadata.append({'language': {'code': 'eng'}})

    add_rights = True
    for element in metadata:
        if 'rights' in element:
            if 'statement' in element['rights'] and 'url' in element['rights']:
                add_rights = False
            else:
                metadata.remove(element)
            break

    if add_rights:
        # add the default rights/license element
        statement = 'This resource is shared under the Creative Commons Attribution CC BY.'
        url = 'http://creativecommons.org/licenses/by/4.0/'
        metadata.append({'rights': {'statement': statement, 'url': url}})

    metadata.append({'identifier': {'name': 'hydroShareIdentifier',
                                    'url': '{0}/resource/{1}'.format(current_site_url(),
                                                                     resource.short_id)}})

    # remove if there exists the 'type' element as system generates this element
    # remove if there exists 'format' elements - since format elements are system generated based
    # on resource content files
    # remove any 'date' element which is not of type 'valid'. All other date elements are
    # system generated
    for element in list(metadata):
        if 'type' in element or 'format' in element:
            metadata.remove(element)
        if 'date' in element:
            if 'type' in element['date']:
                if element['date']['type'] != 'valid':
                    metadata.remove(element)

    metadata.append({'type': {'url': '{0}/terms/{1}'.format(current_site_url(),
                                                            resource.__class__.__name__)}})

    metadata.append({'date': {'type': 'created', 'start_date': resource.created}})
    metadata.append({'date': {'type': 'modified', 'start_date': resource.updated}})

    # only add the resource creator as the creator for metadata if there is not already
    # creator data in the metadata object
    metadata_keys = [element.keys()[0].lower() for element in metadata]
    if 'creator' not in metadata_keys:
        creator_data = get_party_data_from_user(resource.creator)
        metadata.append({'creator': creator_data})


def get_party_data_from_user(user):
    party_data = {}
    user_profile = get_profile(user)
    user_full_name = user.get_full_name()
    if user_full_name:
        party_name = user_full_name
    else:
        party_name = user.username

    party_data['name'] = party_name
    party_data['email'] = user.email
    party_data['description'] = '/user/{uid}/'.format(uid=user.pk)
    party_data['phone'] = user_profile.phone_1
    party_data['organization'] = user_profile.organization
    return party_data


# TODO: make this part of resource api. resource --> self.
def resource_file_add_pre_process(resource, files, user, extract_metadata=False,
                                  source_names=[], **kwargs):
    if __debug__:
        assert(isinstance(source_names, list))
    resource_cls = resource.__class__
    validate_resource_file_size(files)
    validate_resource_file_type(resource_cls, files)
    validate_resource_file_count(resource_cls, files, resource)

    file_validation_dict = {'are_files_valid': True, 'message': 'Files are valid'}
    pre_add_files_to_resource.send(sender=resource_cls, files=files, resource=resource, user=user,
                                   source_names=source_names,
                                   validate_files=file_validation_dict,
                                   extract_metadata=extract_metadata, **kwargs)

    check_file_dict_for_error(file_validation_dict)


# TODO: make this part of resource api. resource --> self.
def resource_file_add_process(resource, files, user, extract_metadata=False,
                              source_names=[], **kwargs):

    from .resource import add_resource_files
    if __debug__:
        assert(isinstance(source_names, list))
    folder = kwargs.pop('folder', None)
    resource_file_objects = add_resource_files(resource.short_id, *files, folder=folder,
                                               source_names=source_names)

    # receivers need to change the values of this dict if file validation fails
    # in case of file validation failure it is assumed the resource type also deleted the file
    file_validation_dict = {'are_files_valid': True, 'message': 'Files are valid'}
    post_add_files_to_resource.send(sender=resource.__class__, files=files,
                                    source_names=source_names,
                                    resource=resource, user=user,
                                    validate_files=file_validation_dict,
                                    extract_metadata=extract_metadata, **kwargs)

    check_file_dict_for_error(file_validation_dict)

    resource_modified(resource, user, overwrite_bag=False)
    return resource_file_objects


# TODO: move this to BaseResource
def create_empty_contents_directory(resource):
    res_contents_dir = resource.file_path
    istorage = resource.get_irods_storage()
    if not istorage.exists(res_contents_dir):
        istorage.session.run("imkdir", None, '-p', res_contents_dir)


def add_file_to_resource(resource, f, folder=None, source_name='',
                         move=False):
    """
    Add a ResourceFile to a Resource.  Adds the 'format' metadata element to the resource.
    :param resource: Resource to which file should be added
    :param f: File-like object to add to a resource
    :param source_name: the logical file name of the resource content file for
                        federated iRODS resource or the federated zone name;
                        By default, it is empty. A non-empty value indicates
                        the file needs to be added into the federated zone, either
                        from local disk where f holds the uploaded file from local
                        disk, or from the federated zone directly where f is empty
                        but source_name has the whole data object
                        iRODS path in the federated zone
    :param move: indicate whether the file should be copied or moved from private user
                 account to proxy user account in federated zone; A value of False
                 indicates copy is needed, a value of True indicates no copy, but
                 the file will be moved from private user account to proxy user account.
                 The default value is False.

    :return: The identifier of the ResourceFile added.
    """
    if f:

        openfile = File(f) if not isinstance(f, UploadedFile) else f
        ret = ResourceFile.create(resource, openfile, folder=folder, source=None, move=False)

        # add format metadata element if necessary
        file_format_type = get_file_mime_type(f.name)

    elif source_name:
        try:
            # create from existing iRODS file
            ret = ResourceFile.create(resource, None, folder=folder, source=source_name, move=move)
        except SessionException as ex:
            try:
                ret.delete()
            except Exception:
                pass
            # raise the exception for the calling function to inform the error on the page interface
            raise SessionException(ex.exitcode, ex.stdout, ex.stderr)

        # add format metadata element if necessary
        file_format_type = get_file_mime_type(source_name)

    else:
        raise ValueError('Invalid input parameter is passed into this add_file_to_resource() '
                         'function')

    # TODO: generate this from data in ResourceFile rather than extension
    if file_format_type not in [mime.value for mime in resource.metadata.formats.all()]:
        resource.metadata.create_element('format', value=file_format_type)

    return ret


def add_metadata_element_to_xml(root, md_element, md_fields):
    """
    helper function to generate xml elements for a given metadata element that belongs to
    'hsterms' namespace

    :param root: the xml document root element to which xml elements for the specified
    metadata element needs to be added
    :param md_element: the metadata element object. The term attribute of the metadata
    element object is used for naming the root xml element for this metadata element.
    If the root xml element needs to be named differently, then this needs to be a tuple
    with first element being the metadata element object and the second being the name
    for the root element.
    Example:
    md_element=self.Creator    # the term attribute of the Creator object will be used
    md_element=(self.Creator, 'Author') # 'Author' will be used

    :param md_fields: a list of attribute names of the metadata element (if the name to be used
     in generating the xml element name is same as the attribute name then include the
     attribute name as a list item. if xml element name needs to be different from the
     attribute name then the list item must be a tuple with first element of the tuple being
     the attribute name and the second element being what will be used in naming the xml
     element)
     Example:
     [('first_name', 'firstName'), 'phone', 'email']
     # xml sub-elements names: firstName, phone, email
    """
    from lxml import etree
    from hs_core.models import CoreMetaData

    name_spaces = CoreMetaData.NAMESPACES
    if isinstance(md_element, tuple):
        element_name = md_element[1]
        md_element = md_element[0]
    else:
        element_name = md_element.term

    hsterms_newElem = etree.SubElement(root,
                                       "{{{ns}}}{new_element}".format(
                                           ns=name_spaces['hsterms'],
                                           new_element=element_name))
    hsterms_newElem_rdf_Desc = etree.SubElement(
        hsterms_newElem, "{{{ns}}}Description".format(ns=name_spaces['rdf']))
    for md_field in md_fields:
        if isinstance(md_field, tuple):
            field_name = md_field[0]
            xml_element_name = md_field[1]
        else:
            field_name = md_field
            xml_element_name = md_field

        if hasattr(md_element, field_name):
            attr = getattr(md_element, field_name)
            if attr:
                field = etree.SubElement(hsterms_newElem_rdf_Desc,
                                         "{{{ns}}}{field}".format(ns=name_spaces['hsterms'],
                                                                  field=xml_element_name))
                field.text = str(attr)


class ZipContents(object):
    """
    Extract the contents of a zip file one file at a time
    using a generator.
    """
    def __init__(self, zip_file):
        self.zip_file = zip_file

    def black_list_path(self, file_path):
        return file_path.startswith('__MACOSX/')

    def black_list_name(self, file_name):
        return file_name == '.DS_Store'

    def get_files(self):
        temp_dir = tempfile.mkdtemp()
        try:
            file_path = None
            for name_path in self.zip_file.namelist():
                if not self.black_list_path(name_path):
                    name = os.path.basename(name_path)
                    if name != '':
                        if not self.black_list_name(name):
                            self.zip_file.extract(name_path, temp_dir)
                            file_path = os.path.join(temp_dir, name_path)
                            logger.debug("Opening {0} as File with name {1}".format(file_path,
                                                                                    name_path))
                            f = File(file=open(file_path, 'rb'),
                                     name=name_path)
                            f.size = os.stat(file_path).st_size
                            yield f
        finally:
            shutil.rmtree(temp_dir)


def get_file_storage():
    return IrodsStorage() if getattr(settings, 'USE_IRODS', False) else DefaultStorage()


def resolve_request(request):
    if request.POST:
        return request.POST

    if request.data:
        return request.data

    return {}
