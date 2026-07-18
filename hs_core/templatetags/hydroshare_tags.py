from json import dumps
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.html import format_html
from future.builtins import int
from mezzanine import template

from hs_access_control.models.privilege import (PrivilegeCodes,
                                                UserResourcePrivilege)
from hs_core.authentication import build_oidc_url
from hs_core.enums import DataciteSubmissionStatus
from hs_core.hydroshare.utils import get_resource_by_shortkey, normalize_name

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
def privilege_code_to_name(privilege_code):
    if privilege_code == PrivilegeCodes.OWNER:
        return 'Owned'
    elif privilege_code == PrivilegeCodes.CHANGE:
        return 'Editable'
    elif privilege_code == PrivilegeCodes.VIEW:
        return 'Viewable'
    else:
        return 'Discovered'


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
        if not res_obj.cached_metadata.get('published_date', None):
            published_date = res_obj.cached_metadata['published_date']
            return to_date(published_date)
        else:
            return res_obj.metadata.dates.all().filter(type='published').first().start_date
    else:
        return ''


@register.filter
def resource_type(content):
    if isinstance(content, dict) and 'resource_type' in content:
        if content['resource_type'] in RES_TYPE_TO_DISPLAY_TYPE_MAPPINGS:
            return RES_TYPE_TO_DISPLAY_TYPE_MAPPINGS[content['resource_type']]
        else:
            return content['resource_type']
    content_model = content.get_content_model()
    if content_model.resource_type in RES_TYPE_TO_DISPLAY_TYPE_MAPPINGS:
        return RES_TYPE_TO_DISPLAY_TYPE_MAPPINGS[content_model.resource_type]
    return content_model._meta.verbose_name


@register.filter
def resource_first_author(content):
    if not content:
        return ''

    first_creator = None

    # Handle list of dictionaries (creator data)
    if isinstance(content, list):
        for creator_dict in content:
            if creator_dict.get('order') == 1:
                # Create a simple object-like structure from the dictionary
                class CreatorFromDict:
                    def __init__(self, data):
                        self.name = data.get('name', '')
                        self.organization = data.get('organization', '')
                        self.relative_uri = data.get('relative_uri', '')
                        self.is_active_user = data.get('is_active_user', False)

                first_creator = CreatorFromDict(creator_dict)
                break
    else:
        # Handle BaseResource object
        for creator in content.metadata.creators.all():
            if creator.order == 1:
                first_creator = creator
                break

    if not first_creator:
        return ''

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
def relative_s3_path(s3_file_name):
    idx = s3_file_name.find('/data/contents/')
    return s3_file_name[idx + 1:]


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
        identifiers = []
        if cr['email']:
            cr_dict["email"] = cr['email']
        if cr['address']:
            cr_dict["address"] = {
                "@type": "PostalAddress",
                "streetAddress": cr['address']
            }
        if cr['name']:
            cr_dict["@type"] = "Person"
            cr_dict["name"] = name_without_commas(cr['name'])
            if cr['organization']:
                affl_dict = {
                    "@type": "Organization",
                    "name": cr['organization']
                }
                cr_dict["affiliation"] = affl_dict
        else:
            cr_dict["@type"] = "Organization"
            cr_dict["name"] = cr['organization']

        if cr['relative_uri']:
            if cr['name']:
                # append www.hydroshare.org since schema.org script is only embedded in production
                urls.append("https://www.hydroshare.org" + cr['relative_uri'])
            else:
                # organization
                urls.append(cr['relative_uri'])
        if cr['homepage']:
            urls.append(cr['homepage'])
        if cr['identifiers']:
            for k in cr['identifiers']:
                identifier_value = cr['identifiers'][k]
                urls.append(identifier_value)
                identifiers.append(identifier_value)
        if len(identifiers) == 1:
            cr_dict['identifier'] = identifiers[0]
            cr_dict['sameAs'] = identifiers[0]
        elif len(identifiers) > 1:
            cr_dict['identifier'] = identifiers
            cr_dict['sameAs'] = identifiers
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
def json_dumps(value):
    return dumps(value)


