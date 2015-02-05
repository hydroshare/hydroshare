"""
Module extracts metadata from NetCDF file to complete the required HydroShare NetCDF Science Metadata

Reference code
reprojection
http://gis.stackexchange.com/questions/78838/how-to-convert-projected-coordinates-to-lat-lon-using-python

"""
__author__ = 'Tian Gan'

from nc_utils import *
import json
import netCDF4
from pyproj import Proj, transform
import numpy
from collections import OrderedDict


def get_nc_meta_json(nc_file_name):
    """
    (string)-> json string

    Return: the netCDF Dublincore and Type specific Metadata
    """

    nc_meta_dict = get_nc_meta_dict(nc_file_name)
    nc_meta_json = json.dumps(nc_meta_dict)
    return nc_meta_json


def get_nc_meta_dict(nc_file_name):
    """
    (string)-> dict

    Return: the netCDF Dublincore and Type specific Metadata
    """

    if isinstance(nc_file_name, netCDF4.Dataset):
        nc_dataset = nc_file_name
    else:
        nc_dataset = get_nc_dataset(nc_file_name)

    dublin_core_meta = get_dublin_core_meta(nc_dataset)
    type_specific_meta = get_type_specific_meta(nc_dataset)
    nc_meta_dict = {'dublin_core_meta': dublin_core_meta, 'type_specific_meta': type_specific_meta}
    nc_dataset.close()

    return nc_meta_dict


def get_dublin_core_meta(nc_dataset):
    """
    (object)-> dict

    Return: the netCDF dublin core metadata
    """

    nc_global_meta = extract_nc_global_meta(nc_dataset)
    nc_coverage_meta = extract_nc_coverage_meta(nc_dataset)
    dublin_core_meta = dict(nc_global_meta.items() + nc_coverage_meta.items())

    return dublin_core_meta


def extract_nc_global_meta(nc_dataset):
    """
    (object)->dict

    Return netCDF global attributes info which correspond to dublincore meta attributes
    """

    nc_global_meta = {}

    dublincore_vs_convention = {
        #'creator_name': ['creator_name', 'creator_institution'],
        #'creator_email': ['creator_email'],
        #'creator_uri': ['creator_uri'],
        #'contributor_name': ['contributor_name'],
        'convention': ['Conventions'],
        'title': ['title'],
        'subject': ['keywords'],
        'description': ['summary', 'comment', ],
        'rights': ['license'],
        'references': ['references'],
        'source': ['source']

    }  # key is the dublincore attributes, value is corresponding attributes from ACDD and CF convention

    for dublincore, convention in dublincore_vs_convention.items():
        for option in convention:
            if hasattr(nc_dataset, option):
                raw_str = nc_dataset.__dict__[option]
                refined_str = raw_str.replace("\\n", '')
                nc_global_meta[dublincore] = ' '.join(refined_str.split())
                break

    return nc_global_meta


def extract_nc_coverage_meta(nc_dataset):
    """
    (object)->dict

    Return netCDF time start and end info
    """
    period_info = get_period_info(nc_dataset)
    original_box_info = get_original_box_info(nc_dataset)
    box_info = get_box_info(nc_dataset, original_box_info)

    nc_coverage_meta = {
        'period': period_info,
        'box': box_info,
        'original-box': original_box_info,
    }
    return nc_coverage_meta


def get_period_info(nc_dataset):
    """
    (object)-> dict

    Return: the netCDF original coverage period info
    """
    nc_coordinate_variables_detail = get_nc_coordinate_variables_detail(nc_dataset)
    period_info = {}
    for var_name, var_detail in nc_coordinate_variables_detail.items():
        coor_type = var_detail['coordinate_type']
        if coor_type == 'T':
            period_info = {
                'start': var_detail['coordinate_start'],
                'end': var_detail['coordinate_end'],
                #'units': var_detail['coordinate_units']
            }
    return period_info


def get_original_box_info(nc_dataset):
    """
    (object)-> dict

    Return: the netCDF original coverage box info
    """

    nc_coordinate_variables_detail = get_nc_coordinate_variables_detail(nc_dataset)
    original_box_info = {}
    for var_name, var_detail in nc_coordinate_variables_detail.items():
        coor_type = var_detail['coordinate_type']
        if coor_type == 'X':
            original_box_info['westlimit'] = min(var_detail['coordinate_start'], var_detail['coordinate_end'])
            original_box_info['eastlimit'] = max(var_detail['coordinate_start'], var_detail['coordinate_end'])
            original_box_info['units'] = var_detail['coordinate_units']
        elif coor_type == 'Y':
            original_box_info['southlimit'] = min(var_detail['coordinate_start'], var_detail['coordinate_end'])
            original_box_info['northlimit'] = max(var_detail['coordinate_start'], var_detail['coordinate_end'])
            original_box_info['units'] = var_detail['coordinate_units']

    if re.match('degree', original_box_info.get('units', ''), re.I):
        original_box_info['units'] = 'degree'

    if original_box_info:
        original_box_info['projection'] = get_nc_grid_mapping_projection_name(nc_dataset)

    return original_box_info


