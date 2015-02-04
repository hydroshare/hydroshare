"""
Module extracts metadata from NetCDF file to complete the required HydroShare NetCDF Science Metadata

Reference code：
reprojection:
http://gis.stackexchange.com/questions/78838/how-to-convert-projected-coordinates-to-lat-lon-using-python

"""
__author__ = 'Tian Gan'

from nc_utils import *
import json
import netCDF4
from pyproj import Proj, transform
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
        'creator_name': ['creator_name', 'creator_institution'],
        'creator_email': ['creator_email'],
        'creator_uri': ['creator_uri'],
        'contributor_name': ['contributor_name'],
        #'convention': ['Conventions'],
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

    nc_coverage_meta = {
        'period': {},
        'box': {},
        'original-box': {}
    }
    nc_coordinate_variables_detail = get_nc_coordinate_variables_detail(nc_dataset)

    # get the info of 'period' and 'original-box'
    for var_name, var_detail in nc_coordinate_variables_detail.items():
        coor_type = var_detail['coordinate_type']
        if coor_type == 'T':
            nc_coverage_meta['period'] = {
                'start': var_detail['coordinate_start'],
                'end': var_detail['coordinate_end'],
                #'units': var_detail['coordinate_units']
            }
        elif coor_type == 'X':
            nc_coverage_meta['original-box']['westlimit'] = var_detail['coordinate_start']
            nc_coverage_meta['original-box']['eastlimit'] = var_detail['coordinate_end']
            nc_coverage_meta['original-box']['units'] = var_detail['coordinate_units']

        elif coor_type == 'Y':
            nc_coverage_meta['original-box']['southlimit'] = var_detail['coordinate_start']
            nc_coverage_meta['original-box']['northlimit'] = var_detail['coordinate_end']
            nc_coverage_meta['original-box']['units'] = var_detail['coordinate_units']

    if ('units' in nc_coverage_meta['original-box']) and (re.match('degree', nc_coverage_meta['original-box']['units'], re.I)):
        nc_coverage_meta['original-box']['units'] = 'degree'

    nc_coverage_meta['original-box']['projection'] = get_nc_grid_mapping_projection_name(nc_dataset)
    ## ToDo consider the boundary variable info for spatial meta!

    # get the info of the 'box' as wgs84 web mercator
    if set(['northlimit','westlimit','southlimit','eastlimit']).issubset(nc_coverage_meta['original-box'].keys()):
        if nc_coverage_meta['original-box']['projection'] != 'Unknown':
                pass
        elif nc_coverage_meta['original-box'].get('units', None) == 'degree':
            ori_proj = Proj(init='epsg:4326')  # suppose the ggeographic cs is wgs84 refer to how arcgis is doing
            wgs84_proj = Proj(init='epsg:3875')

            westlimit,northlimit = transform(ori_proj,wgs84_proj,
                                              nc_coverage_meta['original-box']['westlimit'],
                                              nc_coverage_meta['original-box']['northlimit'])

            eastlimit,southlimit = transform(ori_proj,wgs84_proj,
                                              nc_coverage_meta['original-box']['eastlimit'],
                                              nc_coverage_meta['original-box']['southlimit'])

            nc_coverage_meta['box']['southlimit'] = southlimit
            nc_coverage_meta['box']['northlimit'] = northlimit
            nc_coverage_meta['box']['eastlimit'] = eastlimit
            nc_coverage_meta['box']['westlimit'] = westlimit

    return nc_coverage_meta


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



