__author__ = 'hydro'

from mezzanine.pages.page_processors import processor_for
from models import *
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML
from forms import *
from hs_core import page_processors
from hs_core.forms import MetaDataElementDeleteForm
from django.forms.models import formset_factory
from hs_core.views import *
from functools import partial, wraps

@processor_for(NetcdfResource)
# when the resource is created this page will be shown
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    if not edit_resource:
        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=None)
        extended_metadata_exists = False
        if content_model.metadata.variables.all():
            extended_metadata_exists = True
        context['extended_metadata_exists'] = extended_metadata_exists

        # add the variables context
        context['variables'] = content_model.metadata.variables.all() # the variables is the field name from NetCDFMetaData model

        # add the original coverage context
        if content_model.metadata.originalCoverage:
            ori_coverage_data_dict = {}
            ori_coverage_data_dict['name'] = content_model.metadata.originalCoverage.value.get('name', None)
            ori_coverage_data_dict['units'] = content_model.metadata.originalCoverage.value['units']
            ori_coverage_data_dict['projection'] = content_model.metadata.originalCoverage.value.get('projection', None)
            ori_coverage_data_dict['northlimit'] = content_model.metadata.originalCoverage.value['northlimit']
            ori_coverage_data_dict['eastlimit'] = content_model.metadata.originalCoverage.value['eastlimit']
            ori_coverage_data_dict['southlimit'] = content_model.metadata.originalCoverage.value['southlimit']
            ori_coverage_data_dict['westlimit'] = content_model.metadata.originalCoverage.value['westlimit']
            context['originalCoverage'] = ori_coverage_data_dict

    else:
        # Original Coverage in editing mode # get the context from content_model
        ori_coverage_data_dict = {}
        if content_model.metadata.originalCoverage:
            ori_coverage_data_dict['name'] = content_model.metadata.originalCoverage.value.get('name', None)
            ori_coverage_data_dict['units'] = content_model.metadata.originalCoverage.value['units']
            ori_coverage_data_dict['projection'] = content_model.metadata.originalCoverage.value.get('projection', None)
            ori_coverage_data_dict['northlimit'] = content_model.metadata.originalCoverage.value['northlimit']
            ori_coverage_data_dict['eastlimit'] = content_model.metadata.originalCoverage.value['eastlimit']
            ori_coverage_data_dict['southlimit'] = content_model.metadata.originalCoverage.value['southlimit']
            ori_coverage_data_dict['westlimit'] = content_model.metadata.originalCoverage.value['westlimit']
        else:
            ori_coverage_data_dict = None

        original_coverage_spatial_form = OriginalCoverageSpatialForm(initial = ori_coverage_data_dict, instance=content_model.metadata.originalCoverage, res_short_id=content_model.short_id,
                                     allow_edit = edit_resource, element_id=content_model.metadata.originalCoverage.id if content_model.metadata.originalCoverage else None)


        # Variable Forms in editing mode
        VariableFormSetEdit = formset_factory(wraps(VariableForm)(partial(VariableForm, allow_edit=edit_resource)), formset=BaseFormSet, extra=0)
        variable_formset = VariableFormSetEdit(initial=content_model.metadata.variables.all().values(), prefix='variable')
        add_variable_modal_form = VariableForm(allow_edit=edit_resource, res_short_id=content_model.short_id)
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

        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=ext_md_layout)
        context['variable_formset'] = variable_formset
        context['add_variable_modal_form'] = add_variable_modal_form
        context['original_coverage_spatial_form'] = original_coverage_spatial_form

    hs_core_dublin_context = add_dublin_core(request, page)
    context.update(hs_core_dublin_context)
    return context
