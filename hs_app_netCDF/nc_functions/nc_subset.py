"""
module used to extract data of a netCDF variable based on subset information.

Subset WorkFlow:
1 User gives a netcdf file name -> show data variables list
2 User gives a variable name for subset -> check variable subset availability. If yes, show all dimensions data values
3 Choose the dimension values (start, end) -> check the dimension value (start <= end)(js check).
                                              If yes, create subset netcdf file

"""

__author__ = 'Tian Gan'

from nc_utils import *
from datetime import datetime

nc_subset_info = {
    'file_name': 'sample1.nc',
    'var_name': 'pr',
    'lon': [0, 0],
    'lat': [0, 6],
    'time': [0, 0],
    }

nc_subset_info = {
    'file_name': 'prcp.nc',
    'var_name': 'prcp',
    'x': [0, 3],
    'y': [0, 6],
    'time': [0, 1],
    } # has time bounds and grid mapping

nc_subset_info = {
    'file_name': 'rtof.nc',
    'var_name': 'salinity',
    'MT': [0, 0],
    'Depth': [2, 2],
    'Y': [0, 5],
    'X': [0, 5]
    }


# Functions for Creating subset info ###################################################################################
def get_nc_data_variable_names(nc_file_name):
    """
    (string) -> list

    Return: netcdf data variable names
    """
    nc_dataset = get_nc_dataset(nc_file_name)
    nc_data_variable_names = get_nc_data_variable_namelist(nc_dataset)

    return nc_data_variable_names


def check_nc_variable_for_subset(nc_file_name, nc_var_name):
    """
    (string, string) -> bool

    Return: True if the variable is available for subsetting
    """
    nc_dataset = get_nc_dataset(nc_file_name)
    nc_variable = get_nc_variable(nc_dataset, nc_var_name)
    if nc_variable and set(nc_variable.dimensions).issubset(nc_dataset.dimensions.keys()):
        check_file = True
    else:
        check_file = False

    return check_file


def get_nc_variable_dimensions_value(nc_file_name, nc_var_name):
    """
    (string,string) -> Dict

    Return: dimension values for each dimension of the variable
    """
    nc_variable_dimensions_value = OrderedDict()
    nc_dataset = get_nc_dataset(nc_file_name)
    nc_variable = get_nc_variable(nc_dataset, nc_var_name)
    nc_coordinate_variable_namelist = get_nc_coordinate_variable_namelist(nc_dataset)

    for var_dim_name in nc_variable.dimensions:
        if var_dim_name in nc_coordinate_variable_namelist:
            dim_var = nc_dataset.variables[var_dim_name]
            dim_values = dim_var[:].tolist()
            dim_coor_type = get_nc_variable_coordinate_type(dim_var)
            if dim_coor_type == 'T':
                time_units = dim_var.units if hasattr(dim_var, 'units') else ''
                time_calendar = dim_var.calendar if hasattr(dim_var, 'calendar') else 'standard'
                if time_units and time_calendar:
                    try:
                        for i in range(0, len(dim_values)):
                            dim_values[i] = netCDF4.num2date(dim_values[i], units=time_units, calendar=time_calendar)
                    except:
                        pass
        else:
            dim_values = range(1, len(nc_dataset.dimensions[var_dim_name])+1)

        nc_variable_dimensions_value[var_dim_name] = [str(i) for i in dim_values]

    return nc_variable_dimensions_value


# Functions for Creating subset Netcdf file ############################################################################
def create_subset_nc_file(nc_subset_info):
    """
    (dict) -> file

    Return: data subset netCDF file based on the subset info and the original netCDF file
            the netCDF must follow the CF convention otherwise it won't work well

    """

    # define nc_rootgroup
    nc_rootgroup = define_nc_rootgroup(nc_subset_info)

    # define dimensions
    nc_rootgroup = define_nc_dimensions(nc_rootgroup, nc_subset_info)

    # define coordinate variable
    nc_rootgroup = define_nc_coordinate_variables(nc_rootgroup, nc_subset_info)

    # define data variable
    nc_rootgroup = define_nc_data_variable(nc_rootgroup, nc_subset_info)

    # define grid mapping variable
    nc_rootgroup = define_nc_grid_mapping_variable(nc_rootgroup, nc_subset_info)

    # define auxiliary coordinate variable
    nc_rootgroup = define_auxiliary_coordinate_variable(nc_rootgroup, nc_subset_info)

    # define bounds variable
    nc_rootgroup = define_coordinate_bounds_variable(nc_rootgroup, nc_subset_info)

    nc_rootgroup.close()

    return nc_rootgroup


#  define nc_rootgroup ##############################################################################
def define_nc_rootgroup(nc_subset_info):
    nc_global_attributes = get_nc_global_attributes(nc_subset_info)
    nc_rootgroup = create_nc_rootgroup(nc_global_attributes)

    return nc_rootgroup