@register.filter
def resource_files_json_ld(resource):
    """Return a JSON-LD array of schema.org MediaObject entries for each resource file.
    Satisfies MetaDIG entity.name.present by emitting at minimum name and encodingFormat
    for every file in the resource."""
    entries = []
    for f in resource.files.all():
        entry = {
            "@type": "MediaObject",
            "name": f.file_name,
        }
        if f.mime_type:
            entry["encodingFormat"] = f.mime_type
        entries.append(entry)
    return dumps(entries, indent=4) if entries else ""


@register.filter
def relation_values_json(relations, relation_type):
    values = [rel.get('value') for rel in relations if rel.get('type') == relation_type and rel.get('value')]
    return dumps(values) if values else ""


@register.filter
def first_relation_value_for_types(relations, relation_types):
    relation_type_list = [relation_type.strip() for relation_type in relation_types.split(',') if relation_type.strip()]
    for relation_type in relation_type_list:
        for relation in relations or []:
            if relation.get('type') == relation_type and relation.get('value'):
                return relation.get('value')
    return ""


@register.filter
def provenance_trace_json(relations):
    lineage_relation_types = {'source', 'isVersionOf', 'isPartOf', 'hasPart'}
    values = [rel.get('value') for rel in (relations or [])
              if rel.get('type') in lineage_relation_types and rel.get('value')]
    return dumps(values) if values else ""


@register.filter
def schemaorg_contact_point_json(creators):
    if not creators:
        return ""

    sorted_creators = sorted(creators, key=lambda creator: creator.get('order') if creator.get('order') is not None else 999999)
    creator = sorted_creators[0]

    contact_point = {
        '@type': 'ContactPoint'
    }

    creator_name = creator.get('name')
    creator_organization = creator.get('organization')
    if creator_name:
        contact_point['name'] = name_without_commas(creator_name)
    elif creator_organization:
        contact_point['name'] = creator_organization
    else:
        return ""

    if creator.get('email'):
        contact_point['email'] = creator['email']
    if creator.get('phone'):
        contact_point['telephone'] = creator['phone']
    if creator_organization:
        contact_point['affiliation'] = {
            '@type': 'Organization',
            'name': creator_organization
        }

    identifiers = []
    if creator.get('identifiers'):
        identifiers = [value for value in creator.get('identifiers').values() if value]

    urls = []
    if creator.get('relative_uri') and creator_name:
        urls.append('https://www.hydroshare.org' + creator.get('relative_uri'))
    if creator.get('homepage'):
        urls.append(creator.get('homepage'))
    urls.extend(identifiers)

    unique_urls = list(dict.fromkeys(urls))
    if len(unique_urls) == 1:
        contact_point['url'] = unique_urls[0]
    elif len(unique_urls) > 1:
        contact_point['url'] = unique_urls

    unique_identifiers = list(dict.fromkeys(identifiers))
    if len(unique_identifiers) == 1:
        contact_point['identifier'] = unique_identifiers[0]
        contact_point['sameAs'] = unique_identifiers[0]
    elif len(unique_identifiers) > 1:
        contact_point['identifier'] = unique_identifiers
        contact_point['sameAs'] = unique_identifiers

    return dumps(contact_point, sort_keys=True, indent=4)


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


@register.filter
def show_publication_status(resource):
    if resource.raccess.review_pending:
        return True

    doi = resource.doi
    if doi.endswith(resource.short_id):
        return False
    if (doi.endswith(DataciteSubmissionStatus.PENDING.value)
            and not doi.endswith(DataciteSubmissionStatus.UPDATE_PENDING.value)):
        return True
    if (doi.endswith(DataciteSubmissionStatus.FAILURE.value)
            and not doi.endswith(DataciteSubmissionStatus.UPDATE_FAILURE.value)):
        return True

    return False


@register.simple_tag
def get_resource_url(short_id):
    """
    Returns the absolute URL for a resource given its short_id.
    """
    if not short_id:
        return ""
    return "/resource/{}/".format(short_id)


@register.filter(name='to_date')
def to_date(value):
    """
    Converts an ISO format date string into a datetime object.
    """
    if isinstance(value, str):
        try:
            # Handle ISO format with or without microseconds
            if '.' in value:
                return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f%z')
            return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S%z')
        except (ValueError, TypeError):
            try:
                # Fallback for different ISO 8601 format
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                return None
    return value
