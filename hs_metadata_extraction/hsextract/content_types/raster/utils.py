import os
import re
import tempfile
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path

import numpy
from osgeo import gdal, osr
from osgeo.gdalconst import GA_ReadOnly
from pycrs.parse import from_unknown_wkt
from hsextract import s3_client as s3


def extract_from_tif_file(tif_file):
    temp_dir = tempfile.gettempdir()
    local_copy = os.path.join(temp_dir, os.path.basename(tif_file))
    s3.get_file(tif_file, local_copy)

    ext = os.path.splitext(tif_file)[1]
    full_path = os.path.dirname(tif_file)
    if ext != ".vrt":
        filename = create_vrt_file(local_copy)
        #s3.put_file(filename, os.path.join(full_path, filename))
        tif_files = [local_copy]
    else:
        filename = local_copy
        tif_files = list_tif_files(filename)
        tif_files = [os.path.join(full_path, f)
                     for f in tif_files] + [tif_file]
    # file validation and metadaadatta extraction
    file_type_metadata = extract_metadata_from_vrt(filename)
    file_type_metadata["content_files"] = tif_files

    return file_type_metadata


def create_vrt_file(tif_file):
    """tif_file exists in temp directory - retrieved from irods"""

    # create vrt file
    temp_dir = tempfile.gettempdir()
    tif_file_name = os.path.basename(tif_file)
    vrt_file_path = os.path.join(temp_dir, f'{tif_file_name}.vrt')
    # os.mknod(vrt_file_path)
    input_file = gdal.Open(tif_file)
    output_file = gdal.Translate(vrt_file_path, input_file, format="VRT")

    # edit VRT contents
    tree = ET.parse(vrt_file_path)
    root = tree.getroot()
    for element in root.iter('SourceFilename'):
        element.text = tif_file_name
        element.attrib['relativeToVRT'] = '1'

    tree.write(vrt_file_path)

    return vrt_file_path


