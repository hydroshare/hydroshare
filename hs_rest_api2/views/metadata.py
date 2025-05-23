from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework.exceptions import NotFound

from hs_core import hydroshare
from hs_rest_api2.metadata import ingest_resource_metadata, ingest_aggregation_metadata, \
    aggregation_metadata_json_loads, resource_metadata_json_loads
from rest_framework.decorators import api_view

from hs_core.views import ACTION_TO_AUTHORIZE
from hs_core.views.utils import authorize
from hs_rest_api2 import serializers
from hs_access_control.models.utilities import get_user_resource_privilege
from hs_access_control.models.privilege import PrivilegeCodes


@swagger_auto_schema(method='put', request_body=serializers.ResourceMetadataInSerializer,
                     responses={200: serializers.ResourceMetadataSerializer},
                     operation_description="Update Resource level metadata in json",)
@swagger_auto_schema(method='get', responses={200: serializers.ResourceMetadataSerializer},
                     operation_description="Get Resource level metadata json")
@api_view(['GET', 'PUT'])
def resource_metadata_json(request, pk):
    if request.method == 'PUT':
        resource, _, _ = authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
        if resource.raccess.published:
            raise PermissionDenied
        md = request.data
        return JsonResponse(ingest_resource_metadata(resource, md))

    resource, _, _ = authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
    md_json = resource_metadata_json_loads(resource)
    return JsonResponse(md_json)


