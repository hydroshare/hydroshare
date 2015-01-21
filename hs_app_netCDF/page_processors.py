__author__ = 'hydro'

from mezzanine.pages.page_processors import processor_for
from models import *
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML
from forms import *
from hs_core import page_processors
from hs_core.forms import MetaDataElementDeleteForm
from django.forms.models import formset_factory

@processor_for(NetcdfResource)
# when the resource is created this page will be shown
def landing_page(request, page):
    content_model = page.get_content_model()
    if request.method == 'GET':
        VariableFormSetEdit = formset_factory(VariableForm, formset=BaseVariableFormSet, extra=0)
        variable_formset = VariableFormSetEdit(initial=content_model.metadata.variables.all().values(), prefix='variable')
        add_variable_modal_form = VariableForm(res_short_id=content_model.short_id)
        ext_md_layout = Layout(
                                VariableLayoutEdit,
                                ModalDialogLayoutAddVariable
                            )

        for form in variable_formset.forms:
            if len(form.initial) > 0:
                form.delete_modal_form = MetaDataElementDeleteForm(content_model.short_id, 'variable', form.initial['id'])
                form.action = "/hsapi/_internal/%s/variable/%s/update-metadata/" % (content_model.short_id, form.initial['id'])
                form.number = form.initial['id']
            else:
                form.action = "/hsapi/_internal/%s/variable/add-metadata/" % content_model.short_id

        context = page_processors.get_page_context(page, request.user, extended_metadata_layout=ext_md_layout)
        context['variable_formset'] = variable_formset
        context['add_variable_modal_form'] = add_variable_modal_form
        return context
