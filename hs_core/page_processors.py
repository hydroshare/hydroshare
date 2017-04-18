from functools import partial, wraps

from django.core.exceptions import PermissionDenied
from django.forms.models import formset_factory

from mezzanine.pages.page_processors import processor_for

from hs_core.models import AbstractResource, GenericResource, Relation
from hs_core import languages_iso
from forms import CreatorForm, ContributorForm, SubjectsForm, AbstractForm, RelationForm, \
    SourceForm, FundingAgencyForm, BaseCreatorFormSet, BaseContributorFormSet, BaseFormSet, \
    MetaDataElementDeleteForm, CoverageTemporalForm, CoverageSpatialForm, ExtendedMetadataForm
from hs_tools_resource.models import SupportedResTypes, ToolResource
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE, show_relations_section, \
    can_user_copy_resource
from hs_core.hydroshare.resource import METADATA_STATUS_SUFFICIENT, METADATA_STATUS_INSUFFICIENT
from hs_tools_resource.utils import parse_app_url_template


@processor_for(GenericResource)
def landing_page(request, page):
    edit_resource = check_resource_mode(request)

    return get_page_context(page, request.user, resource_edit=edit_resource, request=request)


# resource type specific app needs to call this method to inject a crispy_form layout
# object for displaying metadata UI for the extended metadata for their resource
def get_page_context(page, user, resource_edit=False, extended_metadata_layout=None, request=None):
    """
    :param page: which page to get the template context for
    :param user: the user who is viewing the page
    :param resource_edit: True if and only if the page should render in edit mode
    :param extended_metadata_layout: layout information used to build an ExtendedMetadataForm
    :param request: the Django request associated with the page load
    :return: the basic template context (a python dict) used to render a resource page. can and
    should be extended by page/resource-specific page_processors


    TODO: refactor to make it clear that there are two different modes = EDITABLE | READONLY
                - split into two functions: get_readonly_page_context(...) and
                get_editable_page_context(...)
    """
    file_type_error = ''
    if request:
        file_type_error = request.session.get("file_type_error", None)
        if file_type_error:
            del request.session["file_type_error"]

    content_model = page.get_content_model()
    # whether the user has permission to view this resource
    can_view = content_model.can_view(request)
    if not can_view:
        raise PermissionDenied()

    discoverable = content_model.raccess.discoverable
    validation_error = None
    resource_is_mine = False
    if user.is_authenticated():
        resource_is_mine = content_model.rlabels.is_mine(user)

    metadata_status = _get_metadata_status(content_model)

    belongs_to_collections = content_model.collections.all()

    relevant_tools = None
    tool_homepage_url = None
    if not resource_edit:  # In view mode
        content_model_str = str(content_model.content_model).lower()
        if content_model_str.lower() == "toolresource":
            if content_model.metadata.homepage_url.exists():
                tool_homepage_url = content_model.metadata.homepage_url.first().value

        relevant_tools = []
        # loop through all SupportedResTypes objs (one webapp resources has one
        # SupportedResTypes obj)
        for res_type in SupportedResTypes.objects.all():
            supported_flag = False
            for supported_type in res_type.supported_res_types.all():
                if content_model_str == supported_type.description.lower():
                    supported_flag = True
                    break

            if supported_flag:
                # reverse lookup: metadata obj --> res obj
                tool_res_obj = ToolResource.objects.get(object_id=res_type.object_id)
                if tool_res_obj:
                    sharing_status_supported = False

                    supported_sharing_status_obj = tool_res_obj.metadata.\
                        supported_sharing_status.first()
                    if supported_sharing_status_obj is not None:
                        suppored_sharing_status_str = supported_sharing_status_obj.\
                                                      get_sharing_status_str()
                        if len(suppored_sharing_status_str) > 0:
                            res_sharing_status = content_model.raccess.sharing_status
                            if suppored_sharing_status_str.lower().\
                                    find(res_sharing_status.lower()) != -1:
                                sharing_status_supported = True
                    else:
                        # backward compatible: webapp without supported_sharing_status metadata
                        # is considered to support all sharing status
                        sharing_status_supported = True

                    if sharing_status_supported:
                        is_authorized = authorize(
                            request, tool_res_obj.short_id,
                            needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE,
                            raises_exception=False)[1]
                        if is_authorized:
                            tool_url = tool_res_obj.metadata.url_bases.first().value \
                                if tool_res_obj.metadata.url_bases.first() else None
                            tool_icon_url = tool_res_obj.metadata.tool_icon.first().data_url \
                                if tool_res_obj.metadata.tool_icon.first() else "raise-img-error"
                            hs_term_dict_user = {}
                            hs_term_dict_user["HS_USR_NAME"] = request.user.username if \
                                request.user.is_authenticated() else "anonymous"
                            tool_url_new = parse_app_url_template(
                                tool_url, [content_model.get_hs_term_dict(), hs_term_dict_user])
                            if tool_url_new is not None:
                                tl = {'title': str(tool_res_obj.metadata.title.value),
                                      'icon_url': tool_icon_url,
                                      'url': tool_url_new}
                                relevant_tools.append(tl)

    just_created = False
    just_copied = False
    create_resource_error = None
    just_published = False
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

        just_published = request.session.get('just_published', False)
        if 'just_published' in request.session:
            del request.session['just_published']

    bag_url = AbstractResource.bag_url(content_model.short_id)

    if user.is_authenticated():
        show_content_files = user.uaccess.can_view_resource(content_model)
    else:
        # if anonymous user getting access to a private resource (since resource is discoverable),
        # then don't show content files
        show_content_files = content_model.raccess.public

    allow_copy = can_user_copy_resource(content_model, user)

    qholder = content_model.raccess.get_quota_holder()

    # user requested the resource in READONLY mode
    if not resource_edit:
        temporal_coverages = content_model.metadata.coverages.all().filter(type='period')
        if len(temporal_coverages) > 0:
            temporal_coverage_data_dict = {}
            temporal_coverage = temporal_coverages[0]
            temporal_coverage_data_dict['start_date'] = temporal_coverage.value['start']
            temporal_coverage_data_dict['end_date'] = temporal_coverage.value['end']
            temporal_coverage_data_dict['name'] = temporal_coverage.value.get('name', '')
        else:
            temporal_coverage_data_dict = None

        spatial_coverages = content_model.metadata.coverages.all().exclude(type='period')

        if len(spatial_coverages) > 0:
            spatial_coverage_data_dict = {}
            spatial_coverage = spatial_coverages[0]
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
        else:
            spatial_coverage_data_dict = None

        keywords = ",".join([sub.value for sub in content_model.metadata.subjects.all()])
        languages_dict = dict(languages_iso.languages)
        language = languages_dict[content_model.metadata.language.code] if \
            content_model.metadata.language else None
        title = content_model.metadata.title.value if content_model.metadata.title else None
        abstract = content_model.metadata.description.abstract if \
            content_model.metadata.description else None

        missing_metadata_elements = content_model.metadata.get_required_missing_elements()

        context = {
                   'resource_edit_mode': resource_edit,
                   'metadata_form': None,
                   'citation': content_model.get_citation(),
                   'title': title,
                   'abstract': abstract,
                   'creators': content_model.metadata.creators.all(),
                   'contributors': content_model.metadata.contributors.all(),
                   'temporal_coverage': temporal_coverage_data_dict,
                   'spatial_coverage': spatial_coverage_data_dict,
                   'language': language,
                   'keywords': keywords,
                   'rights': content_model.metadata.rights,
                   'sources': content_model.metadata.sources.all(),
                   'relations': content_model.metadata.relations.all(),
                   'show_relations_section': show_relations_section(content_model),
                   'fundingagencies': content_model.metadata.funding_agencies.all(),
                   'metadata_status': metadata_status,
                   'missing_metadata_elements': missing_metadata_elements,
                   'validation_error': validation_error if validation_error else None,
                   'resource_creation_error': create_resource_error,
                   'relevant_tools': relevant_tools,
                   'tool_homepage_url': tool_homepage_url,
                   'file_type_error': file_type_error,
                   'just_created': just_created,
                   'just_copied': just_copied,
                   'just_published': just_published,
                   'bag_url': bag_url,
                   'show_content_files': show_content_files,
                   'discoverable': discoverable,
                   'resource_is_mine': resource_is_mine,
                   'allow_resource_copy': allow_copy,
                   'is_resource_specific_tab_active': False,
                   'quota_holder': qholder,
                   'belongs_to_collections': belongs_to_collections
        }

        if 'task_id' in request.session:
            task_id = request.session.get('task_id', None)
            if task_id:
                context['task_id'] = task_id
            del request.session['task_id']

        if 'download_path' in request.session:
            download_path = request.session.get('download_path', None)
            if download_path:
                context['download_path'] = download_path
            del request.session['download_path']

        return context

    # user requested the resource in EDIT MODE

    # whether the user has permission to change the model
    can_change = content_model.can_change(request)
    if not can_change:
        raise PermissionDenied()

    add_creator_modal_form = CreatorForm(allow_edit=can_change, res_short_id=content_model.short_id)
    add_contributor_modal_form = ContributorForm(allow_edit=can_change,
                                                 res_short_id=content_model.short_id)
    add_relation_modal_form = RelationForm(allow_edit=can_change,
                                           res_short_id=content_model.short_id)
    add_source_modal_form = SourceForm(allow_edit=can_change, res_short_id=content_model.short_id)
    add_fundingagency_modal_form = FundingAgencyForm(allow_edit=can_change,
                                                     res_short_id=content_model.short_id)

    keywords = ",".join([sub.value for sub in content_model.metadata.subjects.all()])
    subjects_form = SubjectsForm(initial={'value': keywords}, allow_edit=can_change,
                                 res_short_id=content_model.short_id, element_id=None)

    abstract_form = AbstractForm(instance=content_model.metadata.description,
                                 allow_edit=can_change, res_short_id=content_model.short_id,
                                 element_id=content_model.metadata.description.id if
                                 content_model.metadata.description else None)

    CreatorFormSetEdit = formset_factory(wraps(CreatorForm)(partial(CreatorForm,
                                                                    allow_edit=can_change)),
                                         formset=BaseCreatorFormSet, extra=0)

    creator_formset = CreatorFormSetEdit(initial=content_model.metadata.creators.all().values(),
                                         prefix='creator')
    index = 0

    # TODO: dont track index manually. use enumerate, or zip

    for creator_form in creator_formset.forms:
        creator_form.action = "/hsapi/_internal/%s/creator/%s/update-metadata/" % \
                              (content_model.short_id, creator_form.initial['id'])
        creator_form.number = creator_form.initial['id']
        index += 1

    ContributorFormSetEdit = formset_factory(wraps(ContributorForm)(partial(ContributorForm,
                                                                            allow_edit=can_change)),
                                             formset=BaseContributorFormSet, extra=0)
    contributor_formset = ContributorFormSetEdit(initial=content_model.metadata.contributors.all().
                                                 values(), prefix='contributor')

    index = 0
    # TODO: dont track index manually. use enumerate, or zip
    for contributor_form in contributor_formset.forms:
        contributor_form.action = "/hsapi/_internal/%s/contributor/%s/update-metadata/" % \
                                  (content_model.short_id, contributor_form.initial['id'])
        contributor_form.number = contributor_form.initial['id']
        index += 1

    RelationFormSetEdit = formset_factory(wraps(RelationForm)(partial(RelationForm,
                                                                      allow_edit=can_change)),
                                          formset=BaseFormSet, extra=0)
    relation_formset = RelationFormSetEdit(initial=content_model.metadata.relations.all().values(),
                                           prefix='relation')

    for relation_form in relation_formset.forms:
        relation_form.action = "/hsapi/_internal/%s/relation/%s/update-metadata/" % \
                               (content_model.short_id, relation_form.initial['id'])
        relation_form.number = relation_form.initial['id']

    SourceFormSetEdit = formset_factory(wraps(SourceForm)(partial(SourceForm,
                                                                  allow_edit=can_change)),
                                        formset=BaseFormSet, extra=0)
    source_formset = SourceFormSetEdit(initial=content_model.metadata.sources.all().values(),
                                       prefix='source')

    for source_form in source_formset.forms:
        source_form.action = "/hsapi/_internal/%s/source/%s/update-metadata/" % \
                             (content_model.short_id, source_form.initial['id'])
        source_form.delete_modal_form = MetaDataElementDeleteForm(content_model.short_id,
                                                                  'source',
                                                                  source_form.initial['id'])
        source_form.number = source_form.initial['id']

    FundingAgencyFormSetEdit = formset_factory(wraps(FundingAgencyForm)(partial(
        FundingAgencyForm, allow_edit=can_change)), formset=BaseFormSet, extra=0)
    fundingagency_formset = FundingAgencyFormSetEdit(
        initial=content_model.metadata.funding_agencies.all().values(), prefix='fundingagency')

    for fundingagency_form in fundingagency_formset.forms:
        action = "/hsapi/_internal/{}/fundingagnecy/{}/update-metadata/"
        action = action.format(content_model.short_id, fundingagency_form.initial['id'])
        fundingagency_form.action = action
        fundingagency_form.number = fundingagency_form.initial['id']

    temporal_coverages = content_model.metadata.coverages.all().filter(type='period')
    temporal_coverage_data_dict = {}
    if len(temporal_coverages) > 0:
        temporal_coverage = temporal_coverages[0]
        temporal_coverage_data_dict['start'] = temporal_coverage.value['start']
        temporal_coverage_data_dict['end'] = temporal_coverage.value['end']
        temporal_coverage_data_dict['name'] = temporal_coverage.value.get('name', '')
        temporal_coverage_data_dict['id'] = temporal_coverage.id
    else:
        temporal_coverage = None

    coverage_temporal_form = CoverageTemporalForm(initial=temporal_coverage_data_dict,
                                                  allow_edit=can_change,
                                                  res_short_id=content_model.short_id,
                                                  element_id=temporal_coverage.id if
                                                  temporal_coverage else None)

    spatial_coverages = content_model.metadata.coverages.all().exclude(type='period')
    spatial_coverage_data_dict = {'type': 'point'}
    if len(spatial_coverages) > 0:
        spatial_coverage = spatial_coverages[0]
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
    else:
        spatial_coverage = None

    coverage_spatial_form = CoverageSpatialForm(initial=spatial_coverage_data_dict,
                                                allow_edit=can_change,
                                                res_short_id=content_model.short_id,
                                                element_id=spatial_coverage.id if
                                                spatial_coverage else None)

    metadata_form = ExtendedMetadataForm(resource_mode='edit' if can_change else 'view',
                                         extended_metadata_layout=extended_metadata_layout)

    context = {
               'resource_edit_mode': resource_edit,
               'metadata_form': metadata_form,
               'creator_formset': creator_formset,
               'add_creator_modal_form': add_creator_modal_form,
               'creator_profilelink_formset': None,
               'title': content_model.metadata.title,
               'abstract_form': abstract_form,
               'contributor_formset': contributor_formset,
               'add_contributor_modal_form': add_contributor_modal_form,
               'relation_formset': relation_formset,
               'add_relation_modal_form': add_relation_modal_form,
               'source_formset': source_formset,
               'add_source_modal_form': add_source_modal_form,
               'fundingagnency_formset': fundingagency_formset,
               'add_fundinagency_modal_form': add_fundingagency_modal_form,
               'coverage_temporal_form': coverage_temporal_form,
               'coverage_spatial_form': coverage_spatial_form,
               'spatial_coverage': spatial_coverage_data_dict,
               'subjects_form': subjects_form,
               'metadata_status': metadata_status,
               'missing_metadata_elements': content_model.metadata.get_required_missing_elements(),
               'citation': content_model.get_citation(),
               'extended_metadata_layout': extended_metadata_layout,
               'bag_url': bag_url,
               'current_user': user,
               'show_content_files': show_content_files,
               'validation_error': validation_error if validation_error else None,
               'discoverable': discoverable,
               'resource_is_mine': resource_is_mine,
               'quota_holder': qholder,
               'relation_source_types': tuple((type_value, type_display)
                                              for type_value, type_display in Relation.SOURCE_TYPES
                                              if type_value != 'isReplacedBy' and
                                              type_value != 'isVersionOf' and
                                              type_value != 'hasPart'),
               'is_resource_specific_tab_active': False,
               'belongs_to_collections': belongs_to_collections
    }

    return context


def check_resource_mode(request):
    """
    Determines whether the `request` represents an attempt to edit a resource.
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
            edit_resource = request.GET.get('resource-mode', None) == 'edit'
    else:
        edit_resource = True

    return edit_resource


def check_for_validation(request):
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
