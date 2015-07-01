__author__ = 'drew'

from mezzanine.pages.page_processors import processor_for
from models import *
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML
from hs_core import page_processors
from hs_core.views import *
from hs_geographic_feature_resource.forms import *

@processor_for(GeographicFeatureResource)
# when the resource is created this page will be shown
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    if not edit_resource: # not editing mode
        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=None, request=request)
        extended_metadata_exists = False

        if content_model.metadata.originalcoverage.all() :
            extended_metadata_exists = True

        context['extended_metadata_exists'] = extended_metadata_exists

        # # add the variables context
        # context['variables'] = content_model.metadata.variables.all() # the variables is the field name from NetCDFMetaData model
        #
        # add the original coverage context
        ori_cov_dict = {}
        ori_cov_obj = content_model.metadata.originalcoverage.all().first()
        if ori_cov_obj:
            ori_cov_dict['northlimit'] = ori_cov_obj.extent['northlimit']
            ori_cov_dict['eastlimit'] = ori_cov_obj.extent['eastlimit']
            ori_cov_dict['southlimit'] = ori_cov_obj.extent['southlimit']
            ori_cov_dict['westlimit'] = ori_cov_obj.extent['westlimit']
            ori_cov_dict['projection_string'] = ori_cov_obj.projection_string

            context['original_coverage'] = ori_cov_dict
        else:
            context['original_coverage'] = None

    else: # editing mode

        # origina coverage_form
        ori_cov_obj = content_model.metadata.originalcoverage.all().first()
        ori_coverage_data_dict = {}
        if ori_cov_obj:
            ori_coverage_data_dict['projection_string'] = ori_cov_obj.projection_string
            ori_coverage_data_dict['northlimit'] = ori_cov_obj.extent['northlimit']
            ori_coverage_data_dict['eastlimit'] = ori_cov_obj.extent['eastlimit']
            ori_coverage_data_dict['southlimit'] = ori_cov_obj.extent['southlimit']
            ori_coverage_data_dict['westlimit'] = ori_cov_obj.extent['westlimit']
        else:
            ori_cov_obj = None

        ori_coverage_form = OriginalCoverageForm(initial=ori_coverage_data_dict,
                                                        res_short_id=content_model.short_id,
                                                        allow_edit=edit_resource,
                                                        element_id=ori_cov_obj.id if ori_cov_obj else None)
        ori_coverage_layout = HTML('<div class="form-group col-lg-6 col-xs-12" id="originalcoverage"> '
                                   '{% load crispy_forms_tags %} '
                                   '{% crispy ori_coverage_form %} '
                                   '</div>')

        # update context
        ext_md_layout = Layout(
                                ori_coverage_layout,
                                )
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=ext_md_layout)
        context['ori_coverage_form'] = ori_coverage_form

    hs_core_context = add_generic_context(request, page)
    context.update(hs_core_context)

    return context
