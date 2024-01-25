import asyncio
import copy
import errno
import logging
import mimetypes
import os
import shutil
import tempfile
import urllib
from urllib.parse import quote
from urllib.request import pathname2url, url2pathname
from uuid import uuid4

import aiohttp
from asgiref.sync import sync_to_async
from datetime import date
from django.apps import apps
from django.contrib.auth.models import Group, User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files import File
from django.core.files.storage import DefaultStorage
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import URLValidator, validate_email
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from mezzanine.conf import settings

from django_irods.icommands import SessionException
from django_irods.storage import IrodsStorage
from hs_access_control.models.community import Community
from hs_core.hydroshare.hs_bagit import create_bag_metadata_files
from hs_core.models import AbstractResource, BaseResource, GeospatialRelation, ResourceFile
from hs_core.signals import post_create_resource, pre_add_files_to_resource, pre_create_resource
from theme.models import QuotaMessage

logger = logging.getLogger(__name__)


class ResourceFileSizeException(Exception):
    pass


class ResourceFileValidationException(Exception):
    pass


class QuotaException(Exception):
    pass


class ResourceCopyException(Exception):
    pass


class ResourceVersioningException(Exception):
    pass


def get_resource_types():
    resource_types = []
    for model in apps.get_models():
        if issubclass(model, AbstractResource) and model != BaseResource:
            if not getattr(model, 'archived_model', False):
                resource_types.append(model)
    return resource_types


def get_content_types():
    content_types = []
    from hs_file_types.models.base import AbstractLogicalFile
    for model in apps.get_models():
        if issubclass(model, AbstractLogicalFile):
            content_types.append(model)
    return content_types


def get_resource_instance(app, model_name, pk, or_404=True):
    model = apps.get_model(app, model_name)
    if or_404:
        return get_object_or_404(model, pk=pk)
    else:
        return model.objects.get(pk=pk)


def get_resource_by_shortkey(shortkey, or_404=True):
    try:
        res = BaseResource.objects.select_related("raccess").get(short_id=shortkey)
    except BaseResource.DoesNotExist:
        if or_404:
            raise Http404(shortkey)
        else:
            raise
    content = res.get_content_model()
    content.raccess = res.raccess
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

    tgt = None
    if str(user).isnumeric():
        try:
            tgt = User.objects.get(pk=int(user))
        except ValueError:
            pass
        except ObjectDoesNotExist:
            pass
    else:
        try:
            tgt = User.objects.get(username__iexact=user)
        except ObjectDoesNotExist:
            try:
                tgt = User.objects.get(email__iexact=user)
            except ObjectDoesNotExist:
                pass

    if tgt is None:
        if raise404:
            raise Http404('User not found')
        else:
            raise ObjectDoesNotExist('User not found')

    return tgt


def group_from_id(grp):
    if isinstance(grp, Group):
        return grp

    try:
        tgt = Group.objects.get(name=grp)
    except ObjectDoesNotExist:
        try:
            tgt = Group.objects.get(pk=int(grp))
        except ValueError:
            raise Http404('Group not found')
        except TypeError:
            raise Http404('Group not found')
        except ObjectDoesNotExist:
            raise Http404('Group not found')
    return tgt


def community_from_id(community):
    if isinstance(community, Community):
        return community

    try:
        tgt = Community.objects.get(name=community)
    except ObjectDoesNotExist:
        try:
            tgt = Community.objects.get(id=int(community))
        except ValueError:
            raise Http404('Community not found')
        except TypeError:
            raise Http404('Community not found')
        except ObjectDoesNotExist:
            raise Http404('Community not found')
    return tgt


