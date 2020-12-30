import time

from django.conf import settings
from django.shortcuts import render
from django.views.generic import TemplateView

from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE


class ResourceLandingAPIView(TemplateView):

    def get(self, request, *args, **kwargs):
        maps_key = settings.MAPS_KEY if hasattr(settings, 'MAPS_KEY') else ''
        shortkey = 'bd8ab9a69c2a46009cc63966bec68b5f'  # TODO OBRIEN
        res, authorized, user = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
        content_model = res.get_content_model()

        start = time.time()
        context = {
            'data': 'Sample Test Data',
            'time': (time.time() - start) / 1000,
            'cm': content_model,
            'resource_edit_mode': False,
            'metadata_form': None,
            'abstract': 'This is an abstract',
            'creators': ['Sierra, CZO'],
            'title': 'Resource Title 1',
            'keywords': '["keywd1"]',
            'language': 'English',
            'readme': '',
            'contributors': [],
            'relations': [],
            'sources': [],
            'fundingagencies': [],
            'resource_creation_error': None,
            'tool_homepage_url': None,
            'file_type_error': None,
            'temporal_coverage': {'test': 'test'},  # dict
            'spatial_coverage': {'type': 'point', 'default_units': 'Decimal degrees',
                               'default_projection': 'WGS 84 EPSG:4326', 'exists': False},
            'metadata_status': 'Insufficient to publish or make public',
            'missing_metadata_elements': ['Abstract', 'Keywords'],
            'citation': 'Sierra, C. s. (2020). sadf, HydroShare, http://localhost:8000/resource/3a77bccab2a24bf483ab5cd4f33c6921',
            'custom_citation': '',
            'citation_id': None,
            'rights': 'This resource is shared under the Creative Commons Attribution CC BY. http://creativecommons.org/licenses/by/4.0/',
            'bag_url': '/django_irods/download/bags/3a77bccab2a24bf483ab5cd4f33c6921.zip?url_download=False&zipped=False&aggregation=False',
            'current_user': 'czo_sierra',
            'show_content_files': True,
            'validation_error': None,
            'discoverable': False,
            'resource_is_mine': False,
            'quota_holder': 'czo_sierra',
            'just_created': False,
            'relation_source_types': ('isCopiedFrom', 'The content of this resource was copied from'),
            'show_web_reference_note': False,
            'belongs_to_collections': [],
            'maps_key': maps_key
        }

        return render(request, 'hs_resource_landing/index.html', context)
