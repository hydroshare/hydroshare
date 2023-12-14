
from future.builtins import int
from json import dumps

from django.utils.html import format_html
from django.conf import settings
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from mezzanine import template

from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_core.authentication import build_oidc_url
from hs_core.search_indexes import normalize_name
from hs_access_control.models.privilege import PrivilegeCodes, UserResourcePrivilege

register = template.Library()

RES_TYPE_TO_DISPLAY_TYPE_MAPPINGS = {"CompositeResource": "Resource",
                                     "CollectionResource": "Collection",
                                     "ToolResource": "App Connector"
                                     }


@register.filter
def user_permission(content, arg):
    user_pk = arg
    permission = "None"
    res_obj = content
    urp = UserResourcePrivilege.objects.filter(user__id=user_pk, resource=res_obj).first()
    if urp is not None:
        if urp.privilege == PrivilegeCodes.OWNER:
            permission = "Owner"
        elif urp.privilege == PrivilegeCodes.CHANGE:
            permission = "Edit"
        elif urp.privilege == PrivilegeCodes.VIEW:
            permission = "View"

    if permission == "None":
        if res_obj.raccess.published or res_obj.raccess.discoverable or res_obj.raccess.public:
            permission = "Open Access"
    return permission


@register.filter
def user_resource_labels(resource, user):
    # get a list of labels associated with a specified resource by a given user
    if hasattr(resource, 'has_labels') and resource.has_labels:
        return resource.rlabels.get_labels(user)
    return []


@register.filter
def get_user_privilege(resource, user):
    user_privilege = resource.raccess.get_effective_privilege(user, ignore_superuser=True)
    if user_privilege == PrivilegeCodes.OWNER:
        self_access_level = 'Owned'
    elif user_privilege == PrivilegeCodes.CHANGE:
        self_access_level = 'Editable'
    elif user_privilege == PrivilegeCodes.VIEW:
        self_access_level = 'Viewable'
    else:
        self_access_level = "Discovered"
    return self_access_level


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
def is_url(content):
    """
    Check whether the content is a valid URL
    """
    validator = URLValidator()
    try:
        validator(content)
    except ValidationError:
        return False
    return True


@register.filter
def published_date(res_obj):
    if res_obj.raccess.published:
        return res_obj.metadata.dates.all().filter(type='published').first().start_date
    else:
        return ''


@register.filter
def resource_type(content):
    content_model = content.get_content_model()
    if content_model.resource_type in RES_TYPE_TO_DISPLAY_TYPE_MAPPINGS:
        return RES_TYPE_TO_DISPLAY_TYPE_MAPPINGS[content_model.resource_type]
    return content_model._meta.verbose_name


@register.filter
def resource_first_author(content):
    if not content:
        return ''

    first_creator = None
    for creator in content.metadata.creators.all():
        if creator.order == 1:
            first_creator = creator
            break

    if first_creator.name:
        if first_creator.relative_uri and first_creator.is_active_user:
            return format_html('<a href="{desc}">{name}</a>',
                               desc=first_creator.relative_uri,
                               name=first_creator.name)
        else:
            return format_html('<span>{name}</span>', name=first_creator.name)
    elif first_creator.organization:
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

    if not content.is_authenticated:
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

    if not content.is_authenticated:
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


@register.filter(name='join')
def join(value, delimiter):
    """
        Returns the array joined with delimiter
    """
    return f'{delimiter}'.join(value)


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
    return fed_irods_file_name[idx + 1:]


@register.filter
def resource_replaced_by(res):
    return res.get_relation_version_res_url('isReplacedBy')


@register.filter
def resource_version_of(res):
    return res.get_relation_version_res_url('isVersionOf')


@register.filter
def resource_from_uuid(id):
    if not id:
        return None
    return get_resource_by_shortkey(id)


