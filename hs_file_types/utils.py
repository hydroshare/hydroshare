import json
import os
from operator import lt, gt

from dateutil import parser
from django.apps import apps
from django.db import transaction
from rdflib import RDFS, Graph
from rdflib.namespace import DC, Namespace

from hs_core.hydroshare import utils, get_resource_file
from hs_file_types.models.base import AbstractLogicalFile
from .models import (
    GenericLogicalFile,
    GeoRasterLogicalFile,
    NetCDFLogicalFile,
    GeoFeatureLogicalFile,
    RefTimeseriesLogicalFile,
    TimeSeriesLogicalFile,
    FileSetLogicalFile,
    ModelProgramLogicalFile,
    ModelInstanceLogicalFile,
    CSVLogicalFile,
)


def get_SupportedAggTypes_choices():
    """
    This function harvests all existing aggregation types in system,
    and puts them in a list:
    [
        ["AGGREGATION_CLASS_NAME_1", "AGGREGATION_VERBOSE_NAME_1"],
        ["AGGREGATION_CLASS_NAME_2", "AGGREGATION_VERBOSE_NAME_2"],
        ...
        ["AGGREGATION_CLASS_NAME_N", "AGGREGATION_VERBOSE_NAME_N"],
    ]
    """

    result_list = []
    agg_types_list = get_aggregation_types()
    for r_type in agg_types_list:
        class_name = r_type.__name__
        verbose_name = r_type.get_aggregation_display_name()
        result_list.append([class_name, verbose_name])
    return result_list


def get_aggregation_types():
    aggregation_types = []
    for model in apps.get_models():
        if issubclass(model, AbstractLogicalFile):
            if not getattr(model, "archived_model", False):
                aggregation_types.append(model)
    return aggregation_types


def update_target_spatial_coverage(target):
    """Updates target spatial coverage based on the contained spatial coverages of
    aggregations (file type). Note: This action will overwrite any existing target spatial
    coverage data.

    :param  target: an instance of CompositeResource or FileSetLogicalFile or ModelInstanceLogicalFile
    """

    if isinstance(target, FileSetLogicalFile) or isinstance(
        target, ModelInstanceLogicalFile
    ):
        spatial_coverages = [
            lf.metadata.spatial_coverage
            for lf in target.get_children()
            if lf.metadata.spatial_coverage is not None
        ]
    else:
        spatial_coverages = [
            lf.metadata.spatial_coverage
            for lf in target.logical_files
            if lf.metadata.spatial_coverage is not None and not lf.has_parent
        ]

    if not spatial_coverages:
        # no aggregation level spatial coverage data exist - no need to update resource
        # spatial coverage
        return

    bbox_limits = {
        "box": {
            "northlimit": "northlimit",
            "southlimit": "southlimit",
            "eastlimit": "eastlimit",
            "westlimit": "westlimit",
        },
        "point": {
            "northlimit": "north",
            "southlimit": "north",
            "eastlimit": "east",
            "westlimit": "east",
        },
    }

    def set_coverage_data(res_coverage_value, lfo_coverage_element, box_limits):
        comparison_operator = {
            "northlimit": lt,
            "southlimit": gt,
            "eastlimit": lt,
            "westlimit": gt,
        }
        for key in list(comparison_operator.keys()):
            if comparison_operator[key](
                res_coverage_value[key], lfo_coverage_element.value[box_limits[key]]
            ):
                res_coverage_value[key] = lfo_coverage_element.value[box_limits[key]]

    cov_type = "point"
    bbox_value = {
        "northlimit": -90,
        "southlimit": 90,
        "eastlimit": -180,
        "westlimit": 180,
        "projection": "WGS 84 EPSG:4326",
        "units": "Decimal degrees",
    }

    if len(spatial_coverages) > 1:
        # check if one of the coverage is of type box
        if any(sp_cov.type == "box" for sp_cov in spatial_coverages):
            cov_type = "box"
        else:
            # check if the coverages represent different locations
            unique_lats = set([sp_cov.value["north"] for sp_cov in spatial_coverages])
            unique_lons = set([sp_cov.value["east"] for sp_cov in spatial_coverages])
            if len(unique_lats) == 1 and len(unique_lons) == 1:
                cov_type = "point"
            else:
                cov_type = "box"
        if cov_type == "point":
            sp_cov = spatial_coverages[0]
            bbox_value = dict()
            bbox_value["projection"] = "WGS 84 EPSG:4326"
            bbox_value["units"] = "Decimal degrees"
            bbox_value["north"] = sp_cov.value["north"]
            bbox_value["east"] = sp_cov.value["east"]
        else:
            for sp_cov in spatial_coverages:
                if sp_cov.type == "box":
                    box_limits = bbox_limits["box"]
                    set_coverage_data(bbox_value, sp_cov, box_limits)
                else:
                    # point type coverage
                    box_limits = bbox_limits["point"]
                    set_coverage_data(bbox_value, sp_cov, box_limits)

    elif len(spatial_coverages) == 1:
        sp_cov = spatial_coverages[0]
        if sp_cov.type == "box":
            cov_type = "box"
            bbox_value["projection"] = "WGS 84 EPSG:4326"
            bbox_value["units"] = "Decimal degrees"
            bbox_value["northlimit"] = sp_cov.value["northlimit"]
            bbox_value["eastlimit"] = sp_cov.value["eastlimit"]
            bbox_value["southlimit"] = sp_cov.value["southlimit"]
            bbox_value["westlimit"] = sp_cov.value["westlimit"]
        else:
            # point type coverage
            cov_type = "point"
            bbox_value = dict()
            bbox_value["projection"] = "WGS 84 EPSG:4326"
            bbox_value["units"] = "Decimal degrees"
            bbox_value["north"] = sp_cov.value["north"]
            bbox_value["east"] = sp_cov.value["east"]

    spatial_cov = target.metadata.spatial_coverage
    if spatial_cov:
        spatial_cov.type = cov_type
        place_name = spatial_cov.value.get("name", None)
        if place_name is not None:
            bbox_value["name"] = place_name
        spatial_cov._value = json.dumps(bbox_value)
        spatial_cov.save()
    else:
        target.metadata.create_element("coverage", type=cov_type, value=bbox_value)