def get_box_info(nc_dataset, original_box_info):
    """
    (object)-> dict

    Return: the netCDF coverage box info as wgs84 crs
    """
    box_info = {}

    # condition 1: check the original-box info
    if original_box_info.get('projection', ''):
        projection_import_string = get_nc_grid_mapping_projection_import_string(nc_dataset)
        if projection_import_string:
            ori_proj = Proj(projection_import_string)
            wgs84_proj = Proj(init='epsg:4326')
            box_info['westlimit'], box_info['northlimit'] = transform(ori_proj, wgs84_proj,
                                                                      original_box_info['westlimit'],
                                                                      original_box_info['northlimit'])
            box_info['eastlimit'], box_info['southlimit'] = transform(ori_proj, wgs84_proj,
                                                                      original_box_info['eastlimit'],
                                                                      original_box_info['southlimit'])
    elif original_box_info.get('units', '') == 'degree':
        box_info['southlimit'] = original_box_info['southlimit']
        box_info['northlimit'] = original_box_info['northlimit']
        box_info['eastlimit'] = original_box_info['eastlimit'] #if original_box_info['eastlimit'] <= 180 else original_box_info['eastlimit']-360
        box_info['westlimit'] = original_box_info['westlimit'] #if original_box_info['westlimit'] <= 180 else original_box_info['westlimit']-360

    # condition 2: check the auxiliary coordinate
    nc_variables = get_nc_auxiliary_coordinate_variables(nc_dataset)
    if (not box_info) and nc_variables:
        for var_name, nc_variable in nc_variables.items():
            var_standard_name = getattr(nc_variable, 'standard_name', getattr(nc_variable, 'long_name', None))
            if var_standard_name:
                if re.match(var_standard_name, 'latitude', re.I):
                    lat_data = nc_variable[:]
                    box_info['southlimit'] = lat_data[numpy.unravel_index(lat_data.argmin(), lat_data.shape)]
                    box_info['northlimit'] = lat_data[numpy.unravel_index(lat_data.argmax(), lat_data.shape)]
                elif re.match(var_standard_name, 'longitude', re.I):
                    lon_data = nc_variable[:]
                    westlimit = lon_data[numpy.unravel_index(lon_data.argmin(), lon_data.shape)]
                    eastlimit = lon_data[numpy.unravel_index(lon_data.argmax(), lon_data.shape)]
                    box_info['westlimit'] = westlimit #if westlimit <= 180 else westlimit-360
                    box_info['eastlimit'] = eastlimit #if eastlimit <= 180 else eastlimit-360

    if box_info:
        box_info['units'] = 'degree'

    return box_info


def get_type_specific_meta(nc_dataset):
    """
    (object)-> dict

    Return: the netCDF type specific metadata
    """

    nc_data_variables = get_nc_data_variables(nc_dataset)
    type_specific_meta = extract_nc_data_variables_meta(nc_data_variables)

    return type_specific_meta


def extract_nc_data_variables_meta(nc_data_variables):
    """
    (dict) -> dict

    Return : the netCDF data variable metadata which are required by HS system.
    """
    nc_data_variables_meta = {}
    for var_name, var_obj in nc_data_variables.items():
        nc_data_variables_meta[var_name] = {
            'name': var_name,
            'unit': var_obj.units if hasattr(var_obj, 'units') else '',
            'shape': ','.join(var_obj.dimensions),
            'type': str(var_obj.dtype),
            'descriptive_name': var_obj.long_name if hasattr(var_obj, 'long_name') else '',
            'missing_value': str(var_obj.missing_value if hasattr(var_obj, 'missing_value') else ''),
        }

        # check type element info:
        nc_type_list = ['S1', 'int8', 'int16', 'int32', 'float32', 'float64']
        if nc_data_variables_meta[var_name]['type'] not in nc_type_list:
            nc_data_variables_meta[var_name]['type'] = 'unknown'

    return nc_data_variables_meta