def get_nc_global_attributes(nc_subset_info):
    # copy all global attribute info from original file
    nc_dataset = get_nc_dataset(nc_subset_info['file_name'])
    nc_global_attributes = {}
    for attr_name, attr_info in nc_dataset.__dict__.items():
        if isinstance(attr_info, basestring):
            nc_global_attributes[attr_name] = attr_info

    # add format and name info
    nc_global_attributes['file_format'] = nc_dataset.file_format
    nc_global_attributes['file_name'] = nc_subset_info['file_name']

    # add or modify the history info
    new_history = u'\n {0}: subset of "{1}" variable from the original netCDF data by HydroShare website.'\
        .format(datetime.now().strftime('%a %b %d %X %Y'), nc_subset_info['var_name'])
    if nc_global_attributes.has_key('history'):
        nc_global_attributes['history'] += new_history
    else:
        nc_global_attributes['history'] = new_history

    nc_dataset.close()
    return nc_global_attributes


def create_nc_rootgroup(nc_global_attributes):
    # initiate a rootgroup
    file_name = 'subset_' + nc_global_attributes.pop('file_name')
    file_format = nc_global_attributes.pop('file_format')
    nc_rootgroup = netCDF4.Dataset(file_name, 'w', format=file_format)

    # add global attributes
    for attr_name, attr_info in nc_global_attributes.items():
        nc_rootgroup.__setattr__(attr_name, attr_info)

    return nc_rootgroup


# define dimensions ##################################################################################
def define_nc_dimensions(nc_rootgroup, nc_subset_info):
    nc_dimension_info = get_nc_dimension_info(nc_subset_info)
    nc_rootgroup = create_nc_dimensions(nc_rootgroup, nc_dimension_info)

    return nc_rootgroup


def get_nc_dimension_info(nc_subset_info):
    nc_dataset = get_nc_dataset(nc_subset_info['file_name'])
    nc_dimensions = nc_dataset.dimensions
    nc_dimension_info = OrderedDict([])

    for dim_name, dim_obj in nc_dimensions.items():
        if nc_subset_info.has_key(dim_name):
            if dim_obj.isunlimited():
                nc_dimension_info[dim_name] = None
            else:
                nc_dimension_info[dim_name] = nc_subset_info[dim_name][1]-nc_subset_info[dim_name][0]+1

    nc_dataset.close()
    return nc_dimension_info


def create_nc_dimensions(nc_rootgroup, nc_dimension_info):
    for dim_name, dim_len in nc_dimension_info.items():
        nc_rootgroup.createDimension(dim_name, dim_len)

    return nc_rootgroup


# define coordinate variables ###############################################################################
def define_nc_coordinate_variables(nc_rootgroup, nc_subset_info):

    # find out dimension corresponding coordinate variable name
    nc_dataset = get_nc_dataset(nc_subset_info['file_name'])
    nc_dimensions = nc_dataset.variables[nc_subset_info['var_name']].dimensions
    nc_all_variables = nc_dataset.variables
    nc_dim_coor_mapping = {}
    for var_name, var_obj in nc_all_variables.items():
        if len(var_obj.shape) == 1 and var_name == var_obj.dimensions[0]:
            nc_dim_coor_mapping[var_obj.dimensions[0]] = var_name

    # add coordinate variable info
    for dim_name, coor_var_name in nc_dim_coor_mapping.items():
        coor_var = nc_dataset.variables[coor_var_name]
        # initiate coordinate variable
        nc_rootgroup.createVariable(coor_var_name, coor_var.dtype, (dim_name,))
        # copy coordinate attributes
        for attr_name, attr_info in coor_var.__dict__.items():
            nc_rootgroup.variables[coor_var_name].__setattr__(attr_name, attr_info)
        # assign coordinate subset value
        slice_start = nc_subset_info[dim_name][0]
        slice_end = nc_subset_info[dim_name][1]
        slice_obj = slice(slice_start, slice_end+1, 1)
        subset_data = coor_var[:][slice_obj]
        nc_rootgroup.variables[coor_var_name][:] = subset_data

    return nc_rootgroup


# define data variable #######################################################################################
def define_nc_data_variable(nc_rootgroup, nc_subset_info):
    nc_dataset = get_nc_dataset(nc_subset_info['file_name'])
    nc_variable_name = nc_subset_info['var_name']
    nc_variable = nc_dataset.variables[nc_variable_name]

    # initiate coordinate variable
    nc_rootgroup.createVariable(nc_variable_name, nc_variable.dtype,
                                nc_variable.dimensions,
                                fill_value=nc_variable._FillValue if hasattr(nc_variable, '_FillValue')else None)
    # copy coordinate attributes
    for attr_name, attr_info in nc_variable.__dict__.items():
        if attr_name != '_FillValue':
            nc_rootgroup.variables[nc_variable_name].__setattr__(attr_name, attr_info)
    # assign data variable value
    nc_variable_data = nc_variable[:]
    nc_variable_dimension_namelist = nc_variable.dimensions
    slice_obj = []
    for dim_name in nc_variable_dimension_namelist:
        slice_start = nc_subset_info[dim_name][0]
        slice_end = nc_subset_info[dim_name][1]
        slice_obj.append(slice(slice_start, slice_end+1, 1))
    subset_data = nc_variable_data[tuple(slice_obj)]
    nc_rootgroup.variables[nc_variable_name][:] = subset_data

    return nc_rootgroup


