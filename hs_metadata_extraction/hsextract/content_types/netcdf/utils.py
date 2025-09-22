"""
Module extracts metadata from NetCDF file to complete the required HydroShare NetCDF
Science Metadata

References
reprojection
    http://gis.stackexchange.com/questions/78838/how-to-convert-projected-coordinates-to-
    lat-lon-using-python
datatype
    http://docs.scipy.org/doc/numpy/reference/arrays.dtypes.html
    http://docs.scipy.org/doc/numpy/user/basics.types.html
    http://www.unidata.ucar.edu/software/netcdf/docs/enhanced_model.html
coverage info by acdd:
    http://wiki.esipfed.org/index.php/Attribute_Convention_for_Data_Discovery

Module provides utility functions to manipulate netCDF dataset.
- classify variable types of coordinate, coordinate bounds, grid mapping, scientific data,
    auxiliary coordinate
- show original metadata of a variable

Reference code
http://netcdf4-python.googlecode.com/svn/trunk/docs/netCDF4-module.html
"""

import json
import re
import tempfile
import os
from collections import OrderedDict

import dateutil.parser
import netCDF4
import numpy
from osgeo import osr
from pyproj import Transformer
from hsextract import s3_client as s3


def get_nc_meta_json(nc_file_name):
    """
    (string)-> json string

    Return: the netCDF Dublincore and Type specific Metadata
    """

    nc_meta_dict = get_nc_meta_dict(nc_file_name)
    nc_meta_json = json.dumps(nc_meta_dict, indent=2)
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

    res_dublin_core_meta = get_dublin_core_meta(nc_dataset)
    res_type_specific_meta = get_type_specific_meta(nc_dataset)
    nc_dataset.close()

    md = combine_metadata(res_dublin_core_meta, res_type_specific_meta)

    md["content_files"] = [nc_file_name]
    return md


# Functions for dublin core meta
def get_dublin_core_meta(nc_dataset):
    """
    (object)-> dict

    Return: the netCDF dublin core metadata
    """

    nc_global_meta = extract_nc_global_meta(nc_dataset)

    try:
        nc_coverage_meta = extract_nc_coverage_meta(nc_dataset)
    except Exception:
        nc_coverage_meta = {}

    dublin_core_meta = dict(list(nc_global_meta.items()) + list(nc_coverage_meta.items()))

    return dublin_core_meta