def get_user_zone_status_info(user):
    """
    This function should be called to determine whether user zone functionality should be
    enabled or not on the web site front end
    Args:
        user: the requesting user
    Returns:
        enable_user_zone boolean indicating whether user zone functionality should be enabled or
        not on the web site front end
    """
    if user is None:
        return None
    if not hasattr(user, 'userprofile') or user.userprofile is None:
        return None

    enable_user_zone = user.userprofile.create_irods_user_account and settings.REMOTE_USE_IRODS
    return enable_user_zone


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
                                      settings.HS_IRODS_PROXY_USER_IN_USER_ZONE)
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
            zone=zone, local_proxy_user=settings.HS_IRODS_PROXY_USER_IN_USER_ZONE)
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
    if isinstance(irods_fnames, str):
        ifnames = irods_fnames.split(',')
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
                raise Exception(str(ex))
        irods_storage.getFile(ifname, tmpfile)
        ret_file_list.append(tmpfile)
    return ret_file_list


# TODO: make the local cache file (and cleanup) part of ResourceFile state?
def get_file_from_irods(resource, file_path, temp_dir=None):
    """
    Copy the file (given by file_path) from iRODS (local or federated zone)
    over to django (temp directory) which is
    necessary for manipulating the file (e.g. metadata extraction, zipping etc.).
    Note: The caller is responsible for cleaning the temp directory

    :param  resource: an instance of CompositeResource
    :param  file_path: storage path (absolute path) of a file in iRODS
    :param  temp_dir: (optional) existing temp directory to which the file will be copied from
    irods. If temp_dir is None then a new temporary directory will be created.
    :return: path of the copied file
    """

    istorage = resource.get_irods_storage()
    file_name = os.path.basename(file_path)

    if temp_dir is not None:
        if not temp_dir.startswith(settings.TEMP_FILE_DIR):
            raise ValueError("Specified temp directory is not valid")
        elif not os.path.exists(temp_dir):
            raise ValueError("Specified temp directory doesn't exist")

        tmpdir = temp_dir
    else:
        tmpdir = get_temp_dir()

    tmpfile = os.path.join(tmpdir, file_name)
    istorage.getFile(file_path, tmpfile)
    copied_file = tmpfile
    return copied_file


def get_temp_dir():
    """Creates a temporary directory"""

    tmpdir = os.path.join(settings.TEMP_FILE_DIR, uuid4().hex)
    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir)
    os.makedirs(tmpdir)
    return tmpdir


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

    # if resource has logical files, then those logical files also need copying
    map_logical_files = {}
    for src_logical_file in src_res.logical_files:
        map_logical_files[src_logical_file] = src_logical_file.get_copy(tgt_res)

    def copy_file_to_target_resource(scr_file, save_to_db=True):
        kwargs = {}
        src_storage_path = scr_file.get_storage_path(resource=src_res)
        tgt_storage_path = src_storage_path.replace(src_res.short_id, tgt_res.short_id)
        kwargs['content_object'] = tgt_res
        kwargs['file_folder'] = scr_file.file_folder
        if tgt_res.is_federated:
            kwargs['resource_file'] = None
            kwargs['fed_resource_file'] = tgt_storage_path
        else:
            kwargs['resource_file'] = tgt_storage_path
            kwargs['fed_resource_file'] = None

        if save_to_db:
            return ResourceFile.objects.create(**kwargs)
        else:
            return ResourceFile(**kwargs)

    # use bulk_create for files without logical file to copy all files at once
    files_bulk_create = []
    files_without_logical_file = files.filter(logical_file_object_id__isnull=True)
    for f in files_without_logical_file:
        file_to_save = copy_file_to_target_resource(f, save_to_db=False)
        files_bulk_create.append(file_to_save)

    if files_bulk_create:
        ResourceFile.objects.bulk_create(files_bulk_create, batch_size=settings.BULK_UPDATE_CREATE_BATCH_SIZE)

    # copy files with logical file one at a time
    files_with_logical_file = files\
        .filter(logical_file_object_id__isnull=False)\
        .select_related('logical_file_content_type')

    seen_logical_files = {}
    for f in files_with_logical_file:
        if (f.logical_file_object_id, f.logical_file_content_type.id) not in seen_logical_files:
            # accessing logical_file for each file (f.logical_file) generates one database query
            seen_logical_files[(f.logical_file_object_id, f.logical_file_content_type.id)] = f.logical_file

        logical_file = seen_logical_files[(f.logical_file_object_id, f.logical_file_content_type.id)]
        new_resource_file = copy_file_to_target_resource(f)
        tgt_logical_file = map_logical_files[logical_file]
        tgt_logical_file.add_resource_file(new_resource_file)

    for lf in map_logical_files:
        if lf.type_name() == 'ModelProgramLogicalFile':
            # for any model program logical files in original resource need to copy the model program file types
            lf.copy_mp_file_types(tgt_logical_file=map_logical_files[lf])
        elif lf.type_name() == 'ModelInstanceLogicalFile':
            # for any model instance logical files in original resource need to set the executed_by (FK) relation
            lf.copy_executed_by(tgt_logical_file=map_logical_files[lf])

    if src_res.resource_type.lower() == "collectionresource":
        # clone contained_res list of original collection and add to new collection
        # note that new collection resource will not contain "deleted resources"
        tgt_res.resources.set(src_res.resources.all())