def update_target_temporal_coverage(target):
    """Updates target temporal coverage based on the contained temporal coverages of
    aggregations (file type).
    Note: This action will overwrite any existing target temporal
    coverage data.

    :param  target: an instance of CompositeResource or FileSetLogicalFile or ModelInstanceLogicalFile
    """
    if isinstance(target, FileSetLogicalFile) or isinstance(
        target, ModelInstanceLogicalFile
    ):
        temporal_coverages = [
            lf.metadata.temporal_coverage
            for lf in target.get_children()
            if lf.metadata.temporal_coverage is not None
        ]
    else:
        temporal_coverages = [
            lf.metadata.temporal_coverage
            for lf in target.logical_files
            if lf.metadata.temporal_coverage is not None and not lf.has_parent
        ]

    if not temporal_coverages:
        # no aggregation level temporal coverage data - no update at resource level is needed
        return

    date_data = {"start": None, "end": None}

    def set_date_value(date_data, coverage_element, key):
        comparison_operator = gt if key == "start" else lt
        if date_data[key] is None:
            date_data[key] = coverage_element.value[key]
        else:
            if comparison_operator(
                parser.parse(date_data[key]), parser.parse(coverage_element.value[key])
            ):
                date_data[key] = coverage_element.value[key]

    for temp_cov in temporal_coverages:
        start_date = parser.parse(temp_cov.value["start"])
        end_date = parser.parse(temp_cov.value["end"])
        temp_cov.value["start"] = start_date.strftime("%m/%d/%Y")
        temp_cov.value["end"] = end_date.strftime("%m/%d/%Y")
        set_date_value(date_data, temp_cov, "start")
        set_date_value(date_data, temp_cov, "end")

    temp_cov = target.metadata.temporal_coverage
    if date_data["start"] is not None and date_data["end"] is not None:
        if temp_cov:
            temp_cov._value = json.dumps(date_data)
            temp_cov.save()
        else:
            target.metadata.create_element("coverage", type="period", value=date_data)


