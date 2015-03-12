__author__ = 'Hong Yi'
from mezzanine.pages.page_processors import processor_for
from models import RasterResource
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML
from forms import *
from hs_core import page_processors
from django.forms.models import formset_factory
from hs_core.views import *

# page processor to populate raster resource specific metadata into my-resources template page
@processor_for(RasterResource)
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=None)
    extended_metadata_exists = False
    if content_model.metadata.cellInformation or content_model.metadata.bandInformation:
        extended_metadata_exists = True

    context['extended_metadata_exists'] = extended_metadata_exists
    if not edit_resource:
        # get the context from hs_core
        context['cellInformation'] = content_model.metadata.cellInformation
        context['bandInformation'] = content_model.metadata.bandInformation
    else:
        cellinfo_form = CellInfoForm(instance=content_model.metadata.cellInformation, res_short_id=content_model.short_id,
                                     allow_edit = True if content_model.metadata.cellInformation.noDataValue is None else False,
                                    element_id=content_model.metadata.cellInformation.id if content_model.metadata.cellInformation else None)

        BandInfoFormSetEdit = formset_factory(wraps(BandInfoForm)(partial(BandInfoForm, allow_edit=edit_resource)), formset=BaseBandInfoFormSet, extra=0)
        bandinfo_formset = BandInfoFormSetEdit(initial=content_model.metadata.bandInformation.values(), prefix='bandinformation')
        ext_md_layout = Layout(
                            AccordionGroup('CellInformation (required)',
                                HTML("<div class='form-group' id='cellinformation'> "
                                '{% load crispy_forms_tags %} '
                                '{% crispy cellinfo_form %} '
                                '</div>'),
                                ),
                            BandInfoLayoutEdit
                        )
        for form in bandinfo_formset.forms:
            if len(form.initial) > 0:
                form.action = "/hsapi/_internal/%s/bandinformation/%s/update-metadata/" % (content_model.short_id, form.initial['id'])
                form.number = form.initial['id']

        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=ext_md_layout)
        context['cellinfo_form']=cellinfo_form
        context['bandinfo_formset']=bandinfo_formset

    hs_core_dublin_context = add_dublin_core(request, page)
    context.update(hs_core_dublin_context)
    return context
