"""Page processors for hs_core app."""

import json
from dateutil import parser

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.html import mark_safe, escapejs

from hs_communities.models import Topic
from hs_core import languages_iso
from hs_core.hydroshare.resource import METADATA_STATUS_SUFFICIENT, METADATA_STATUS_INSUFFICIENT, \
    res_has_web_reference
from hs_core.models import Relation
from hs_core.views.utils import show_relations_section, \
    rights_allows_copy
from hs_odm2.models import ODM2Variable
from .forms import ExtendedMetadataForm


def get_page_context(page, user, resource_edit=False, extended_metadata_layout=None, request=None, content_model=None):
    """Route to appropriate page context function based on resource_edit mode.

    :param page: which page to get the template context for
    :param user: the user who is viewing the page
    :param resource_edit: True if and only if the page should render in edit mode
    :param extended_metadata_layout: layout information used to build an ExtendedMetadataForm
    :param request: the Django request associated with the page load
    :param content_model: the resource content model
    :return: the basic template context (a python dict) used to render a resource page
    """
    if content_model is None:
        content_model = page.get_content_model()

    if resource_edit:
        return get_editable_page_context(content_model, user, extended_metadata_layout, request)
    else:
        return get_readonly_page_context(content_model, user, request)


def get_readonly_page_context(content_model, user, request=None):
    """Get template context for resource in READONLY mode.

    :param content_model: the resource content model
    :param user: the user who is viewing the page
    :param request: the Django request associated with the page load

    :return: the template context dict for readonly resource page
    """
    file_type_error = ''
    if request:
        file_type_error = request.session.get("file_type_error", None)
        if file_type_error:
            del request.session["file_type_error"]

    show_content_files = _should_show_content_files(content_model, user)

    can_view = content_model.can_view(request)
    if not can_view and not show_content_files:
        raise PermissionDenied()

    discoverable = content_model.raccess.discoverable
    validation_error = None
    resource_is_mine = _is_resource_mine(content_model, user)

    metadata_status = _get_metadata_status(content_model)

    belongs_to_collections = content_model.collections.all().select_related('raccess')

    tool_homepage_url = None
    landing_page_res_obj = content_model
    landing_page_res_type_str = landing_page_res_obj.resource_type
    if landing_page_res_type_str.lower() == "toolresource":
        if landing_page_res_obj.metadata.app_home_page_url:
            tool_homepage_url = content_model.metadata.app_home_page_url.value

    just_created = False
    just_copied = False
    create_resource_error = None
    if request:
        validation_error = check_for_validation(request)

        just_created = request.session.get('just_created', False)
        if 'just_created' in request.session:
            del request.session['just_created']

        just_copied = request.session.get('just_copied', False)
        if 'just_copied' in request.session:
            del request.session['just_copied']

        create_resource_error = request.session.get('resource_creation_error', None)
        if 'resource_creation_error' in request.session:
            del request.session['resource_creation_error']

    bag_url = content_model.bag_url

    rights_allow_copy = rights_allows_copy(content_model, user)

    qholder = content_model.quota_holder

    readme = _get_readme_content(content_model)
    has_web_ref = res_has_web_reference(content_model)

    content_model.update_relation_meta()

    # Update resource view count
    content_model.update_view_count()

    languages_dict = dict(languages_iso.languages)
    cached_language_code = content_model.cached_metadata.get('language', None)
    if cached_language_code:
        language = languages_dict[cached_language_code]
    else:
        language = None

    missing_metadata_elements_for_publication = content_model.metadata.get_required_missing_elements('published')
    missing_metadata_elements_for_discoverable = content_model.metadata.get_required_missing_elements()
    recommended_missing_elements = content_model.metadata.get_recommended_missing_elements()
    maps_key = settings.MAPS_KEY if hasattr(settings, 'MAPS_KEY') else ''

    context = {
        'cm': content_model,
        'resource_edit_mode': False,
        'metadata_form': None,
        'citation': content_model.get_citation(forceHydroshareURI=False),
        'custom_citation': content_model.get_custom_citation(),
        'title': content_model.cached_metadata.get('title', {}),
        'readme': readme,
        'abstract': content_model.cached_metadata.get('abstract', {}),
        'creators': content_model.cached_metadata.get('creators', []),
        'contributors': content_model.cached_metadata.get('contributors', []),
        'temporal_coverage': content_model.cached_metadata.get('temporal_coverage', {}),
        'spatial_coverage': content_model.cached_metadata.get('spatial_coverage', {}),
        'keywords': content_model.cached_metadata.get('subjects', []),
        'language': language,
        'rights': content_model.cached_metadata.get('rights', {}),
        'relations': content_model.cached_metadata.get('relations', []),
        'geospatial_relations': content_model.cached_metadata.get('geospatial_relations', []),
        'show_relations_section': show_relations_section(content_model),
        'fundingagencies': content_model.cached_metadata.get('funding_agencies', []),
        'metadata_status': metadata_status,
        'missing_metadata_elements_for_discoverable': missing_metadata_elements_for_discoverable,
        'missing_metadata_elements_for_publication': missing_metadata_elements_for_publication,
        'recommended_missing_elements': recommended_missing_elements,
        'validation_error': validation_error if validation_error else None,
        'resource_creation_error': create_resource_error,
        'tool_homepage_url': tool_homepage_url,
        'file_type_error': file_type_error,
        'just_created': just_created,
        'just_copied': just_copied,
        'bag_url': bag_url,
        'show_content_files': show_content_files,
        'discoverable': discoverable,
        'resource_is_mine': resource_is_mine,
        'rights_allow_copy': rights_allow_copy,
        'quota_holder': qholder,
        'belongs_to_collections': belongs_to_collections,
        'show_web_reference_note': has_web_ref,
        'current_user': user,
        'maps_key': maps_key
    }

    return context