def get_logical_file_type(res, file_id, hs_file_type=None, fail_feedback=True):
    """Return the logical file type associated with a new file"""
    if hs_file_type is None:
        res_file = utils.get_resource_file_by_id(res, file_id)
        ext_to_type = {
            ".tif": "GeoRaster",
            ".tiff": "GeoRaster",
            ".vrt": "GeoRaster",
            ".nc": "NetCDF",
            ".shp": "GeoFeature",
            ".json": "RefTimeseries",
            ".sqlite": "TimeSeries",
            ".csv": "CSV",
        }
        file_name = str(res_file)
        root, ext = os.path.splitext(file_name)
        ext = ext.lower()
        if ext in ext_to_type:
            # Check for special case of RefTimeseries having 2 extensions
            if ext == ".json":
                if not file_name.lower().endswith(".refts.json"):
                    if fail_feedback:
                        raise ValueError(
                            "Unsupported aggregation extension. Supported aggregation "
                            "extensions are: {}".format(list(ext_to_type.keys()))
                        )
            hs_file_type = ext_to_type[ext]
        else:
            if fail_feedback:
                raise ValueError(
                    "Unsupported aggregation extension. Supported aggregation "
                    "extensions are: {}".format(list(ext_to_type.keys()))
                )
            return None

    file_type_map = {
        "SingleFile": GenericLogicalFile,
        "FileSet": FileSetLogicalFile,
        "GeoRaster": GeoRasterLogicalFile,
        "NetCDF": NetCDFLogicalFile,
        "GeoFeature": GeoFeatureLogicalFile,
        "RefTimeseries": RefTimeseriesLogicalFile,
        "TimeSeries": TimeSeriesLogicalFile,
        "ModelProgram": ModelProgramLogicalFile,
        "ModelInstance": ModelInstanceLogicalFile,
        "CSV": CSVLogicalFile,
    }

    if hs_file_type not in file_type_map:
        if fail_feedback:
            raise ValueError(
                "Unsupported aggregation type. Supported aggregation types are: {"
                "}".format(list(file_type_map.keys()))
            )
        return None
    logical_file_type_class = file_type_map[hs_file_type]
    return logical_file_type_class


def get_logical_file(agg_type_name):
    file_type_map = {
        "GeographicRasterAggregation": GeoRasterLogicalFile,
        "SingleFileAggregation": GenericLogicalFile,
        "FileSetAggregation": FileSetLogicalFile,
        "MultidimensionalAggregation": NetCDFLogicalFile,
        "GeographicFeatureAggregation": GeoFeatureLogicalFile,
        "ReferencedTimeSeriesAggregation": RefTimeseriesLogicalFile,
        "TimeSeriesAggregation": TimeSeriesLogicalFile,
        "ModelProgramAggregation": ModelProgramLogicalFile,
        "ModelInstanceAggregation": ModelInstanceLogicalFile,
        "CSVFileAggregation": CSVLogicalFile,
    }
    return file_type_map[agg_type_name]


def is_aggregation_metadata_file(file):
    return file.name.endswith("_meta.xml")


def is_map_file(file):
    return file.name.endswith("_resmap.xml") or file.name == "resourcemap.xml"


def is_resource_metadata_file(file):
    return os.path.basename(file.name) == "resourcemetadata.xml"


def identify_and_ingest_metadata_files(resource, files):
    res_files, meta_files, map_files = identify_metadata_files(files)
    ingest_metadata_files(resource, meta_files, map_files)


def ingest_metadata_files(resource, meta_files, map_files, unzip_temp_folder=""):
    # refresh to pick up any new possible aggregations
    resource_metadata_file = None
    for f in meta_files:
        if is_resource_metadata_file(f):
            resource_metadata_file = f
        elif is_aggregation_metadata_file(f):
            ingest_logical_file_metadata_from_file(f, resource, map_files, unzip_temp_folder)
    # process the resource level metadata last, some aggregation metadata is pushed to the resource level
    if resource_metadata_file:
        resource.refresh_from_db()
        graph = Graph().parse(data=resource_metadata_file.read())
        try:
            with transaction.atomic():
                resource.metadata.ingest_metadata(graph)
        except: # noqa
            # logger.exception("Error processing resource metadata file")
            raise
    resource.setAVU("metadata_dirty", True)
    resource.setAVU("bag_modified", True)


def identify_metadata_files(files):

    res_files = []
    meta_files = []
    map_files = []
    for f in files:
        if is_resource_metadata_file(f) or is_aggregation_metadata_file(f):
            meta_files.append(f)
        elif is_map_file(f):
            map_files.append(f)
        else:
            res_files.append(f)
    return res_files, meta_files, map_files


def get_map_graph(subject, map_files, unzip_temp_folder=""):
    map_name = subject.split("data/contents/", 1)[1]
    map_name = map_name.split("#", 1)[0]
    if unzip_temp_folder:
        unzip_temp_folder = f"/{unzip_temp_folder}"
    for map_file in map_files:
        if unzip_temp_folder in map_file.name:
            map_file_name = map_file.name.replace(unzip_temp_folder, "", 1)
        else:
            map_file_name = map_file.name
        if map_file_name.endswith(map_name):
            return Graph().parse(data=map_file.read())
    raise Exception(f"Could not find _resmap.xml for {subject}")


