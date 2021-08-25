import json

from django.db import transaction
from django.http import JsonResponse, HttpResponse
from drf_yasg.utils import swagger_auto_schema
from hs_core.hydroshare.hs_bagit import create_bag_metadata_files
from rest_framework.decorators import api_view

from hs_core.views import serializers, ACTION_TO_AUTHORIZE
from hs_core.views.utils import authorize


def resource_metadata(resource):
    from hsmodels.schemas import load_rdf
    file_with_path = resource.scimeta_path
    istorage = resource.get_irods_storage()
    with istorage.open(file_with_path) as f:
        metadata = load_rdf(f.read())
        return metadata


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


def metadata_json(resource):
    return json.loads(resource_metadata(resource).json())


@swagger_auto_schema(method='put', request_body=serializers.ResourceCreateRequestValidator,
                     operation_description="Create a resource",)
@api_view(['GET', 'PUT'])
def resource_metadata_json(request, pk):
    if request.method == 'GET':
        resource, _, _ = authorize(request, pk,
                                   needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
        md_json = metadata_json(resource)
        return JsonResponse(md_json)

    resource, _, _ = authorize(request, pk,
                               needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    data = request.data
    ingest_resource_metadata(resource, data)
    return HttpResponse(status=204)