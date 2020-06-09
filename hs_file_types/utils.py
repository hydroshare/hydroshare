import json
import os
from dateutil import parser
from operator import lt, gt
from hs_core.hydroshare import utils

from .models import GeoRasterLogicalFile, NetCDFLogicalFile, GeoFeatureLogicalFile, \
    RefTimeseriesLogicalFile, TimeSeriesLogicalFile, GenericLogicalFile, FileSetLogicalFile

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


def update_target_spatial_coverage(target):
    """Updates target spatial coverage based on the contained spatial coverages of
    aggregations (file type). Note: This action will overwrite any existing target spatial
    coverage data.

    :param  target: an instance of CompositeResource or FileSetLogicalFile
    """

    if isinstance(target, FileSetLogicalFile):
        spatial_coverages = [lf.metadata.spatial_coverage for lf in target.get_children()
                             if lf.metadata.spatial_coverage is not None]
    else:
        spatial_coverages = [lf.metadata.spatial_coverage for lf in target.logical_files
                             if lf.metadata.spatial_coverage is not None and not lf.has_parent]

    if not spatial_coverages:
        # no aggregation level spatial coverage data exist - no need to update resource
        # spatial coverage
        return

    bbox_limits = {'box': {'northlimit': 'northlimit', 'southlimit': 'southlimit',
                           'eastlimit': 'eastlimit', 'westlimit': 'westlimit'},
                   'point': {'northlimit': 'north', 'southlimit': 'north',
                             'eastlimit': 'east', 'westlimit': 'east'}
                   }

    def set_coverage_data(res_coverage_value, lfo_coverage_element, box_limits):
        comparison_operator = {'northlimit': lt, 'southlimit': gt, 'eastlimit': lt,
                               'westlimit': gt}
        for key in list(comparison_operator.keys()):
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

    spatial_cov = target.metadata.spatial_coverage
    if spatial_cov:
        spatial_cov.type = cov_type
        place_name = spatial_cov.value.get('name', None)
        if place_name is not None:
            bbox_value['name'] = place_name
        spatial_cov._value = json.dumps(bbox_value)
        spatial_cov.save()
    else:
        target.metadata.create_element("coverage", type=cov_type, value=bbox_value)


def update_target_temporal_coverage(target):
    """Updates target temporal coverage based on the contained temporal coverages of
    aggregations (file type).
    Note: This action will overwrite any existing target temporal
    coverage data.

    :param  target: an instance of CompositeResource or FileSetLogicalFile
    """
    if isinstance(target, FileSetLogicalFile):
        temporal_coverages = [lf.metadata.temporal_coverage for lf in target.get_children()
                              if lf.metadata.temporal_coverage is not None]
    else:
        temporal_coverages = [lf.metadata.temporal_coverage for lf in target.logical_files
                              if lf.metadata.temporal_coverage is not None and not lf.has_parent]

    if not temporal_coverages:
        # no aggregation level temporal coverage data - no update at resource level is needed
        return

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

    temp_cov = target.metadata.temporal_coverage
    if date_data['start'] is not None and date_data['end'] is not None:
        if temp_cov:
            temp_cov._value = json.dumps(date_data)
            temp_cov.save()
        else:
            target.metadata.create_element("coverage", type='period', value=date_data)


def get_logical_file_type(res, file_id, hs_file_type=None, fail_feedback=True):
    """ Return the logical file type associated with a new file """
    if hs_file_type is None:
        res_file = utils.get_resource_file_by_id(res, file_id)
        ext_to_type = {".tif": "GeoRaster", ".tiff": "GeoRaster", ".vrt": "GeoRaster",
                       ".nc": "NetCDF", ".shp": "GeoFeature", ".json": "RefTimeseries",
                       ".sqlite": "TimeSeries"}
        file_name = str(res_file)
        root, ext = os.path.splitext(file_name)
        ext = ext.lower()
        if ext in ext_to_type:
            # Check for special case of RefTimeseries having 2 extensions
            if ext == ".json":
                if not file_name.lower().endswith(".refts.json"):
                    if fail_feedback:
                        raise ValueError("Unsupported aggregation extension. Supported aggregation "
                                         "extensions are: {}".format(list(ext_to_type.keys())))
            hs_file_type = ext_to_type[ext]
        else:
            if fail_feedback:
                raise ValueError("Unsupported aggregation extension. Supported aggregation "
                                 "extensions are: {}".format(list(ext_to_type.keys())))
            return None

    file_type_map = {"SingleFile": GenericLogicalFile,
                     "FileSet": FileSetLogicalFile,
                     "GeoRaster": GeoRasterLogicalFile,
                     "NetCDF": NetCDFLogicalFile,
                     'GeoFeature': GeoFeatureLogicalFile,
                     'RefTimeseries': RefTimeseriesLogicalFile,
                     'TimeSeries': TimeSeriesLogicalFile}
    if hs_file_type not in file_type_map:
        if fail_feedback:
            raise ValueError("Unsupported aggregation type. Supported aggregation types are: {"
                             "}".format(list(ext_to_type.keys())))
        return None
    logical_file_type_class = file_type_map[hs_file_type]
    return logical_file_type_class


def set_logical_file_type(res, user, file_id, hs_file_type=None, folder_path='', extra_data={},
                          fail_feedback=True):
    """ set the logical file type for a new file """
    logical_file_type_class = get_logical_file_type(res, file_id, hs_file_type, fail_feedback)

    try:
        # Some aggregations use the folder name for the aggregation name
        folder_path = folder_path.rstrip('/') if folder_path else folder_path
        if extra_data:
            logical_file_type_class.set_file_type(resource=res, user=user, file_id=file_id,
                                                  folder_path=folder_path, extra_data=extra_data)
        else:
            logical_file_type_class.set_file_type(resource=res, user=user, file_id=file_id,
                                                  folder_path=folder_path)
    except:
        if fail_feedback:
            raise
