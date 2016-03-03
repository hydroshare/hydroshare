from string import Template
from hs_core.hydroshare import utils
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

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
    try:
        all_term_dict = {}
        for term_dict in term_dict_list:
            all_term_dict.update(term_dict)

        new_url_string = Template(new_url_string).substitute(all_term_dict)

    except Exception as ex:
        new_url_string = "INVALID_URL"
    finally:
        return new_url_string

# loop through all existing res type classes to harvest all supported HS Terms
def get_all_supported_hs_terms():
    all_supported_term_list = []

    res_cls_list = utils.get_resource_types()
    for res_cls in res_cls_list:
        res_terms = res_cls.get_supported_hs_term_names()
        all_supported_term_list = list(set(all_supported_term_list) | set(res_terms))

    return all_supported_term_list

# check if all ${...} terms match terms pre-defined in all resouece type classes
def validate_hs_terms_in_url_template(url_template_string):
    result = {"status": "success", "msg": ""}
    try:
        all_supported_term_list = get_all_supported_hs_terms()

        # HS_USR_NAME is not defined in any resouce type class
        all_supported_term_list.append("HS_USR_NAME")

        term_count = len(all_supported_term_list)
        dummy_value_list = ["DUMMY_VALUE"] * term_count
        dummy_term_dict = dict(zip(all_supported_term_list, dummy_value_list))
        new_url_string = Template(url_template_string).substitute(dummy_term_dict)

    except KeyError as ex:
        result["status"] = "error"
        result["msg"] = "Found undefined term: " + ex.message
    except ValueError as ex:
        result["status"] = "error"
        result["msg"] = ex.message
    except Exception as ex:
        result["status"] = "error"
        result["msg"] = ex.message
    finally:
        return result

# check url
def validate_url(url):
    is_valid = True
    my_url_validator = URLValidator()
    my_url = url # url to be verified

    try:
       my_url_validator(my_url)
    except ValidationError:
        is_valid = False
    finally:
        return is_valid
