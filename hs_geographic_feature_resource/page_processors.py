from crispy_forms.layout import Layout, HTML
from django.http import HttpResponseRedirect
from dominate.tags import legend, table, tbody, tr, th, div
from mezzanine.pages.page_processors import processor_for

from hs_core import page_processors
from hs_core.views import add_generic_context
from hs_geographic_feature_resource.forms import OriginalCoverageForm, GeometryInformationForm
from models import GeographicFeatureResource


@processor_for(GeographicFeatureResource)
# when the resource is created this page will be shown
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    if not edit_resource:  # non-edit mode
        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource,
                                                   extended_metadata_layout=None, request=request)
        if isinstance(context, HttpResponseRedirect):
            # sending user to login page
            return context

        extended_metadata_exists = False

        if content_model.metadata.originalcoverage:
            extended_metadata_exists = True

        context['extended_metadata_exists'] = extended_metadata_exists

        # add the original coverage context
        geom_info_for_view = {}
        geom_info = content_model.metadata.geometryinformation
        if geom_info:
            geom_info_for_view['geometryType'] = geom_info.geometryType
            geom_info_for_view['featureCount'] = geom_info.featureCount
            context['geometry_information'] = geom_info_for_view

        ori_cov_dict = {}
        ori_cov_obj = content_model.metadata.originalcoverage
        if ori_cov_obj:
            ori_cov_dict['northlimit'] = ori_cov_obj.northlimit
            ori_cov_dict['eastlimit'] = ori_cov_obj.eastlimit
            ori_cov_dict['southlimit'] = ori_cov_obj.southlimit
            ori_cov_dict['westlimit'] = ori_cov_obj.westlimit
            ori_cov_dict['projection_string'] = ori_cov_obj.projection_string
            ori_cov_dict['projection_name'] = ori_cov_obj.projection_name
            ori_cov_dict['datum'] = ori_cov_obj.datum
            ori_cov_dict['unit'] = ori_cov_obj.unit
            context['original_coverage'] = ori_cov_dict

        field_info_list = content_model.metadata.fieldinformations.all()
        field_info_list_context = []
        for field_info in field_info_list:
            field_info_dict_item = {}
            field_info_dict_item["fieldName"] = field_info.fieldName
            field_info_dict_item["fieldType"] = field_info.fieldType
            field_info_dict_item["fieldTypeCode"] = field_info.fieldTypeCode
            field_info_dict_item["fieldWidth"] = field_info.fieldWidth
            field_info_dict_item["fieldPrecision"] = field_info.fieldPrecision
            field_info_list_context.append(field_info_dict_item)
        context['field_information'] = field_info_list_context

    else:  # editing mode
        # now editing is allowed for resource specific metadata
        geom_info_for_view = {}
        geom_info = content_model.metadata.geometryinformation
        if geom_info:
            geom_info_for_view['geometryType'] = geom_info.geometryType
            geom_info_for_view['featureCount'] = geom_info.featureCount

        geom_information_form = GeometryInformationForm(initial=geom_info_for_view,
                                                        res_short_id=content_model.short_id,
                                                        allow_edit=False,
                                                        element_id=geom_info.id
                                                        if geom_info else None)

        geom_information_layout = HTML('<div class="form-group col-lg-6 col-xs-12" '
                                       'id="geometryinformation">'
                                       '{% load crispy_forms_tags %}'
                                       '{% crispy geom_information_form %}'
                                       '</div>')

        # origina coverage_form
        ori_cov_obj = content_model.metadata.originalcoverage
        ori_coverage_data_dict = {}
        if ori_cov_obj:
            ori_coverage_data_dict['projection_string'] = ori_cov_obj.projection_string
            ori_coverage_data_dict['projection_name'] = ori_cov_obj.projection_name
            ori_coverage_data_dict['datum'] = ori_cov_obj.datum
            ori_coverage_data_dict['unit'] = ori_cov_obj.unit
            ori_coverage_data_dict['northlimit'] = ori_cov_obj.northlimit
            ori_coverage_data_dict['eastlimit'] = ori_cov_obj.eastlimit
            ori_coverage_data_dict['southlimit'] = ori_cov_obj.southlimit
            ori_coverage_data_dict['westlimit'] = ori_cov_obj.westlimit

        ori_coverage_form = OriginalCoverageForm(initial=ori_coverage_data_dict,
                                                 res_short_id=content_model.short_id,
                                                 allow_edit=False,
                                                 element_id=ori_cov_obj.id
                                                 if ori_cov_obj else None)
        ori_coverage_layout = HTML('<div class="form-group col-lg-6 '
                                   'col-xs-12" id="originalcoverage"> '
                                   '{% load crispy_forms_tags %} '
                                   '{% crispy ori_coverage_form %} '
                                   '</div>')
        root_div = div(cls="col-md-12 col-sm-12 pull-left", style="margin-bottom:40px;")
        with root_div:
            legend('Field Information')
            with table(style="width: 100%;"):
                with tbody():
                    with tr(cls='row'):
                        th('Name')
                        th('Type')
                        th('Width')
                        th('Precision')

                    for field_info in content_model.metadata.fieldinformations.all():
                        field_info.get_html(pretty=False)

        ext_md_layout = Layout(geom_information_layout,
                               ori_coverage_layout,
                               HTML(root_div.render()))

        context = page_processors.get_page_context(page,
                                                   request.user,
                                                   resource_edit=edit_resource,
                                                   extended_metadata_layout=ext_md_layout,
                                                   request=request)
        context['ori_coverage_form'] = ori_coverage_form
        context['geom_information_form'] = geom_information_form

    context['edit_mode'] = edit_resource
    hs_core_context = add_generic_context(request, page)
    context.update(hs_core_context)

    return context
