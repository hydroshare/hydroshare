__author__ = 'tonycastronova'

from models import *
from crispy_forms.layout import Layout, HTML
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
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource,
                                                   extended_metadata_layout=None)
        extended_metadata_exists = False
        if content_model.metadata.program:
            extended_metadata_exists = True

        context['extended_metadata_exists'] = extended_metadata_exists
        context['mpmetadata'] = content_model.metadata.program


    else:
        output_form = mp_form(files=content_model.files, instance=content_model.metadata.program,
                              res_short_id=content_model.short_id,
                              element_id=content_model.metadata.program.id if content_model.metadata.program else None)

        ext_md_layout = Layout(
                        HTML("<div class='form-group col-lg-4 col-xs-12' id='site'> "
                                '{% load crispy_forms_tags %} '
                                '{% crispy output_form %} '
                             '</div>'),
                )

        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource,
                                                   extended_metadata_layout=ext_md_layout)

        context['resource_type'] = 'Model Program Resource'
        context['output_form'] = output_form

    hs_core_context = add_generic_context(request, page)
    context.update(hs_core_context)
    return context