@sync_to_async
def _get_relations():
    return list(GeospatialRelation.objects.all())


@sync_to_async
def _save_relation(relation, json):
    return relation.update_from_geoconnex_response(json)


async def get_jsonld_from_geoconnex(relation, client):
    relative_id = relation.value.split("ref/").pop()
    collection = relative_id.split("/")[0]
    id = relative_id.split("/")[1]
    url = f"/collections/{collection}/items/{id}?" \
        "f=jsonld&lang=en-US&skipGeometry=true"
    logger.debug(f"CHECKING RELATION '{relation.text}'")
    async with client.get(url) as resp:
        return await _save_relation(relation, await resp.json())


async def update_geoconnex_texts(relations=[]):
    # Task to update Relations from Geoconnex API
    if not relations:
        relations = await _get_relations()
    validator = URLValidator(regex="geoconnex")
    relations = [r for r in relations if isGeoconnexUrl(r.value, validator)]
    async with aiohttp.ClientSession("https://reference.geoconnex.us") as client:
        await asyncio.gather(*[
            get_jsonld_from_geoconnex(relation, client)
            for relation in relations
        ])
    logger.debug("DONE CHECKING RELATIONS")


def isGeoconnexUrl(text, validator=None):
    if not validator:
        validator = URLValidator(regex="geoconnex")
    try:
        validator(text)
        return True
    except ValidationError:
        return False


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
    # generate metadata and map xml files for logical files in the target resource
    for logical_file in dest_res.logical_files:
        logical_file.create_aggregation_xml_documents()


# TODO: should be BaseResource.mark_as_modified.
def resource_modified(resource, by_user=None, overwrite_bag=True):
    """
    Set an AVU flag that forces the bag to be recreated before fetch.

    This indicates that some content of the bag has been edited.

    """

    if not by_user:
        user = None
    else:
        if isinstance(by_user, User):
            user = by_user
        else:
            try:
                user = User.objects.get(username=by_user)
            except User.DoesNotExist:
                user = None
    if user:
        resource.last_changed_by = user

    resource.updated = now().isoformat()
    # seems this is the best place to sync resource title with metadata title
    resource.title = resource.metadata.title.value
    resource.save()
    res_modified_date = resource.metadata.dates.all().filter(type='modified').first()
    if res_modified_date:
        resource.metadata.update_element('date', res_modified_date.id)

    if overwrite_bag:
        create_bag_metadata_files(resource)

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
    file_name = "{}".format(file_name)
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
    valid, size = check_resource_files(resource_files)
    if not valid:
        raise_file_size_exception()
    # if no exception, return the total size of all files
    return size


def validate_resource_file_count(resource_cls, files):
    if len(files) > 0:
        resource_type = resource_cls.__name__
        if resource_type != "CompositeResource":
            err_msg = "Content files are not allowed in {res_type} resource"
            err_msg = err_msg.format(res_type=resource_cls)
            raise ResourceFileValidationException(err_msg)