def aggregation_metadata_json(request, pk, aggregation_path):
    if request.method == 'PUT':
        resource, _, _ = authorize(request, pk,
                                   needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
        if resource.raccess.published:
            raise PermissionDenied
        metadata_json = request.data
        return JsonResponse(ingest_aggregation_metadata(resource, metadata_json, aggregation_path))

    resource, _, _ = authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
    md_json = aggregation_metadata_json_loads(resource, aggregation_path)
    return JsonResponse(md_json)


@swagger_auto_schema(method='put', request_body=serializers.GeographicFeatureMetadataInSerializer, response={204: None},
                     responses={200: serializers.GeographicFeatureMetadataSerializer},
                     operation_description="Update Geographic Feature aggregation metadata with json",)
@swagger_auto_schema(method='get', responses={200: serializers.GeographicFeatureMetadataSerializer},
                     operation_description="Get Geographic Feature aggregation metadata json")
@api_view(['GET', 'PUT'])
def geographic_feature_metadata_json(request, pk, aggregation_path):
    return aggregation_metadata_json(request, pk, aggregation_path)


@swagger_auto_schema(method='put', request_body=serializers.GeographicRasterMetadataInSerializer, response={204: None},
                     responses={200: serializers.GeographicRasterMetadataSerializer},
                     operation_description="Update Geographic Raster aggregation metadata with json",)
@swagger_auto_schema(method='get', responses={200: serializers.GeographicRasterMetadataSerializer},
                     operation_description="Get Geographic Raster aggregation metadata json")
@api_view(['GET', 'PUT'])
def geographic_raster_metadata_json(request, pk, aggregation_path):
    return aggregation_metadata_json(request, pk, aggregation_path)


@swagger_auto_schema(method='put', request_body=serializers.TimeSeriesMetadataInSerializer, response={204: None},
                     responses={200: serializers.TimeSeriesMetadataSerializer},
                     operation_description="Update Time Series aggregation metadata with json",)
@swagger_auto_schema(method='get', responses={200: serializers.TimeSeriesMetadataSerializer},
                     operation_description="Get Time Series aggregation metadata json")
@api_view(['GET', 'PUT'])
def time_series_metadata_json(request, pk, aggregation_path):
    return aggregation_metadata_json(request, pk, aggregation_path)


@swagger_auto_schema(method='put', request_body=serializers.FileSetMetadataInSerializer, response={204: None},
                     responses={200: serializers.FileSetMetadataSerializer},
                     operation_description="Update FileSet aggregation metadata with json",)
@swagger_auto_schema(method='get', responses={200: serializers.FileSetMetadataSerializer},
                     operation_description="Get FileSet aggregation metadata json")
@api_view(['GET', 'PUT'])
def file_set_metadata_json(request, pk, aggregation_path):
    return aggregation_metadata_json(request, pk, aggregation_path)


@swagger_auto_schema(method='put', request_body=serializers.MultidimensionalMetadataInSerializer, response={204: None},
                     responses={200: serializers.MultidimensionalMetadataSerializer},
                     operation_description="Update Multidimensional aggregation metadata with json",)
@swagger_auto_schema(method='get', responses={200: serializers.MultidimensionalMetadataSerializer},
                     operation_description="Get Multidimensional aggregation metadata json")
@api_view(['GET', 'PUT'])
def multidimensional_metadata_json(request, pk, aggregation_path):
    return aggregation_metadata_json(request, pk, aggregation_path)


@swagger_auto_schema(method='put', request_body=serializers.ReferencedTimeSeriesMetadataInSerializer,
                     responses={200: serializers.ReferencedTimeSeriesMetadataSerializer},
                     response={204: None},
                     operation_description="Update Referenced TimeSeries aggregation metadata with json",)
@swagger_auto_schema(method='get', responses={200: serializers.ReferencedTimeSeriesMetadataSerializer},
                     operation_description="Get Referenced TimeSeries aggregation metadata json")
@api_view(['GET', 'PUT'])
def referenced_time_series_metadata_json(request, pk, aggregation_path):
    return aggregation_metadata_json(request, pk, aggregation_path)


@swagger_auto_schema(method='put', request_body=serializers.SingleFileMetadataInSerializer, response={204: None},
                     responses={200: serializers.SingleFileMetadataSerializer},
                     operation_description="Update Single File aggregation metadata with json",)
@swagger_auto_schema(method='get', responses={200: serializers.SingleFileMetadataSerializer},
                     operation_description="Get Single File aggregation metadata json")
@api_view(['GET', 'PUT'])
def single_file_metadata_json(request, pk, aggregation_path):
    return aggregation_metadata_json(request, pk, aggregation_path)


@swagger_auto_schema(method='put', request_body=serializers.CSVFileMetadataInSerializer, response={204: None},
                     responses={200: serializers.CSVFileMetadataSerializer},
                     operation_description="Update CSV File aggregation metadata with json",)
@swagger_auto_schema(method='get', responses={200: serializers.CSVFileMetadataSerializer},
                     operation_description="Get CSV File aggregation metadata json")
@api_view(['GET', 'PUT'])
def csv_file_metadata_json(request, pk, aggregation_path):
    return aggregation_metadata_json(request, pk, aggregation_path)


@swagger_auto_schema(method='put', request_body=serializers.ModelProgramMetadataInSerializer, response={204: None},
                     responses={200: serializers.ModelProgramMetadataSerializer},
                     operation_description="Update Model Program aggregation metadata with json",)
@swagger_auto_schema(method='get', responses={200: serializers.ModelProgramMetadataSerializer},
                     operation_description="Get Model Program aggregation metadata json")
@api_view(['GET', 'PUT'])
def model_program_metadata_json(request, pk, aggregation_path):
    return aggregation_metadata_json(request, pk, aggregation_path)


@swagger_auto_schema(method='put', request_body=serializers.ModelInstanceMetadataInSerializer, response={204: None},
                     responses={200: serializers.ModelInstanceMetadataSerializer},
                     operation_description="Update Model Instance aggregation metadata with json",)
@swagger_auto_schema(method='get', responses={200: serializers.ModelInstanceMetadataSerializer},
                     operation_description="Get Model Instance aggregation metadata json")
@api_view(['GET', 'PUT'])
def model_instance_metadata_json(request, pk, aggregation_path):
    return aggregation_metadata_json(request, pk, aggregation_path)


@swagger_auto_schema(method='get', responses={200: serializers.ResourceSharingStatusSerializer},
                     operation_description="Get the sharing status of a resource")
@api_view(['GET'])
def resource_sharing_status_json(_, pk):
    try:
        res = hydroshare.utils.get_resource_by_shortkey(pk, or_404=False)
    except ObjectDoesNotExist:
        raise NotFound(detail=f"No resource was found for resource id:{pk}")

    if res.raccess.published:
        return JsonResponse({"sharing_status": "published"})
    elif res.raccess.public:
        return JsonResponse({"sharing_status": "public"})
    elif res.raccess.discoverable:
        return JsonResponse({"sharing_status": "discoverable"})
    return JsonResponse({"sharing_status": "private"})


@swagger_auto_schema(method='get', responses={200: serializers.ResourcePermissionSerializer},
                     operation_description="Get the permission of a user on a resource")
@api_view(['GET'])
def resource_permission_json(request, pk):
    if request.user.is_authenticated:
        user_id = request.user.id
    else:
        user_id = None

    privilege = get_user_resource_privilege(user_id, pk)
    if privilege == PrivilegeCodes.OWNER:
        permission = "owner"
    elif privilege == PrivilegeCodes.CHANGE:
        permission = "edit"
    elif privilege == PrivilegeCodes.VIEW:
        permission = "view"
    else:
        permission = "none"

    return JsonResponse({"permission": permission})
