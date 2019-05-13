from crispy_forms.layout import Layout, HTML
from django.http import HttpResponseRedirect
from mezzanine.pages.page_processors import processor_for

from forms import ScriptForm
from hs_core import page_processors
from hs_core.views import add_generic_context
from models import ScriptResource


@processor_for(ScriptResource)
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    if not edit_resource:
        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource,
                                                   extended_metadata_layout=None, request=request)
        if isinstance(context, HttpResponseRedirect):
            # sending user to login page
            return context

        extended_metadata_exists = False
        if content_model.metadata.program:
            extended_metadata_exists = True

        context['extended_metadata_exists'] = extended_metadata_exists
        context['script_metadata'] = content_model.metadata.program

        # get the helptext for each mp field
        attributes = [
            (f, f.model if f.model else None)
            for f in content_model.metadata.scriptspecificmetadata.model._meta.get_fields()
            if not f.is_relation
                or f.one_to_one
                or (f.many_to_one and f.related_model)
        ]
        attribute_dict = {}
        for att in attributes:
            if hasattr(att[0], 'help_text'):
                attribute_dict[att[0].attname] = att[0].help_text
        context["scripthelptext"] = attribute_dict

    else:
        output_form = ScriptForm(instance=content_model.metadata.program,
                                 res_short_id=content_model.short_id,
                                 element_id=content_model.metadata.program.id
                                 if content_model.metadata.program else None)

        ext_md_layout = Layout(
                HTML('<div class="col-sm-12">'
                     '{% load crispy_forms_tags %} '
                     '{% crispy output_form %} '
                     '</div>'),
        )

        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource,
                                                   extended_metadata_layout=ext_md_layout, request=request)

        context['output_form'] = output_form

    hs_core_context = add_generic_context(request, page)
    context.update(hs_core_context)

    return context
