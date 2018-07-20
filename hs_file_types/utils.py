import json
import os
from dateutil import parser
from operator import lt, gt
from hs_core.hydroshare import utils

from .models import GeoRasterLogicalFile, NetCDFLogicalFile, GeoFeatureLogicalFile, \
    RefTimeseriesLogicalFile, TimeSeriesLogicalFile, GenericLogicalFile

from hs_file_types.models.base import AbstractLogicalFile
from django.apps import apps


def get_SupportedAggTypes_choices():
    """
    This function harvests all existing aggregation types in system,
    and puts them in a list:
    [
        ["AGGREGATION_CLASS_NAME_1", "AGGREGATION_VERBOSE_NAME_1"],
        ["AGGREGATION_CLASS_NAME_2", "AGGREGATION_VERBOSE_NAME_2"],
        ...
        ["AGGREGATION_CLASS_NAME_N", "AGGREGATION_VERBOSE_NAME_N"],
    ]
    """

    result_list = []
    agg_types_list = get_aggregation_types()
    for r_type in agg_types_list:
        class_name = r_type.__name__
        verbose_name = r_type.get_aggregation_display_name()
        result_list.append([class_name, verbose_name])
    return result_list


def get_aggregation_types():
    aggregation_types = []
    for model in apps.get_models():
        if issubclass(model, AbstractLogicalFile):
            if not getattr(model, 'archived_model', False):
                aggregation_types.append(model)
    return aggregation_types


def update_resource_coverage_element(resource):
    """Update resource spatial and temporal coverage based on the corresponding coverages
    from all the contained aggregations (logical file) only if the resource coverage is not
    already set"""

    # update resource spatial coverage only if it is empty
    if resource.metadata.spatial_coverage is None:
        update_resource_spatial_coverage(resource)

    # update resource temporal coverage only if it empty
    if resource.metadata.temporal_coverage is None:
        update_resource_temporal_coverage(resource)


def update_resource_spatial_coverage(resource):
    """Updates resource spatial coverage based on the contained spatial coverages of
    aggregations (file type). Note: This action will overwrite any existing resource spatial
    coverage data.
    :param  resource: an instance of composite resource
    """
    spatial_coverages = [lf.metadata.spatial_coverage for lf in resource.logical_files
                         if lf.metadata.spatial_coverage is not None]

    bbox_limits = {'box': {'northlimit': 'northlimit', 'southlimit': 'southlimit',
                           'eastlimit': 'eastlimit', 'westlimit': 'westlimit'},
                   'point': {'northlimit': 'north', 'southlimit': 'north',
                             'eastlimit': 'east', 'westlimit': 'east'}
                   }

    def set_coverage_data(res_coverage_value, lfo_coverage_element, box_limits):
        comparison_operator = {'northlimit': lt, 'southlimit': gt, 'eastlimit': lt,
                               'westlimit': gt}
        for key in comparison_operator.keys():
            if comparison_operator[key](res_coverage_value[key],
                                        lfo_coverage_element.value[box_limits[key]]):
                res_coverage_value[key] = lfo_coverage_element.value[box_limits[key]]

    cov_type = "point"
    bbox_value = {'northlimit': -90, 'southlimit': 90, 'eastlimit': -180, 'westlimit': 180,
                  'projection': 'WGS 84 EPSG:4326', 'units': "Decimal degrees"}

    if len(spatial_coverages) > 1:
        # check if one of the coverage is of type box
        if any(sp_cov.type == 'box' for sp_cov in spatial_coverages):
            cov_type = 'box'
        else:
            # check if the coverages represent different locations
            unique_lats = set([sp_cov.value['north'] for sp_cov in spatial_coverages])
            unique_lons = set([sp_cov.value['east'] for sp_cov in spatial_coverages])
            if len(unique_lats) == 1 and len(unique_lons) == 1:
                cov_type = 'point'
            else:
                cov_type = 'box'
        if cov_type == 'point':
            sp_cov = spatial_coverages[0]
            bbox_value = dict()
            bbox_value['projection'] = 'WGS 84 EPSG:4326'
            bbox_value['units'] = 'Decimal degrees'
            bbox_value['north'] = sp_cov.value['north']
            bbox_value['east'] = sp_cov.value['east']
        else:
            for sp_cov in spatial_coverages:
                if sp_cov.type == "box":
                    box_limits = bbox_limits['box']
                    set_coverage_data(bbox_value, sp_cov, box_limits)
                else:
                    # point type coverage
                    box_limits = bbox_limits['point']
                    set_coverage_data(bbox_value, sp_cov, box_limits)

    elif len(spatial_coverages) == 1:
        sp_cov = spatial_coverages[0]
        if sp_cov.type == "box":
            cov_type = 'box'
            bbox_value['projection'] = 'WGS 84 EPSG:4326'
            bbox_value['units'] = 'Decimal degrees'
            bbox_value['northlimit'] = sp_cov.value['northlimit']
            bbox_value['eastlimit'] = sp_cov.value['eastlimit']
            bbox_value['southlimit'] = sp_cov.value['southlimit']
            bbox_value['westlimit'] = sp_cov.value['westlimit']
        else:
            # point type coverage
            cov_type = "point"
            bbox_value = dict()
            bbox_value['projection'] = 'WGS 84 EPSG:4326'
            bbox_value['units'] = 'Decimal degrees'
            bbox_value['north'] = sp_cov.value['north']
            bbox_value['east'] = sp_cov.value['east']

    spatial_cov = resource.metadata.spatial_coverage
    if len(spatial_coverages) > 0:
        if spatial_cov:
            spatial_cov.type = cov_type
            place_name = spatial_cov.value.get('name', None)
            if place_name is not None:
                bbox_value['name'] = place_name
            spatial_cov._value = json.dumps(bbox_value)
            spatial_cov.save()
        else:
            resource.metadata.create_element("coverage", type=cov_type, value=bbox_value)
    else:
        # delete spatial coverage element for the resource since the content files don't
        # have any spatial coverage
        if spatial_cov:
            spatial_cov.delete()


