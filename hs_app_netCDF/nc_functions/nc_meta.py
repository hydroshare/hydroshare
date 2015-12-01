"""
Module extracts metadata from NetCDF file to complete the required HydroShare NetCDF Science Metadata

References
reprojection
    http://gis.stackexchange.com/questions/78838/how-to-convert-projected-coordinates-to-lat-lon-using-python
datatype
    http://docs.scipy.org/doc/numpy/reference/arrays.dtypes.html
    http://docs.scipy.org/doc/numpy/user/basics.types.html
    http://www.unidata.ucar.edu/software/netcdf/docs/enhanced_model.html
coverage info by acdd:
    http://wiki.esipfed.org/index.php/Attribute_Convention_for_Data_Discovery

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

    dublin_core_meta = get_dublin_core_meta(nc_dataset)
    type_specific_meta = get_type_specific_meta(nc_dataset)
    nc_meta_dict = {'dublin_core_meta': dublin_core_meta, 'type_specific_meta': type_specific_meta}
    nc_dataset.close()

    return nc_meta_dict


# Functions for dublin  core meta #####################################################################################
def get_dublin_core_meta(nc_dataset):
    """
    (object)-> dict

    Return: the netCDF dublin core metadata
    """

    nc_global_meta = extract_nc_global_meta(nc_dataset)

    try:
        nc_coverage_meta = extract_nc_coverage_meta(nc_dataset)
    except:
        nc_coverage_meta = {}

    dublin_core_meta = dict(nc_global_meta.items() + nc_coverage_meta.items())

    return dublin_core_meta


def extract_nc_global_meta(nc_dataset):
    """
    (object)->dict

    Return netCDF global attributes info which correspond to dublincore meta attributes
    """

    nc_global_meta = {}

    dublincore_vs_convention = {
        'creator_name': ['creator_name'],
        'creator_email': ['creator_email'],
        'creator_uri': ['creator_uri'],
        'contributor_name': ['contributor_name'],
        'convention': ['Conventions'],
        'title': ['title'],
        'subject': ['keywords'],
        'description': ['summary', 'comment'],
        'rights': ['license'],
        'references': ['references'],
        'source': ['source']

    }  # key is the dublincore attributes, value is corresponding attributes from ACDD and CF convention

    for dublincore, convention in dublincore_vs_convention.items():
        for option in convention:
            if hasattr(nc_dataset, option) and nc_dataset.__dict__[option]:
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

    projection_info = get_projection_info(nc_dataset)

    period_info = get_period_info(nc_dataset)

    original_box_info = get_original_box_info(nc_dataset)
    for name in original_box_info.keys():
        original_box_info[name] = str(original_box_info[name])

    box_info = get_box_info(nc_dataset)
    for name in box_info.keys():
        box_info[name] = str(box_info[name])


    nc_coverage_meta = {
        'projection-info': projection_info,
        'period': period_info,
        'box': box_info,
        'original-box': original_box_info,
    }

    return nc_coverage_meta


def get_projection_info(nc_dataset):
    """
    (object)-> dict

    Return: the netCDF original projection proj4 string
    """
    projection_info = {}
    projection_text = get_nc_grid_mapping_projection_import_string(nc_dataset)
    if projection_text:
        projection_info['type'] = 'Proj4 String'
        projection_info['text'] = projection_text

    return projection_info


def get_period_info(nc_dataset):
    """
    (object)-> dict

    Return: the netCDF original coverage period info
    """

    if get_period_info_by_acdd_convention(nc_dataset):
        period_info = get_period_info_by_acdd_convention(nc_dataset)
    else:
        period_info = get_period_info_by_data(nc_dataset)

    return period_info


def get_period_info_by_acdd_convention(nc_dataset):
    """
    (object)-> dict

    Return: the netCDF original coverage period info by looking for the ACDD convention terms
    """

    period_info = {}

    if nc_dataset.__dict__.get('time_coverage_start', '') and nc_dataset.__dict__.get('time_coverage_end', ''):
        period_info['start'] = str(nc_dataset.__dict__['time_coverage_start'])
        period_info['end'] = str(nc_dataset.__dict__['time_coverage_end'])

    return period_info


def get_period_info_by_data(nc_dataset):
    """
    (object)-> dict

    Return: the netCDF original coverage period info by looking into the data
    """

    period_info = {}
    coor_type_mapping = get_nc_variables_coordinate_type_mapping(nc_dataset)
    for coor_type in ['TA', 'TC']:
        limit_meta = get_limit_meta_by_coor_type(nc_dataset, coor_type, coor_type_mapping)
        try:
            if limit_meta:
                if limit_meta['start'].year and limit_meta['end'].year:
                    period_info['start'] = limit_meta['start'].strftime('%Y-%m-%d %H:%M:%S')
                    period_info['end'] = limit_meta['end'].strftime('%Y-%m-%d %H:%M:%S')
                    break
        except:
            continue

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
            # check if the westlimit and eastlimit are in -180-180
            westlimit = float(box_info['westlimit'])
            eastlimit = float(box_info['eastlimit'])
            box_info['westlimit'] = check_lon_limit(westlimit, eastlimit)[0]
            box_info['eastlimit'] = check_lon_limit(westlimit, eastlimit)[1]

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
        # change the value as string
        for name in box_info.keys():
            box_info[name] = str(box_info[name])
        box_info['units'] = 'Decimal degrees'
        box_info['projection'] = 'WGS 84 EPSG:4326'

    return box_info


def check_lon_limit(westlimit, eastlimit):
    """
    (num, num)-> [num,num]

    Return: given the original westlimit and eastlimit values in degree units, convert them in -180-180 range and
            make sure eastlimit > westlimit
    """

    # chech if limit is in range of -180-180
    if westlimit > 180:
        westlimit -=360
    if eastlimit > 180:
        eastlimit -=360

    # check if westlimit < eastlimit
    if westlimit == eastlimit:
        westlimit = -180
        eastlimit = 180
    elif westlimit > eastlimit:
        if (180 - westlimit) >= (eastlimit+180):
            eastlimit = 180
        else:
            westlimit = -180

    return [westlimit, eastlimit]


def get_original_box_info(nc_dataset):
    """
    (object)-> dict

    Return: the netCDF original coverage box info
    """
    original_box_info = {}

    if get_original_box_info_by_acdd_convention(nc_dataset):
        original_box_info = get_original_box_info_by_acdd_convention(nc_dataset)
    else:
        original_box_info = get_original_box_info_by_data(nc_dataset)

    return original_box_info


def get_original_box_info_by_acdd_convention(nc_dataset):
    """
    (object)-> dict

    Return: the netCDF original coverage box info by looking for acdd convention terms
    """

    original_box_info = {}
    if nc_dataset.__dict__.get('geospatial_lat_min', '') and nc_dataset.__dict__.get('geospatial_lat_max', '')\
            and nc_dataset.__dict__.get('geospatial_lon_min', '') and nc_dataset.__dict__.get('geospatial_lon_max', ''):
        original_box_info['southlimit'] = str(nc_dataset.__dict__['geospatial_lat_min'])
        original_box_info['northlimit'] = str(nc_dataset.__dict__['geospatial_lat_max'])
        original_box_info['westlimit'] = str(nc_dataset.__dict__['geospatial_lon_min'])
        original_box_info['eastlimit'] = str(nc_dataset.__dict__['geospatial_lon_max'])
        original_box_info['units'] = 'degree'
    # TODO: check the geospatial_bounds and geospatial_bounds_crs attributes

    return original_box_info


def get_original_box_info_by_data(nc_dataset):
    """
    (object)-> dict

    Return: the netCDF original coverage box info by looking into the data
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

    nc_data_variables = nc_dataset.variables #get_nc_data_variables(nc_dataset)
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
            'unit': var_obj.units if (hasattr(var_obj, 'units') and var_obj.units) else 'Unknown',
            'shape': ','.join(var_obj.dimensions) if var_obj.dimensions else 'Not defined',
            'descriptive_name': var_obj.long_name if hasattr(var_obj, 'long_name') else '',
            'missing_value': str(var_obj.missing_value if hasattr(var_obj, 'missing_value') else ''),
            'method': str(var_obj.comment if hasattr(var_obj, 'comment') else ''),
        }

        # check and add variable 'type' info:
        nc_data_type_dict = {
            'int8': 'Byte',
            'int16': 'Short',
            'int32': 'Int',
            'int64': 'Int64',
            'float32': 'Float',
            'float64': 'Double',
            'uint8': 'Unsigned Byte',
            'uint16': 'Unsigned Short',
            'uint32': 'Unsigned Int',
            'uint64': 'Unsigned Int64',
        }

        if var_obj.dimensions:
            try:
                if isinstance(var_obj.datatype, netCDF4.CompoundType) or isinstance(var_obj.datatype, netCDF4.VLType):
                    nc_data_variables_meta[var_name]['type'] = 'User Defined Type'
                elif var_obj.datatype.name in nc_data_type_dict.keys():
                    nc_data_variables_meta[var_name]['type'] = nc_data_type_dict[var_obj.datatype.name]
                elif ('string' in var_obj.datatype.name) or ('unicode' in var_obj.datatype.name):
                    nc_data_variables_meta[var_name]['type'] = 'Char' if '8' in var_obj.datatype.name else 'String'
                else:
                    nc_data_variables_meta[var_name]['type'] = 'Unknown'
            except:
                nc_data_variables_meta[var_name]['type'] = 'Unknown'
        else:
            nc_data_variables_meta[var_name]['type'] = 'Unknown'


    return nc_data_variables_meta



