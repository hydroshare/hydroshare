from __future__ import absolute_import
from rest_framework.exceptions import *
import json
import os
import string

from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import UploadedFile

from ga_resources.utils import get_user
from hs_core import hydroshare
from hs_core.hydroshare import check_resource_type
from hs_core.models import AbstractMetaDataElement, GenericResource
from hs_core.signals import pre_metadata_element_create
from hs_core.hydroshare import file_size_limit
from hs_core.hydroshare.utils import raise_file_size_exception
from django_irods.storage import IrodsStorage

# Since an SessionException will be raised for all irods-related operations from django_irods module,
# there is no need to raise iRODS SessionException from within this function
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
    :return: None, but the downloaded file from the iRODS will be appended to res_files list for uploading
    """
    irods_storage = IrodsStorage()
    irods_storage.set_user_session(username=username, password=password, host=host, port=port, zone=zone)
    ifnames = string.split(irods_fnames, ',')
    for ifname in ifnames:
        size = irods_storage.size(ifname)
        if size > file_size_limit:
            raise_file_size_exception()
        tmpFile = irods_storage.download(ifname)
        fname = os.path.basename(ifname.rstrip(os.sep))
        res_files.append(UploadedFile(file=tmpFile, name=fname, size=size))

def authorize(request, res_id, discoverable=False, edit=False, view=False,
              full=False, superuser=False, raises_exception=True):
    """
    Authorizes the user making this request for the OR of the parameters.  If the user has ANY permission set to True in
    the parameter list, then this returns True else False.
    """
    user = get_user(request)
    try:
        res = hydroshare.utils.get_resource_by_shortkey(res_id, or_404=False)
    except ObjectDoesNotExist:
        raise NotFound(detail="No resource was found for resource id:%s" % res_id)

    if discoverable and (edit is False and view is False and full is False and superuser is False):
        authorized = res.raccess.discoverable
    elif user.is_authenticated():
        authorized = (view and user.uaccess.can_view_resource(res)) or \
                     (edit and user.uaccess.can_change_resource(res)) or \
                     (full and user.uaccess.owns_resource(res)) or \
                     (discoverable and res.raccess.discoverable) or \
                     (superuser and user.is_superuser)
    else:
        authorized = (view and res.raccess.public) or \
                     (discoverable and res.raccess.discoverable)
                     
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
                element_attribute = getattr(element_class(), attribute_name, None)
                if element_attribute is None or callable(element_attribute):
                    element_attribute_names_valid = False
                    validation_errors['metadata'].append("Invalid attribute name:%s found for metadata element name:%s." % (attribute_name, k))

            if element_attribute_names_valid:
                if is_core_element:
                    element_resource_class = GenericResource().__class__
                else:
                    element_resource_class = resource_class

                handler_response = pre_metadata_element_create.send(sender=element_resource_class, element_name=k,
                                                                request=MetadataElementRequest(**v))
                for receiver, response in handler_response:
                    if 'is_valid' in response:
                        if not response['is_valid']:
                            validation_errors['metadata'].append("Invalid data found for metadata element name:%s." % k)
                    else:
                        validation_errors['metadata'].append("Invalid data found for metadata element name:%s." % k)

    if len(validation_errors['metadata']) > 0:
        raise ValidationError(detail=validation_errors)


class MetadataElementRequest(object):
    def __init__(self, **element_data_dict):
        self.POST = element_data_dict


def create_form(formclass, request):
    try:
        params = formclass(data=json.loads(request.body))
    except ValueError:
        params = formclass(data=request.REQUEST)

    return params

