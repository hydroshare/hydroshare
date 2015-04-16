"""
Module provides utility functions to manipulate netCDF dataset.
- classify variable types of coordinate, coordinate bounds, grid mapping, scientific data, auxiliary coordinate
- show original metadata of a variable

Reference code
http://netcdf4-python.googlecode.com/svn/trunk/docs/netCDF4-module.html
"""
__author__ = 'Tian Gan'


import netCDF4
import re
from collections import OrderedDict
import numpy


# Functions for General Purpose ####################################################################################
def get_nc_dataset(nc_file_name):
    """
    (string)-> object

    Return: the netCDF dataset
    """
    try:
        nc_dataset = netCDF4.Dataset(nc_file_name, 'r')
    except:
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

    if nc_variable_name in nc_dataset.variables.keys():
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

    nc_variable_original_meta = OrderedDict([('dimension', str(nc_variable.dimensions)),
                                             ('shape', str(nc_variable.shape)),
                                             ('data_type', str(nc_variable.dtype))])

    for key, value in nc_variable.__dict__.items():
        nc_variable_original_meta[key] = str(value)

    return nc_variable_original_meta


# Functions for coordinate information of the dataset ##################################################################
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
        "A": get_nc_auxiliary_coordinate_variables(nc_dataset)
    }
    nc_variables_coordinate_type_mapping = {}

    for variables_type, variables_dict in nc_variables_dict.items():
        for var_name, var_obj in variables_dict.items():
            var_coor_type_name = get_nc_variable_coordinate_type(var_obj) + variables_type
            nc_variables_coordinate_type_mapping[var_name] = var_coor_type_name
            if hasattr(var_obj, 'bounds') and nc_dataset.variables.get(var_obj.bounds, None):
                var_coor_bounds_type_name = var_coor_type_name+'_bnd'
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
            'projection_y_coordinate': 'Y'
        }
        for standard_name, coor_type in compare_dict.items():
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
            time_units = ['days', 'hours', 'minutes', 'seconds', 'milliseconds', 'microseconds'] # see python netcdf4
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
    if nc_variable_name in nc_variables_coordinate_type_mapping.keys():
        nc_variable = nc_dataset.variables[nc_variable_name]
        nc_variable_data = nc_variable[:]
        nc_variable_coordinate_type = nc_variables_coordinate_type_mapping[nc_variable_name]
        coordinate_max = None
        coordinate_min = None
        if nc_variable_data.size:
            coordinate_min = nc_variable_data[numpy.unravel_index(nc_variable_data.argmin(), nc_variable_data.shape)]
            coordinate_max = nc_variable_data[numpy.unravel_index(nc_variable_data.argmax(), nc_variable_data.shape)]
            coordinate_units = nc_variable.units if hasattr(nc_variable, 'units') else ''

            if (nc_variable_coordinate_type in ['TC', 'TA', 'TC_bnd', 'TA_bnd']):
                index = nc_variables_coordinate_type_mapping.values().index(nc_variable_coordinate_type[:2])
                var_name = nc_variables_coordinate_type_mapping.keys()[index]
                var_obj = nc_dataset.variables[var_name]
                time_units = var_obj.units if hasattr(var_obj, 'units') else ''
                time_calendar = var_obj.calendar if hasattr(var_obj, 'calendar') else 'standard'

                if time_units and time_calendar:
                    try:
                        coordinate_min = netCDF4.num2date(coordinate_min, units=time_units, calendar=time_calendar)
                        coordinate_max = netCDF4.num2date(coordinate_max, units=time_units, calendar=time_calendar)
                        coordinate_units = time_units
                    except:
                        pass

            nc_variable_coordinate_meta = {
                'coordinate_type': nc_variable_coordinate_type,
                'coordinate_units': coordinate_units,
                'coordinate_start': coordinate_min,
                'coordinate_end': coordinate_max
            }

    return nc_variable_coordinate_meta


# Functions for Coordinate Variable#####################################################################################
# coordinate variable has the following attributes:
# 1) it has 1 dimension
# 2) its name is the same as its dimension name (COARDS convention)
# 3) coordinate variable sometimes doesn't represent the real lat lon time vertical info
# 4) coordinate variable sometimes has associated bound variable if it represents the real lat lon time vertical info

def get_nc_coordinate_variables(nc_dataset):
    """
    (object)-> dict

    Return netCDF coordinate variable
    """

    nc_all_variables = nc_dataset.variables
    nc_coordinate_variables = {}
    for var_name, var_obj in nc_all_variables.items():
        if len(var_obj.shape) == 1 and var_name == var_obj.dimensions[0]:
            nc_coordinate_variables[var_name] = nc_dataset.variables[var_name]

    return nc_coordinate_variables


def get_nc_coordinate_variable_namelist(nc_dataset):
    """
    (object)-> list

    Return netCDF coordinate variable names
    """
    nc_coordinate_variables = get_nc_coordinate_variables(nc_dataset)
    nc_coordinate_variable_namelist = nc_coordinate_variables.keys()

    return nc_coordinate_variable_namelist


