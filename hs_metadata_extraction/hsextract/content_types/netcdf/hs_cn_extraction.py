import os
import tempfile
import xarray
import numpy as np
from pyproj import CRS

from hsextract.hs_cn_schemas.schema.src import base
from hsextract.hs_cn_schemas.schema.src import dataset
from hsextract.hs_cn_schemas.schema.src import datavariable
from hsextract import s3_client


def inspect_dimensions(ds: xarray.Dataset) -> None:
    # get dimension information
    print(f"{25 * '-'}\nDimension Information\n{25 * '-'}\n")
    for dimname, size in ds.sizes.items():
        print(f'* {dimname} --> Size: {size}\n')


def inspect_coordinates(ds: xarray.Dataset) -> None:
    # get coordinate information
    print(f"{25 * '-'}\nCoordinate Information\n{25 * '-'}\n")
    for coordname in ds.coords.keys():
        print(f"* {coordname}")
        print(f"\tUnit: {ds.coords[coordname].attrs.get('units', 'unknown')}")
        print(f"\tDescription: {
              ds.coords[coordname].attrs.get('long_name', 'None')}")
        print(f"\tType: {ds.coords[coordname].dtype}")
        print(f"\tShape: {ds.coords[coordname].shape}")


def inspect_variables(ds: xarray.Dataset) -> None:
    # get variable information
    # get coordinate information
    print(f"{25 * '-'}\nVariable Information\n{25 * '-'}\n")
    for varname in ds.variables.keys():
        if varname in ds.coords.keys():
            continue

        print(f"* {varname}")
        print(f"\tUnit: {ds.variables[varname].attrs.get('units', 'unknown')}")
        print(f"\tDescription: {ds.variables[
              varname].attrs.get('long_name', 'none')}")
        print(f"\tType: {ds.variables[varname].dtype}")
        print(f"\tCoordinates: ({', '.join(ds[varname].coords.keys())})")
        print(f"\tShape: {ds.variables[varname].shape}")


def get_crs_from_dataset_metadata(ds: xarray.Dataset) -> xarray.Dataset:
    """
    Set the CRS of an xarray.Dataset using metadata from a 'crs' or 'spatial_ref' variable.

    Parameters:
        ds (xarray.Dataset): Input dataset

    Returns:
        xarray.Dataset: Dataset with CRS set via rioxarray
    """

    # Identify CRS variable
    crs_var = None
    for name in ['crs', 'spatial_ref']:
        if name in ds.variables:
            crs_var = ds[name]
            break

    if crs_var is None:
        return None
        # raise ValueError("No CRS variable found (expected 'crs' or 'spatial_ref').")

    attrs = crs_var.attrs

    # Try to extract CRS from known attributes
    if "epsg_code" in attrs:
        crs = CRS.from_epsg(int(str(attrs["epsg_code"]).split(":")[-1]))
    elif "crs_wkt" in attrs:
        crs = CRS.from_wkt(attrs["crs_wkt"])
    elif "proj4_params" in attrs:
        crs = CRS.from_proj4(attrs["proj4_params"])
    elif "grid_mapping_name" in attrs and attrs["grid_mapping_name"] == "latitude_longitude":
        crs = CRS.from_epsg(4326)
    elif "esri_pe_string" in attrs:
        crs = CRS.from_wkt(attrs['esri_pe_string'])
    else:
        return None

    return crs


def get_spatial_bounds(ds: xarray.Dataset) -> dict[str, float]:

    def is_lat(coord):
        std = coord.attrs.get("standard_name", "").lower()
        units = coord.attrs.get("units", "").lower()
        axis = coord.attrs.get("axis", "").upper()
        name = coord.name.lower()
        return (
            std == "latitude"
            or "degrees_north" in units
            or name in ["lat", "latitude", "y"]
            or axis == "Y"
        )

    def is_lon(coord):
        std = coord.attrs.get("standard_name", "").lower()
        units = coord.attrs.get("units", "").lower()
        axis = coord.attrs.get("axis", "").upper()
        name = coord.name.lower()
        return (
            std == "longitude"
            or "degrees_east" in units
            or name in ["lon", "longitude", "x"]
            or axis == "X"
        )

    lat_coord = None
    lon_coord = None

    for coord in ds.coords.values():
        if lat_coord is None and is_lat(coord):
            lat_coord = coord
        if lon_coord is None and is_lon(coord):
            lon_coord = coord

    if lat_coord is None or lon_coord is None:
        raise ValueError("Could not identify spatial coordinates.")

    # Handle 1D and 2D coordinate cases
    lat_vals = lat_coord.values
    lon_vals = lon_coord.values

    bounds = {
        "lat_min": float(np.nanmin(lat_vals)),
        "lat_max": float(np.nanmax(lat_vals)),
        "lon_min": float(np.nanmin(lon_vals)),
        "lon_max": float(np.nanmax(lon_vals)),
    }

    return bounds