@register.filter
def res_uuid_from_res_path(path):
    prefix_str = 'resource/'
    prefix_idx = path.find(prefix_str)
    if prefix_idx >= 0:
        sidx = prefix_idx + len(prefix_str)
        # resource uuid is 32 bits
        return path[sidx:sidx + 32]
    else:
        return path


@register.filter
def remove_last_char(statement):
    return statement[:len(statement) - 1]


@register.filter
def five_options_around(page):
    """ Create five page numbers around current page for discovery pagination. """
    if page.number <= 3:
        return list(range(1, min(5, page.paginator.num_pages) + 1))
    elif page.number >= (page.paginator.num_pages - 2):
        return list(range(max((page.paginator.num_pages - 4), 1),
                          page.paginator.num_pages + 1))
    else:
        return list(range(max(1, (page.number - 2)),
                          min((page.number + 2), page.paginator.num_pages) + 1))


@register.filter
def normalize_human_name(name):
    """ Normalize 'First M. Last' to 'Last, First M.'"""
    return normalize_name(name)


@register.filter
def display_name_to_class(value):
    """ Converts an aggregation display name to a string that is usable as a CSS class name """
    return value.replace(" ", "_").lower()


@register.filter
def creator_json_ld_element(crs):
    """ return json ld element for creators for schema.org script embedded on resource landing page"""
    crs_array = []
    for cr in crs:
        cr_dict = {}
        urls = []
        if cr.email:
            cr_dict["email"] = cr.email
        if cr.address:
            cr_dict["address"] = {
                "@type": "PostalAddress",
                "streetAddress": cr.address
            }
        if cr.name:
            cr_dict["@type"] = "Person"
            cr_dict["name"] = name_without_commas(cr.name)
            if cr.organization:
                affl_dict = {
                    "@type": "Organization",
                    "name": cr.organization
                }
                cr_dict["affiliation"] = affl_dict
        else:
            cr_dict["@type"] = "Organization"
            cr_dict["name"] = cr.organization

        if cr.relative_uri:
            if cr.name:
                # append www.hydroshare.org since schema.org script is only embedded in production
                urls.append("https://www.hydroshare.org" + cr.relative_uri)
            else:
                # organization
                urls.append(cr.relative_uri)
        if cr.homepage:
            urls.append(cr.homepage)
        if cr.identifiers:
            for k in cr.identifiers:
                urls.append(cr.identifiers[k])
        if len(urls) == 1:
            cr_dict['url'] = urls[0]
        elif len(urls) > 1:
            cr_dict['url'] = urls
        crs_array.append(cr_dict)
    # reformat json dumped str a bit to fix the indentation issue with the last bracket
    default_dump = dumps({"@list": crs_array}, sort_keys=True, indent=6)
    format_dump = '{}    {}'.format(default_dump[:-1], default_dump[-1])
    return format_dump


@register.filter
def is_debug(page):
    return settings.DEBUG


@register.filter
def discoverable(item):
    """ used in templates for discovery to avoid non-indicative results. """
    if item is None or item == 'Unknown':
        return ""
    return item


@register.filter
def signup_url(request):
    if settings.ENABLE_OIDC_AUTHENTICATION:
        return build_oidc_url(request).replace('/auth?', '/registrations?')
    return "/sign-up/"


@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    """
    Return encoded URL parameters that are the same as the current
    request's parameters, only with the specified GET parameters added or changed.

    It also removes any empty parameters to keep things neat,
    so you can remove a parm by setting it to ``""``.

    For example, if you're on the page ``/things/?with_frosting=true&page=5``,
    then

    <a href="/things/?{% param_replace page=3 %}">Page 3</a>

    would expand to

    <a href="/things/?with_frosting=true&page=3">Page 3</a>

    Based on
    https://stackoverflow.com/questions/22734695/next-and-before-links-for-a-django-paginated-query/22735278#22735278
    """
    d = context['request'].GET.copy()
    for k, v in kwargs.items():
        d[k] = v
    for k in [k for k, v in d.items() if not v]:
        del d[k]
    return d.urlencode()
