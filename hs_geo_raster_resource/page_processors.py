__author__ = 'Hong Yi'
from mezzanine.pages.page_processors import processor_for
from models import RasterResource
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML
from forms import *
from hs_core import page_processors
from django.forms.models import formset_factory
from hs_core.views import *
from functools import partial, wraps

# page processor to populate raster resource specific metadata into my-resources template page
@processor_for(RasterResource)
# TODO: problematic permissions
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=None, request=request)
    extended_metadata_exists = False
    if content_model.metadata.cellInformation or content_model.metadata.bandInformation:
        extended_metadata_exists = True

    context['extended_metadata_exists'] = extended_metadata_exists
    if not edit_resource:
        # get the context from content_model
        if content_model.metadata.originalCoverage:
            ori_coverage_data_dict = {}
            ori_coverage_data_dict['units'] = content_model.metadata.originalCoverage.value['units']
            ori_coverage_data_dict['projection'] = content_model.metadata.originalCoverage.value.get('projection', None)
            ori_coverage_data_dict['northlimit'] = content_model.metadata.originalCoverage.value['northlimit']
            ori_coverage_data_dict['eastlimit'] = content_model.metadata.originalCoverage.value['eastlimit']
            ori_coverage_data_dict['southlimit'] = content_model.metadata.originalCoverage.value['southlimit']
            ori_coverage_data_dict['westlimit'] = content_model.metadata.originalCoverage.value['westlimit']
            context['originalCoverage'] = ori_coverage_data_dict
        context['cellInformation'] = content_model.metadata.cellInformation
        context['bandInformation'] = content_model.metadata.bandInformation
    else:
        # cellinfo_form
        cellinfo_form = CellInfoForm(instance=content_model.metadata.cellInformation, res_short_id=content_model.short_id,
                                     allow_edit = True,
                                    element_id=content_model.metadata.cellInformation.id if content_model.metadata.cellInformation else None)
        cellinfo_layout = HTML("<div class='form-group col-lg-6 col-xs-12' id='CellInformation'> "
                                 '{% load crispy_forms_tags %} '
                                 '{% crispy cellinfo_form %} '
                                 '</div>')
        # bandinfo_formset
        BandInfoFormSetEdit = formset_factory(wraps(BandInfoForm)(partial(BandInfoForm, allow_edit=edit_resource)), formset=BaseBandInfoFormSet, extra=0)
        bandinfo_formset = BandInfoFormSetEdit(initial=content_model.metadata.bandInformation.values(), prefix='BandInformation')

        for form in bandinfo_formset.forms:
            if len(form.initial) > 0:
                form.action = "/hsapi/_internal/%s/bandinformation/%s/update-metadata/" % (content_model.short_id, form.initial['id'])
                form.number = form.initial['id']

        # origina coverage_form
        ori_cov_obj = content_model.metadata.originalCoverage
        ori_coverage_data_dict = {}
        if ori_cov_obj:
            ori_coverage_data_dict['units'] = ori_cov_obj.value['units']
            ori_coverage_data_dict['projection'] = ori_cov_obj.value.get('projection', None)
            ori_coverage_data_dict['northlimit'] = ori_cov_obj.value['northlimit']
            ori_coverage_data_dict['eastlimit'] = ori_cov_obj.value['eastlimit']
            ori_coverage_data_dict['southlimit'] = ori_cov_obj.value['southlimit']
            ori_coverage_data_dict['westlimit'] = ori_cov_obj.value['westlimit']
        else:
            ori_cov_obj = None

        ori_coverage_form = OriginalCoverageSpatialForm(initial=ori_coverage_data_dict,
                                                        res_short_id=content_model.short_id,
                                                        allow_edit=edit_resource,
                                                        element_id=ori_cov_obj.id if ori_cov_obj else None)
        ori_coverage_layout = HTML('<div class="form-group col-lg-6 col-xs-12" id="originalcoverage"> '
                                   '{% load crispy_forms_tags %} '
                                   '{% crispy ori_coverage_form %} '
                                   '</div>')

        # update context
        ext_md_layout = Layout(HTML("<div class='row'>"),
                                ori_coverage_layout,
                                cellinfo_layout,
                                BandInfoLayoutEdit,
                               HTML("</div>")
        )
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=ext_md_layout, request=request)
        context['ori_coverage_form'] = ori_coverage_form
        context['cellinfo_form'] = cellinfo_form
        context['bandinfo_formset'] = bandinfo_formset

    hs_core_context = add_generic_context(request, page)
    context.update(hs_core_context)

    return context