def extract_nc_global_meta(nc_dataset):
    """
    (object)->dict

    Return netCDF global attributes info which correspond to dublincore meta attributes
    """

    nc_global_meta = {}

    # key is the dublincore attributes,
    # value is corresponding attributes from ACDD and CF convention
    dublincore_vs_convention = {
        'creator_name': ['creator_name'],
        'creator_email': ['creator_email'],
        'creator_url': ['creator_url'],
        'contributor_name': ['contributor_name'],
        'convention': ['Conventions'],
        'title': ['title'],
        'subject': ['keywords'],
        'description': ['summary', 'comment'],
        'rights': ['license'],
        'references': ['references'],
        'source': ['source'],
    }

    for dublincore, convention in list(dublincore_vs_convention.items()):
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

    Return netCDF spatial reference (original coverage), spatial coverage and temporal coverage
    """

    projection_info = get_projection_info(nc_dataset)

    period_info = get_period_info(nc_dataset)

    original_box_info = get_original_box_info(nc_dataset)
    for name in list(original_box_info.keys()):
        if name.endswith("limit"):
            original_box_info[name] = float(original_box_info[name])
        else:
            original_box_info[name] = str(original_box_info[name])
        if name == 'units' and original_box_info[name].lower() == 'm':
            original_box_info[name] = 'Meter'

    box_info = get_box_info(nc_dataset)
    for name in list(box_info.keys()):
        if name.endswith("limit"):
            box_info[name] = float(box_info[name])
        else:
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
    projection_info = get_nc_grid_mapping_projection_import_string_dict(nc_dataset)

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
        period_info['start'] = nc_dataset.__dict__['time_coverage_start']
        period_info['end'] = nc_dataset.__dict__['time_coverage_end']

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
        except Exception:
            continue

    return period_info


def get_box_info(nc_dataset):
    """
    (object)-> dict

    Return: the netCDF spatial coverage box info as wgs84 crs
    """
    box_info = {}
    original_box_info = get_original_box_info(nc_dataset)

    if original_box_info:
        # derive spatial coverage from spatial reference (original coverage)
        if original_box_info.get('units', '').lower() == 'degree':  # geographic coor x, y
            box_info = original_box_info
            # check if the westlimit and eastlimit are in -180-180
            westlimit = float(box_info['westlimit'])
            eastlimit = float(box_info['eastlimit'])
            box_info['westlimit'] = check_lon_limit(westlimit, eastlimit)[0]
            box_info['eastlimit'] = check_lon_limit(westlimit, eastlimit)[1]

        elif original_box_info.get('projection', ''):  # projection coor x, y
            projection_import_string_dict = get_nc_grid_mapping_projection_import_string_dict(nc_dataset)
            if projection_import_string_dict.get('type') == 'Proj4 String':
                try:
                    transformer = Transformer.from_crs(projection_import_string_dict['text'], "epsg:4326")
                    box_info['northlimit'], box_info['westlimit'] = transformer.transform(
                        original_box_info['westlimit'], original_box_info['northlimit']
                    )
                    box_info['southlimit'], box_info['eastlimit'] = transformer.transform(
                        original_box_info['eastlimit'], original_box_info['southlimit']
                    )
                except Exception:
                    pass
            elif projection_import_string_dict.get('type') == 'WKT String':
                try:
                    # create wgs84 geographic coordinate system
                    wgs84_cs = osr.SpatialReference()
                    wgs84_cs.ImportFromEPSG(4326)
                    original_cs = osr.SpatialReference()
                    original_cs.ImportFromWkt(projection_import_string_dict.get('text'))
                    crs_transform = osr.CoordinateTransformation(original_cs, wgs84_cs)
                    box_info['westlimit'], box_info['northlimit'] = crs_transform.TransformPoint(
                        float(original_box_info['westlimit']), float(original_box_info['northlimit'])
                    )[:2]

                    box_info['eastlimit'], box_info['southlimit'] = crs_transform.TransformPoint(
                        float(original_box_info['eastlimit']), float(original_box_info['southlimit'])
                    )[:2]
                except Exception:
                    pass

    if not box_info:  # spatial coverage was not computed from spatial reference
        # get the spatial coverage as per ACDD convention
        box_info = get_original_box_info_by_acdd_convention(nc_dataset)
    if box_info:
        # change the value as string
        for name in list(box_info.keys()):
            box_info[name] = str(box_info[name])
        box_info['units'] = 'Decimal degrees'
        box_info['projection'] = 'WGS 84 EPSG:4326'

    return box_info


def check_lon_limit(westlimit, eastlimit):
    """
    (num, num)-> [num,num]

    Return: given the original westlimit and eastlimit values in degree units,
    convert them in -180-180 range and make sure eastlimit > westlimit
    """

    # check if limit is in range of -180-180
    if westlimit > 180:
        westlimit -= 360
    if eastlimit > 180:
        eastlimit -= 360

    # check if westlimit < eastlimit
    if westlimit == eastlimit:
        westlimit = -180
        eastlimit = 180
    elif westlimit > eastlimit:
        if (180 - westlimit) >= (eastlimit + 180):
            eastlimit = 180
        else:
            westlimit = -180

    return [westlimit, eastlimit]


def get_original_box_info(nc_dataset):
    """
    (object)-> dict

    Return: the netCDF original coverage box info
    """

    original_box_info = get_original_box_info_by_data(nc_dataset)

    if original_box_info:
        if original_box_info.get('units', '') == 'degree':
            original_box = get_original_box_info_by_acdd_convention(nc_dataset)
            if original_box:
                original_box_info = original_box

    return original_box_info


def get_original_box_info_by_acdd_convention(nc_dataset):
    """
    (object)-> dict

    Return: the netCDF original coverage box info by looking for acdd convention terms
    """

    original_box_info = {}
    if (
        nc_dataset.__dict__.get('geospatial_lat_min', '')
        and nc_dataset.__dict__.get('geospatial_lat_max', '')
        and nc_dataset.__dict__.get('geospatial_lon_min', '')
        and nc_dataset.__dict__.get('geospatial_lon_max', '')
    ):
        original_box_info['southlimit'] = str(nc_dataset.__dict__['geospatial_lat_min'])
        original_box_info['northlimit'] = str(nc_dataset.__dict__['geospatial_lat_max'])
        original_box_info['westlimit'] = str(nc_dataset.__dict__['geospatial_lon_min'])
        original_box_info['eastlimit'] = str(nc_dataset.__dict__['geospatial_lon_max'])
        original_box_info['units'] = 'degree'
        original_box_info['projection'] = get_nc_grid_mapping_crs_name(nc_dataset)
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
            original_box_info['projection'] = get_nc_grid_mapping_crs_name(nc_dataset)
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
            limits_info = dict(list(limits_info.items()) + list(limit_meta.items()))
        else:
            limits_info = {}
            break

    return limits_info


def get_limit_meta_by_coor_type(nc_dataset, coor_type, coor_type_mapping):
    """
    (obj, str, dict) -> dict

    Return: based on the coordinate type (XA,YA,XC,YC,TA,TC) return the limits
            start and end values and units
    """

    limit_meta = {}
    coor_start = []
    coor_end = []
    coor_units = ''

    var_name_list = list(coor_type_mapping.keys())
    coor_type_list = list(coor_type_mapping.values())

    for coor_type_name in [coor_type, coor_type + '_bnd']:
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
            limit_meta = {'southlimit': coor_min, 'northlimit': coor_max}
        if "T" in coor_type:
            limit_meta = {'start': coor_min, 'end': coor_max}

        if coor_units:
            limit_meta['units'] = coor_units
    else:
        limit_meta = {}

    return limit_meta


# Functions for type specific meta
def get_type_specific_meta(nc_dataset):
    """
    (object)-> dict

    Return: the netCDF type specific metadata
    """

    nc_data_variables = nc_dataset.variables  # get_nc_data_variables(nc_dataset)
    type_specific_meta = extract_nc_data_variables_meta(nc_data_variables)
    variables = [val for val in type_specific_meta.values()]

    return variables


def extract_nc_data_variables_meta(nc_data_variables):
    """
    (dict) -> dict

    Return : the netCDF data variable metadata which are required by HS system.
    """
    nc_data_variables_meta = {}
    for var_name, var_obj in list(nc_data_variables.items()):
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
                elif var_obj.datatype.name in list(nc_data_type_dict.keys()):
                    nc_data_variables_meta[var_name]['type'] = nc_data_type_dict[var_obj.datatype.name]
                elif ('string' in var_obj.datatype.name) or ('unicode' in var_obj.datatype.name):
                    nc_data_variables_meta[var_name]['type'] = 'Char' if '8' in var_obj.datatype.name else 'String'
                else:
                    nc_data_variables_meta[var_name]['type'] = 'Unknown'
            except Exception:
                nc_data_variables_meta[var_name]['type'] = 'Unknown'
        else:
            nc_data_variables_meta[var_name]['type'] = 'Unknown'

    return nc_data_variables_meta


# Functions for General Purpose
def get_nc_dataset(nc_file_name):
    """
    (string)-> object

    Return: the netCDF dataset
    """
    try:
        temp_dir = tempfile.gettempdir()
        local_copy = os.path.join(temp_dir, os.path.basename(nc_file_name))
        s3.get_file(nc_file_name, local_copy)
        nc_dataset = netCDF4.Dataset(local_copy, 'r')
    except Exception:
        nc_dataset = None

    return nc_dataset


def get_nc_variable(nc_file_name, nc_variable_name):
    """
    (string, string) -> obj

    Return: netcdf variable by the given variable name
    """

    if isinstance(nc_file_name, netCDF4.Dataset):
        nc_dataset = nc_file_name
    else:
        nc_dataset = get_nc_dataset(nc_file_name)

    if nc_variable_name in list(nc_dataset.variables.keys()):
        nc_variable = nc_dataset.variables[nc_variable_name]
    else:
        nc_variable = None

    return nc_variable


def get_nc_variable_original_meta(nc_dataset, nc_variable_name):
    """
    (object, string)-> OrderedDict

    Return: netCDF variable original metadata information defined in the netCDF file
    """

    nc_variable = nc_dataset.variables[nc_variable_name]

    nc_variable_original_meta = OrderedDict(
        [
            ('dimension', str(nc_variable.dimensions)),
            ('shape', str(nc_variable.shape)),
            ('data_type', str(nc_variable.dtype)),
        ]
    )

    for key, value in list(nc_variable.__dict__.items()):
        nc_variable_original_meta[key] = str(value)

    return nc_variable_original_meta


# Functions for coordinate information of the dataset
# The functions below will call functions defined for auxiliary, coordinate and bounds variables.
def get_nc_variables_coordinate_type_mapping(nc_dataset):
    """
    (object)-> dict

    Return: XC,YC,ZC,TC, Unknown_C for coordinate variable
            XA, YA, ZA, TA Unknown_A for auxiliary variable
            XC_bnd, YC_bnd, ZC_bnd, TC_bnd, Unknown_bnd for coordinate bounds variable
            XA_bnd, YA_bnd, ZA_bnd, TA_bnd, Unknown_A_bnd for auxiliary coordinate bounds variable
    """
    nc_variables_dict = {
        "C": get_nc_coordinate_variables(nc_dataset),
        "A": get_nc_auxiliary_coordinate_variables(nc_dataset),
    }
    nc_variables_coordinate_type_mapping = {}

    for variables_type, variables_dict in list(nc_variables_dict.items()):
        for var_name, var_obj in list(variables_dict.items()):
            var_coor_type_name = get_nc_variable_coordinate_type(var_obj) + variables_type
            nc_variables_coordinate_type_mapping[var_name] = var_coor_type_name
            if hasattr(var_obj, 'bounds') and nc_dataset.variables.get(var_obj.bounds, None):
                var_coor_bounds_type_name = var_coor_type_name + '_bnd'
                nc_variables_coordinate_type_mapping[var_obj.bounds] = var_coor_bounds_type_name

    return nc_variables_coordinate_type_mapping


def get_nc_variable_coordinate_type(nc_variable):
    """
    (object)-> string

    Return: One of X, Y, Z, T is assigned to variable.
            If not discerned as X, Y, Z, T, Unknown is returned
    """

    if hasattr(nc_variable, 'axis') and nc_variable.axis:
        return nc_variable.axis

    nc_variable_standard_name = getattr(nc_variable, 'standard_name', getattr(nc_variable, 'long_name', None))
    if nc_variable_standard_name:
        compare_dict = {
            'latitude': 'Y',
            'longitude': 'X',
            'time': 'T',
            'projection_x_coordinate': 'X',
            'projection_y_coordinate': 'Y',
        }
        for standard_name, coor_type in list(compare_dict.items()):
            if re.match(standard_name, nc_variable_standard_name, re.I):
                return coor_type

    if hasattr(nc_variable, 'positive'):
        return 'Z'

    if hasattr(nc_variable, 'units') and nc_variable.units:
        if re.match('degree(s)?.e(ast)?', nc_variable.units, re.I):
            return 'X'
        elif re.match('degree(s)?.n(orth)?', nc_variable.units, re.I):
            return 'Y'
        else:
            info = nc_variable.units.split(' ')
            time_units = ['days', 'hours', 'minutes', 'seconds', 'milliseconds', 'microseconds']  # see python netcdf4
            if len(info) >= 3 and (info[0].lower() in time_units) and info[1].lower() == 'since':
                return 'T'

    return 'Unknown'


def get_nc_variable_coordinate_meta(nc_dataset, nc_variable_name):
    """
    (object)-> dict

    Return: coordinate meta data if the variable is related to a coordinate type:
            coordinate or auxiliary coordinate variable or bounds variable
    """
    nc_variables_coordinate_type_mapping = get_nc_variables_coordinate_type_mapping(nc_dataset)
    nc_variable_coordinate_meta = {}
    if nc_variable_name in list(nc_variables_coordinate_type_mapping.keys()):
        nc_variable = nc_dataset.variables[nc_variable_name]
        nc_variable_data = nc_variable[:]
        nc_variable_coordinate_type = nc_variables_coordinate_type_mapping[nc_variable_name]
        coordinate_max = None
        coordinate_min = None
        if nc_variable_data.size:
            coordinate_min = nc_variable_data[numpy.unravel_index(nc_variable_data.argmin(), nc_variable_data.shape)]
            coordinate_max = nc_variable_data[numpy.unravel_index(nc_variable_data.argmax(), nc_variable_data.shape)]
            coordinate_units = nc_variable.units if hasattr(nc_variable, 'units') else ''

            if nc_variable_coordinate_type in ['TC', 'TA', 'TC_bnd', 'TA_bnd']:
                index = list(nc_variables_coordinate_type_mapping.values()).index(nc_variable_coordinate_type[:2])
                var_name = list(nc_variables_coordinate_type_mapping.keys())[index]
                var_obj = nc_dataset.variables[var_name]
                time_units = var_obj.units if hasattr(var_obj, 'units') else ''
                time_calendar = var_obj.calendar if hasattr(var_obj, 'calendar') else 'standard'

                if time_units and time_calendar:
                    try:
                        coordinate_min = netCDF4.num2date(coordinate_min, units=time_units, calendar=time_calendar)
                        coordinate_max = netCDF4.num2date(coordinate_max, units=time_units, calendar=time_calendar)
                        coordinate_units = time_units
                    except Exception:
                        pass

            nc_variable_coordinate_meta = {
                'coordinate_type': nc_variable_coordinate_type,
                'coordinate_units': coordinate_units,
                'coordinate_start': coordinate_min,
                'coordinate_end': coordinate_max,
            }

    return nc_variable_coordinate_meta


# Functions for Coordinate Variable
# coordinate variable has the following attributes:
# 1) it has 1 dimension
# 2) its name is the same as its dimension name (COARDS convention)
# 3) coordinate variable sometimes doesn't represent the real lat lon time vertical info
# 4) coordinate variable sometimes has associated bound variable if it represents
#    the real lat lon time vertical info


def get_nc_coordinate_variables(nc_dataset):
    """
    (object)-> dict

    Return netCDF coordinate variable
    """

    nc_all_variables = nc_dataset.variables
    nc_coordinate_variables = {}
    for var_name, var_obj in list(nc_all_variables.items()):
        if len(var_obj.shape) == 1 and var_name == var_obj.dimensions[0]:
            nc_coordinate_variables[var_name] = nc_dataset.variables[var_name]

    return nc_coordinate_variables


def get_nc_coordinate_variable_namelist(nc_dataset):
    """
    (object)-> list

    Return netCDF coordinate variable names
    """
    nc_coordinate_variables = get_nc_coordinate_variables(nc_dataset)
    nc_coordinate_variable_namelist = list(nc_coordinate_variables.keys())

    return nc_coordinate_variable_namelist


# Functions for Auxiliary Coordinate Variable
# auxiliary variable has the following attributes:
# 1) it is used when the variable dimensions are not representing the lat, lon,
#    time and vertical coordinate
# 2) the data variable will include 'coordinates' attribute to store the name of the
#    auxiliary coordinate variable


def get_nc_auxiliary_coordinate_variable_namelist(nc_dataset):
    """
    (object) -> list

    Return: the netCDF auxiliary coordinate variable names
    """

    nc_all_variables = nc_dataset.variables
    raw_namelist = []
    for var_name, var_obj in list(nc_all_variables.items()):
        if hasattr(var_obj, 'coordinates'):
            raw_namelist.extend(var_obj.coordinates.split(' '))

    nc_auxiliary_coordinate_variable_namelist = list(set(raw_namelist))

    return nc_auxiliary_coordinate_variable_namelist


def get_nc_auxiliary_coordinate_variables(nc_dataset):
    """
    (object) -> dict

    Return: the netCDF auxiliary coordinate variables
    Format: {'var_name': var_obj}
    """

    nc_auxiliary_coordinate_variable_namelist = get_nc_auxiliary_coordinate_variable_namelist(nc_dataset)
    nc_auxiliary_coordinate_variables = {}
    for name in nc_auxiliary_coordinate_variable_namelist:
        if nc_dataset.variables.get(name, ''):
            nc_auxiliary_coordinate_variables[name] = nc_dataset.variables[name]

    return nc_auxiliary_coordinate_variables


# Functions for Bounds Variable
# the Bounds variable has the following attributes:
# 1) bounds variable is used to define the cell
# 2) It is associated with the coordinate or auxiliary coordinate variable.
# 3) If a coordinate or an auxiliary coordinate variable has bounds variable,
#    the has the attributes 'bounds'


def get_nc_coordinate_bounds_variables(nc_dataset):
    """
    (object) -> dict

    Return: the netCDF coordinate bounds variable
    Format: {'var_name': var_obj}
    """
    nc_coordinate_variables = get_nc_coordinate_variables(nc_dataset)
    nc_auxiliary_coordinate_variables = get_nc_auxiliary_coordinate_variables(nc_dataset)
    nc_coordinate_bounds_variables = {}
    for var_name, var_obj in list(
        dict(list(nc_coordinate_variables.items()) + list(nc_auxiliary_coordinate_variables.items())).items()
    ):
        if hasattr(var_obj, 'bounds') and nc_dataset.variables.get(var_obj.bounds, None):
            nc_coordinate_bounds_variables[var_obj.bounds] = nc_dataset.variables[var_obj.bounds]

    return nc_coordinate_bounds_variables


def get_nc_coordinate_bounds_variable_namelist(nc_dataset):
    """
    (object) -> list

    Return: the netCDF coordinate bound variable names
    """

    nc_coordinate_bounds_variables = get_nc_coordinate_bounds_variables(nc_dataset)
    nc_coordinate_bounds_variable_namelist = list(nc_coordinate_bounds_variables.keys())

    return nc_coordinate_bounds_variable_namelist


# Function for Data Variable
def get_nc_data_variables(nc_dataset):
    """
    (object) -> dict

    Return: the netCDF Data variables
    """

    nc_non_data_variables_namelist = list(get_nc_variables_coordinate_type_mapping(nc_dataset).keys())

    nc_data_variables = {}
    for var_name, var_obj in list(nc_dataset.variables.items()):
        if (var_name not in nc_non_data_variables_namelist) and (len(var_obj.shape) >= 1):
            nc_data_variables[var_name] = var_obj

    return nc_data_variables


def get_nc_data_variable_namelist(nc_dataset):
    """
    (object) -> list

    Return: the netCDF Data variables names
    """

    nc_data_variables = get_nc_data_variables(nc_dataset)
    nc_data_variable_namelist = list(nc_data_variables.keys())

    return nc_data_variable_namelist


# Functions for Grid Mapping Variable
def get_nc_grid_mapping_variable_name(nc_dataset):
    """
    (object)-> string

    Return: the netCDF grid mapping variable name
    """
    nc_all_variables = nc_dataset.variables
    nc_grid_mapping_variable_name = ''
    for var_name, var_obj in list(nc_all_variables.items()):
        if hasattr(var_obj, 'grid_mapping_name') and var_obj.grid_mapping_name:
            nc_grid_mapping_variable_name = var_name

    return nc_grid_mapping_variable_name


def get_nc_grid_mapping_variable(nc_dataset):
    """
    (object)-> object

    Return: the netCDF grid mapping variable object
    """

    nc_all_variables = nc_dataset.variables
    nc_grid_mapping_variable = None
    for var_name, var_obj in list(nc_all_variables.items()):
        if hasattr(var_obj, 'grid_mapping_name'):
            nc_grid_mapping_variable = var_obj

    return nc_grid_mapping_variable


def get_nc_grid_mapping_projection_name(nc_dataset):
    """
    (object)-> string
    Return: the netCDF grid mapping projection name
    """

    nc_grid_mapping_variable = get_nc_grid_mapping_variable(nc_dataset)
    nc_grid_mapping_projection_name = getattr(nc_grid_mapping_variable, 'grid_mapping_name', '')

    return nc_grid_mapping_projection_name


def get_nc_grid_mapping_crs_name(nc_dataset):
    """
    (object)-> string

    Return: the netCDF grid mapping crs projection name. This will take the wkt name as
            the first option and then take the grid mapping name as the second option.
    """

    nc_grid_mapping_variable = get_nc_grid_mapping_variable(nc_dataset)
    nc_grid_mapping_crs_name = ''

    for attribute_name in ['crs_wkt', 'spatial_ref', 'esri_pe_string']:
        if hasattr(nc_grid_mapping_variable, attribute_name):
            projection_string = getattr(nc_grid_mapping_variable, attribute_name)
            try:
                spatial_ref = osr.SpatialReference()
                spatial_ref.ImportFromWkt(projection_string)
                if spatial_ref.IsProjected():
                    nc_grid_mapping_crs_name = spatial_ref.GetAttrValue('projcs', 0)
                else:
                    nc_grid_mapping_crs_name = spatial_ref.GetAttrValue('geogcs', 0)
                break
            except Exception:
                break

    if nc_grid_mapping_crs_name == '':
        nc_grid_mapping_crs_name = get_nc_grid_mapping_projection_name(nc_dataset)

    return nc_grid_mapping_crs_name


def get_nc_grid_mapping_projection_import_string_dict(nc_dataset):
    """
    (object)-> dict

    Return: the netCDF grid mapping info dictionary proj4 or WKT string used for creating projection
            object with pyproj.Proj() or gdal
    Reference: Cf convention for grid mapping projection
               http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/build/ch05s06.html
    """

    projection_import_string_dict = {}

    # get the proj name, proj variable
    nc_grid_mapping_projection_name = get_nc_grid_mapping_projection_name(nc_dataset)
    nc_grid_mapping_variable = get_nc_grid_mapping_variable(nc_dataset)

    # get the projection string and type
    projection_string = ''
    for attribute_name in ['proj4', 'crs_wkt', 'spatial_ref', 'esri_pe_string']:
        if hasattr(nc_grid_mapping_variable, attribute_name):
            projection_string = getattr(nc_grid_mapping_variable, attribute_name)
            break

    if projection_string:
        projection_type = 'Proj4 String' if attribute_name == 'proj4' else 'WKT String'
        try:
            spatial_ref = osr.SpatialReference()
            spatial_ref.ImportFromWkt(projection_string)
            datum = spatial_ref.GetAttrValue("DATUM", 0) if spatial_ref.GetAttrValue("DATUM", 0) else ''
        except Exception:
            datum = ''

    else:
        proj_names = {
            'albers_conical_equal_area': 'aea',
            'azimuthal_equidistant': 'aeqd',
            'lambert_azimuthal_equal_area': 'laea',
            'lambert_conformal_conic': 'lcc',  # tested with prcp.nc
            'lambert_cylindrical_equal_area': 'cea',
            'mercator': 'merc',
            'orthographic': 'ortho',
            'polar_stereographic': 'stere',
            'stereographic': 'stere',
            'transverse_mercator': 'tmerc',  # test with swe.nc
            'vertical_perspective': 'geos',
        }

        proj_paras = {
            '+y_0': 'false_northing',
            '+x_0': 'false_easting',
            '+k_0': 'scale_factor_at_projection_origin,scale_factor_at_central_meridian',
            '+lat_0': 'latitude_of_projection_origin',
            '+lon_0': 'longitude_of_projection_origin,longitude_of_central_meridian,'
            'straight_vertical_longitude_from_pole',
            '+h': 'perspective_point_height',
            '+a': 'semi_major_axis',
            '+b': 'semi_minor_axis',
        }

        standard_parallel_types = ['albers_conical_equal_area', 'lambert_conformal_conic']

        # create the projection import string
        proj_info_list = []

        if nc_grid_mapping_projection_name in list(proj_names.keys()):
            # add projection name
            proj_info_list.append('+proj={0}'.format(proj_names[nc_grid_mapping_projection_name]))

            # add basic parameters
            for proj4_para, cf_para in list(proj_paras.items()):
                for para in cf_para.split(','):
                    if hasattr(nc_grid_mapping_variable, para):
                        proj_info_list.append('{0}={1}'.format(proj4_para, getattr(nc_grid_mapping_variable, para)))
                        break

            # add standard parallel para
            if hasattr(nc_grid_mapping_variable, 'standard_parallel'):
                if nc_grid_mapping_projection_name in standard_parallel_types:
                    str_value = str(nc_grid_mapping_variable.standard_parallel).strip('[]').split()
                    try:
                        num_value = sorted([float(x) for x in str_value])
                        if num_value.__len__() <= 2:
                            proj_info_list.extend(['lat_{0}={1}'.format(i + 1, j) for i, j in enumerate(num_value)])
                    except Exception:
                        pass
                else:
                    proj_info_list.append('{0}={1}'.format('+lat_ts', nc_grid_mapping_variable.standard_parallel))

        projection_string = ' '.join(proj_info_list)
        projection_type = 'Proj4 String'
        datum = ''

    if projection_string:
        projection_import_string_dict = {
            'text': projection_string,
            'type': projection_type,
            'datum': datum,
        }

    return projection_import_string_dict


def add_original_coverage_metadata(extracted_metadata):
    """
    Adds data for the original coverage element to the *metadata_list*
    :param metadata_list: list to  which original coverage data needs to be added
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :return:
    """

    ori_cov = {}
    if extracted_metadata.get('original-box'):
        coverage_data = extracted_metadata['original-box']
        projection_string_type = ""
        projection_string_text = ""
        datum = ""
        if extracted_metadata.get('projection-info'):
            projection_string_type = extracted_metadata['projection-info']['type']
            projection_string_text = extracted_metadata['projection-info']['text']
            datum = extracted_metadata['projection-info']['datum']

        ori_cov = {
            'spatial_reference': {
                **coverage_data,
                'projection_string_type': projection_string_type,
                'projection_string': projection_string_text,
                'datum': datum,
            }
        }
    if ori_cov:
        return ori_cov


def add_creators_metadata(extracted_metadata):
    """
    Adds data for creator(s) to the *metadata_list*
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :param existing_creators: a QuerySet object for existing creators
    :return:
    """
    if extracted_metadata.get('creator_name'):
        name = extracted_metadata['creator_name']
        # add creator only if there is no creator already with the same name
        email = extracted_metadata.get('creator_email', '')
        url = extracted_metadata.get('creator_url', '')
        creator = {'creator': {'name': name, 'email': email, 'homepage': url}}
        return creator


def add_contributors_metadata(extracted_metadata):
    """
    Adds data for contributor(s) to the *metadata_list*
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :return:
    """
    if extracted_metadata.get('contributor_name'):
        name_list = extracted_metadata['contributor_name'].split(',')
        for name in name_list:
            # add contributor only if there is no contributor already with the
            # same name
            contributor = {'contributor': {'name': name}}
            return contributor


def add_title_metadata(extracted_metadata):
    """
    Adds data for the title element to the *metadata_list*
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :return:
    """
    if extracted_metadata.get('title'):
        res_title = {'title': extracted_metadata['title']}
        return res_title


def add_abstract_metadata(extracted_metadata):
    """
    Adds data for the abstract (Description) element to the *metadata_list*
    :param metadata_list: list to  which abstract data needs to be added
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :return:
    """

    if extracted_metadata.get('description'):
        description = {'abstract': extracted_metadata['description']}
        return description


def add_variable_metadata(extracted_metadata):
    """
    Adds variable(s) related data to the *metadata_list*
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :return:
    """
    variables = []
    for var_meta in extracted_metadata:
        meta_info = {}
        for element, value in list(var_meta.items()):
            if value != '':
                meta_info[element] = value
        variables.append(meta_info)
    return {"variables": variables}


def add_spatial_coverage_metadata(extracted_metadata):
    """
    Adds data for one spatial coverage metadata element to the *metadata_list**
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :return:
    """
    if extracted_metadata.get('box'):
        return {'spatial_coverage': extracted_metadata['box']}


def add_temporal_coverage_metadata(extracted_metadata):
    """
    Adds data for one temporal metadata element to the *metadata_list*
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :return:
    """
    if extracted_metadata.get('period'):
        start = dateutil.parser.isoparse(extracted_metadata['period']['start']).isoformat()
        end = dateutil.parser.isoparse(extracted_metadata['period']['end']).isoformat()
        return {'period_coverage': {"start": start, "end": end}}


def add_keywords_metadata(extracted_metadata):
    """
    Adds data for subject/keywords element to the *metadata_list*
    :param extracted_metadata: a dict containing netcdf extracted metadata
    metadata extraction is for NetCDF resource
    :return:
    """
    if extracted_metadata.get('subject'):
        keywords = extracted_metadata['subject'].split(',')
        return {'subjects': keywords}


def combine_metadata(extracted_core_meta, extracted_specific_meta):
    """
    Helper function to populate metadata lists (*res_meta_list* and *file_meta_list*) with
    extracted metadata from the NetCDF file. These metadata lists are then used for creating
    metadata element objects by the caller.
    :param extracted_core_meta: a dict of extracted dublin core metadata
    :param extracted_specific_meta: a dict of extracted metadata that is NetCDF specific
    :return:
    """

    metadata = {}
    # add title
    title = add_title_metadata(extracted_core_meta)
    if title:
        metadata.update(title)

    # add abstract (Description element)
    abstract = add_abstract_metadata(extracted_core_meta)
    if abstract:
        metadata.update(abstract)

    # add keywords
    keywords = add_keywords_metadata(extracted_core_meta)
    if keywords:
        metadata.update(keywords)

    # add creators:
    creators = add_creators_metadata(extracted_core_meta)
    if creators:
        metadata.update(creators)

    # add contributors:
    contributors = add_contributors_metadata(extracted_core_meta)
    if contributors:
        metadata.update(contributors)

    # add relation of type 'source' (applies only to NetCDF resource type)
    if extracted_core_meta.get('source'):
        relation = {'relation': {'type': 'source', 'value': extracted_core_meta['source']}}
        metadata.update(relation)

    # add relation of type 'references' (applies only to NetCDF resource type)
    if extracted_core_meta.get('references'):
        relation = {'relation': {'type': 'references', 'value': extracted_core_meta['references']}}
        metadata.update(relation)

    # add rights (applies only to NetCDF resource type)
    if extracted_core_meta.get('rights'):
        raw_info = extracted_core_meta.get('rights')
        b = re.search("(?P<url>https?://[^\s]+)", raw_info)
        url = b.group('url') if b else ''
        statement = raw_info.replace(url, '') if url else raw_info
        rights = {'rights': {'statement': statement, 'url': url}}
        metadata.update(rights)

    # add coverage - period
    period_coverage = add_temporal_coverage_metadata(extracted_core_meta)
    if period_coverage:
        metadata.update(period_coverage)

    # add coverage - box
    spatial_coverage = add_spatial_coverage_metadata(extracted_core_meta)
    if spatial_coverage:
        metadata.update(spatial_coverage)

    # add variables
    variables = add_variable_metadata(extracted_specific_meta)
    if variables:
        metadata.update(variables)

    # add original spatial coverage
    original_coverage = add_original_coverage_metadata(extracted_core_meta)
    if original_coverage:
        metadata.update(original_coverage)

    return metadata
