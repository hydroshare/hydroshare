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

    try:
        dublin_core_meta = get_dublin_core_meta(nc_dataset)
    except:
        dublin_core_meta = {}

    try:
        type_specific_meta = get_type_specific_meta(nc_dataset)
    except:
        type_specific_meta = {}

    nc_meta_dict = {'dublin_core_meta': dublin_core_meta, 'type_specific_meta': type_specific_meta}
    nc_dataset.close()

    return nc_meta_dict


# def get_nc_meta_dict(nc_file_name):
#     """
#     (string)-> dict
#
#     Return: the netCDF Dublincore and Type specific Metadata
#     """
#
#     if isinstance(nc_file_name, netCDF4.Dataset):
#         nc_dataset = nc_file_name
#     else:
#         nc_dataset = get_nc_dataset(nc_file_name)
#
#     dublin_core_meta = get_dublin_core_meta(nc_dataset)
#     type_specific_meta = get_type_specific_meta(nc_dataset)
#     nc_meta_dict = {'dublin_core_meta': dublin_core_meta, 'type_specific_meta': type_specific_meta}
#     nc_dataset.close()
#
#     return nc_meta_dict


## Functions for dublin  core meta #####################################################################################
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
    box_info = get_box_info(nc_dataset)

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

    period_info = {}
    coor_type_mapping = get_nc_variables_coordinate_type_mapping(nc_dataset)
    for coor_type in ['TA', 'TC']:
        limit_meta = get_limit_meta_by_coor_type(nc_dataset, coor_type, coor_type_mapping)
        if limit_meta:
            period_info['start'] = limit_meta['start']
            period_info['end'] = limit_meta['end']
            break

    return period_info


def get_box_info(nc_dataset):
    """
    (object)-> dict

    Return: the netCDF coverage box info as wgs84 crs
    """
    box_info = {}
    original_box_info = get_original_box_info(nc_dataset)

    if original_box_info:
        if original_box_info.get('units', '') == 'degree':  # geographic coor x, y
            box_info = original_box_info
        elif original_box_info.get('projection', ''):  # projection coor x, y
            projection_import_string = get_nc_grid_mapping_projection_import_string(nc_dataset)
            if projection_import_string:
                try:
                    ori_proj = Proj(projection_import_string)
                    wgs84_proj = Proj(init='epsg:4326')
                    box_info['westlimit'], box_info['northlimit'] = transform(ori_proj, wgs84_proj,
                                                                              original_box_info['westlimit'],
                                                                              original_box_info['northlimit'])
                    box_info['eastlimit'], box_info['southlimit'] = transform(ori_proj, wgs84_proj,
                                                                              original_box_info['eastlimit'],
                                                                              original_box_info['southlimit'])
                except:
                    pass

    if box_info:
        box_info['units'] = 'Decimal degrees'
        box_info['projection'] = 'WGS 84 EPSG:4326'

    return box_info


def get_original_box_info(nc_dataset):
    """
    (object)-> dict

    Return: the netCDF original coverage box info
    """

    original_box_info = {}

    for info_source in ['A', 'C']:  # check auxiliary and coordinate variables
        limits_info = get_limits_info(nc_dataset, info_source)
        if limits_info:
            original_box_info = limits_info
            original_box_info['projection'] = get_nc_grid_mapping_projection_name(nc_dataset)
            break

    return original_box_info


def get_limits_info(nc_dataset, info_source):
    """
    (obj, str) -> dict

    Return: dictionary including the 4 box limits name and their values and the units
    """

    limits_info = {}
    coor_type_mapping = get_nc_variables_coordinate_type_mapping(nc_dataset)

    # get all limits values and units
    for coor_dir in ['X', 'Y']:
        coor_type = coor_dir + info_source
        limit_meta = get_limit_meta_by_coor_type(nc_dataset, coor_type, coor_type_mapping)
        if limit_meta:
            limits_info = dict(limits_info.items()+limit_meta.items())
        else:
            limits_info = {}
            break

    # refine X value when longitude is larger than 180
    if limits_info.get('units', '') == 'degree':
        westlimit = limits_info['westlimit']
        eastlimit = limits_info['eastlimit']
        if westlimit > 180 or eastlimit > 180:
            if eastlimit - westlimit == 360:
                westlimit = -180
                eastlimit = 180
            else:
                if westlimit >= 180:
                    westlimit -= 360
                    eastlimit -= 360
                else:
                    if (180 - westlimit) >= (eastlimit-180):
                        eastlimit = 180
                    else:
                        westlimit = -180
                        eastlimit -= 360
        limits_info['westlimit'] = westlimit
        limits_info['eastlimit'] = eastlimit

    # change the value as string
    if limits_info:
        for name, value in limits_info.items():
            limits_info[name] = str(value)

    return limits_info


def get_limit_meta_by_coor_type(nc_dataset, coor_type, coor_type_mapping):
    """
    (obj, str, dict) -> dict

    Return: based on the coordinate type (XA,YA,XC,YC,TA,TC) return the limits start and end values and units
    """

    limit_meta = {}
    coor_start = []
    coor_end = []
    coor_units = ''

    var_name_list = coor_type_mapping.keys()
    coor_type_list = coor_type_mapping.values()

    for coor_type_name in [coor_type, coor_type+'_bnd']:
        if coor_type_name in coor_type_list:
            index = coor_type_list.index(coor_type_name)
            var_name = var_name_list[index]
            var_coor_meta = get_nc_variable_coordinate_meta(nc_dataset, var_name)

            if var_coor_meta.get('coordinate_start') is not None:
                coor_start.append(var_coor_meta.get('coordinate_start'))
            if var_coor_meta.get('coordinate_end') is not None:
                coor_end.append(var_coor_meta.get('coordinate_end'))
            if coor_units == '':
                coor_units = var_coor_meta.get('coordinate_units', '')
                if re.match('degree', coor_units, re.I):
                    coor_units = 'degree'

    if coor_start and coor_end:
        coor_min = min(coor_start)
        coor_max = max(coor_end)
        if "X" in coor_type:
            limit_meta = {
                'westlimit': coor_min,
                'eastlimit': coor_max,
            }
        elif "Y" in coor_type:
            limit_meta = {
                'southlimit': coor_min,
                'northlimit': coor_max
            }
        if "T" in coor_type:
            limit_meta = {
                'start': coor_min,
                'end': coor_max
            }

        if coor_units:
            limit_meta['units'] = coor_units
    else:
        limit_meta = {}

    return limit_meta


# Functions for type specific meta ##################################################################################
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
        nc_type_dict = {
            'S1': 'Char',
            'int8': 'Byte',
            'int16': 'Short',
            'int32': 'Int',
            'float32': 'Float',
            'float64': 'Double'
        }

        nc_type_original_name = nc_data_variables_meta[var_name]['type']
        if nc_type_original_name in nc_type_dict.keys():
            nc_data_variables_meta[var_name]['type'] = nc_type_dict[nc_type_original_name]
        else:
            nc_data_variables_meta[var_name]['type'] = 'unknown'

    return nc_data_variables_meta



