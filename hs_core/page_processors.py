from mezzanine.pages.page_processors import processor_for
from hs_core.models import GenericResource
from forms import *

@processor_for(GenericResource)
def landing_page(request, page):
    content_model = page.get_content_model()
    creator_formset = CreatorFormSet(request.POST or None, prefix='creator')
    contributor_formset = ContributorFormSet(request.POST or None, prefix='contributor')
    #creator_profilelink_formset = ProfileLinksFormset(request.POST or None, prefix='creators_links')
    add_creator_modal_form = CreatorForm(res_short_id=content_model.short_id)

    if request.method == "GET":
        CreatorFormSetEdit = formset_factory(CreatorForm, formset=BaseCreatorFormSet, extra=0)
        creator_formset = CreatorFormSetEdit(initial=content_model.metadata.creators.all().values(), prefix='creator')
        index = 0
        creators = content_model.metadata.creators.all()
        links = []
        ProfileLinksFormSetEdit = formset_factory(ProfileLinksForm, formset=BaseProfileLinkFormSet, extra=0)

        for creator_form in creator_formset.forms:
            #links.append(creators[index].external_links.all().values('type', 'url'))
            creator_form.helper.form_method = 'post'
            creator_form.helper.form_tag = True
            creator_form.helper.form_action = "/hsapi/_internal/%s/creator/%s/update-metadata/" % (content_model.short_id, creator_form.initial['id'])
            creator_form.profile_link_formset = ProfileLinksFormSetEdit(initial=creators[index].external_links.all().values('type', 'url'), prefix='creator_links-%s' % index)
            creator_form.delete_modal_form = MetaDataElementDeleteForm(content_model.short_id, 'creator', creator_form.initial['id'])
            index += 1

        ContributorFormSetEdit = formset_factory(ContributorForm, formset=BaseContributorFormSet, extra=0)
        contributor_formset = ContributorFormSetEdit(initial=content_model.metadata.contributors.all().values(), prefix='contributor')
        ext_md_layout = None
        metadata_form = MetaDataForm(resource_mode='edit', extended_metadata_layout=ext_md_layout)


        #creator_helper = CreatorFormSetHelper()
        context = {'metadata_form': metadata_form, 'creator_formset': creator_formset,
                   'add_creator_modal_form': add_creator_modal_form,
                   'creator_profilelink_formset': None, 'title': content_model.metadata.title,
                   'abstract': content_model.metadata.description,
                   'contributor_formset': contributor_formset, 'extended_metadata_layout': ext_md_layout}

        return context


def get_page_context(page, extended_metadata_layout=None):
    content_model = page.get_content_model()
    creator_formset = CreatorFormSet(initial=content_model.metadata.creators.all().values(), prefix='creator')
    index = 0
    creators = content_model.metadata.creators.all()
    for form in creator_formset.forms:
        form.profile_link_formset = ProfileLinksFormset(initial=creators[index].external_links.all().values(), prefix='creator_links-%s' % index)
        index += 1

    contributor_formset = ContributorFormSet(initial=content_model.metadata.contributors.all().values(), prefix='contributor')

    metadata_form = MetaDataForm(extended_metadata_layout=extended_metadata_layout)


    #creator_helper = CreatorFormSetHelper()
    context = {'metadata_form': metadata_form, 'creator_formset': creator_formset,
               'creator_profilelink_formset': None, 'title': content_model.metadata.title,
               'abstract': content_model.metadata.description,
               'contributor_formset': contributor_formset}

    return context