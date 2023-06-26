import logging
import math
from string import Template

from hs_collection_resource.models import CollectionResource
from hs_composite_resource.models import CompositeResource

logger = logging.getLogger(__name__)


def parse_app_url_template(url_template_string, term_dict_list=()):
    """
    This func replaces pre-defined HS Terms in url_template_string with real values;
    Example: http://www.myapps.com/app1/?res_type=${HS_RES_TYPE}
        --> http://www.myapps.com/app1/?res_type=CompositeResource
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
        log_msg = "[WebApp] '{0}' cannot be parsed by term_dict {1}, skipping."
        log_msg = log_msg.format(new_url_string, str(merged_term_dic))
        logger.debug(log_msg)
        new_url_string = None
    finally:
        return new_url_string


def get_SupportedResTypes_choices():
    """
    This function generates a list of resource types currently supported for web app
    """

    supported_resource_types = [[CompositeResource.__name__, CompositeResource.display_name],
                                [CollectionResource.__name__, CollectionResource.display_name]]

    return supported_resource_types


def get_SupportedSharingStatus_choices():
    return [['Published', 'Published'],
            ['Public', 'Public'],
            ['Discoverable', 'Discoverable'],
            ['Private', 'Private'],
            ]


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])
