from mezzanine.pages.page_processors import processor_for

from hs_core.models import GenericResource
from hs_core import languages_iso
from forms import *
from hs_tools_resource.models import ToolResourceType

@processor_for(GenericResource)
def landing_page(request, page):
    if request.method == "GET":
        resource_mode = request.session.get('resource-mode', None)
        if resource_mode == 'edit':
            edit_resource = True
            del request.session['resource-mode']
        else:
            edit_resource = False
    else:
        edit_resource = True

    return get_page_context(page, request.user, resource_edit=edit_resource, request=request)

# resource type specific app needs to call this method to inject a crispy_form layout
# object for displaying metadata UI for the extended metadata for their resource
def get_page_context(page, user, resource_edit=False, extended_metadata_layout=None, request=None):
    file_type_error=''
    if request:
        file_type_error = request.session.get("file_type_error", None)
        if file_type_error:
            del request.session["file_type_error"]

    content_model = page.get_content_model()
    edit_mode = False
    file_validation_error = None
    if user.username == 'admin' or \
                    content_model.creator == user or \
                    user in (content_model.owners.all() | content_model.edit_users.all()):
        edit_mode = True

    metadata_status = _get_metadata_status(content_model)

    relevant_tools = []
    for res_type in ToolResourceType.objects.all():
        if str(content_model.content_model).lower() in str(res_type.tool_res_type).lower():
            url = res_type.content_object.resource.metadata.url_bases.first()
            if url:
                tl = {'title': res_type.content_object.resource.title,
                      'url': "{}{}{}".format(url.value, "/?res_id=", content_model.short_id)}
                relevant_tools.append(tl)


    just_created = False
    if request:
        file_validation_error = check_for_file_validation(request)

        just_created = request.session.get('just_created', False)
        if 'just_created' in request.session:
            del request.session['just_created']

    bag_url = "/django_irods/download/?path=bags/{res_id}.zip".format(res_id=content_model.short_id)

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
            spatial_coverage_data_dict['projection'] = spatial_coverage.value.get('projection', None)
            spatial_coverage_data_dict['type'] = spatial_coverage.type
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
            spatial_coverage_data_dict = None

        keywords = ",".join([sub.value for sub in content_model.metadata.subjects.all()])
        languages_dict = dict(languages_iso.languages)
        language = languages_dict[content_model.metadata.language.code] if content_model.metadata.language else None
        title = content_model.metadata.title.value if content_model.metadata.title else None
        abstract = content_model.metadata.description.abstract if content_model.metadata.description else None
        context = {'metadata_form': None,
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
                   'metadata_status': metadata_status,
                   'missing_metadata_elements': content_model.metadata.get_required_missing_elements(),
                   'supported_file_types': content_model.get_supported_upload_file_types(),
                   'allow_multiple_file_upload': content_model.can_have_multiple_files(),
                   'file_validation_error': file_validation_error if file_validation_error else None,
                   'relevant_tools': relevant_tools,
                   'file_type_error': file_type_error,
                   'just_created': just_created,
                   'bag_url': bag_url
        }
        return context

    # resource in edit mode
    add_creator_modal_form = CreatorForm(allow_edit=edit_mode, res_short_id=content_model.short_id)
    add_contributor_modal_form = ContributorForm(allow_edit=edit_mode, res_short_id=content_model.short_id)
    add_relation_modal_form = RelationForm(allow_edit=edit_mode, res_short_id=content_model.short_id)
    add_source_modal_form = SourceForm(allow_edit=edit_mode, res_short_id=content_model.short_id)

    title_form = TitleForm(instance=content_model.metadata.title, allow_edit=edit_mode, res_short_id=content_model.short_id,
                             element_id=content_model.metadata.title.id if content_model.metadata.title else None)

    keywords = ",".join([sub.value for sub in content_model.metadata.subjects.all()])
    subjects_form = SubjectsForm(initial={'value': keywords}, allow_edit=edit_mode, res_short_id=content_model.short_id,
                             element_id=None)

    abstract_form = AbstractForm(instance=content_model.metadata.description, allow_edit=edit_mode, res_short_id=content_model.short_id,
                             element_id=content_model.metadata.description.id if content_model.metadata.description else None)

    CreatorFormSetEdit = formset_factory(wraps(CreatorForm)(partial(CreatorForm, allow_edit=edit_mode)), formset=BaseCreatorFormSet, extra=0)

    creator_formset = CreatorFormSetEdit(initial=content_model.metadata.creators.all().values(), prefix='creator')
    index = 0
    creators = content_model.metadata.creators.all()
    ProfileLinksFormSetEdit = formset_factory(ProfileLinksForm, formset=BaseProfileLinkFormSet, extra=0)

    for creator_form in creator_formset.forms:
        creator_form.action = "/hsapi/_internal/%s/creator/%s/update-metadata/" % (content_model.short_id, creator_form.initial['id'])
        creator_form.profile_link_formset = ProfileLinksFormSetEdit(initial=creators[index].external_links.all().values('type', 'url'), prefix='creator_links-%s' % index)

        # TODO: Temporarily the delete profile link is disabled on the resource landing page as we do not how the functionality for this button be implemented
        for link_form in creator_form.profile_link_formset.forms:
            link_form.helper.layout[1][0] = StrictButton('Delete link', css_class=link_form.helper.delete_btn_class, disabled="disabled")

        creator_form.delete_modal_form = MetaDataElementDeleteForm(content_model.short_id, 'creator', creator_form.initial['id'])
        creator_form.number = creator_form.initial['id']
        index += 1

    ContributorFormSetEdit = formset_factory(wraps(ContributorForm)(partial(ContributorForm, allow_edit=edit_mode)), formset=BaseContributorFormSet, extra=0)
    contributor_formset = ContributorFormSetEdit(initial=content_model.metadata.contributors.all().values(), prefix='contributor')

    contributors = content_model.metadata.contributors.all()
    index = 0
    for contributor_form in contributor_formset.forms:
        contributor_form.action = "/hsapi/_internal/%s/contributor/%s/update-metadata/" % (content_model.short_id, contributor_form.initial['id'])
        contributor_form.profile_link_formset = ProfileLinksFormSetEdit(initial=contributors[index].external_links.all().values('type', 'url'), prefix='contributor_links-%s' % index)

        # TODO: Temporarily the delete profile link is disabled on the resource landing page as we do not know how the functionality for this button be implemented
        for link_form in contributor_form.profile_link_formset.forms:
            link_form.helper.layout[1][0] = StrictButton('Delete link', css_class=link_form.helper.delete_btn_class, disabled="disabled")

        contributor_form.delete_modal_form = MetaDataElementDeleteForm(content_model.short_id, 'contributor', contributor_form.initial['id'])
        contributor_form.number = contributor_form.initial['id']
        index += 1

    RelationFormSetEdit = formset_factory(wraps(RelationForm)(partial(RelationForm, allow_edit=edit_mode)), formset=BaseFormSet, extra=0)
    relation_formset = RelationFormSetEdit(initial=content_model.metadata.relations.all().values(), prefix='relation')

    for relation_form in relation_formset.forms:
        relation_form.action = "/hsapi/_internal/%s/relation/%s/update-metadata/" % (content_model.short_id, relation_form.initial['id'])
        relation_form.delete_modal_form = MetaDataElementDeleteForm(content_model.short_id, 'relation', relation_form.initial['id'])
        relation_form.number = relation_form.initial['id']

    SourceFormSetEdit = formset_factory(wraps(SourceForm)(partial(SourceForm, allow_edit=edit_mode)), formset=BaseFormSet, extra=0)
    source_formset = SourceFormSetEdit(initial=content_model.metadata.sources.all().values(), prefix='source')

    # IdentifierFormSetEdit = formset_factory(IdentifierForm, formset=BaseFormSet, extra=0)
    # identifier_formset = IdentifierFormSetEdit(initial=content_model.metadata.identifiers.all().values(), prefix='identifier')
    #
    # FormatFormSetEdit = formset_factory(FormatForm, formset=BaseFormSet, extra=0)
    # format_formset = FormatFormSetEdit(initial=content_model.metadata.formats.all().values(), prefix='format')

    for source_form in source_formset.forms:
        source_form.action = "/hsapi/_internal/%s/source/%s/update-metadata/" % (content_model.short_id, source_form.initial['id'])
        source_form.delete_modal_form = MetaDataElementDeleteForm(content_model.short_id, 'source', source_form.initial['id'])
        source_form.number = source_form.initial['id']

    rights_form = RightsForm(instance=content_model.metadata.rights,
                             allow_edit=edit_mode,
                             res_short_id=content_model.short_id,
                             element_id=content_model.metadata.rights.id if content_model.metadata.rights else None)

    language_form = LanguageForm(instance=content_model.metadata.language,
                                 allow_edit=edit_mode,
                                 res_short_id=content_model.short_id,
                                 element_id=content_model.metadata.language.id if content_model.metadata.language
                                 else None)

    # valid_dates = content_model.metadata.dates.all().filter(type='valid')
    # if len(valid_dates) > 0:
    #     valid_date = valid_dates[0]
    # else:
    #     valid_date = None

    # valid_date_form = ValidDateForm(instance=valid_date,
    #                                 allow_edit=edit_mode,
    #                                 res_short_id=content_model.short_id,
    #                                 element_id=valid_date.id if valid_date else None)

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

    coverage_temporal_form = CoverageTemporalForm(initial= temporal_coverage_data_dict,
                                                  allow_edit=edit_mode,
                                                  res_short_id=content_model.short_id,
                                                  element_id=temporal_coverage.id if temporal_coverage else None)

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
                                                allow_edit=edit_mode,
                                                res_short_id=content_model.short_id,
                                                element_id=spatial_coverage.id if spatial_coverage else None)

    # metadata_form = MetaDataForm(resource_mode='edit' if edit_mode else 'view',
    #                              extended_metadata_layout=extended_metadata_layout)

    metadata_form = ExtendedMetadataForm(resource_mode='edit' if edit_mode else 'view',
                                 extended_metadata_layout=extended_metadata_layout)

    context = {'metadata_form': metadata_form,
               'title_form': title_form,
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
               'rights_form': rights_form,
               #'identifier_formset': identifier_formset,
               'language_form': language_form,
               #'valid_date_form': valid_date_form,
               'coverage_temporal_form': coverage_temporal_form,
               'coverage_spatial_form': coverage_spatial_form,
               #'format_formset': format_formset,
               'subjects_form': subjects_form,
               'metadata_status': metadata_status,
               'citation': content_model.get_citation(),
               'extended_metadata_layout': extended_metadata_layout,
               'bag_url': bag_url,
               'file_validation_error': file_validation_error if file_validation_error else None
    }

    return context


def check_resource_mode(request):
    if request.method == "GET":
        resource_mode = request.session.get('resource-mode', None)
        if resource_mode == 'edit':
            edit_resource = True
            del request.session['resource-mode']
        else:
            edit_resource = False
    else:
        edit_resource = True

    return edit_resource

def check_for_file_validation(request):
    if request.method == "GET":
        file_validation_error = request.session.get('file_validation_error', None)
        if file_validation_error:
            del request.session['file_validation_error']
            return file_validation_error

    return None

def _get_metadata_status(resource):
    if resource.metadata.has_all_required_elements():
        metadata_status = "Sufficient to make public"
    else:
        metadata_status = "Insufficient to make public"

    return metadata_status
