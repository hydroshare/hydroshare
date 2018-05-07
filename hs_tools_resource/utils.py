import os
from string import Template
import logging
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_types, get_resource_by_shortkey
from django_irods.icommands import SessionException


logger = logging.getLogger(__name__)


def parse_app_url_template(url_template_string, term_dict_list=()):
    """
    This func replaces pre-defined HS Terms in url_template_string with real values;
    Example: http://www.myapps.com/app1/?res_type=${HS_RES_TYPE}
        --> http://www.myapps.com/app1/?res_type=GenericResource
    :param url_template_string: The url template string contains HS Terms
    :param term_dict_list: a list of dict that stores pairs of Term Name and Term Value
    :return: the updated url string, or None if template contains undefined terms
    """

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


def do_work_when_launching_app_as_needed(app_shortkey, res_shortkey, user):
    """
    check whether there are extra work needed to be done when the app is launched.
    :param app_shortkey: shortkey of the app tool resource to be launched
    :param res_shortkey: shortkey of the resource launching the app tool resource
    :param user: requesting user
    :return: error message if an exception is raised; otherwise, return None
    """

    # When app resource has iRODS federation target path and target resource defined as
    # extended metadata, the resource needs to be pushed to the specified iRODS federation path
    # in the specified iRODS storage resource.
    try:
        res = get_resource_by_shortkey(res_shortkey)
        app_res = get_resource_by_shortkey(app_shortkey)

        # check whether irods_path_key and irods_resc_key are added as extended metadata of the
        # app tool resource, and if they are, pass them out as context variables for app launcher
        # to push resource to federated iRODS path accordingly
        irods_path_key = 'irods_federation_target_path'
        irods_resc_key = 'irods_federation_target_resource'
        filterd_app_obj = BaseResource.objects.filter(short_id=app_shortkey).filter(
            extra_metadata__has_key=irods_path_key).filter(
            extra_metadata__has_key=irods_resc_key).first()
        if filterd_app_obj:
            if not user.is_authenticated():
                return "Only authorized users can launch the web app tool - Please sign in first."
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
            return None
    except SessionException as ex:
        return ex.stderr
    except Exception as ex:
        return ex.message
