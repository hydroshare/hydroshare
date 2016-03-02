from string import Template

def parse_app_url_template(url_template_string, term_dict_list=[]):
    '''
    This func replaces pre-defined HS Terms in url_template_string with real values;
    Example: http://www.myapps.com/app1/?res_id=${HS_RES_TYPE}
        --> http://www.myapps.com/app1/?res_id=GenericResource
    Note: this func will keep unknown Terms unchanged
    :param url_template_string: The url template string contains HS Terms
    :param term_dict_list: a list of dict that stores pairs of Term Name and Term Value
    :return: the updated url string
    '''

    new_url_string = url_template_string
    for term_dict in term_dict_list:
        new_url_string = Template(new_url_string).safe_substitute(term_dict)

    return new_url_string