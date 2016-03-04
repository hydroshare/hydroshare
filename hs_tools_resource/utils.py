from string import Template
import logging

logger = logging.getLogger(__name__)

def parse_app_url_template(url_template_string, term_dict_list=()):
    '''
    This func replaces pre-defined HS Terms in url_template_string with real values;
    Example: http://www.myapps.com/app1/?res_type=${HS_RES_TYPE}
        --> http://www.myapps.com/app1/?res_type=GenericResource
    :param url_template_string: The url template string contains HS Terms
    :param term_dict_list: a list of dict that stores pairs of Term Name and Term Value
    :return: the updated url string, or None if template contains undefined terms
    '''
    new_url_string = url_template_string
    merged_term_dic = {}
    try:
        for term_dict in term_dict_list:
            merged_term_dic.update(term_dict)

        new_url_string = Template(new_url_string).substitute(merged_term_dic)
    except Exception as ex:
        logger.exception("[WebApp] '{0}' cannot be parsed by term_dict {1}.".format(new_url_string, str(merged_term_dic)))
        new_url_string = None
    finally:
        return new_url_string