# coding=utf-8
from mezzanine.pages.page_processors import processor_for

from hs_core import page_processors
from hs_core.views import add_generic_context

from .models import CompositeResource


@processor_for(CompositeResource)
def landing_page(request, page):
    """
        A typical Mezzanine page processor.

    """
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)
    context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource,
                                               extended_metadata_layout=None, request=request)
    extended_metadata_exists = False
    if not edit_resource:
        # check the file metadata
        # TODO: retrieve metadata based on per logical_file in the resource
        res_file = content_model.files.all().first()
        if res_file is not None:
            if res_file.logical_file is not None and \
                            res_file.logical_file_type_name == "GeoRasterLogicalFile":
                if res_file.logical_file.has_metadata:
                    ori_coverage_data_dict = dict()
                    ori_coverage_data_dict['units'] = res_file.metadata.originalCoverage.value[
                        'units']
                    ori_coverage_data_dict[
                        'projection'] = res_file.metadata.originalCoverage.value.get(
                        'projection', None)
                    ori_coverage_data_dict['northlimit'] = \
                    res_file.metadata.originalCoverage.value['northlimit']
                    ori_coverage_data_dict['eastlimit'] = \
                    res_file.metadata.originalCoverage.value['eastlimit']
                    ori_coverage_data_dict['southlimit'] = \
                    res_file.metadata.originalCoverage.value['southlimit']
                    ori_coverage_data_dict['westlimit'] = \
                    res_file.metadata.originalCoverage.value['westlimit']
                    context['originalCoverage'] = ori_coverage_data_dict
                    context['cellInformation'] = res_file.metadata.cellInformation
                    context['bandInformation'] = res_file.metadata.bandInformation

    hs_core_context = add_generic_context(request, page)
    context.update(hs_core_context)

    return context
