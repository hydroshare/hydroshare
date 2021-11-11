import json
import os
from datetime import datetime, timezone

from django.db import transaction
from django.http import JsonResponse, HttpResponse
from drf_yasg.utils import swagger_auto_schema
from pydantic import ValidationError as PydanticValidationError
from rest_framework.exceptions import ValidationError

from hs_core.hydroshare.hs_bagit import create_bag_metadata_files
from rest_framework.decorators import api_view

from hs_core.models import ResourceFile
from hs_core.views import ACTION_TO_AUTHORIZE
from hs_core.views.utils import authorize
from hs_file_types.utils import ingest_logical_file_metadata
from hs_rest_api2 import serializers
from hs_rest_api2.serializers import ResourceMetadataInForbidExtra

from hsmodels.schemas.aggregations import GeographicFeatureMetadataIn, GeographicRasterMetadataIn, \
    MultidimensionalMetadataIn, SingleFileMetadataIn, FileSetMetadataIn, TimeSeriesMetadataIn, \
    ReferencedTimeSeriesMetadataIn, ModelProgramMetadata, ModelProgramMetadataIn, ModelInstanceMetadata, \
    ModelInstanceMetadataIn

from hsmodels.schemas import ResourceMetadata, GeographicFeatureMetadata, GeographicRasterMetadata, \
    MultidimensionalMetadata, SingleFileMetadata, FileSetMetadata, TimeSeriesMetadata, ReferencedTimeSeriesMetadata


def load_metadata(istorage, file_with_path):
    from hsmodels.schemas import load_rdf
    with istorage.open(file_with_path) as f:
        metadata = load_rdf(f.read())
        return metadata


def resource_metadata(resource):
    file_with_path = resource.scimeta_path
    istorage = resource.get_irods_storage()
    return load_metadata(istorage, file_with_path)


def ingest_resource_metadata(resource, incoming_metadata):
    from hsmodels.schemas.resource import ResourceMetadata
    from hsmodels.schemas import rdf_graph
    r_md = resource_metadata(resource).dict()
    try:
        incoming_r_md = ResourceMetadataInForbidExtra(**incoming_metadata)
    except PydanticValidationError as e:
        raise ValidationError(e)
    # merge existing metadata with incoming, incoming overrides existing
    merged_metadata = {**r_md,
                       **incoming_r_md.dict(exclude_defaults=True),
                       "modified": datetime.now(timezone.utc).isoformat()}
    res_metadata = ResourceMetadata(**merged_metadata)

    graph = rdf_graph(res_metadata)
    try:
        with transaction.atomic():
            resource.metadata.delete_all_elements()
            resource.metadata.ingest_metadata(graph)
    except:
        # logger.exception("Error processing resource metadata file")
        raise
    create_bag_metadata_files(resource)
    resource.setAVU("bag_modified", True)


def _resource_metadata_json(resource):
    return json.loads(resource_metadata(resource).json())


@swagger_auto_schema(method='put', request_body=serializers.ResourceMetadataInSerializer,
                     operation_description="Update Resource level metadata in json",)
@swagger_auto_schema(method='get', responses={200: serializers.ResourceMetadataSerializer},
                     operation_description="Get Resource level metadata json")
