import os
import tempfile
import rasterio
import mimetypes
import xml.etree.ElementTree as ET
from glob import glob
from pyproj import CRS

from hs_cloudnative_schemas.schema import base
from hs_cloudnative_schemas.schema import dataset
from hs_cloudnative_schemas.schema import datavariable
from hsextract.utils.file import file_metadata
from hsextract import s3_client as s3


mimetypes.add_type("application/x-esri-shapefile", ".shp")
mimetypes.add_type("application/x-esri-shx", ".shx")
mimetypes.add_type("application/x-dbase", ".dbf")
mimetypes.add_type("text/plain", ".prj")
mimetypes.add_type("text/plain", ".cpg")
mimetypes.add_type("text/plain", ".asc")
mimetypes.add_type("application/geo+json", ".geojson")
mimetypes.add_type("application/gml+xml", ".gml")


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
    if filepath.endswith('.vrt'):
        # If the file is a VRT, we need to extract the TIF files it references
        tif_files = list_tif_files(local_copy)
        for tif_file in tif_files:
            local_copy_tif_file = os.path.join(
                temp_dir, os.path.basename(tif_file))
            bucket, key = tif_file.split("/", 1)
            s3.download_file(bucket, key, local_copy)
            s3.get_file(bucket, key, local_copy_tif_file)

    src = rasterio.open(local_copy)

    # Cell Information
    cell_columns = src.width
    cell_rows = src.height
    # cell_data_type = src.dtypes[0]
    # cell_x_size = src.transform.a
    # cell_y_size = abs(src.transform.e)

    # Build dataset dimensions.
    dimensions = [
        datavariable.Dimension(
            name='columns',
            shape=cell_columns
        ),
        datavariable.Dimension(
            name='rows',
            shape=cell_rows)
    ]

    if multiband:
        dimensions.insert(0, datavariable.Dimension(
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
    geo = base.GeoShape(box=box_str, validate_bbox=validate_bbox)

    crs = CRS.from_wkt(src.crs.wkt)
    srs = base.SpatialReference(
        name=crs.name,
        srsType=crs.type_name.split(' ')[0],
        code=crs.to_string(),
        wktString=crs.to_wkt()
    )

    place = base.Place(
        geo=geo,
        srs=srs
    )

    gridvariables = []
    for band_idx in band_data.keys():
        variables = datavariable.DataVariable(
            name=f'Band {band_idx}',
            dataType=band_data[band_idx]['dtype'],
            minValue=band_data[band_idx]['min_value'],
            maxValue=band_data[band_idx]['max_value'],
            noDataValue=band_data[band_idx]['nan_value'],
            band=band_idx,
            dimensions=band_data[band_idx]['dims'],
        )
        gridvariables.append(variables)

    # get all file names that match the patter of the input filepath
    search_path = f"{'.'.join(filepath.split('.')[:-1])}.*"
    associated_files = glob(search_path)
    files = []
    for fpath in associated_files:
        file_md, _ = file_metadata(fpath)
        files.append(file_md)

    return dataset.ScientificDataset(
        variableMeasured=gridvariables,
        dimensions=dimensions,
        associatedMedia=files,
        spatialCoverage=place,
        additionalType=dataset.AdditionalType.GEOGRAPHIC_RASTER,
    )
