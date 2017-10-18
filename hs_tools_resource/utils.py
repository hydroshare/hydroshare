from string import Template
import logging
from hs_core.hydroshare.utils import get_resource_types
from hs_file_types.utils import get_file_types

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


def get_SupportedFileTypes_choices():
    """
    This function harvests all existing file types in system,
    and puts them in a list (except for WebApp (ToolResource) Resource type):
    [
        ["RESOURCE_CLASS_NAME_1", "RESOURCE_VERBOSE_NAME_1"],
        ["RESOURCE_CLASS_NAME_2", "RESOURCE_VERBOSE_NAME_2"],
        ...
        ["RESOURCE_CLASS_NAME_N", "RESOURCE_VERBOSE_NAME_N"],
    ]
    """

    result_list = []
    file_types_list = get_file_types()
    for r_type in file_types_list:
        class_name = r_type.__name__
        verbose_name = r_type._meta.verbose_name
        result_list.append([class_name, class_name])
    return result_list