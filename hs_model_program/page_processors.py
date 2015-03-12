__author__ = 'tonycastronova'

from models import *
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML
from forms import *
from hs_core import page_processors
from hs_core.views import *

@processor_for(ModelProgramResource)
# when the resource is created this page will be shown
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    if not edit_resource:
        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=None)
        extended_metadata_exists = False
        if content_model.metadata.mpmetadata.all():
            extended_metadata_exists = True

        context['extended_metadata_exists'] = extended_metadata_exists
        context['mpmetadata'] = content_model.metadata.mpmetadata.all().first()


    else:

        output_form = mp_form(files = content_model.files, instance=content_model.metadata.mpmetadata.all().first(), res_short_id=content_model.short_id, element_id=content_model.metadata.mpmetadata.all().first().id if content_model.metadata.mpmetadata.all().first() else None)


        ext_md_layout = Layout(
                                AccordionGroup('Model Program Extended Metadata',
                                    HTML("<div class='form-group' id='extended_metadata'> "
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy output_form %} '
                                     '</div>'),
                                ),
                        )


        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=ext_md_layout)

        context['resource_type'] = 'Model Program Resource'
        context['output_form'] = output_form
    hs_core_dublin_context = add_dublin_core(request, page)
    context.update(hs_core_dublin_context)


    return context