def build_dimensions(ds: xarray.Dataset) -> dict[datavariable.Dimension]:
    dims = {}
    for dimname, size in ds.sizes.items():
        var = ds.variables.get(dimname, None)
        attrs = var.attrs if var is not None else {}

        description = attrs.get('long_name', None)
        # units = attrs.get('units', None)
        # resolution = attrs.get('resolution', None)

        dims[dimname] = datavariable.Dimension(name=dimname,
                                               description=description,
                                               # units=units,
                                               # resolution=resolution,
                                               shape=ds.sizes.get(dimname))
    return dims


def build_variables(ds: xarray.Dataset,
                    compute_statistics=True) -> list[datavariable.DataVariable]:

    variables = []
    for varname in ds.variables.keys():

        v = ds[varname]

        # skip if this is a dimension
        if varname in v.dims:
            continue

        var_dims = [d for d in v.dims]
        if len(var_dims) == 0:
            var_dims = ['Dimensionless']

        # making this optional because it could be prohibitive
        # for large files.
        minValue = None
        maxValue = None
        if compute_statistics:
            minValue = v.min().item() or None
            maxValue = v.max().item() or None

        variables.append(datavariable.DataVariable(
            name=varname,
            dimensions=var_dims,
            description=v.attrs.get('long_name', None),
            unit=v.attrs.get('units', 'Unitless'),
            minValue=minValue,
            maxValue=maxValue,
            dataType=str(v.dtype) or None
        )
        )
    return variables


def build_coordinates(ds: xarray.Dataset,
                      dims: dict[datavariable.Dimension]) -> list[datavariable.DataVariable]:
    coords = []
    for coord_name, coord in ds.coords.items():

        coordinate_dimensions = [dim_name for dim_name in coord.dims]
        coords.append(datavariable.DataVariable(name=coord_name,
                                                description=coord.attrs.get(
                                                    'long_name', None),
                                                unit=coord.attrs.get(
                                                    'units', None),
                                                # resolution = coord.attrs.get('resolution', None),
                                                dimensions=coordinate_dimensions,
                                                )
                      )
    return coords


def encode_netcdf(filepath: str,
                  validate_bbox: bool = True,
                  compute_statistics: bool = True) -> dataset.ScientificDataset:

    temp_dir = tempfile.gettempdir()
    local_copy = os.path.join(temp_dir, os.path.basename(filepath))
    bucket, key = filepath.split("/", 1)
    s3_client.download_file(bucket, key, local_copy)
    ds = xarray.load_dataset(local_copy, engine='netcdf4')
    md_metadata = encode_multidimensional_metadata(
        ds, filepath, validate_bbox, compute_statistics)
    os.remove(local_copy)  # Clean up the local copy
    return md_metadata


def encode_zarr(filepath: str,
                validate_bbox: bool = True,
                compute_statistics: bool = True) -> dataset.ScientificDataset:

    temp_dir = tempfile.gettempdir()
    local_copy = os.path.join(temp_dir, os.path.basename(filepath))
    bucket, key = filepath.split("/", 1)
    s3_client.download_file(bucket, key, local_copy)
    # , chunks={"time":-1, "lat":"auto", "lon":"auto"})
    ds = xarray.open_zarr(local_copy, consolidated=False)
    md = encode_multidimensional_metadata(
        ds, filepath, validate_bbox, compute_statistics)
    os.remove(local_copy)
    return md


def encode_multidimensional_metadata(ds: xarray.Dataset,
                                     filepath: str,
                                     validate_bbox: bool = True,
                                     compute_statistics: bool = True) -> dataset.ScientificDataset:

    bounds = get_spatial_bounds(ds)
    box_str = f"{bounds['lat_min']} {bounds['lon_min']} {
        bounds['lat_max']} {bounds['lon_max']}"
    geo = base.GeoShape(box=box_str, validate_bbox=validate_bbox)
    crs = get_crs_from_dataset_metadata(ds)

    if crs:
        srs = base.SpatialReference(
            name=crs.name,
            srsType=crs.type_name.split(' ')[0],
            code=crs.to_string(),
            wktString=crs.to_wkt()
        )
    else:
        srs = None

    place = base.Place(
        geo=geo,
        srs=srs
    )

    dims = build_dimensions(ds)

    # return dims
    variables = build_variables(ds, compute_statistics)

    coordinates = build_coordinates(ds, dims)

    meta = dataset.ScientificDataset(variableMeasured=variables,
                                     coordinates=coordinates,
                                     dimensions=list(dims.values()),
                                     spatialCoverage=place,
                                     additionalType=dataset.AdditionalType.MULTIDIMENSIONAL)

    return meta