# Functions for Auxiliary Coordinate Variable ########################################################################
# auxiliary variable has the following attributes:
# 1) it is used when the variable dimensions are not representing the lat, lon, time and vertical coordinate
# 2) the data variable will include 'coordinates' attribute to store the name of the auxiliary coordinate variable

def get_nc_auxiliary_coordinate_variable_namelist(nc_dataset):
    """
    (object) -> list

    Return: the netCDF auxiliary coordinate variable names
    """

    nc_all_variables = nc_dataset.variables
    raw_namelist = []
    for var_name, var_obj in nc_all_variables.items():
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


# Functions for Bounds Variable ######################################################
# the Bounds variable has the following attributes:
# 1) bounds variable is used to define the cell
# 2) It is associated with the coordinate or auxiliary coordinate variable.
# 3) If a coordinate or an auxiliary coordinate variable has bounds variable, the has the attributes 'bounds'

def get_nc_coordinate_bounds_variables(nc_dataset):
    """
    (object) -> dict

    Return: the netCDF coordinate bounds variable
    Format: {'var_name': var_obj}
    """
    nc_coordinate_variables = get_nc_coordinate_variables(nc_dataset)
    nc_auxiliary_coordinate_variables = get_nc_auxiliary_coordinate_variables(nc_dataset)
    nc_coordinate_bounds_variables = {}
    for var_name, var_obj in dict(nc_coordinate_variables.items() + nc_auxiliary_coordinate_variables.items()).items():
        if hasattr(var_obj, 'bounds') and nc_dataset.variables.get(var_obj.bounds, None):
            nc_coordinate_bounds_variables[var_obj.bounds] = nc_dataset.variables[var_obj.bounds]

    return nc_coordinate_bounds_variables


def get_nc_coordinate_bounds_variable_namelist(nc_dataset):
    """
    (object) -> list

    Return: the netCDF coordinate bound variable names
    """

    nc_coordinate_bounds_variables = get_nc_coordinate_bounds_variables(nc_dataset)
    nc_coordinate_bounds_variable_namelist = nc_coordinate_bounds_variables.keys()

    return nc_coordinate_bounds_variable_namelist


# Function for Data Variable ##################################################################################
def get_nc_data_variables(nc_dataset):
    """
    (object) -> dict

    Return: the netCDF Data variables
    """

    nc_non_data_variables_namelist = get_nc_variables_coordinate_type_mapping(nc_dataset).keys()

    nc_data_variables = {}
    for var_name, var_obj in nc_dataset.variables.items():
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


# Function for Grid Mapping Variable ###############################################################################
def get_nc_grid_mapping_variable_name(nc_dataset):
    """
    (object)-> string

    Return: the netCDF grid mapping variable name
    """
    nc_all_variables = nc_dataset.variables
    nc_grid_mapping_variable_name = ''
    for var_name, var_obj in nc_all_variables.items():
        if hasattr(var_obj, 'grid_mapping_name')and var_obj.grid_mapping_name:
            nc_grid_mapping_variable_name = var_name

    return nc_grid_mapping_variable_name


def get_nc_grid_mapping_variable(nc_dataset):
    """
    (object)-> object

    Return: the netCDF grid mapping variable object
    """

    nc_all_variables = nc_dataset.variables
    nc_grid_mapping_variable = None
    for var_name, var_obj in nc_all_variables.items():
        if hasattr(var_obj, 'grid_mapping_name'):
            nc_grid_mapping_variable = var_obj

    return nc_grid_mapping_variable


def get_nc_grid_mapping_projection_name(nc_dataset):
    """
    (object)-> string

    Return: the netCDF grid mapping projection name
    """

    nc_grid_mapping_variable = get_nc_grid_mapping_variable(nc_dataset)
    if nc_grid_mapping_variable is not None:
        nc_grid_mapping_projection_name = nc_grid_mapping_variable.grid_mapping_name
    else:
        nc_grid_mapping_projection_name = ''

    return nc_grid_mapping_projection_name