def convert_file_size_to_unit(size, unit):
    """
    Convert file size to unit for quota comparison
    :param size: in byte unit
    :param unit: should be one of the four: 'KB', 'MB', 'GB', or 'TB'
    :return: the size converted to the pass-in unit
    """
    unit = unit.lower()
    if unit not in ('kb', 'mb', 'gb', 'tb'):
        raise ValidationError('Pass-in unit for file size conversion must be one of KB, MB, GB, '
                              'or TB')
    factor = 1024.0
    kbsize = size / factor
    if unit == 'kb':
        return kbsize
    mbsize = kbsize / factor
    if unit == 'mb':
        return mbsize
    gbsize = mbsize / factor
    if unit == 'gb':
        return gbsize
    tbsize = gbsize / factor
    if unit == 'tb':
        return tbsize


def validate_user_quota(user_or_username, size):
    """
    validate to make sure the user is not over quota with the newly added size
    :param user_or_username: the user to be validated
    :param size: the newly added file size to add on top of the user's used quota to be validated.
                 size input parameter should be in byte unit
    :return: raise exception for the over quota case
    """
    # todo 5228 check when we run this validation
    if user_or_username:
        if isinstance(user_or_username, User):
            user = user_or_username
        else:
            try:
                user = User.objects.get(username=user_or_username)
            except User.DoesNotExist:
                user = None
    else:
        user = None

    if user:
        # validate it is within quota hard limit
        uq = user.quotas.filter(zone='hydroshare').first()
        if uq:
            if not QuotaMessage.objects.exists():
                QuotaMessage.objects.create()
            qmsg = QuotaMessage.objects.first()
            enforce_flag = qmsg.enforce_quota
            if enforce_flag:
                hard_limit = qmsg.hard_limit_percent
                used_size = uq.add_to_used_value(size)
                used_percent = uq.used_percent
                rounded_percent = round(used_percent, 2)
                rounded_used_val = round(used_size, 4)
                if used_percent >= hard_limit or uq.grace_period_ends <= date.today():
                    msg_template_str = '{}{}\n\n'.format(qmsg.enforce_content_prepend,
                                                         qmsg.content)
                    msg_str = msg_template_str.format(used=rounded_used_val,
                                                      unit=uq.unit,
                                                      allocated=uq.allocated_value,
                                                      zone=uq.zone,
                                                      percent=rounded_percent)
                    raise QuotaException(msg_str)


def resource_pre_create_actions(resource_type, resource_title, page_redirect_url_key,
                                files=(), metadata=None,
                                requesting_user=None, **kwargs):
    from .resource import check_resource_type
    from hs_core.views.utils import validate_metadata

    if not resource_title:
        resource_title = 'Untitled resource'
    else:
        resource_title = resource_title.strip()
        if len(resource_title) == 0:
            resource_title = 'Untitled resource'

    resource_cls = check_resource_type(resource_type)
    if len(files) > 0:
        size = validate_resource_file_size(files)
        validate_resource_file_count(resource_cls, files)
        # validate it is within quota hard limit
        validate_user_quota(requesting_user, size)

    if not metadata:
        metadata = []
    else:
        validate_metadata(metadata, resource_type)

    page_url_dict = {}
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
                             user=requesting_user, **kwargs)

    if len(files) > 0:
        check_file_dict_for_error(file_validation_dict)

    return page_url_dict, resource_title, metadata


def resource_post_create_actions(resource, user, metadata, **kwargs):
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
    metadata_keys = [list(element.keys())[0].lower() for element in metadata]
    if 'creator' not in metadata_keys:
        creator_data = get_party_data_from_user(resource.creator)
        metadata.append({'creator': creator_data})


