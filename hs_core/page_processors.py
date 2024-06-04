"""Page processors for hs_core app."""

import json

from dateutil import parser
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils.html import mark_safe, escapejs
from mezzanine.pages.page_processors import processor_for

from hs_communities.models import Topic
from hs_core import languages_iso
from hs_core.hydroshare.resource import METADATA_STATUS_SUFFICIENT, METADATA_STATUS_INSUFFICIENT, \
    res_has_web_reference
from hs_core.models import BaseResource, Relation
from hs_core.views.utils import show_relations_section, \
    rights_allows_copy, check_hs_read_only_mode
from hs_odm2.models import ODM2Variable
from .forms import ExtendedMetadataForm


@processor_for(BaseResource)
def landing_page(request, page):
    """Return resource landing page context."""
    edit_resource = check_resource_mode(request)

    return get_page_context(page, request.user, resource_edit=edit_resource, request=request)


def get_page_context(page, user, resource_edit=False, extended_metadata_layout=None, request=None):
    """Inject a crispy_form layout into the page to display additional metadata.

    :param page: which page to get the template context for
    :param user: the user who is viewing the page
    :param resource_edit: True if and only if the page should render in edit mode
    :param extended_metadata_layout: layout information used to build an ExtendedMetadataForm
    :param request: the Django request associated with the page load
    :return: the basic template context (a python dict) used to render a resource page. can and
    should be extended by page/resource-specific page_processors

    Resource type specific app needs to call this method to inject a crispy_form layout
    object for displaying metadata UI for the additional metadata for their resource

    TODO: refactor to make it clear that there are two different modes = EDITABLE | READONLY
                - split into two functions: get_readonly_page_context(...) and
                get_editable_page_context(...)
    """
    hs_read_only_mode = check_hs_read_only_mode(raise_exception=False)
    if resource_edit:
        resource_edit = not hs_read_only_mode
    if hs_read_only_mode:
        messages.info(request, "HydroShare is in read-only mode - resource editing is disabled.")

    file_type_error = ''
    if request:
        file_type_error = request.session.get("file_type_error", None)
        if file_type_error:
            del request.session["file_type_error"]

    content_model = page.get_content_model()

    show_content_files = content_model.raccess.public or content_model.raccess.allow_private_sharing
    if not show_content_files and user.is_authenticated:
        show_content_files = user.uaccess.can_view_resource(content_model)

    can_view = content_model.can_view(request)
    if not can_view and not show_content_files:
        raise PermissionDenied()

    discoverable = content_model.raccess.discoverable
    validation_error = None
    resource_is_mine = False
    if user.is_authenticated:
        resource_is_mine = content_model.rlabels.is_mine(user)

    metadata_status = _get_metadata_status(content_model)

    belongs_to_collections = content_model.collections.all().select_related('raccess')

    tool_homepage_url = None
    if not resource_edit:  # In view mode
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

    readme = content_model.get_readme_file_content()
    if readme is None:
        readme = ''
    has_web_ref = res_has_web_reference(content_model)

    keywords = json.dumps([sub.value for sub in content_model.metadata.subjects.all()])
    topics = Topic.objects.all().values_list('name', flat=True).order_by('name')
    topics = list(topics)  # force QuerySet evaluation
    if not hs_read_only_mode:
        content_model.update_relation_meta()
    creators = content_model.metadata.creators.all()

    # user requested the resource in READONLY mode
    if not resource_edit:
        if not hs_read_only_mode:
            content_model.update_view_count()
        temporal_coverage = content_model.metadata.temporal_coverage
        temporal_coverage_data_dict = {}
        if temporal_coverage:
            start_date = parser.parse(temporal_coverage.value['start'])
            end_date = parser.parse(temporal_coverage.value['end'])
            temporal_coverage_data_dict['start_date'] = start_date.strftime('%Y-%m-%d')
            temporal_coverage_data_dict['end_date'] = end_date.strftime('%Y-%m-%d')
            temporal_coverage_data_dict['name'] = temporal_coverage.value.get('name', '')

        spatial_coverage = content_model.metadata.spatial_coverage
        spatial_coverage_data_dict = {}
        spatial_coverage_data_dict['default_units'] = \
            content_model.metadata.spatial_coverage_default_units
        spatial_coverage_data_dict['default_projection'] = \
            content_model.metadata.spatial_coverage_default_projection
        spatial_coverage_data_dict['exists'] = False
        if spatial_coverage:
            spatial_coverage_data_dict['exists'] = True
            spatial_coverage_data_dict['name'] = spatial_coverage.value.get('name', None)
            spatial_coverage_data_dict['units'] = spatial_coverage.value['units']
            spatial_coverage_data_dict['zunits'] = spatial_coverage.value.get('zunits', None)
            spatial_coverage_data_dict['projection'] = spatial_coverage.value.get('projection',
                                                                                  None)
            spatial_coverage_data_dict['type'] = spatial_coverage.type
            if spatial_coverage.type == 'point':
                spatial_coverage_data_dict['east'] = spatial_coverage.value['east']
                spatial_coverage_data_dict['north'] = spatial_coverage.value['north']
                spatial_coverage_data_dict['elevation'] = spatial_coverage.value.get('elevation',
                                                                                     None)
            else:
                spatial_coverage_data_dict['northlimit'] = spatial_coverage.value['northlimit']
                spatial_coverage_data_dict['eastlimit'] = spatial_coverage.value['eastlimit']
                spatial_coverage_data_dict['southlimit'] = spatial_coverage.value['southlimit']
                spatial_coverage_data_dict['westlimit'] = spatial_coverage.value['westlimit']
                spatial_coverage_data_dict['uplimit'] = spatial_coverage.value.get('uplimit', None)
                spatial_coverage_data_dict['downlimit'] = spatial_coverage.value.get('downlimit',
                                                                                     None)
        languages_dict = dict(languages_iso.languages)
        language = languages_dict[content_model.metadata.language.code] if \
            content_model.metadata.language else None
        title = content_model.metadata.title.value if content_model.metadata.title else None
        abstract = content_model.metadata.description.abstract if \
            content_model.metadata.description else None

        missing_metadata_elements_for_publication = content_model.metadata.get_required_missing_elements('published')
        missing_metadata_elements_for_discoverable = content_model.metadata.get_required_missing_elements()
        recommended_missing_elements = content_model.metadata.get_recommended_missing_elements()
        maps_key = settings.MAPS_KEY if hasattr(settings, 'MAPS_KEY') else ''

        context = {
            'cm': content_model,
            'resource_edit_mode': resource_edit,
            'metadata_form': None,
            'citation': content_model.get_citation(forceHydroshareURI=False),
            'custom_citation': content_model.get_custom_citation(),
            'title': title,
            'readme': readme,
            'abstract': abstract,
            'creators': creators,
            'contributors': content_model.metadata.contributors.all(),
            'temporal_coverage': temporal_coverage_data_dict,
            'spatial_coverage': spatial_coverage_data_dict,
            'keywords': keywords,
            'language': language,
            'rights': content_model.metadata.rights,
            'relations': content_model.metadata.relations.all(),
            'geospatial_relations': content_model.metadata.geospatialrelations.all(),
            'show_relations_section': show_relations_section(content_model),
            'fundingagencies': content_model.metadata.funding_agencies.all(),
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

    # user requested the resource in EDIT MODE

    # whether the user has permission to change the model
    can_change = content_model.can_change(request)
    if not can_change:
        raise PermissionDenied()

    temporal_coverage = content_model.metadata.temporal_coverage
    temporal_coverage_data_dict = {}
    if temporal_coverage:
        start_date = parser.parse(temporal_coverage.value['start'])
        end_date = parser.parse(temporal_coverage.value['end'])
        temporal_coverage_data_dict['start'] = start_date.strftime('%m-%d-%Y')
        temporal_coverage_data_dict['end'] = end_date.strftime('%m-%d-%Y')
        temporal_coverage_data_dict['name'] = temporal_coverage.value.get('name', '')
        temporal_coverage_data_dict['id'] = temporal_coverage.id

    spatial_coverage = content_model.metadata.spatial_coverage
    spatial_coverage_data_dict = {'type': 'point'}
    spatial_coverage_data_dict['default_units'] = \
        content_model.metadata.spatial_coverage_default_units
    spatial_coverage_data_dict['default_projection'] = \
        content_model.metadata.spatial_coverage_default_projection
    spatial_coverage_data_dict['exists'] = False
    if spatial_coverage:
        spatial_coverage_data_dict['exists'] = True
        spatial_coverage_data_dict['name'] = spatial_coverage.value.get('name', None)
        spatial_coverage_data_dict['units'] = spatial_coverage.value['units']
        spatial_coverage_data_dict['zunits'] = spatial_coverage.value.get('zunits', None)
        spatial_coverage_data_dict['projection'] = spatial_coverage.value.get('projection', None)
        spatial_coverage_data_dict['type'] = spatial_coverage.type
        spatial_coverage_data_dict['id'] = spatial_coverage.id
        if spatial_coverage.type == 'point':
            spatial_coverage_data_dict['east'] = spatial_coverage.value['east']
            spatial_coverage_data_dict['north'] = spatial_coverage.value['north']
            spatial_coverage_data_dict['elevation'] = spatial_coverage.value.get('elevation', None)
        else:
            spatial_coverage_data_dict['northlimit'] = spatial_coverage.value['northlimit']
            spatial_coverage_data_dict['eastlimit'] = spatial_coverage.value['eastlimit']
            spatial_coverage_data_dict['southlimit'] = spatial_coverage.value['southlimit']
            spatial_coverage_data_dict['westlimit'] = spatial_coverage.value['westlimit']
            spatial_coverage_data_dict['uplimit'] = spatial_coverage.value.get('uplimit', None)
            spatial_coverage_data_dict['downlimit'] = spatial_coverage.value.get('downlimit', None)

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
        'resource_edit_mode': resource_edit,
        'metadata_form': metadata_form,
        'creators': creators,
        'title': content_model.metadata.title,
        'readme': readme,
        'contributors': content_model.metadata.contributors.all(),
        'relations': content_model.metadata.relations.all(),
        'geospatial_relations': content_model.metadata.geospatialrelations.all(),
        'fundingagencies': content_model.metadata.funding_agencies.all(),
        'temporal_coverage': temporal_coverage_data_dict,
        'spatial_coverage': spatial_coverage_data_dict,
        'keywords': keywords,
        'metadata_status': metadata_status,
        'missing_metadata_elements_for_discoverable': content_model.metadata.get_required_missing_elements(),
        'recommended_missing_elements': content_model.metadata.get_recommended_missing_elements(),
        'citation': content_model.get_citation(forceHydroshareURI=False),
        'custom_citation': content_model.get_custom_citation(),
        'citation_id': citation_id,
        'rights': content_model.metadata.rights,
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
