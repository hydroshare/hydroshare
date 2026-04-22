
import geopandas
import pyogrio
import mimetypes

from pydantic import ValidationError

from hs_cloudnative_schemas.schema import base
from hs_cloudnative_schemas.schema import dataset
from hs_cloudnative_schemas.schema import datavariable
from hsextract.utils.file import file_metadata
from hsextract.utils.s3 import s3_config, s3fsInstance


mimetypes.add_type("image/tiff", ".tif")
mimetypes.add_type("text/plain", ".asc")


def replace_extension(filepath, new_ext):
    if filepath.endswith(".shp.xml"):
        return '.'.join(filepath.split('.')[:-2]) + new_ext
    return '.'.join(filepath.split('.')[:-1]) + new_ext


def encode_vector_metadata(filepath, validate_bbox=True):

    # get all file names that match the pattern of the input filepath
    search_path = f"{'.'.join(filepath.split('.')[:-1])}.*"
    associated_files = s3fsInstance.glob(search_path)

    endpoint_url = s3_config["endpoint_url"]
    endpoint = endpoint_url.split("//")[-1]
    use_https = "YES" if endpoint_url.startswith("https://") else "NO"
    pyogrio.set_gdal_config_options({
        'AWS_S3_ENDPOINT': endpoint,
        'AWS_ACCESS_KEY_ID': s3_config["aws_access_key_id"],
        'AWS_SECRET_ACCESS_KEY': s3_config["aws_secret_access_key"],
        'AWS_VIRTUAL_HOSTING': 'FALSE',
        'AWS_HTTPS': use_https,
    })

    try:
        gdf = geopandas.read_file(f"/vsis3/{filepath}", engine="pyogrio")
    finally:
        # Clear credentials from GDAL state after use
        pyogrio.set_gdal_config_options({
            'AWS_ACCESS_KEY_ID': None,
            'AWS_SECRET_ACCESS_KEY': None,
        })

    feature_count = len(gdf)

    dimensions = [datavariable.Dimension(
        name='feature_index',
        shape=str(feature_count),
        description='index of spatial features',
    )]

    fields = {}
    field_names = list(gdf.columns)
    for fname in field_names:
        meta = {}
        meta.update({'dtype': str(gdf[fname].dtype)})
        meta.update({'dimension': dimensions[0].name})

        # try to get min and max values with exception
        # handling because some fields may not support
        # reduce, e.g. geometry.
        try:
            meta.update({'min_value': gdf[fname].min().item()})
            meta.update({'max_value': gdf[fname].max().item()})

        except Exception:
            pass
        fields[fname] = meta

    # geometry_type = gdf.geom_type.unique()[0]

    # extent
    extent_west, extent_south, extent_east, extent_north = gdf.total_bounds
    box_str = f'{extent_south} {extent_west} {extent_north} {extent_east}'
    # Bbox validation expects geographic lat/lon degrees. For projected CRS values
    # (e.g., meters), strict validation will fail even when metadata is valid.
    should_validate_bbox = validate_bbox and (gdf.crs is None or gdf.crs.is_geographic)
    try:
        geo = base.GeoShape(box=box_str, validate_bbox=should_validate_bbox)
    except ValidationError:
        geo = base.GeoShape(box=box_str, validate_bbox=False)

    # srs
    srs = None
    if gdf.crs is not None:
        crs_type = "Geographic" if gdf.crs.is_geographic else "Projected"

        srs = base.SpatialReference(
            name=gdf.crs.name,
            srsType=crs_type,
            code=gdf.crs.srs,
            wktString=gdf.crs.to_wkt()
        )

    place = base.Place(
        geo=geo,
        srs=srs,
    )

    variables = []
    for field_name, field_values in fields.items():

        minValue = field_values[
            'min_value'] if 'min_value' in field_values else None
        maxValue = field_values[
            'max_value'] if 'max_value' in field_values else None

        variable = datavariable.DataVariable(
            name=field_name,
            dataType=field_values['dtype'],
            minValue=minValue,
            maxValue=maxValue,
            dimensions=field_values['dimension']
        )
        variables.append(variable)

    files = []
    for fpath in associated_files:
        file_md = file_metadata(fpath)
        files.append(file_md)

    return dataset.ScientificDataset(
        variableMeasured=variables,
        dimensions=dimensions,
        associatedMedia=files,
        spatialCoverage=place,
        additionalType=dataset.AdditionalType.GEOGRAPHIC_FEATURE,
    )