def get_nc_grid_mapping_projection_import_string(nc_dataset):
    """
    (object)-> string

    Return: the netCDF grid mapping proj4 string used for creating projection object with pyproj.Proj()
    Reference: Cf convention for grid mapping projection
    """
    # get the proj name, proj variable
    nc_grid_mapping_projection_name = get_nc_grid_mapping_projection_name(nc_dataset)
    nc_grid_mapping_projection_import_string = ''
    nc_grid_mapping_variable = get_nc_grid_mapping_variable(nc_dataset)

    # get the proj info from cf convention
    albers_conical_equal_area = OrderedDict([
        ('+proj=', 'aea'),
        ('+lat_1=', 'standard_parallel'),
        ('+lat_0=', 'latitude_of_projection_origin'),
        ('+lon_0=', 'longitude_of_central_meridian'),
        ('+x_0=', 'false_easting'),
        ('+y_0=','false_northing'),
    ])
    azimuthal_equidistant = OrderedDict([
        ('+proj=', 'aeqd'),
        ('+lat_0=', 'latitude_of_projection_origin'),
        ('+lon_0=', 'longitude_of_projection_origin'),
        ('+x_0=', 'false_easting'),
        ('+y_0=','false_northing'),
    ])
    lambert_azimuthal_equal_area = OrderedDict([
        ('+proj=', 'laea'),
        ('+lat_0=', 'latitude_of_projection_origin'),
        ('+lon_0=', 'longitude_of_projection_origin'),
        ('+x_0=', 'false_easting'),
        ('+y_0=', 'false_northing'),
    ])
    lambert_conformal_conic = OrderedDict([
        ('+proj=', 'lcc'),
        ('+lat_1=', 'standard_parallel'),
        ('+lat_0=', 'latitude_of_projection_origin'),
        ('+lon_0=', 'longitude_of_central_meridian'),
        ('+x_0=', 'false_easting'),
        ('+y_0=', 'false_northing'),
    ])  # tested with real nc file

    lambert_cylindrical_equal_area =OrderedDict([
        ('+proj=', 'cea'),
        ('+lat_ts=', 'scale_factor_at_projection_origin'),
        ('+lat_ts=', 'standard_parallel'),
        ('+lon_0=', 'longitude_of_projection_origin'),
        ('+x_0=', 'false_easting'),
        ('+y_0=', 'false_northing'),
    ])
    mercator = OrderedDict([
        ('+proj=', 'merc'),
        ('+k_0=', 'scale_factor_at_projection_origin'),
        ('+lat_ts=', 'standard_parallel'),
        ('+lon_0=', 'longitude_of_projection_origin'),
        ('+x_0=', 'false_easting'),
        ('+y_0=', 'false_northing'),
    ])
    orthographic = OrderedDict([
        ('+proj=', 'ortho'),
        ('+lat_0=', 'latitude_of_projection_origin'),
        ('+lon_0=', 'longitude_of_projection_origin'),
        ('+x_0=', 'false_easting'),
        ('+y_0=', 'false_northing'),
    ])
    polar_stereographic = OrderedDict([
        ('+proj=', 'stere'),
        ('+k_0=', 'scale_factor_at_projection_origin'),
        ('+lat_ts=', 'standard_parallel'),
        ('+lat_0=', 'latitude_of_projection_origin'),
        ('+lon_0=', 'straight_vertical_longitude_from_pole'),
        ('+x_0=', 'false_easting'),
        ('+y_0=', 'false_northing'),
    ])
    #rotated_latitude_longitude = {}
    stereographic = OrderedDict([
        ('+proj=', 'stere'),
        ('+lat_0=', 'latitude_of_projection_origin'),
        ('+lon_0=', 'longitude_of_projection_origin'),
        ('+x_0=', 'false_easting'),
        ('+y_0=', 'false_northing'),
    ])
    transverse_mercator = OrderedDict([
        ('+proj=', 'tmerc'),
        ('+k_0=', 'scale_factor_at_projection_origin'),
        ('+lat_0=', 'latitude_of_projection_origin'),
        ('+lon_0=', 'longitude_of_projection_origin'),
        ('+x_0=', 'false_easting'),
        ('+y_0=', 'false_northing'),
    ])
    vertical_perspective = OrderedDict([
        ('+proj=', 'geos'),
        ('+h=', 'perspective_point_height'),
        ('+lon_0=', 'longitude_of_projection_origin'),
        ('+x_0=', 'false_easting'),
        ('+y_0=', 'false_northing'),
    ])

    cf_convention_proj_info = {
        'albers_conical_equal_area': albers_conical_equal_area,
        'azimuthal_equidistant': azimuthal_equidistant,
        'lambert_azimuthal_equal_area': lambert_azimuthal_equal_area,
        'lambert_conformal_conic': lambert_conformal_conic,
        'lambert_cylindrical_equal_area': lambert_cylindrical_equal_area,
        'mercator': mercator,
        'orthographic': orthographic,
        'polar_stereographic': polar_stereographic,
        #'rotated_latitude_longitude': rotated_latitude_longitude,
        'stereographic': stereographic,
        'transverse_mercator': transverse_mercator,
        'vertical_perspective': vertical_perspective
    }

    # get the projection import string
    for proj_name, proj_para_dict in cf_convention_proj_info.items():
        if re.match(proj_name, nc_grid_mapping_projection_name, re.I):
            proj4_string = ''
            for para_name, para_value in proj_para_dict.items():
                if para_name == '+proj=':
                    proj4_string = proj4_string + '+proj=' + para_value
                elif hasattr(nc_grid_mapping_variable, para_value):
                    if para_name == '+lat_1=':
                        value = str(nc_grid_mapping_variable.standard_parallel).strip('[]').split()
                        if len(value) == 1:
                            proj4_string = proj4_string + ' +lat_1='+value[0]
                        elif len(value) == 2:
                            a = float(value[0])
                            b = float(value[1])
                            proj4_string = proj4_string + ' +lat_1='+str(min(a, b))+' +lat_2='+str(max(a, b))
                    else:
                        proj4_string = proj4_string + ' ' + para_name + str(getattr(nc_grid_mapping_variable, para_value))
                else:
                    proj4_string = ''
                    break

            if proj4_string != '':
                nc_grid_mapping_projection_import_string = proj4_string

            break

    return nc_grid_mapping_projection_import_string










