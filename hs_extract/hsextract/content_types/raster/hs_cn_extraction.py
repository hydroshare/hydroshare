import logging
import os
import tempfile
import rasterio
import mimetypes
import xml.etree.ElementTree as ET
from pyproj import CRS

from hs_cloudnative_schemas.schema.base import GeoShape, SpatialReference, Place
from hs_cloudnative_schemas.schema.dataset import ScientificDataset, AdditionalType
from hs_cloudnative_schemas.schema.datavariable import DataVariable, Dimension
from hsextract.utils.file import file_metadata
from hsextract.utils.s3 import find, s3_client as s3


mimetypes.add_type("application/x-esri-shapefile", ".shp")
mimetypes.add_type("application/x-esri-shx", ".shx")
mimetypes.add_type("application/x-dbase", ".dbf")
mimetypes.add_type("text/plain", ".prj")
mimetypes.add_type("text/plain", ".cpg")
mimetypes.add_type("text/plain", ".asc")
mimetypes.add_type("application/geo+json", ".geojson")
mimetypes.add_type("application/gml+xml", ".gml")

def list_tif_files_s3(raster_file):
    temp_dir = tempfile.gettempdir()
    vrt_file = raster_file if raster_file.endswith('.vrt') else None
    if not vrt_file:
        parent_dir = os.path.dirname(raster_file)
        vrt_files = [file for file in find(parent_dir) if file.endswith('.vrt')]
        for file in vrt_files:
            local_copy = os.path.join(temp_dir, os.path.basename(file))
            bucket, key = file.split("/", 1)
            s3.download_file(bucket, key, local_copy)
            tif_files = list_tif_files(local_copy)
            if os.path.basename(raster_file) in tif_files:
                vrt_file = file
                break
    local_copy = os.path.join(temp_dir, os.path.basename(vrt_file))
    bucket, key = vrt_file.split("/", 1)
    s3.download_file(bucket, key, local_copy)
    with open(local_copy, "r") as f:
        vrt_string = f.read()
    root = ET.fromstring(vrt_string)
    file_names_in_vrt = [
        file_name.text for file_name in root.iter('SourceFilename')]
    return file_names_in_vrt


def list_tif_files(vrt_file):
    with open(vrt_file, "r") as f:
        vrt_string = f.read()
    root = ET.fromstring(vrt_string)
    file_names_in_vrt = [
        file_name.text for file_name in root.iter('SourceFilename')]
    return file_names_in_vrt


def encode_raster_metadata(filepath, multiband=False, validate_bbox=True):
    temp_dir = tempfile.gettempdir()
    local_copy = os.path.join(temp_dir, os.path.basename(filepath))
    bucket, key = filepath.split("/", 1)
    s3.download_file(bucket, key, local_copy)
    logging.info(f"Downloaded {filepath} to {local_copy}")
    if filepath.endswith('.vrt'):
        # If the file is a VRT, we need to extract the TIF files it references
        tif_file = list_tif_files(local_copy)[0]
        tif_file = os.path.join(os.path.dirname(filepath), tif_file)
        logging.info(f"VRT references the following TIF files: {tif_file}")
        local_copy_tif_file = os.path.join(
            temp_dir, os.path.basename(tif_file))
        logging.info(f"Downloading referenced TIF file {tif_file} to {local_copy_tif_file}")
        bucket, key = tif_file.split("/", 1)
        s3.download_file(bucket, key, local_copy_tif_file)
        local_copy = local_copy_tif_file

    src = rasterio.open(local_copy)

    # Cell Information
    cell_columns = src.width
    cell_rows = src.height
    # cell_data_type = src.dtypes[0]
    # cell_x_size = src.transform.a
    # cell_y_size = abs(src.transform.e)

    # Build dataset dimensions.
    dimensions = [
        Dimension(
            name='columns',
            shape=cell_columns
        ),
        Dimension(
            name='rows',
            shape=cell_rows)
    ]

    if multiband:
        dimensions.insert(0, Dimension(
            name='band',
            shape=src.count
        ))

    # Bands
    num_bands = src.count
    band_data = {}
    for band in range(1, num_bands + 1):
        dat = src.read(band)
        dims = ['columns', 'rows'] if not multiband else [
            'band', 'columns', 'rows']
        band_meta = dict(
            min_value=dat.min().item(),
            max_value=dat.max().item(),
            nan_value=src.nodatavals[band - 1],
            dtype=str(dat.dtype),
            dims=dims
        )
        band_data[band] = band_meta

    # Extent
    extent_west, extent_south, extent_east, extent_north = src.bounds

    # Other metadata
    # name = src.name.split('/')[1:][0]
    src.close()

    # Encode metadata
    box_str = f'{extent_south} {extent_west} {extent_north} {extent_east}'
    geo = GeoShape(box=box_str, validate_bbox=validate_bbox)

    crs = CRS.from_wkt(src.crs.wkt)
    srs = SpatialReference(
        name=crs.name,
        srsType=crs.type_name.split(' ')[0],
        code=crs.to_string(),
        wktString=crs.to_wkt()
    )

    place = Place(
        geo=geo,
        srs=srs
    )

    gridvariables = []
    for band_idx in band_data.keys():
        variables = DataVariable(
            name=f'Band {band_idx}',
            dataType=band_data[band_idx]['dtype'],
            minValue=band_data[band_idx]['min_value'],
            maxValue=band_data[band_idx]['max_value'],
            noDataValue=band_data[band_idx]['nan_value'],
            band=band_idx,
            dimensions=band_data[band_idx]['dims'],
        )
        gridvariables.append(variables)

    return ScientificDataset(
        variableMeasured=gridvariables,
        dimensions=dimensions,
        spatialCoverage=place,
        additionalType=AdditionalType.GEOGRAPHIC_RASTER,
    )