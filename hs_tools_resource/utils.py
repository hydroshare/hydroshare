import os
from string import Template
import logging
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_types, get_resource_by_shortkey
from django_irods.icommands import SessionException
from hs_tools_resource.app_keys import irods_path_key, irods_resc_key, user_auth_flag_key


logger = logging.getLogger(__name__)


class WebAppLaunchException(Exception):
    pass


def parse_app_url_template(url_template_string, term_dict_list=()):
    """
    This func replaces pre-defined HS Terms in url_template_string with real values;
    Example: http://www.myapps.com/app1/?res_type=${HS_RES_TYPE}
        --> http://www.myapps.com/app1/?res_type=GenericResource
    :param url_template_string: The url template string contains HS Terms
    :param term_dict_list: a list of dict that stores pairs of Term Name and Term Value
    :return: the updated url string, or None if template contains undefined terms
    """

    if not url_template_string:
        return None

    new_url_string = url_template_string
    merged_term_dic = {}
    try:
        for term_dict in term_dict_list:
            merged_term_dic.update(term_dict)

        new_url_string = Template(new_url_string).substitute(merged_term_dic)
    except Exception:
        logger.exception("[WebApp] '{0}' cannot be parsed by term_dict {1}.".
                         format(new_url_string, str(merged_term_dic)))
        new_url_string = None
    finally:
        return new_url_string


def get_SupportedResTypes_choices():
    """
    This function harvests all existing resource types in system,
    and puts them in a list (except for WebApp (ToolResource) Resource type):
    [
        ["RESOURCE_CLASS_NAME_1", "RESOURCE_VERBOSE_NAME_1"],
        ["RESOURCE_CLASS_NAME_2", "RESOURCE_VERBOSE_NAME_2"],
        ...
        ["RESOURCE_CLASS_NAME_N", "RESOURCE_VERBOSE_NAME_N"],
    ]
    """

    result_list = []
    res_types_list = get_resource_types()
    for r_type in res_types_list:
        class_name = r_type.__name__
        verbose_name = r_type._meta.verbose_name
        if "toolresource" != class_name.lower():
            result_list.append([class_name, verbose_name])
    return result_list


def get_SupportedSharingStatus_choices():
    return [['Published', 'Published'],
            ['Public', 'Public'],
            ['Discoverable', 'Discoverable'],
            ['Private', 'Private'],
            ]


def copy_res_to_specified_federated_irods_server_as_needed(app_shortkey, res_shortkey, user):
    """
    When app resource has iRODS federation target path and target resource defined as
    extended metadata, the resource needs to be pushed to the specified iRODS federation path
    in the specified iRODS storage resource.
    :param app_shortkey: shortkey of the app tool resource to be launched
    :param res_shortkey: shortkey of the resource launching the app tool resource
    :param user: requesting user
    :return:
    """
    # check whether irods_path_key and irods_resc_key are added as extended metadata of the
    # app tool resource, and if they are, push resource to specified iRODS target accordingly
    filterd_app_obj = BaseResource.objects.filter(short_id=app_shortkey).filter(
        extra_metadata__has_key=irods_path_key).filter(
        extra_metadata__has_key=irods_resc_key).first()
    if filterd_app_obj:
        try:
            res = get_resource_by_shortkey(res_shortkey)
            app_res = get_resource_by_shortkey(app_shortkey)
            user_auth_key_exist = BaseResource.objects.filter(short_id=app_shortkey).filter(
                extra_metadata__has_key=user_auth_flag_key).first()
            if user_auth_key_exist:
                req_user_auth = True \
                    if app_res.extra_metadata[user_auth_flag_key].lower() == 'true' \
                    else False
                if req_user_auth and not user.is_authenticated():
                    err_msg = "Only authorized users can launch the web app tool - " \
                              "Please sign in first."
                    raise WebAppLaunchException(err_msg)

            irods_path = app_res.extra_metadata[irods_path_key]
            irods_resc = app_res.extra_metadata[irods_resc_key]
            istorage = res.get_irods_storage()
            src_path = res.root_path
            # delete all temporary resources copied to this user's space before pushing resource
            dest_path = os.path.join(irods_path, user.username)
            if istorage.exists(dest_path):
                istorage.delete(dest_path)
            dest_path = os.path.join(dest_path, res_shortkey)
            istorage.copyFiles(src_path, dest_path, irods_resc)
        except SessionException as ex:
            raise WebAppLaunchException(ex.stderr)
        except Exception as ex:
            raise WebAppLaunchException(ex.message)


def do_work_when_launching_app_as_needed(app_shortkey, res_shortkey, user):
    """
    check whether there are extra work needed to be done when the app is launched.
    :param app_shortkey: shortkey of the app tool resource to be launched
    :param res_shortkey: shortkey of the resource launching the app tool resource
    :param user: requesting user
    :return:
    """
    copy_res_to_specified_federated_irods_server_as_needed(app_shortkey, res_shortkey, user)