def get_user_party_name(user):
    user_profile = get_profile(user)
    if user.last_name and user.first_name:
        if user_profile.middle_name:
            party_name = '%s, %s %s' % (user.last_name, user.first_name,
                                        user_profile.middle_name)
        else:
            party_name = '%s, %s' % (user.last_name, user.first_name)
    elif user.last_name:
        party_name = user.last_name
    elif user.first_name:
        party_name = user.first_name
    elif user_profile.middle_name:
        party_name = user_profile.middle_name
    else:
        party_name = ''
    return party_name


def get_party_data_from_user(user):
    party_data = {}
    user_profile = get_profile(user)
    party_name = get_user_party_name(user)

    party_data['name'] = party_name
    party_data['email'] = user.email
    party_data['hydroshare_user_id'] = user.pk
    party_data['phone'] = user_profile.phone_1
    party_data['organization'] = user_profile.organization
    party_data['identifiers'] = user_profile.identifiers
    return party_data


# TODO: make this part of resource api. resource --> self.
def resource_file_add_pre_process(resource, files, user, extract_metadata=False,
                                  source_names=[], **kwargs):
    if __debug__:
        assert (isinstance(source_names, list))

    if resource.raccess.published and not user.is_superuser:
        raise ValidationError("Only admin can add files to a published resource")

    resource_cls = resource.__class__
    if len(files) > 0:
        size = validate_resource_file_size(files)
        validate_user_quota(resource.get_quota_holder(), size)
        validate_resource_file_count(resource_cls, files)

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
        assert (isinstance(source_names, list))

    if resource.raccess.published and not user.is_superuser:
        raise ValidationError("Only admin can add files to a published resource")

    folder = kwargs.pop('folder', '')
    full_paths = kwargs.pop('full_paths', {})
    auto_aggregate = kwargs.pop('auto_aggregate', True)
    resource_file_objects = add_resource_files(resource.short_id, *files, folder=folder,
                                               source_names=source_names, full_paths=full_paths,
                                               auto_aggregate=auto_aggregate, user=user)
    resource.refresh_from_db()
    return resource_file_objects


# TODO: move this to BaseResource
def create_empty_contents_directory(resource):
    res_contents_dir = resource.file_path
    istorage = resource.get_irods_storage()
    if not istorage.exists(res_contents_dir):
        istorage.session.run("imkdir", None, '-p', res_contents_dir)


def add_file_to_resource(resource, f, folder='', source_name='',
                         check_target_folder=False, add_to_aggregation=True, user=None,
                         save_file_system_metadata=False):
    """
    Add a ResourceFile to a Resource.  Adds the 'format' metadata element to the resource.
    :param  resource: Resource to which file should be added
    :param  f: File-like object to add to a resource
    :param  folder: folder at which the file will live
    :param  source_name: the logical file name of the resource content file for
                        federated iRODS resource or the federated zone name;
                        By default, it is empty. A non-empty value indicates
                        the file needs to be added into the federated zone, either
                        from local disk where f holds the uploaded file from local
                        disk, or from the federated zone directly where f is empty
                        but source_name has the whole data object
                        iRODS path in the federated zone
    :param  check_target_folder: if true and the resource is a composite resource then uploading
    a file to the specified folder will be validated before adding the file to the resource
    :param  add_to_aggregation: if true and the resource is a composite resource then the file
    being added to the resource also will be added to a fileset aggregation if such an aggregation
    exists in the file path
    :param  user: user who is adding file to the resource
    :param  save_file_system_metadata: if True, file system metadata will be retrieved from iRODS and saved in DB
    :return: The identifier of the ResourceFile added.
    """

    # validate parameters
    if resource.raccess.published:
        if user is None or not user.is_superuser:
            raise ValidationError("Only admin can add files to a published resource")

    if check_target_folder and resource.resource_type != 'CompositeResource':
        raise ValidationError("Resource must be a CompositeResource for validating target folder")

    if f:
        if check_target_folder and folder:
            tgt_full_upload_path = os.path.join(resource.file_path, folder)
            if not resource.can_add_files(target_full_path=tgt_full_upload_path):
                err_msg = "File can't be added to this folder which represents an aggregation"
                raise ValidationError(err_msg)
        openfile = File(f) if not isinstance(f, UploadedFile) else f
        ret = ResourceFile.create(resource, openfile, folder=folder, source=None)
        if add_to_aggregation:
            if folder and resource.resource_type == 'CompositeResource':
                aggregation = resource.get_model_aggregation_in_path(folder)
                if aggregation is None:
                    aggregation = resource.get_fileset_aggregation_in_path(folder)
                if aggregation is not None:
                    # make the added file part of the fileset or model program/instance aggregation
                    aggregation.add_resource_file(ret)

        # add format metadata element if necessary
        file_format_type = get_file_mime_type(f.name)

    elif source_name:
        try:
            # create from existing iRODS file
            ret = ResourceFile.create(resource, file=None, folder=folder, source=source_name)
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
    if not resource.metadata.formats.filter(value=file_format_type).exists():
        resource.metadata.create_element('format', value=file_format_type)
    if save_file_system_metadata:
        ret.set_system_metadata(resource=resource)

    return ret


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


