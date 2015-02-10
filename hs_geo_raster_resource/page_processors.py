__author__ = 'Hong Yi'
from mezzanine.pages.page_processors import processor_for
from models import RasterResource
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML
from forms import *
from hs_core import page_processors

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
        # cell_info_form = CellInfoForm(instance=content_model.metadata.cellInformation, res_short_id=content_model.short_id,
        #                 element_id=content_model.metadata.cellInformation.id if content_model.metadata.cellInformation else None)
        band_info_form = []
        for band in content_model.metadata.bandInformation:
            band_form = BandInfoForm(instance=band, res_short_id=content_model.short_id,
                            element_id=band.id if band else None)
            band_info_form.append(band_form)

        ext_md_layout = Layout(
                AccordionGroup('Band Information (required)',
                    HTML('<div class="form-group" id="bandinfo"> '
                        '{% load crispy_forms_tags %} '
                        '{% crispy  band_form %} '
                        '</div> '),
                    ),
                )

        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=ext_md_layout)
        #context['cell_info_form'] = cell_info_form
        #context['cellInformation'] = content_model.metadata.cellInformation
        #for i in range(len(band_info_form)):
        #    context['band_form_'+str(i)] = band_info_form[i]
        context['band_form']=band_form
    return context