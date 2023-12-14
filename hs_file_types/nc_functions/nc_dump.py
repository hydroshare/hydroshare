"""
Module used to get the header info of netcdf file

WORKFLOW:
There are two ways to get the netcdf header string.
1) method1 run ncdump -h by python subprocess module: get_nc_dump_string_by_ncdump()
2) method2 use the netCDF4 python lib to look into the netcdf to extract the the header info:
   get_nc_dump_string()
3) get_netcdf_header_file() will try the first method and if it fails it will call the second method

NOTES:
1) make sure the 'ncdump' is registered by the system path. otherwise suprocess won't recoganize
   the ncdump command

REF
ncdump c code:
    http://www.unidata.ucar.edu/software/netcdf/docs/ncdump_8c_source.html
json dump dict in pretty format:
    http://stackoverflow.com/questions/3229419/pretty-printing-nested-dictionaries-in-python
subprocess call:
    https://docs.python.org/2/library/subprocess.html
    http://stackoverflow.com/questions/923079/how-can-i-capture-the-stdout-output-of-a-child
    -process/923108#923108
"""

from collections import OrderedDict
from os.path import basename
import os
import json
import subprocess

import netCDF4
from .nc_utils import get_nc_dataset


def get_netcdf_header_file(nc_file_name, dump_folder=''):
    """
    (string,string) -> file

    Return: given the full netcdf file path name, return text file for the netcdf header information
    """

    # create a new text file
    # name with no file extension
    nc_file_basename = '.'.join(basename(nc_file_name).split('.')[:-1])
    nc_dump_file_folder = dump_folder if dump_folder else os.getcwd()
    nc_dump_file_name = nc_dump_file_folder + '/' + nc_file_basename + '_header_info.txt'
    nc_dump_file = open(nc_dump_file_name, 'w')

    # write the nc_dump string in text fle
    dump_string = get_nc_dump_string_by_ncdump(nc_file_name) \
        if get_nc_dump_string_by_ncdump(nc_file_name) else get_nc_dump_string(nc_file_name)
    if dump_string:
        nc_dump_file.write(dump_string)


def get_nc_dump_string_by_ncdump(nc_file_name):
    """
    (string) -> string

    Return: string create by running "ncdump -h" command for netcdf file.
    """

    try:
        process = subprocess.Popen(['ncdump', '-h', nc_file_name], stdout=subprocess.PIPE, encoding="UTF-8")
        nc_dump_string = process.communicate()[0]
    except Exception:
        nc_dump_string = ''

    return nc_dump_string


def get_nc_dump_string(nc_file_name):
    """
    (string) -> string

    Return: string created by python netCDF4 lib similar as the "ncdump -h" command for netcdf file.
    """
    try:
        nc_dataset = get_nc_dataset(nc_file_name)
        nc_file_basename = '.'.join(basename(nc_file_name).split('.')[:-1])
        nc_dump_dict = get_nc_dump_dict(nc_dataset)
        if nc_dump_dict:
            nc_dump_string = 'netcdf {0} \n'.format(nc_file_basename)
            nc_dump_string += json.dumps(nc_dump_dict, indent=4)
        else:
            nc_dump_string = ''
    except Exception:
        nc_dump_string = ''

    return nc_dump_string


def get_nc_dump_dict(nc_group):
    """
    (obj) -> dict

    Return: Dictionary storing the header information of netcdf similar as running 'ncdump -h'
    """
    info = OrderedDict()
    if isinstance(nc_group, netCDF4.Dataset):
        if get_dimensions_info(nc_group):
            info['dimensions'] = get_dimensions_info(nc_group)
        if get_variables_info(nc_group):
            info['variables'] = get_variables_info(nc_group)
        if get_global_attr_info(nc_group):
            info['global attributes'] = get_global_attr_info(nc_group)

        if nc_group.groups:
            for group_name, group_obj in list(nc_group.groups.items()):
                try:
                    info['group: ' + group_name] = get_nc_dump_dict(group_obj)
                except Exception:
                    continue

    return info


def get_dimensions_info(nc_group):
    """
    (obj) -> dict

    Return: Dimension info of a netcdf group object.
    """

    dimensions_info = OrderedDict()
    for dim_name, dim_obj in list(nc_group.dimensions.items()):
        try:
            if dim_obj.isunlimited():
                dimensions_info[dim_name] = 'UNLIMITED; // ({0} currently)'.format(len(dim_obj))
            else:
                dimensions_info[dim_name] = len(dim_obj)
        except: # noqa
            continue

    return dimensions_info


def get_global_attr_info(nc_group):
    """
    (obj) -> dict

    Return: global attribute info of a netcdf group object.
    """
    global_attr_info = OrderedDict()
    if nc_group.__dict__:
        for name, val in list(nc_group.__dict__.items()):
            value = str(val).split('\n') if '\n' in str(val) else str(val)
            global_attr_info[name] = value

    return global_attr_info


def get_variables_info(nc_group):
    """
    (obj) -> dict

    Return: global attribute info of a netcdf group object.
    """
    variables_info = OrderedDict()
    if nc_group.variables:
        for var_name, var_obj in list(nc_group.variables.items()):
            try:
                if isinstance(var_obj.datatype, netCDF4.CompoundType):
                    var_type = 'compound'
                elif isinstance(var_obj.datatype, netCDF4.VLType):
                    var_type = 'variable length'
                else:
                    var_type = var_obj.datatype.name
                var_dimensions = '({0})'.format(','.join(var_obj.dimensions).encode())
                var_title = '{0} {1}{2}'.format(var_type, var_name, var_dimensions)
                variables_info[var_title] = OrderedDict()
                for name, val in list(var_obj.__dict__.items()):
                    value = str(val).split('\n') if '\n' in str(val) else str(val)
                    variables_info[var_title][name] = value
            except Exception:
                continue

    return variables_info
