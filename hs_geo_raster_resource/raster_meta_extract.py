"""
Module extracting metadata from raster file to complete part of the required HydroShare Raster Science Metadata.
The expected metadata elements are defined in the HydroShare raster resource specification.
"""
__author__ = 'Tian Gan'


import gdal
from gdalconst import *
from osgeo import osr
import json
from collections import OrderedDict


def get_raster_meta_json(raster_file_name):
    """
    (string)-> json string

    Return: the raster science metadata extracted from the raster file
    """

    raster_meta_dict = get_raster_meta_dict(raster_file_name)
    raster_meta_json = json.dumps(raster_meta_dict)
    return raster_meta_json


def get_raster_meta_dict(raster_file_name):
    """
    (string)-> dict

    Return: the raster science metadata extracted from the raster file
    """

    # get the raster dataset
    raster_dataset = gdal.Open(raster_file_name, GA_ReadOnly)

    # get the metadata info from raster dataset
    spatial_coverage_info = get_spatial_coverage_info(raster_dataset)
    cell_and_band_info = get_cell_and_band_info(raster_dataset)

    # write meta as dictionary
    raster_meta_dict = {
        'spatial_coverage_info': spatial_coverage_info,
        'cell_and_band_info': cell_and_band_info,
    }

    return raster_meta_dict


def get_spatial_coverage_info(raster_dataset):
    """
    (object) --> dict

    Return: meta of spatial extent and projection of raster
    """

    # get horizontal projection and unit info
    proj_wkt = raster_dataset.GetProjection()
    if proj_wkt:
        spatial_ref = osr.SpatialReference()
        spatial_ref.ImportFromWkt(proj_wkt)
        unit = spatial_ref.GetAttrValue("UNIT", 0)
        projection = spatial_ref.GetAttrValue("PROJECTION", 0) if spatial_ref.GetAttrValue("PROJECTION", 0) \
            else spatial_ref.GetAttrValue("DATUM", 0)
    else:
        unit = ''
        projection = ''

    # get the bounding box
    gt = raster_dataset.GetGeoTransform()
    cols = raster_dataset.RasterXSize
    rows = raster_dataset.RasterYSize
    xarr = [0, cols]
    yarr = [0, rows]
    x_coor = []
    y_coor = []
    for px in xarr:
        for py in yarr:
            x = gt[0]+(px*gt[1])+(py*gt[2])
            y = gt[3]+(px*gt[4])+(py*gt[5])
            x_coor.append(x)
            y_coor.append(y)
        yarr.reverse()
    northlimit = max(y_coor)  # max y
    southlimit = min(y_coor)
    westlimit = min(x_coor)  # min x
    eastlimit = max(x_coor)

    spatial_coverage_info = OrderedDict()
    spatial_coverage_info['name'] ="Raster coverage"
    spatial_coverage_info['projection'] =projection
    spatial_coverage_info['unit'] =unit
    spatial_coverage_info['northlimit'] =northlimit
    spatial_coverage_info['southlimit'] =southlimit
    spatial_coverage_info['eastlimit'] =northlimit
    spatial_coverage_info['westlimit'] =southlimit

    return spatial_coverage_info


def get_cell_and_band_info(raster_dataset):
    """
    (object) --> dict

    Return: meta info of cells in raster
    """
    # get cell size info
    rows = raster_dataset.RasterYSize
    columns = raster_dataset.RasterXSize
    cell_size_x_value = raster_dataset.GetGeoTransform()[1]
    cell_size_y_value = abs(raster_dataset.GetGeoTransform()[5])


    # get coordinate system unit info
    proj_wkt = raster_dataset.GetProjection()
    if proj_wkt:
        spatial_ref = osr.SpatialReference()
        spatial_ref.ImportFromWkt(proj_wkt)
        cell_size_unit = spatial_ref.GetAttrValue("UNIT", 0)
    else:
        cell_size_unit = ''

    # get band count, cell no data value, cell data type
    band_count = raster_dataset.RasterCount
    band = raster_dataset.GetRasterBand(1)
    no_data_value = band.GetNoDataValue()
    cell_data_type = gdal.GetDataTypeName(band.DataType)

    cell_and_band_info = OrderedDict()
    cell_and_band_info['rows'] =rows
    cell_and_band_info['columns'] =columns
    cell_and_band_info['cellSizeXValue'] =cell_size_x_value
    cell_and_band_info['cellSizeYValue'] =cell_size_y_value
    cell_and_band_info['cellSizeUnit'] =cell_size_unit
    cell_and_band_info['cellDataType'] =cell_data_type
    cell_and_band_info['cellNoDataValue'] =no_data_value
    cell_and_band_info['bandCount'] =band_count
    return cell_and_band_info