def get_editable_page_context(content_model, user, extended_metadata_layout=None, request=None):
    """Get template context for resource in EDITABLE mode.

    :param content_model: the resource content model
    :param user: the user who is viewing the page
    :param extended_metadata_layout: layout information used to build an ExtendedMetadataForm
    :param request: the Django request associated with the page load

    :return: the template context dict for editable resource page
    """
    show_content_files = _should_show_content_files(content_model, user)

    can_change = content_model.can_change(request)

    # Check permission to change the model
    if not can_change:
        raise PermissionDenied()

    discoverable = content_model.raccess.discoverable
    resource_is_mine = _is_resource_mine(content_model, user)

    metadata_status = _get_metadata_status(content_model)

    belongs_to_collections = content_model.collections.all().select_related('raccess')

    just_created = False
    validation_error = None
    if request:
        validation_error = check_for_validation(request)

        just_created = request.session.get('just_created', False)
        if 'just_created' in request.session:
            del request.session['just_created']

    bag_url = content_model.bag_url

    qholder = content_model.quota_holder

    readme = _get_readme_content(content_model)
    has_web_ref = res_has_web_reference(content_model)

    topics = _get_topics_list()
    content_model.update_relation_meta()

    temporal_coverage = content_model.cached_metadata.get('temporal_coverage', {})
    if temporal_coverage:
        start_date = temporal_coverage.get('start_date')
        temporal_coverage['start_date'] = parser.parse(start_date).strftime('%m/%d/%Y')
        end_date = temporal_coverage.get('end_date')
        temporal_coverage['end_date'] = parser.parse(end_date).strftime('%m/%d/%Y')

    spatial_coverage = content_model.cached_metadata.get('spatial_coverage', {})

    if extended_metadata_layout:
        metadata_form = ExtendedMetadataForm(resource_mode='edit' if can_change else 'view',
                                             extended_metadata_layout=extended_metadata_layout)
    else:
        metadata_form = None

    maps_key = settings.MAPS_KEY if hasattr(settings, 'MAPS_KEY') else ''

    try:
        citation_id = content_model.metadata.citation.first().id
    except: # noqa
        citation_id = None

    context = {
        'cm': content_model,
        'resource_edit_mode': True,
        'metadata_form': metadata_form,
        'creators': content_model.cached_metadata.get('creators', []),
        'title': content_model.cached_metadata.get('title', {}),
        'readme': readme,
        'contributors': content_model.cached_metadata.get('contributors', []),
        'relations': content_model.cached_metadata.get('relations', []),
        'geospatial_relations': content_model.cached_metadata.get('geospatial_relations', []),
        'fundingagencies': content_model.cached_metadata.get('funding_agencies', []),
        'temporal_coverage': temporal_coverage,
        'spatial_coverage': spatial_coverage,
        'keywords': content_model.cached_metadata.get('subjects', []),
        'metadata_status': metadata_status,
        'missing_metadata_elements_for_discoverable': content_model.metadata.get_required_missing_elements(),
        'recommended_missing_elements': content_model.metadata.get_recommended_missing_elements(),
        'citation': content_model.get_citation(forceHydroshareURI=False),
        'custom_citation': content_model.get_custom_citation(),
        'citation_id': citation_id,
        'rights': content_model.cached_metadata.get('rights', {}),
        'bag_url': bag_url,
        'current_user': user,
        'show_content_files': show_content_files,
        'validation_error': validation_error if validation_error else None,
        'discoverable': discoverable,
        'resource_is_mine': resource_is_mine,
        'quota_holder': qholder,
        'just_created': just_created,
        'relation_source_types': tuple((type_value, type_display)
                                       for type_value, type_display in Relation.SOURCE_TYPES
                                       if type_value not in Relation.NOT_USER_EDITABLE),
        'show_web_reference_note': has_web_ref,
        'belongs_to_collections': belongs_to_collections,
        'maps_key': maps_key,
        'topics_json': mark_safe(escapejs(json.dumps(topics))),
        'czo_user': any("CZO National" in x.name for x in user.uaccess.communities),
        'odm2_terms': list(ODM2Variable.all()),
    }

    return context


