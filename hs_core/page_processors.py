from mezzanine.pages.page_processors import processor_for
from hs_core.models import GenericResource
from forms import *

@processor_for(GenericResource)
def landing_page(request, page):
    if request.method == "GET":
        return get_page_context(page)


# resource type specific app needs to call this method to inject a crispy_form layout
# object for displaying metadata UI for the extended metadata for their resource
def get_page_context(page, extended_metadata_layout=None):
    content_model = page.get_content_model()
    add_creator_modal_form = CreatorForm(res_short_id=content_model.short_id)
    add_contributor_modal_form = ContributorForm(res_short_id=content_model.short_id)

    CreatorFormSetEdit = formset_factory(CreatorForm, formset=BaseCreatorFormSet, extra=0)
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

    ContributorFormSetEdit = formset_factory(ContributorForm, formset=BaseContributorFormSet, extra=0)
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

    metadata_form = MetaDataForm(resource_mode='edit', extended_metadata_layout=extended_metadata_layout)

    context = {'metadata_form': metadata_form,
               'creator_formset': creator_formset,
               'add_creator_modal_form': add_creator_modal_form,
               'creator_profilelink_formset': None,
               'title': content_model.metadata.title,
               'abstract': content_model.metadata.description,
               'contributor_formset': contributor_formset,
               'add_contributor_modal_form': add_contributor_modal_form,
               'extended_metadata_layout': extended_metadata_layout}

    return context