def get_aggregation_files(map_graph):
    ORE = Namespace("http://www.openarchives.org/ore/terms/")
    files = []
    for _, _, o in map_graph.triples((None, ORE.aggregates, None)):
        file_path = str(o)
        if not file_path.endswith("_meta.xml"):
            files.append(file_path)
    return files


def ingest_logical_file_metadata_from_file(metadata_file, resource, map_files=[], unzip_temp_folder=""):
    ingest_logical_file_metadata_from_string(metadata_file.read(), resource, map_files, unzip_temp_folder)


def ingest_logical_file_metadata_from_string(metadata_str, resource, map_files=[], unzip_temp_folder=""):
    graph = Graph()
    graph = graph.parse(data=metadata_str)
    ingest_logical_file_metadata(graph, resource, map_files, unzip_temp_folder)


def ingest_logical_file_metadata(graph, resource, map_files=[], unzip_temp_folder=""):
    resource.refresh_from_db()

    agg_type_name = None
    for s, _, _ in graph.triples((None, RDFS.isDefinedBy, None)):
        agg_type_name = s.split("/")[-1]
        break
    if not agg_type_name:
        raise Exception("Could not derive aggregation type from {}".format(graph))

    subject = None
    for s, _, _ in graph.triples((None, DC.rights, None)):
        subject = s.split("/resource/", 1)[1].split("#")[0]
        break
    if not subject:
        raise Exception("Could not derive aggregation path from {}".format(graph))

    logical_file_class = get_logical_file(agg_type_name)
    lf = get_logical_file_by_map_file_path(resource, logical_file_class, subject)

    if not lf:
        # see if the files exist and create it
        map_graph = get_map_graph(subject, map_files, unzip_temp_folder)
        aggregation_files = get_aggregation_files(map_graph)

        if logical_file_class.__name__ in ("ModelInstanceLogicalFile", "ModelProgramLogicalFile"):
            # making an assumption that model program/instance is folder based when there is more than one file
            is_folder_based = len(aggregation_files) > 1
        else:
            is_folder_based = logical_file_class.supports_folder_based_aggregation()

        if is_folder_based:
            file_path = subject.rsplit("/", 1)[0]
            file_path = file_path.split("data/contents/", 1)[1]
            res_file = resource.files.filter(file_folder=file_path).first()
            if res_file:
                set_logical_file_type(
                    res=resource,
                    user=None,
                    file_id=None,
                    folder_path=file_path,
                    logical_file_type_class=logical_file_class,
                    fail_feedback=True,
                )
        else:
            file_path = aggregation_files[0].split("data/contents/", 1)[1]
            res_file = get_resource_file(resource.short_id, file_path)
            if res_file:
                set_logical_file_type(
                    res=resource,
                    user=None,
                    file_id=res_file.pk,
                    logical_file_type_class=logical_file_class,
                    fail_feedback=True,
                )
            else:
                raise ValueError(
                    f"Could not find {file_path} referenced in logical file _meta.xml file {subject}"
                )
        if res_file:
            res_file.refresh_from_db()
            lf = res_file.logical_file
        else:
            raise Exception("Could not find aggregation for {}".format(subject))
        if not lf:
            raise Exception(
                "Files for aggregation in metadata file {} could not be found".format(
                    subject
                )
            )

    with transaction.atomic():
        lf.metadata.delete_all_elements()
        lf.metadata.ingest_metadata(graph)
        lf.create_aggregation_xml_documents()


def get_logical_file_by_map_file_path(resource, logical_file_class, map_file_path):
    for logical_file in logical_file_class.objects.filter(resource=resource):
        if logical_file.map_short_file_path in map_file_path:
            return logical_file
    return None


def set_logical_file_type(
    res,
    user,
    file_id,
    hs_file_type=None,
    folder_path="",
    extra_data={},
    fail_feedback=True,
    logical_file_type_class=None,
):
    """set the logical file type for a new file"""
    if not logical_file_type_class:
        logical_file_type_class = get_logical_file_type(
            res, file_id, hs_file_type, fail_feedback
        )

    try:
        # Some aggregations use the folder name for the aggregation name
        folder_path = folder_path.rstrip("/") if folder_path else folder_path
        if extra_data:
            return logical_file_type_class.set_file_type(
                resource=res,
                user=user,
                file_id=file_id,
                folder_path=folder_path,
                extra_data=extra_data,
            )
        else:
            return logical_file_type_class.set_file_type(
                resource=res, user=user, file_id=file_id, folder_path=folder_path
            )
    except: # noqa
        if fail_feedback:
            raise
        return None
