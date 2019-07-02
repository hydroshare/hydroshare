from __future__ import absolute_import, division, unicode_literals
from future.builtins import int

from django.utils.html import format_html

from mezzanine import template

from hs_core.hydroshare.utils import get_resource_by_shortkey

from hs_core.search_indexes import normalize_name


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
def user_resource_labels(resource, user):
    # get a list of labels associated with a specified resource by a given user
    if resource.has_labels:
        return resource.rlabels.get_labels(user)
    return []


@register.filter
def app_on_open_with_list(content, arg):
    """
    Check whether a webapp resource is on current user's open-with list
    content: resource object
    arg: user object
    """

    user_obj = arg
    res_obj = content
    result = res_obj.rlabels.is_open_with_app(user_obj)
    return result


@register.filter
def resource_type(content):
    return content.get_content_model()._meta.verbose_name


@register.filter
def resource_first_author(content):
    if not content:
        return ''
    if content.first_creator.name and content.first_creator.description:
        return format_html('<a href="{desc}">{name}</a>',
                           desc=content.first_creator.description,
                           name=content.first_creator.name)
    elif content.first_creator.name:
        return format_html('<span>{name}</span>', name=content.first_creator.name)
    else:
        first_creator = content.metadata.creators.filter(order=1).first()
        if first_creator.name:
            return format_html('<span>{name}</span>', name=first_creator.name)
        if first_creator.organization:
            return format_html('<span>{name}</span>', name=first_creator.organization)

        return ''


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
        if content.userprofile.middle_name:
            content = format_html("<a href='/user/{uid}/'>{fn} {mn} {ln}</a>",
                                  fn=content.first_name,
                                  mn=content.userprofile.middle_name,
                                  ln=content.last_name,
                                  uid=content.pk)
        else:
            content = format_html("<a href='/user/{uid}/'>{fn} {ln}</a>",
                                  fn=content.first_name,
                                  ln=content.last_name,
                                  uid=content.pk)
    else:
        content = format_html("<a href='/user/{uid}/'>{un}</a>",
                              uid=content.pk,
                              un=content.username)

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
        if content.userprofile.middle_name:
            content = "{fn} {mn} {ln}".format(fn=content.first_name,
                                              mn=content.userprofile.middle_name,
                                              ln=content.last_name)
        else:
            content = "{fn} {ln}".format(fn=content.first_name, ln=content.last_name)
    else:
        content = content.username

    return content


@register.filter
def name_without_commas(name):
    """
    Takes a name formatted as "[LastNames], [FirstNames]"
    and returns it formatted as "[FirstNames] [LastNames]".
    If a name without commas is passed it is returned unchanged.
    """

    if name and "," in name:
        name_parts = name.split(",")

        if len(name_parts) == 2:
            first_names = name_parts[1].strip()
            last_names = name_parts[0].strip()
            return first_names + " " + last_names

    return name  # default


@register.filter
def display_name(user):
    """
    take a User instance and return the full name of the user regardless of whether the user
    is authenticated or not. This filter is used by changing quota holders.
    """

    if user.first_name:
        content = "{fn} {ln} ({un})".format(fn=user.first_name, ln=user.last_name,
                                            un=user.username)
    else:
        content = user.username

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


@register.filter
def five_options_around(page):
    """ Create five page numbers around current page for discovery pagination. """
    if page.number <= 3:
        return range(1, min(5, page.paginator.num_pages) + 1)
    elif page.number >= (page.paginator.num_pages - 2):
        return range(max((page.paginator.num_pages - 4), 1),
                     page.paginator.num_pages + 1)
    else:
        return range(max(1, (page.number - 2)),
                     min((page.number + 2), page.paginator.num_pages) + 1)


@register.filter
def normalize_human_name(name):
    """ Normalize 'First M. Last' to 'Last, First M.'"""
    return normalize_name(name)


@register.filter
def display_name_to_class(value):
    """ Converts an aggregation display name to a string that is usable as a CSS class name """
    return value.replace(" ", "_").lower()
