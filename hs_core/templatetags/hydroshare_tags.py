from __future__ import absolute_import, division, unicode_literals
from future.builtins import int

from mezzanine import template

from hs_core.hydroshare.utils import get_resource_by_shortkey


register = template.Library()


@register.filter
def user_permission(content, arg):
    user_pk = arg
    permission = "None"
    res_obj = content.get_content_model()
    if res_obj.raccess.owners.filter(pk=user_pk).exists():
        permission = "Owner"
    elif res_obj.raccess.edit_users.filter(pk=user_pk).exists():
        permission = "Edit"
    elif res_obj.raccess.view_users.filter(pk=user_pk).exists():
        permission = "View"

    if permission == "None":
        if res_obj.raccess.published or res_obj.raccess.discoverable or res_obj.raccess.public:
            permission = "Open Access"
    return permission


@register.filter
def resource_type(content):
    return content.get_content_model()._meta.verbose_name


@register.filter
def contact(content):
    """
    Takes a value edited via the WYSIWYG editor, and passes it through
    each of the functions specified by the RICHTEXT_FILTERS setting.
    """
    if not content:
        return ''

    if not content.is_authenticated():
        content = "Anonymous"
    elif content.first_name:
        content = """<a href='/user/{uid}/'>{fn} {ln}<a>""".format(fn=content.first_name,
                                                                   ln=content.last_name,
                                                                   uid=content.pk)
    else:
        content = """<a href='/user/{uid}/'>{un}<a>""".format(uid=content.pk, un=content.username)

    return content


@register.filter
def best_name(content):
    """
    Takes a value edited via the WYSIWYG editor, and passes it through
    each of the functions specified by the RICHTEXT_FILTERS setting.
    """

    if not content.is_authenticated():
        content = "Anonymous"
    elif content.first_name:
        content = """{fn} {ln}""".format(fn=content.first_name, ln=content.last_name,
                                         un=content.username)
    else:
        content = content.username

    return content


@register.filter
def clean_pagination_url(content):
    if "?q=" not in content:
        content += "?q="
    if "&page=" not in content:
        return content
    else:
        clean_content = ''
        parsed_content = content.split("&")
        for token in parsed_content:
            if "page=" not in token:
                clean_content += token + '&'
        clean_content = clean_content[:-1]
        return clean_content


@register.filter
def to_int(value):
    return int(value)


@register.filter
def relative_irods_path(fed_irods_file_name):
    idx = fed_irods_file_name.find('/data/contents/')
    return fed_irods_file_name[idx+1:]


@register.filter
def resource_from_uuid(id):
    return get_resource_by_shortkey(id)


@register.filter
def res_uuid_from_res_path(path):
    prefix_str = 'resource/'
    prefix_idx = path.find(prefix_str)
    if prefix_idx >= 0:
        sidx = prefix_idx+len(prefix_str)
        # resource uuid is 32 bits
        return path[sidx:sidx+32]
    else:
        return path


@register.filter
def remove_last_char(statement):
    return statement[:len(statement)-1]