# define grid mapping variable ###################################################################################
def define_nc_grid_mapping_variable(nc_rootgroup, nc_subset_info):
    nc_dataset = get_nc_dataset(nc_subset_info['file_name'])
    nc_grid_mapping_variable_name = get_nc_grid_mapping_variable_name(nc_dataset)
    if nc_grid_mapping_variable_name:
        nc_grid_mapping_variable = get_nc_grid_mapping_variable(nc_dataset)
        # initiate grid mappping variable variable
        nc_rootgroup.createVariable(nc_grid_mapping_variable_name, nc_grid_mapping_variable.dtype)
        # copy grid mappping variable attributes
        for attr_name, attr_info in nc_grid_mapping_variable .__dict__.items():
            nc_rootgroup.variables[nc_grid_mapping_variable_name].__setattr__(attr_name, attr_info)

    return nc_rootgroup


# define auxiliary coordinate variable for data variable ##########################################################
def define_auxiliary_coordinate_variable(nc_rootgroup, nc_subset_info):
    nc_dataset = get_nc_dataset(nc_subset_info['file_name'])
    nc_auxiliary_coordinate_variables = get_nc_auxiliary_coordinate_variables(nc_dataset)
    if nc_auxiliary_coordinate_variables:
        for nc_variable_name, nc_variable in nc_auxiliary_coordinate_variables.items():
            nc_variable_dimension_namelist = nc_variable.dimensions
            if set(nc_variable_dimension_namelist).issubset(nc_subset_info.keys()):
                # initiate coordinate variable
                nc_rootgroup.createVariable(nc_variable_name, nc_variable.dtype,
                                            nc_variable.dimensions,
                                            fill_value=nc_variable._FillValue if hasattr(nc_variable, '_FillValue')else None)
                # copy coordinate attributes
                for attr_name, attr_info in nc_variable.__dict__.items():
                    if attr_name != '_FillValue':
                        nc_rootgroup.variables[nc_variable_name].__setattr__(attr_name, attr_info)
                # assign data variable value
                nc_variable_data = nc_variable[:]
                slice_obj = []
                for dim_name in nc_variable_dimension_namelist:
                    slice_start = nc_subset_info[dim_name][0]
                    slice_end = nc_subset_info[dim_name][1]
                    slice_obj.append(slice(slice_start, slice_end+1, 1))
                    subset_data = nc_variable_data[tuple(slice_obj)]
                nc_rootgroup.variables[nc_variable_name][:] = subset_data

    return nc_rootgroup


# define coordinate bounds variable ####################################################################################
def define_coordinate_bounds_variable(nc_rootgroup, nc_subset_info):
    nc_dataset = get_nc_dataset(nc_subset_info['file_name'])
    nc_coordinate_bounds_variables = get_nc_coordinate_bounds_variables(nc_dataset)
    if nc_coordinate_bounds_variables:
        for nc_variable_name, nc_variable in nc_coordinate_bounds_variables.items():

            # define the dimension variable if this is not defined before
            nc_variable_dimension_namelist = nc_variable.dimensions
            nc_rootgroup_dimension_namelist = nc_rootgroup.dimensions
            for var_dim in nc_variable_dimension_namelist:
                if var_dim not in nc_rootgroup_dimension_namelist:
                    dim_len = len(nc_dataset.dimensions.get(var_dim, []))
                    if dim_len:
                        nc_rootgroup.createDimension(var_dim, dim_len)
                    else:
                        return nc_rootgroup

            # define the bounds variable
            if set(nc_variable_dimension_namelist).issubset(nc_rootgroup.dimensions.keys()):
                # initiate coordinate variable
                nc_rootgroup.createVariable(nc_variable_name, nc_variable.dtype,
                                            nc_variable.dimensions,
                                            fill_value=nc_variable._FillValue if hasattr(nc_variable, '_FillValue')else None)
                # copy coordinate attributes
                for attr_name, attr_info in nc_variable.__dict__.items():
                    if attr_name != '_FillValue':
                        nc_rootgroup.variables[nc_variable_name].__setattr__(attr_name, attr_info)
                # assign data variable value
                nc_variable_data = nc_variable[:]
                slice_obj = []
                for dim_name in nc_variable_dimension_namelist:
                    if dim_name in nc_subset_info.keys():
                        slice_start = nc_subset_info[dim_name][0]
                        slice_end = nc_subset_info[dim_name][1]
                        slice_obj.append(slice(slice_start, slice_end+1, 1))
                    else:
                        slice_start = 0
                        slice_end = len(nc_rootgroup.dimensions[dim_name])
                        slice_obj.append(slice(slice_start, slice_end, 1))
                    subset_data = nc_variable_data[tuple(slice_obj)]
                nc_rootgroup.variables[nc_variable_name][:] = subset_data
    return nc_rootgroup