def check_aggregations(resource, res_files):
    """
    A helper to support creating aggregations for a given composite resource when new files are
    added to the resource
    Checks for aggregations in each folder first, then checks for aggregations in each file
    :param resource: resource object
    :param res_files: list of ResourceFile objects to check for aggregations creation
    :return:
    """
    new_logical_files = []
    if resource.resource_type == "CompositeResource":
        from hs_file_types.utils import set_logical_file_type

        # check files for aggregation creation
        for res_file in res_files:
            if not res_file.has_logical_file or (res_file.logical_file.is_fileset
                                                 or res_file.logical_file.is_model_instance):
                # create aggregation from file 'res_file'
                logical_file = set_logical_file_type(res=resource, user=None, file_id=res_file.pk,
                                                     fail_feedback=False)
                if logical_file:
                    new_logical_files.append(logical_file)
    return new_logical_files


def build_preview_data_url(resource, folder_path, spatial_coverage):
    """Get a GeoServer layer preview link."""

    if resource.raccess.public is True:
        try:
            geoserver_url = settings.HSWS_GEOSERVER_URL
            resource_id = resource.short_id
            layer_id = '.'.join('/'.join(folder_path.split('/')[2:]).split('.')[:-1])

            for k, v in settings.HSWS_GEOSERVER_ESCAPE.items():
                layer_id = layer_id.replace(k, v)

            layer_id = quote(f'HS-{resource_id}:{layer_id}')

            extent = quote(','.join((
                str(spatial_coverage['westlimit']),
                str(spatial_coverage['southlimit']),
                str(spatial_coverage['eastlimit']),
                str(spatial_coverage['northlimit']),
            )))

            layer_srs = quote(spatial_coverage['projection'][-9:])

            preview_data_url = (
                f'{geoserver_url}/HS-{resource_id}/wms'
                f'?service=WMS&version=1.1&request=GetMap'
                f'&layers={layer_id}'
                f'&bbox={extent}'
                f'&width=800&height=500'
                f'&srs={layer_srs}'
                f'&format=application/openlayers'
            )

        except Exception as e:
            logger.exception("build_preview_data_url: " + str(e))
            preview_data_url = None

    else:
        preview_data_url = None

    return preview_data_url


def encode_resource_url(url):
    """
    URL encodes a full resource file/folder url.
    :param url: a string url
    :return: url encoded string
    """
    parsed_url = urllib.parse.urlparse(url)
    url_encoded_path = pathname2url(parsed_url.path)
    encoded_url = parsed_url._replace(path=url_encoded_path).geturl()
    return encoded_url


def decode_resource_url(url):
    """
    URL decodes a full resource file/folder url.
    :param url: an encoded string url
    :return: url decoded string
    """
    parsed_url = urllib.parse.urlparse(url)
    url_encoded_path = url2pathname(parsed_url.path)
    encoded_url = parsed_url._replace(path=url_encoded_path).geturl()
    return encoded_url