@api_view(['GET', 'PUT'])
def resource_metadata_json(request, pk):
    if request.method == 'GET':
        resource, _, _ = authorize(request, pk,
                                   needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
        md_json = _resource_metadata_json(resource)
        return JsonResponse(md_json)

    resource, _, _ = authorize(request, pk,
                               needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    md = json.loads(request.body)
    ingest_resource_metadata(resource, md)
    return HttpResponse(status=200)


def get_aggregation(resource, file_path):
    file_storage_path = os.path.join(resource.file_path, file_path)
    folder, file_name = ResourceFile.resource_path_is_acceptable(resource, file_storage_path, test_exists=True)
    res_file = ResourceFile.get(resource, file_name, folder)
    return res_file.logical_file


def aggregation_metadata(resource, file_path):
    agg = get_aggregation(resource, file_path)
    return load_metadata(resource.get_irods_storage(), agg.metadata_file_path)


def aggregation_metadata_json_loads(resource, file_path):
    return json.loads(aggregation_metadata(resource, file_path).json())


def ingest_aggregation_metadata(resource, incoming_metadata, file_path, in_schema, out_schema):
    from hsmodels.schemas import rdf_graph
    r_md = aggregation_metadata(resource, file_path).dict()
    try:
        incoming_md = in_schema(**incoming_metadata)
    except PydanticValidationError as e:
        raise ValidationError(e)
    # merge existing metadata with incoming, incoming overrides existing
    merged_metadata = {**r_md,
                       **incoming_md.dict(exclude_defaults=True)}

    # TODO change to aggregation schema
    agg_metadata = out_schema(**merged_metadata)
    graph = rdf_graph(agg_metadata)

    ingest_logical_file_metadata(graph, resource)
    create_bag_metadata_files(resource)
    resource.setAVU("bag_modified", True)


def aggregation_metadata_json(request, pk, aggregation_path, in_schema, out_schema):
    if request.method == 'GET':
        resource, _, _ = authorize(request, pk,
                                   needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
        md_json = aggregation_metadata_json_loads(resource, aggregation_path)
        return JsonResponse(md_json)

    resource, _, _ = authorize(request, pk,
                               needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    metadata_json = json.loads(request.body)
    ingest_aggregation_metadata(resource, metadata_json, aggregation_path, in_schema, out_schema)
    return HttpResponse(status=200)


@swagger_auto_schema(method='put', request_body=serializers.GeographicFeatureMetadataInSerializer,
                     operation_description="Update Geographic Feature aggregation metadata with json",)
@swagger_auto_schema(method='get', responses={200: serializers.GeographicFeatureMetadataSerializer},
                     operation_description="Get Geographic Feature aggregation metadata json")
@api_view(['GET', 'PUT'])
def geographic_feature_metadata_json(request, pk, aggregation_path):
    return aggregation_metadata_json(request, pk, aggregation_path, GeographicFeatureMetadataIn, GeographicFeatureMetadata)


@swagger_auto_schema(method='put', request_body=serializers.GeographicRasterMetadataInSerializer,
                     operation_description="Update Geographic Raster aggregation metadata with json",)
@swagger_auto_schema(method='get', responses={200: serializers.GeographicRasterMetadataSerializer},
                     operation_description="Get Geographic Raster aggregation metadata json")
@api_view(['GET', 'PUT'])
def geographic_raster_metadata_json(request, pk, aggregation_path):
    return aggregation_metadata_json(request, pk, aggregation_path, GeographicRasterMetadataIn, GeographicRasterMetadata)


@swagger_auto_schema(method='put', request_body=serializers.TimeSeriesMetadataInSerializer,
                     operation_description="Update Time Series aggregation metadata with json",)
@swagger_auto_schema(method='get', responses={200: serializers.TimeSeriesMetadataSerializer},
                     operation_description="Get Time Series aggregation metadata json")
@api_view(['GET', 'PUT'])
def time_series_metadata_json(request, pk, aggregation_path):
    return aggregation_metadata_json(request, pk, aggregation_path, TimeSeriesMetadataIn, TimeSeriesMetadata)


@swagger_auto_schema(method='put', request_body=serializers.FileSetMetadataInSerializer,
                     operation_description="Update FileSet aggregation metadata with json",)
@swagger_auto_schema(method='get', responses={200: serializers.FileSetMetadataSerializer},
                     operation_description="Get FileSet aggregation metadata json")
@api_view(['GET', 'PUT'])
def file_set_metadata_json(request, pk, aggregation_path):
    return aggregation_metadata_json(request, pk, aggregation_path, FileSetMetadataIn, FileSetMetadata)


@swagger_auto_schema(method='put', request_body=serializers.MultidimensionalMetadataInSerializer,
                     operation_description="Update Multidimensional aggregation metadata with json",)
@swagger_auto_schema(method='get', responses={200: serializers.MultidimensionalMetadataSerializer},
                     operation_description="Get Multidimensional aggregation metadata json")
@api_view(['GET', 'PUT'])
def multidimensional_metadata_json(request, pk, aggregation_path):
    return aggregation_metadata_json(request, pk, aggregation_path, MultidimensionalMetadataIn, MultidimensionalMetadata)


@swagger_auto_schema(method='put', request_body=serializers.ReferencedTimeSeriesMetadataInSerializer,
                     operation_description="Update Referenced TimeSeries aggregation metadata with json",)
@swagger_auto_schema(method='get', responses={200: serializers.ReferencedTimeSeriesMetadataSerializer},
                     operation_description="Get Referenced TimeSeries aggregation metadata json")
@api_view(['GET', 'PUT'])
def referenced_time_series_metadata_json(request, pk, aggregation_path):
    return aggregation_metadata_json(request, pk, aggregation_path, ReferencedTimeSeriesMetadataIn, ReferencedTimeSeriesMetadata)


@swagger_auto_schema(method='put', request_body=serializers.SingleFileMetadataInSerializer,
                     operation_description="Update Single File aggregation metadata with json",)
@swagger_auto_schema(method='get', responses={200: serializers.SingleFileMetadataSerializer},
                     operation_description="Get Single File aggregation metadata json")
@api_view(['GET', 'PUT'])
def single_file_metadata_json(request, pk, aggregation_path):
    return aggregation_metadata_json(request, pk, aggregation_path, SingleFileMetadataIn, SingleFileMetadata)


@swagger_auto_schema(method='put', request_body=serializers.ModelProgramMetadataInSerializer,
                     operation_description="Update Model Program aggregation metadata with json",)
@swagger_auto_schema(method='get', responses={200: serializers.ModelProgramMetadataSerializer},
                     operation_description="Get Model Program aggregation metadata json")
@api_view(['GET', 'PUT'])
def model_program_metadata_json(request, pk, aggregation_path):
    return aggregation_metadata_json(request, pk, aggregation_path, ModelProgramMetadataIn, ModelInstanceMetadata)


@swagger_auto_schema(method='put', request_body=serializers.ModelInstanceMetadataInSerializer,
                     operation_description="Update Model Instance aggregation metadata with json",)
@swagger_auto_schema(method='get', responses={200: serializers.ModelInstanceMetadataSerializer},
                     operation_description="Get Model Instance aggregation metadata json")
@api_view(['GET', 'PUT'])
def model_instance_metadata_json(request, pk, aggregation_path):
    return aggregation_metadata_json(request, pk, aggregation_path, ModelInstanceMetadataIn, ModelInstanceMetadata)