def extract_metadata_from_vrt(vrt_file_path):
    metadata = []
    res_md_dict = get_raster_meta_dict(vrt_file_path)
    wgs_cov_info = res_md_dict['spatial_coverage_info']['wgs84_coverage_info']
    # add core metadata coverage - box
    if wgs_cov_info and wgs_cov_info["northlimit"] is not None:
        box = {'spatial_coverage': {'type': 'box', **wgs_cov_info}}
        metadata.append(box)

    # Save extended meta spatial reference
    orig_cov_info = res_md_dict['spatial_coverage_info'][
        'original_coverage_info']

    # Here the assumption is that if there is no value for the 'northlimit' then there is no value
    # for the bounding box
    if orig_cov_info['northlimit'] is not None:
        ori_cov = {'spatial_reference': orig_cov_info}
        metadata.append(ori_cov)

    # Save extended meta cell info
    res_md_dict['cell_info']['name'] = os.path.basename(vrt_file_path)
    metadata.append({'cell_information': res_md_dict['cell_info']})

    # Save extended meta band info
    assert len(res_md_dict['band_info']) == 1

    for index, band_info in enumerate(list(res_md_dict['band_info'].values())):
        b_info = {}
        b_info["name"] = band_info["name"]
        b_info["maximum_value"] = band_info["maximumValue"]
        b_info["minimum_value"] = band_info["minimumValue"]
        b_info["no_data_value"] = band_info["noDataValue"]
        b_info["variable_name"] = band_info["variableName"]
        b_info["variable_unit"] = band_info["variableUnit"]
        metadata.append({f'band_information': b_info})

    metadata_dict = {}
    # use the extracted metadata to populate file metadata
    for element in metadata:
        # here k is the name of the element
        # v is a dict of all element attributes/field names and field values
        k, v = list(element.items())[0]
        metadata_dict[k] = v

    return metadata_dict


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

    Return: meta of spatial extent and projection of raster includes both original info
    and wgs84 info
    """
    raster_dataset = gdal.Open(raster_file_name, GA_ReadOnly)
    original_coverage_info = get_original_coverage_info(raster_dataset)
    wgs84_coverage_info = get_wgs84_coverage_info(raster_dataset)
    spatial_coverage_info = {
        'original_coverage_info': original_coverage_info,
        'wgs84_coverage_info': wgs84_coverage_info,
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
        # an exception occurs when doing GetGeoTransform, which means an invalid geotiff is
        # uploaded, print exception
        # to log without blocking the main resource creation workflow since we allow user to
        # upload a tiff file without valid tags
        proj_wkt = None

    if proj_wkt:
        spatial_ref = osr.SpatialReference()
        spatial_ref.ImportFromWkt(proj_wkt)

        # get projection string, datum
        projection_string = proj_wkt
        datum = spatial_ref.GetAttrValue(
            "DATUM", 0) if spatial_ref.GetAttrValue("DATUM", 0) else None

        # get unit info and check spelling
        unit = spatial_ref.GetAttrValue("UNIT", 0)
        if re.match('metre', unit, re.I):
            unit = 'meter'

        # get projection info
        if spatial_ref.IsProjected():
            projection = spatial_ref.GetAttrValue('projcs', 0)
        else:
            projection = spatial_ref.GetAttrValue('geogcs', 0)

    else:
        unit = None
        projection = None
        projection_string = None
        datum = None

    # get the bounding box
    try:
        gt = raster_dataset.GetGeoTransform()
    except Exception as ex:
        # an exception occurs when doing GetGeoTransform, which means an invalid geotiff is
        # uploaded, print exception
        # to log without blocking the main resource creation workflow since we allow user to
        # upload a tiff file without valid tags
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
                x = gt[0] + (px * gt[1]) + (py * gt[2])
                y = gt[3] + (px * gt[4]) + (py * gt[5])
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

    spatial_coverage_info = dict(
        [
            ('northlimit', northlimit),
            ('southlimit', southlimit),
            ('eastlimit', eastlimit),
            ('westlimit', westlimit),
            ('projection', projection),
            ('units', unit),
            ('projection_string', projection_string),
            ('datum', datum),
        ]
    )

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
        # an exception occurs when doing GetGeoTransform, which means an invalid geotiff is
        # uploaded, print exception
        # to log without blocking the main resource creation workflow since we allow user to
        # upload a tiff file without valid tags
        proj = None

    wgs84_coverage_info = OrderedDict()
    original_coverage_info = get_original_coverage_info(raster_dataset)

    if proj and (None not in list(original_coverage_info.values())):
        original_cs = osr.SpatialReference()
        # create wgs84 geographic coordinate system
        wgs84_cs = osr.SpatialReference()
        wgs84_cs.ImportFromEPSG(4326)
        transform = None
        try:
            original_cs.ImportFromWkt(proj)
            # create transform object
            transform = osr.CoordinateTransformation(original_cs, wgs84_cs)
            # If there is a problem with a transform object such as occurs with
            # USA_Contiguous_Albers_Equal_Area_Conic_USGS_version
            # then use the following workaround that uses wkt
            if transform.this is None:
                ogc_wkt = from_unknown_wkt(proj).to_ogc_wkt()
                original_cs.ImportFromWkt(ogc_wkt)
                # create transform object
                transform = osr.CoordinateTransformation(original_cs, wgs84_cs)

        except Exception as ex:
            pass

        # get original bounding box info
        original_northlimit = original_coverage_info['northlimit']
        original_southlimit = original_coverage_info['southlimit']
        original_westlimit = original_coverage_info['westlimit']
        original_eastlimit = original_coverage_info['eastlimit']

        if transform is not None and transform.this is not None:
            # Find bounding box that encapsulates tranformed original bounding
            # box
            xarr = [original_westlimit, original_eastlimit]
            yarr = [original_northlimit, original_southlimit]
            x_wgs84 = []
            y_wgs84 = []
            for px in xarr:
                for py in yarr:
                    xt, yt = transform.TransformPoint(px, py)[:2]
                    x_wgs84.append(xt)
                    y_wgs84.append(yt)
                yarr.reverse()

            wgs84_eastlimit = max(y_wgs84)  # max y
            wgs84_westlimit = min(y_wgs84)
            wgs84_southlimit = min(x_wgs84)  # min x
            wgs84_northlimit = max(x_wgs84)

            wgs84_coverage_info = OrderedDict(
                [
                    ('northlimit', wgs84_northlimit),
                    ('southlimit', wgs84_southlimit),
                    ('eastlimit', wgs84_eastlimit),
                    ('westlimit', wgs84_westlimit),
                    ('units', 'Decimal degrees'),
                    ('projection', 'WGS 84 EPSG:4326'),
                ]
            )

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
        cell_size_x_value = raster_dataset.GetGeoTransform()[
            1] if proj_wkt else 0
        cell_size_y_value = abs(raster_dataset.GetGeoTransform()[
                                5]) if proj_wkt else 0
        band = raster_dataset.GetRasterBand(1)
        cell_data_type = gdal.GetDataTypeName(band.DataType)

        cell_info = OrderedDict(
            [
                ('rows', rows),
                ('columns', columns),
                ('cell_size_x_value', cell_size_x_value),
                ('cell_size_y_value', cell_size_y_value),
                ('cell_data_type', cell_data_type),
            ]
        )
    else:
        cell_info = OrderedDict(
            [
                ('rows', None),
                ('columns', None),
                ('cell_size_x_value', None),
                ('cell_size_y_value', None),
                ('cell_data_type', None),
            ]
        )

    return cell_info


def get_band_info(raster_file_name):
    raster_dataset = gdal.Open(raster_file_name, GA_ReadOnly)

    # get raster band count
    if raster_dataset:
        band_info = {}
        band_count = raster_dataset.RasterCount

        for i in range(0, band_count):
            band = raster_dataset.GetRasterBand(i + 1)
            stats = band.GetStatistics(False, True)
            if stats is not None:
                minimum, maximum, _, _ = stats
            else:
                continue
            no_data = band.GetNoDataValue()
            new_no_data = None

            if no_data and numpy.allclose(minimum, no_data):
                new_no_data = minimum
            elif no_data and numpy.allclose(maximum, no_data):
                new_no_data = maximum

            if new_no_data is not None:
                band.SetNoDataValue(new_no_data)
                minimum, maximum, _, _ = band.ComputeStatistics(False)

            band_info[i + 1] = {
                'name': 'Band_' + str(i + 1),
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
    return band_info


def raster_file_metadata_extraction(raster_path):
    raster_resource_files = []
    vrt_files_for_raster = get_vrt_files(raster_path)

    if len(vrt_files_for_raster) == 1:
        vrt_file = vrt_files_for_raster[0]
        raster_resource_files.extend([vrt_file])
    else:
        # create the .vrt file
        tif_files = [
            f for f in s3.glob(raster_path) if os.path.basename(f) == os.path.basename(raster_path)
        ]
        vrt_file = create_vrt_file(raster_path)

    raster_resource_files.extend(tif_files)


def list_tif_files(vrt_file):
    with open(vrt_file, "r") as f:
        vrt_string = f.read()
    root = ET.fromstring(vrt_string)
    file_names_in_vrt = [
        file_name.text for file_name in root.iter('SourceFilename')]
    return file_names_in_vrt


def list_tif_files_s3(vrt_file):
    with s3.open(vrt_file, "r") as f:
        vrt_string = f.read()
    root = ET.fromstring(vrt_string)
    file_names_in_vrt = [
        file_name.text for file_name in root.iter('SourceFilename')]
    return file_names_in_vrt


def get_vrt_files(raster_path):
    dir_path = os.path.dirname(raster_path)
    vrt_files = [f for f in os.listdir(dir_path) if str(
        Path(f).suffix).lower() == ".vrt"]
    vrt_files_for_raster = []
    if vrt_files:
        for vrt_file in vrt_files:
            file_names_in_vrt = list_tif_files(vrt_file)
            for vrt_ref_raster_name in file_names_in_vrt:
                if raster_path.endswith(vrt_ref_raster_name):
                    vrt_files_for_raster.append(vrt_file)
    return vrt_files_for_raster
