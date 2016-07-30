"""
Module extracting metadata from raster file to complete part of the required HydroShare Raster Science Metadata.
The expected metadata elements are defined in the HydroShare raster resource specification.
Reference code:
http://gis.stackexchange.com/questions/6669/converting-projected-geotiff-to-wgs84-with-gdal-and-python
http://gis.stackexchange.com/questions/57834/how-to-get-raster-corner-coordinates-using-python-gdal-bindings

Update Notes
This is used to process the vrt raster and to extract max, min value of each raster band.
"""


import gdal
from gdalconst import *
from osgeo import osr
from collections import OrderedDict
import re
import logging
import pycrs
import numpy


def get_raster_meta_dict(raster_file_name):
    """
    (string)-> dict

    Return: the raster science metadata extracted from the raster file
    """

    # get the metadata info from raster files
    spatial_coverage_info = get_spatial_coverage_info(raster_file_name)
    cell_info = get_cell_info(raster_file_name)
    band_info = get_band_info(raster_file_name)

    # write meta as dictionary
    raster_meta_dict = {
        'spatial_coverage_info': spatial_coverage_info,
        'cell_info': cell_info,
        'band_info': band_info,
    }

    return raster_meta_dict


def get_spatial_coverage_info(raster_file_name):
    """
    (string) --> dict

    Return: meta of spatial extent and projection of raster includes both original info and wgs84 info
    """
    raster_dataset = gdal.Open(raster_file_name, GA_ReadOnly)
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
    try:
        proj_wkt = raster_dataset.GetProjection()
    except Exception as ex:
        # an exception occurs when doing GetGeoTransform, which means an invalid geotiff is uploaded, print exception
        # to log without blocking the main resource creation workflow since we allow user to upload a tiff file without valid tags
        log = logging.getLogger()
        log.exception(ex.message)
        proj_wkt = None

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
        unit = None
        projection = None

    # get the bounding box
    try:
        gt = raster_dataset.GetGeoTransform()
    except Exception as ex:
        # an exception occurs when doing GetGeoTransform, which means an invalid geotiff is uploaded, print exception
        # to log without blocking the main resource creation workflow since we allow user to upload a tiff file without valid tags
        log = logging.getLogger()
        log.exception(ex.message)
        gt = None

    if gt and proj_wkt:  # only get the bounding box when the projection is defined
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
        northlimit = None
        southlimit = None
        westlimit = None
        eastlimit = None

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
    try:
        proj = raster_dataset.GetProjection()
    except Exception as ex:
        # an exception occurs when doing GetGeoTransform, which means an invalid geotiff is uploaded, print exception
        # to log without blocking the main resource creation workflow since we allow user to upload a tiff file without valid tags
        log = logging.getLogger()
        log.exception(ex.message)
        proj = None

    wgs84_coverage_info = OrderedDict()
    original_coverage_info = get_original_coverage_info(raster_dataset)

    if proj and (None not in original_coverage_info.values()):

        original_cs = osr.SpatialReference()

        try:
            ogc_wkt = pycrs.parser.from_unknown_wkt(proj).to_ogc_wkt()
            original_cs.ImportFromWkt(ogc_wkt)

        except Exception:
            original_cs.ImportFromWkt(proj)

        # create wgs84 geographic coordinate system
        wgs84_cs = osr.SpatialReference()
        wgs84_cs.ImportFromEPSG(4326)

        # get original bounding box info
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


def get_cell_info(raster_file_name):
    """
    (object) --> dict

    Return: meta info of cells in raster
    """

    raster_dataset = gdal.Open(raster_file_name, GA_ReadOnly)

    # get cell size info
    if raster_dataset:
        rows = raster_dataset.RasterYSize
        columns = raster_dataset.RasterXSize
        proj_wkt = raster_dataset.GetProjection()
        cell_size_x_value = raster_dataset.GetGeoTransform()[1] if proj_wkt else 0
        cell_size_y_value = abs(raster_dataset.GetGeoTransform()[5]) if proj_wkt else 0
        band = raster_dataset.GetRasterBand(1)
        cell_data_type = gdal.GetDataTypeName(band.DataType)

        cell_info = OrderedDict([
            ('rows', rows),
            ('columns', columns),
            ('cellSizeXValue', cell_size_x_value),
            ('cellSizeYValue', cell_size_y_value),
            ('cellDataType', cell_data_type),

        ])
    else:
        cell_info = OrderedDict([
            ('rows', None),
            ('columns', None),
            ('cellSizeXValue', None),
            ('cellSizeYValue', None),
            ('cellDataType', None),
        ])

    return cell_info


def get_band_info(raster_file_name):

    raster_dataset = gdal.Open(raster_file_name, GA_ReadOnly)

    import os
    ori_dir = os.getcwd()
    os.chdir(os.path.dirname(raster_file_name))

    # get raster band count
    if raster_dataset:
        band_info = {}
        band_count = raster_dataset.RasterCount

        for i in range(0, band_count):
            band = raster_dataset.GetRasterBand(i+1)
            minimum, maximum, _, _ = band.ComputeStatistics(False)
            no_data = band.GetNoDataValue()
            new_no_data = None

            if numpy.allclose(minimum, no_data):
                new_no_data = minimum
            elif numpy.allclose(maximum, no_data):
                new_no_data = maximum

            if new_no_data:
                band.SetNoDataValue(new_no_data)
                minimum, maximum, _, _ = band.ComputeStatistics(False)

            band_info[i+1] = {
                'name': 'Band_'+str(i+1),
                'variableName': '',
                'variableUnit': band.GetUnitType(),
                'noDataValue': band.GetNoDataValue(),
                'maximumValue': maximum,
                'minimumValue': minimum,
                }
    else:
        band_info = {
                'name': 'Band_1',
                'variableName': '',
                'variableUnit': '',
                'noDataValue': None,
                'maximumValue': None,
                'minimumValue': None,
        }

    raster_dataset = None
    os.chdir(ori_dir)

    return band_info


