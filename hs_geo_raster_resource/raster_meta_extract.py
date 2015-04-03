"""
Module extracting metadata from raster file to complete part of the required HydroShare Raster Science Metadata.
The expected metadata elements are defined in the HydroShare raster resource specification.
Reference code:
http://gis.stackexchange.com/questions/6669/converting-projected-geotiff-to-wgs84-with-gdal-and-python
http://gis.stackexchange.com/questions/57834/how-to-get-raster-corner-coordinates-using-python-gdal-bindings
"""

__author__ = 'Tian Gan'


import gdal
from gdalconst import *
from osgeo import osr
import json
from collections import OrderedDict
import re

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

    Return: meta of spatial extent and projection of raster includes both original info and wgs84 info
    """

    original_coverage_info = get_original_coverage_info(raster_dataset)
    wgs84_coverage_info = get_wgs84_coverage_info(raster_dataset)
    spatial_coverage_info = {
        'original_coverage_info': original_coverage_info,
        'wgs84_coverage_info': wgs84_coverage_info
    }
    return spatial_coverage_info

def get_original_coverage_info(raster_dataset):
    """
    (object) --> dict
    Return: meta of original projection and spatial extent of raster
    """
    # get horizontal projection and unit info
    proj_wkt = raster_dataset.GetProjection()
    if proj_wkt:
        spatial_ref = osr.SpatialReference()
        spatial_ref.ImportFromWkt(proj_wkt)

        # get unit info and check spelling
        unit = spatial_ref.GetAttrValue("UNIT", 0)
        if re.match('metre', unit, re.I):
            unit = 'meter'

        # get projection info
        if spatial_ref.GetAttrValue('PROJCS'):
            proj = spatial_ref.GetAttrValue("PROJECTION", 0) if spatial_ref.GetAttrValue("PROJECTION", 0) else ''
            projection = spatial_ref.GetAttrValue("PROJCS", 0) + ' ' + proj
        else:
            datum = spatial_ref.GetAttrValue("GEOGCS", 0) if spatial_ref.GetAttrValue("DATUM", 0) else ''
            proj = spatial_ref.GetAttrValue("PROJECTION", 0) if spatial_ref.GetAttrValue("PROJECTION", 0) else ''
            projection = datum + ' '+proj
    else:
        unit = 'Unnamed'
        projection = 'Unnamed'

    # get the bounding box
    gt = raster_dataset.GetGeoTransform()
    if gt:
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
    else:
        northlimit = 0
        southlimit = 0
        westlimit = 0
        eastlimit = 0

    spatial_coverage_info = OrderedDict([
        ('northlimit', northlimit),
        ('southlimit', southlimit),
        ('eastlimit', eastlimit),
        ('westlimit', westlimit),
        ('projection', projection),
        ('units', unit)
    ])

    return spatial_coverage_info

def get_wgs84_coverage_info(raster_dataset):
    """
    (object) --> dict
    Return: meta of spatial extent as wgs84 geographic coordinate system of raster
    """
    # get original coordinate system
    original_cs = osr.SpatialReference()
    original_cs.ImportFromWkt(raster_dataset.GetProjection())

    # create wgs84 geographic coordinate system
    wgs84_cs = osr.SpatialReference()
    wgs84_cs.ImportFromEPSG(4326)

    # get original bounding box info
    original_coverage_info = get_original_coverage_info(raster_dataset)
    original_northlimit = original_coverage_info['northlimit']
    original_southlimit = original_coverage_info['southlimit']
    original_westlimit = original_coverage_info['westlimit']
    original_eastlimit = original_coverage_info['eastlimit']

    # create transform object
    transform = osr.CoordinateTransformation(original_cs, wgs84_cs)
    if transform.this is not None:
        # transform original bounding box to wgs84 bounding box
        wgs84_westlimit,wgs84_northlimit = transform.TransformPoint(original_westlimit, original_northlimit)[:2]
        wgs84_eastlimit,wgs84_southlimit = transform.TransformPoint(original_eastlimit, original_southlimit)[:2]

        wgs84_coverage_info = OrderedDict([
            ('northlimit', wgs84_northlimit),
            ('southlimit', wgs84_southlimit),
            ('eastlimit', wgs84_eastlimit),
            ('westlimit', wgs84_westlimit),
            ('units','Decimal degrees'),
            ('projection', 'WGS 84 EPSG:4326')
        ])
        return wgs84_coverage_info
    else:
        return None

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
        if re.match('metre', cell_size_unit, re.I):
            cell_size_unit = 'meter'
    else:
        cell_size_unit = 'Unnamed'

    # get band count, cell no data value, cell data type
    band_count = raster_dataset.RasterCount
    band = raster_dataset.GetRasterBand(1)
    no_data_value = band.GetNoDataValue()
    cell_data_type = gdal.GetDataTypeName(band.DataType)

    cell_and_band_info = OrderedDict([
        ('rows', rows),
        ('columns', columns),
        ('cellSizeXValue', cell_size_x_value),
        ('cellSizeYValue', cell_size_y_value),
        ('cellSizeUnit', cell_size_unit),
        ('cellDataType', cell_data_type),
        ('noDataValue', no_data_value),
        ('bandCount', band_count)
    ])

    return cell_and_band_info




