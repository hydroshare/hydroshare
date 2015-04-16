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
from hs_app_netCDF.forms import ModalDialogLayoutAddVariable

@processor_for(NetcdfResource)
# when the resource is created this page will be shown
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    if not edit_resource: # not editing mode
        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=None)
        extended_metadata_exists = False

        if content_model.metadata.variables.all() or content_model.metadata.ori_coverage.all():
            extended_metadata_exists = True
        elif content_model.files.all():
            for f in content_model.files.all():
                if '_header_info.txt' in f.resource_file.name:
                    extended_metadata_exists = True



        context['extended_metadata_exists'] = extended_metadata_exists

        # add the variables context
        context['variables'] = content_model.metadata.variables.all() # the variables is the field name from NetCDFMetaData model

        # add the original coverage context
        ori_cov_dict = {}
        ori_cov_obj = content_model.metadata.ori_coverage.all().first()
        if ori_cov_obj:
            ori_cov_dict['name'] = ori_cov_obj.value.get('name', None)
            ori_cov_dict['units'] = ori_cov_obj.value['units']
            ori_cov_dict['projection'] = ori_cov_obj.value.get('projection', None)
            ori_cov_dict['northlimit'] = ori_cov_obj.value['northlimit']
            ori_cov_dict['eastlimit'] = ori_cov_obj.value['eastlimit']
            ori_cov_dict['southlimit'] = ori_cov_obj.value['southlimit']
            ori_cov_dict['westlimit'] = ori_cov_obj.value['westlimit']
            ori_cov_dict['projection_string_type'] = ori_cov_obj.projection_string_type
            ori_cov_dict['projection_string_text'] = ori_cov_obj.projection_string_text
            context['original_coverage'] = ori_cov_dict
        else:
            context['original_coverage'] = None

    else: # editing mode

        # Original Coverage in editing mode
        ori_cov_obj = content_model.metadata.ori_coverage.all().first()
        ori_cov_dict = {}
        if ori_cov_obj:
            ori_cov_dict['name'] = ori_cov_obj.value.get('name', None)
            ori_cov_dict['units'] = ori_cov_obj.value['units']
            ori_cov_dict['projection'] = ori_cov_obj.value.get('projection', None)
            ori_cov_dict['northlimit'] = ori_cov_obj.value['northlimit']
            ori_cov_dict['eastlimit'] = ori_cov_obj.value['eastlimit']
            ori_cov_dict['southlimit'] = ori_cov_obj.value['southlimit']
            ori_cov_dict['westlimit'] = ori_cov_obj.value['westlimit']
            ori_cov_dict['projection_string_type'] = ori_cov_obj.projection_string_type
            ori_cov_dict['projection_string_text'] = ori_cov_obj.projection_string_text
        else:
            ori_cov_obj = None

        ori_cov_form = OriginalCoverageForm(initial=ori_cov_dict,
                                            allow_edit=edit_resource,
                                            res_short_id=content_model.short_id,
                                            element_id=ori_cov_obj.id if ori_cov_obj else None)

        ori_cov_form.delete_modal_form = OriginalCoverageMetaDelete(content_model.short_id, 'originalcoverage', ori_cov_obj.id if ori_cov_obj else None)

        # Variable Forms in editing mode
        VariableFormSetEdit = formset_factory(wraps(VariableForm)(partial(VariableForm, allow_edit=edit_resource)), formset=BaseFormSet, extra=0)
        variable_formset = VariableFormSetEdit(initial=content_model.metadata.variables.all().values(), prefix='variable')
        add_variable_modal_form = VariableForm(allow_edit=edit_resource, res_short_id=content_model.short_id)

        for form in variable_formset.forms:
            if len(form.initial) > 0:
                form.delete_modal_form = MetaDataElementDeleteForm(content_model.short_id, 'variable', form.initial['id'])
                form.action = "/hsapi/_internal/%s/variable/%s/update-metadata/" % (content_model.short_id, form.initial['id'])
                form.number = form.initial['id']
            else:
                form.action = "/hsapi/_internal/%s/variable/add-metadata/" % content_model.short_id

        # get the context from hs_core
        ext_md_layout = Layout(
                                AccordionGroup('Original Coverage',
                                     HTML('<div class="form-group" id="originalcoverage"> '
                                            '{% load crispy_forms_tags %} '
                                            '{% crispy original_coverage_form %} '
                                          '</div> '

                                          '<div class="row" style="margin-top:10px">'
                                            '<div class="col-md-10">'
                                                '<input class="btn-danger btn btn-md" onclick="check_ori_meta_status()" type="button" data-toggle="modal" data-target="#delete-original-coverage-element-dialog" value="Delete Original Coverage">'
                                            '</div>'
                                          '</div>'
                                          '{% crispy original_coverage_form.delete_modal_form %} '
                                     ),
                                ),
                                AccordionGroup('Variable', VariableLayoutEdit),
                                ModalDialogLayoutAddVariable,
                            )

        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=ext_md_layout)
        context['variable_formset'] = variable_formset
        context['add_variable_modal_form'] = add_variable_modal_form
        context['original_coverage_form'] = ori_cov_form

    hs_core_context = add_generic_context(request, page)
    context.update(hs_core_context)

    return context