def check_resource_mode(request):
    """Determine whether the `request` represents an attempt to edit a resource.

    A request is considered an attempt
    to edit if any of the following conditions are met:
        1. the HTTP verb is not "GET"
        2. the HTTP verb is "GET" and the 'resource-mode' property is set to 'edit'

    This function erases the 'resource-mode' property of `request.session` if it exists.

    :param request: the `request` for a resource
    :return: True if the request represents an attempt to edit a resource, and False otherwise.
    """
    if request.method == "GET":
        edit_resource = request.session.get('resource-mode', None) == 'edit'
        if edit_resource:
            del request.session['resource-mode']
        else:
            if request.session.get('just_created', False):
                edit_resource = True
            else:
                edit_resource = request.GET.get('resource-mode', None) == 'edit'
    else:
        edit_resource = True

    return edit_resource


def check_for_validation(request):
    """Check for validation error in request session."""
    if request.method == "GET":
        validation_error = request.session.get('validation_error', None)
        if validation_error:
            del request.session['validation_error']
            return validation_error

    return None


def _get_metadata_status(resource):
    if resource.metadata.has_all_required_elements():
        metadata_status = METADATA_STATUS_SUFFICIENT
    else:
        metadata_status = METADATA_STATUS_INSUFFICIENT

    return metadata_status


def _should_show_content_files(content_model, user):
    """Determine whether content files should be shown to the user.

    :param content_model: the resource content model
    :param user: the user viewing the resource
    :return: True if content files should be shown, False otherwise
    """
    show_content_files = content_model.raccess.public or content_model.raccess.allow_private_sharing
    if not show_content_files and user.is_authenticated:
        show_content_files = user.uaccess.can_view_resource(content_model)
    return show_content_files


def _get_readme_content(content_model):
    """Get the readme file content for the resource.

    :param content_model: the resource content model
    :return: readme content as string, or empty string if not found
    """
    readme = content_model.get_readme_file_content()
    if readme is None:
        readme = ''
    return readme


def _get_topics_list():
    """Get list of all topic names.

    :return: list of topic names sorted alphabetically
    """
    topics = Topic.objects.all().values_list('name', flat=True).order_by('name')
    return list(topics)  # force QuerySet evaluation


def _is_resource_mine(content_model, user):
    """Check if the resource has been marked as mine by the user for listing in "my resources".

    :param content_model: the resource content model
    :param user: the user to check if the resource is mine for
    :return: True if the user has marked the resource as mine, False otherwise
    """
    resource_is_mine = False
    if user.is_authenticated:
        resource_is_mine = content_model.rlabels.is_mine(user)
    return resource_is_mine
