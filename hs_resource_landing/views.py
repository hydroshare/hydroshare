import json
import logging
import time
from collections import namedtuple

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from rest_framework.views import APIView

from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE

logger = logging.getLogger(__name__)

DateRange = namedtuple('DateRange', ['start', 'end'])


class ResourceLandingView(TemplateView):

    def get(self, request, *args, **kwargs):
        maps_key = settings.MAPS_KEY if hasattr(settings, 'MAPS_KEY') else ''
        return render(request, 'hs_resource_landing/index.html', {'maps_key': maps_key})


@method_decorator(login_required, name='dispatch')
class ResourceLandingAPI(APIView):

    def __init__(self, **kwargs):
        super(ResourceLandingAPI, self).__init__(**kwargs)

    def get(self, request, shortkey, *args, **kwargs):
        res, authorized, user = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
        start = time.time()

        # 'cm': content_model,
        # 'resource_edit_mode': resource_edit,
        # 'metadata_form': None,
        # 'citation': content_model.get_citation(),
        # 'custom_citation': content_model.get_custom_citation(),
        # 'title': title,
        # 'readme': readme,
        # 'abstract': abstract,
        # 'creators': content_model.metadata.creators.all(),
        # 'contributors': content_model.metadata.contributors.all(),
        # 'temporal_coverage': temporal_coverage_data_dict,
        # 'spatial_coverage': spatial_coverage_data_dict,
        # 'keywords': keywords,
        # 'language': language,
        # 'rights': content_model.metadata.rights,
        # 'sources': content_model.metadata.sources.all(),
        # 'relations': content_model.metadata.relations.all(),
        # 'show_relations_section': show_relations_section(content_model),
        # 'fundingagencies': content_model.metadata.funding_agencies.all(),
        # 'metadata_status': metadata_status,
        # 'missing_metadata_elements': missing_metadata_elements,
        # 'validation_error': validation_error if validation_error else None,
        # 'resource_creation_error': create_resource_error,
        # 'tool_homepage_url': tool_homepage_url,
        # 'file_type_error': file_type_error,
        # 'just_created': just_created,
        # 'just_copied': just_copied,
        # 'just_published': just_published,
        # 'bag_url': bag_url,
        # 'show_content_files': show_content_files,
        # 'discoverable': discoverable,
        # 'resource_is_mine': resource_is_mine,
        # 'rights_allow_copy': rights_allow_copy,
        # 'quota_holder': qholder,
        # 'belongs_to_collections': belongs_to_collections,
        # 'show_web_reference_note': has_web_ref,
        # 'current_user': user,

        # # resources = GenericResource.objects.all()
        # user = User.objects.get(pk=self.request.user.id)
        #
        # grps_member_of = []
        # groups = Group.objects.filter(gaccess__active=True).exclude(name="Hydroshare Author")
        # # for each group set group dynamic attributes
        # for g in groups:
        #     g.is_user_member = user in g.gaccess.members
        #     if g.is_user_member:
        #         grps_member_of.append(g)

        # content_model = page.get_content_model()
        # whether the user has permission to view this resource
        # can_view = content_model.can_view(request)
        # if not can_view:
        #     if user.is_authenticated():
        #         raise PermissionDenied()
        #     return redirect_to_login(request.path)

        # discoverable = content_model.raccess.discoverable
        # validation_error = None
        # resource_is_mine = False
        # if user.is_authenticated():
        #     resource_is_mine = content_model.rlabels.is_mine(user)
        #
        # metadata_status = _get_metadata_status(content_model)
        #
        # belongs_to_collections = content_model.collections.all()
        # discoverable = GenericResource.discoverable_resources.all()
        # public = GenericResource.public_resources.all()

        data = json.dumps({
            'data': 'Sample Test Data',
            'time': (time.time() - start) / 1000,
            'cm': 'content model',
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
        })

        return JsonResponse(data, safe=False, status=200)
