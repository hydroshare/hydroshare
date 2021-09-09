import json
import os

from django.db import transaction
from django.http import JsonResponse, HttpResponse
from drf_yasg.utils import swagger_auto_schema

from hs_core.hydroshare.hs_bagit import create_bag_metadata_files
from rest_framework.decorators import api_view

from hs_core.models import ResourceFile
from hs_core.views import ACTION_TO_AUTHORIZE
from hs_core.views.utils import authorize
from hs_file_types.utils import ingest_logical_file_metadata
from hs_rest_api2 import serializers


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
    # merge existing metadata with incoming, incoming overrides existing
    merged_metadata = {**r_md, **incoming_metadata}
    res_metadata = ResourceMetadata(**merged_metadata)
    rdf_graph(res_metadata)
    graph = rdf_graph(res_metadata)
    try:
        with transaction.atomic():
            resource.metadata.ingest_metadata(graph)
    except:
        # logger.exception("Error processing resource metadata file")
        raise
    create_bag_metadata_files(resource)
    resource.setAVU("bag_modified", True)


def _resource_metadata_json(resource):
    return json.loads(resource_metadata(resource).json())


@swagger_auto_schema(method='put', request_body=serializers.ResourceMetadataSerializer,
                     operation_description="Update Resource level metadata",)
@swagger_auto_schema(method='get', responses={200: serializers.ResourceMetadataSerializer})
@api_view(['GET', 'PUT'])
def resource_metadata_json(request, pk):
    if request.method == 'GET':
        resource, _, _ = authorize(request, pk,
                                   needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
        md_json = _resource_metadata_json(resource)
        return JsonResponse(md_json)

    resource, _, _ = authorize(request, pk,
                               needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    metadata = request.POST.get('metadata', None)
    ingest_resource_metadata(resource, metadata)
    return HttpResponse(status=204)


def get_aggregation(resource, file_path):
    file_storage_path = os.path.join(resource.file_path, file_path)
    folder, file_name = ResourceFile.resource_path_is_acceptable(resource, file_storage_path, test_exists=True)
    res_file = ResourceFile.get(resource, file_name, folder)
    # assert res_file.logical_file

    return res_file.logical_file


def aggregation_metadata(resource, file_path):
    agg = get_aggregation(resource, file_path)
    ingest_logical_file_metadata()
    return load_metadata(resource.get_irods_storage(), agg.metadata_file_path)


def aggregation_metadata_json(resource, file_path):
    return json.loads(aggregation_metadata(resource, file_path).json())


@swagger_auto_schema(method='put', request_body=serializers.GeographicFeatureMetadataSerializer,
                     operation_description="Update Geographic Feature aggregation metadata",)
@swagger_auto_schema(method='get', responses={200: serializers.GeographicFeatureMetadataSerializer})
@api_view(['GET', 'PUT'])
def geographic_feature_metadata_json(request, pk, aggregation_path):
    if request.method == 'GET':
        resource, _, _ = authorize(request, pk,
                                   needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
        md_json = aggregation_metadata_json(resource, aggregation_path)
        return JsonResponse(md_json)

    resource, _, _ = authorize(request, pk,
                               needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    metadata_json_str = request.POST.get('metadata', None)
    metadata_json = json.loads(metadata_json_str)
    ingest_logical_file_metadata(metadata_json, resource)
    return HttpResponse(status=204)