def update_resource_temporal_coverage(resource):
    """Updates resource temporal coverage based on the contained temporal coverages of
    aggregations (file type). Note: This action will overwrite any existing resource temporal
    coverage data.
    :param  resource: an instance of composite resource
    """

    temporal_coverages = [lf.metadata.temporal_coverage for lf in resource.logical_files
                          if lf.metadata.temporal_coverage is not None]

    date_data = {'start': None, 'end': None}

    def set_date_value(date_data, coverage_element, key):
        comparison_operator = gt if key == 'start' else lt
        if date_data[key] is None:
            date_data[key] = coverage_element.value[key]
        else:
            if comparison_operator(parser.parse(date_data[key]),
                                   parser.parse(coverage_element.value[key])):
                date_data[key] = coverage_element.value[key]

    for temp_cov in temporal_coverages:
        start_date = parser.parse(temp_cov.value['start'])
        end_date = parser.parse(temp_cov.value['end'])
        temp_cov.value['start'] = start_date.strftime('%m/%d/%Y')
        temp_cov.value['end'] = end_date.strftime('%m/%d/%Y')
        set_date_value(date_data, temp_cov, 'start')
        set_date_value(date_data, temp_cov, 'end')

    temp_cov = resource.metadata.temporal_coverage
    if date_data['start'] is not None and date_data['end'] is not None:
        if temp_cov:
            temp_cov._value = json.dumps(date_data)
            temp_cov.save()
        else:
            resource.metadata.create_element("coverage", type='period', value=date_data)
    elif temp_cov:
        # delete the temporal coverage for the resource since the content files don't have
        # temporal coverage
        temp_cov.delete()


def set_logical_file_type(res, user, file_id, hs_file_type=None, folder_path=None,
                          fail_feedback=True):
    if hs_file_type is None:
        res_file = utils.get_resource_file_by_id(res, file_id)
        ext_to_type = {".tif": "GeoRaster", ".tiff": "GeoRaster", ".vrt": "GeoRaster",
                       ".nc": "NetCDF", ".shp": "GeoFeature", ".json": "RefTimeseries",
                       ".sqlite": "TimeSeries", ".csv": "TimeSeries"}
        file_name = str(res_file)
        root, ext = os.path.splitext(file_name)
        ext = ext.lower()
        if ext in ext_to_type:
            # Check for special case of RefTimeseries having 2 extensions
            if ext == ".json":
                if not file_name.lower().endswith(".refts.json"):
                    if fail_feedback:
                        raise ValueError("Unsupported aggregation extension. Supported aggregation "
                                         "extensions are: {}".format(ext_to_type.keys()))
            hs_file_type = ext_to_type[ext]
        else:
            if fail_feedback:
                raise ValueError("Unsupported aggregation extension. Supported aggregation "
                                 "extensions are: {}".format(ext_to_type.keys()))
            return

    file_type_map = {"SingleFile": GenericLogicalFile,
                     "GeoRaster": GeoRasterLogicalFile,
                     "NetCDF": NetCDFLogicalFile,
                     'GeoFeature': GeoFeatureLogicalFile,
                     'RefTimeseries': RefTimeseriesLogicalFile,
                     'TimeSeries': TimeSeriesLogicalFile}
    if hs_file_type not in file_type_map:
        if fail_feedback:
            raise ValueError("Unsupported aggregation type. Supported aggregation types are: {"
                             "}".format(ext_to_type.keys()))
        return
    logical_file_type_class = file_type_map[hs_file_type]
    try:
        logical_file_type_class.set_file_type(resource=res, user=user, file_id=file_id,
                                              folder_path=folder_path)
    except:
        if fail_feedback:
            raise
