# $(HS_RES_ID)  resource id
# $(HS_RES_TYPE) resource id
# $(HS_USR_NAME) user name

def HS_term_dict(res_obj, usr_obj):
    term_dict = {}

    if res_obj:
        term_dict["HS_RES_ID"] = res_obj.short_id
        term_dict["HS_RES_TYPE"] = res_obj.resource_type

    if usr_obj:
        term_dict["HS_USR_NAME"] = usr_obj.username if usr_obj.is_authenticated() else "anonymous"

    return term_dict


def parse_app_url(url_string, term_dict):

    new_url_string = url_string
    for key, value in term_dict.iteritems():
        new_url_string = new_url_string.replace("$({0})".format(key), str(value))

    return new_url_string