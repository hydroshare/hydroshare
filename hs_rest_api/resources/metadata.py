import os

from django.http import JsonResponse
from rest_framework.decorators import api_view

from hs_composite_resource.models import CompositeResource
from hs_core.hydroshare.hs_bagit import create_resource_map_xml
from hs_core.hydroshare.utils import current_site_url


@api_view(['GET'])
def all_metadata_files(request, resource_id):
    url_base = current_site_url()
    resource = CompositeResource.objects.get(short_id=resource_id)
    metadata_json = {}
    res_metadata = resource.get_metadata_xml()
    res_map = create_resource_map_xml(resource)
    metadata_json[os.path.join(url_base, resource.resmap_path)] = res_metadata
    metadata_json[os.path.join(url_base, resource.scimeta_path)] = res_map


    for aggregation in resource.logical_files:
        metadata_json[os.path.join(url_base, aggregation.map_file_path)] = aggregation.generate_map_xml()
        metadata_json[os.path.join(url_base, aggregation.metadata_file_path)] = aggregation.metadata.get_xml()

    return JsonResponse(metadata_json)