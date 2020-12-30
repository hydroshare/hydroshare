import logging
from collections import namedtuple

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from rest_framework.views import APIView

from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
from dateutil import parser
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.utils.html import mark_safe, escapejs

from hs_core.forms import ExtendedMetadataForm
from hs_communities.models import Topic
from hs_core import languages_iso
from hs_core.hydroshare.resource import METADATA_STATUS_SUFFICIENT, METADATA_STATUS_INSUFFICIENT, \
    res_has_web_reference
from hs_core.models import Relation
from hs_core.views.utils import show_relations_section, \
    rights_allows_copy
import json

from hs_odm2.models import ODM2Variable

logger = logging.getLogger(__name__)

DateRange = namedtuple('DateRange', ['start', 'end'])


class ResourceLandingView(TemplateView):

    @staticmethod
    def check_for_validation(request):
        """Check for validation error in request session."""
        if request.method == "GET":
            validation_error = request.session.get('validation_error', None)
            if validation_error:
                del request.session['validation_error']
                return validation_error

        return None

    @staticmethod
    def _get_metadata_status(resource):
        if resource.metadata.has_all_required_elements():
            metadata_status = METADATA_STATUS_SUFFICIENT
        else:
            metadata_status = METADATA_STATUS_INSUFFICIENT

        return metadata_status

    def get(self, request, shortkey=None, *args, **kwargs):
        # TODO IF NOT LOGGED IN OR IF SHORTKEY NOT PROVIDED REDIRECT TO APPROPRIATE PAGES

        res, authorized, user = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)

        resource_edit = True
        extended_metadata_layout = None

        file_type_error = ''

        if request:
            file_type_error = request.session.get("file_type_error", None)
            if file_type_error:
                del request.session["file_type_error"]

        content_model = res.get_content_model()

        # whether the user has permission to view this resource
        can_view = content_model.can_view(request)
        if not can_view:
            if user.is_authenticated():
                raise PermissionDenied()
            return redirect_to_login(request.path)

        discoverable = content_model.raccess.discoverable
        validation_error = None
        resource_is_mine = True  # TODO OBRIEN
        if user.is_authenticated():
            resource_is_mine = content_model.rlabels.is_mine(user)

        metadata_status = self._get_metadata_status(content_model)

        belongs_to_collections = content_model.collections.all()

        tool_homepage_url = None
        if not resource_edit:  # In view mode
            landing_page_res_obj = content_model
            landing_page_res_type_str = landing_page_res_obj.resource_type
            if landing_page_res_type_str.lower() == "toolresource":
                if landing_page_res_obj.metadata.app_home_page_url:
                    tool_homepage_url = content_model.metadata.app_home_page_url.value

        # TODO BLOCK OF REINTEGRATING OLD FLOW
        just_created = False
        just_copied = False
        create_resource_error = None
        just_published = False

        if request:
            validation_error = self.check_for_validation(request)

            just_created = request.session.get('just_created', False)
            if 'just_created' in request.session:
                del request.session['just_created']

            just_copied = request.session.get('just_copied', False)
            if 'just_copied' in request.session:
                del request.session['just_copied']

            create_resource_error = request.session.get('resource_creation_error', None)
            if 'resource_creation_error' in request.session:
                del request.session['resource_creation_error']

            just_published = request.session.get('just_published', False)
            if 'just_published' in request.session:
                del request.session['just_published']

        bag_url = content_model.bag_url

        if user.is_authenticated():
            show_content_files = user.uaccess.can_view_resource(content_model)
        else:
            # if anonymous user getting access to a private resource (since resource is discoverable),
            # then don't show content files
            show_content_files = content_model.raccess.public

        rights_allow_copy = rights_allows_copy(content_model, user)

        qholder = content_model.get_quota_holder()

        readme = content_model.get_readme_file_content()
        if readme is None:
            readme = ''
        has_web_ref = res_has_web_reference(content_model)

        keywords = json.dumps([sub.value for sub in content_model.metadata.subjects.all()])
        topics = Topic.objects.all().values_list('name', flat=True).order_by('name')
        topics = list(topics)  # force QuerySet evaluation

        spatial_coverage = content_model.metadata.spatial_coverage
        if not resource_edit:
            spatial_coverage_data_dict = {}
        else:
            spatial_coverage_data_dict = {'type': 'point'}
        spatial_coverage_data_dict['default_units'] = \
            content_model.metadata.spatial_coverage_default_units
        spatial_coverage_data_dict['default_projection'] = \
            content_model.metadata.spatial_coverage_default_projection
        spatial_coverage_data_dict['exists'] = False

        if spatial_coverage:
            spatial_coverage_data_dict['exists'] = True
            spatial_coverage_data_dict['name'] = spatial_coverage.value.get('name', None)
            spatial_coverage_data_dict['units'] = spatial_coverage.value['units']
            spatial_coverage_data_dict['zunits'] = spatial_coverage.value.get('zunits', None)
            spatial_coverage_data_dict['projection'] = spatial_coverage.value.get('projection', None)
            spatial_coverage_data_dict['type'] = spatial_coverage.type
            spatial_coverage_data_dict['id'] = spatial_coverage.id
            if spatial_coverage.type == 'point':
                spatial_coverage_data_dict['east'] = spatial_coverage.value['east']
                spatial_coverage_data_dict['north'] = spatial_coverage.value['north']
                spatial_coverage_data_dict['elevation'] = spatial_coverage.value.get('elevation', None)
            else:
                spatial_coverage_data_dict['northlimit'] = spatial_coverage.value['northlimit']
                spatial_coverage_data_dict['eastlimit'] = spatial_coverage.value['eastlimit']
                spatial_coverage_data_dict['southlimit'] = spatial_coverage.value['southlimit']
                spatial_coverage_data_dict['westlimit'] = spatial_coverage.value['westlimit']
                spatial_coverage_data_dict['uplimit'] = spatial_coverage.value.get('uplimit', None)
                spatial_coverage_data_dict['downlimit'] = spatial_coverage.value.get('downlimit', None)

        temporal_coverage = content_model.metadata.temporal_coverage

        temporal_coverage_data_dict = {}
        if temporal_coverage:
            start_date = parser.parse(temporal_coverage.value['start'])
            end_date = parser.parse(temporal_coverage.value['end'])
            if not resource_edit:
                temporal_coverage_data_dict['start_date'] = start_date.strftime('%Y-%m-%d')
                temporal_coverage_data_dict['end_date'] = end_date.strftime('%Y-%m-%d')
                temporal_coverage_data_dict['name'] = temporal_coverage.value.get('name', '')
            else:
                temporal_coverage_data_dict['start'] = start_date.strftime('%m-%d-%Y')
                temporal_coverage_data_dict['end'] = end_date.strftime('%m-%d-%Y')
                temporal_coverage_data_dict['name'] = temporal_coverage.value.get('name', '')
                temporal_coverage_data_dict['id'] = temporal_coverage.id

        context = {
            'cm': content_model,
            'resource_edit_mode': resource_edit,
            'citation': content_model.get_citation(),
            'custom_citation': content_model.get_custom_citation(),
            'readme': readme,
            'creators': content_model.metadata.creators.all(),
            'contributors': content_model.metadata.contributors.all(),
            'temporal_coverage': temporal_coverage_data_dict,
            'spatial_coverage': spatial_coverage_data_dict,
            'keywords': keywords,
            'rights': content_model.metadata.rights,
            'sources': content_model.metadata.sources.all(),
            'relations': content_model.metadata.relations.all(),
            'fundingagencies': content_model.metadata.funding_agencies.all(),
            'metadata_status': metadata_status,
            'missing_metadata_elements': content_model.metadata.get_required_missing_elements(),
            'validation_error': validation_error if validation_error else None,
            'bag_url': bag_url,
            'current_user': user,
            'show_content_files': show_content_files,
            'discoverable': discoverable,
            'resource_is_mine': resource_is_mine,
            'quota_holder': qholder,
            'just_created': just_created,
            'maps_key': settings.MAPS_KEY if hasattr(settings, 'MAPS_KEY') else '',
            'show_web_reference_note': has_web_ref,
            'belongs_to_collections': belongs_to_collections,
            'metadata_form': None
        }

        if not resource_edit:

            # VIEW MODE

            content_model.update_view_count(request)

            languages_dict = dict(languages_iso.languages)
            language = languages_dict[content_model.metadata.language.code] if \
                content_model.metadata.language else None
            title = content_model.metadata.title.value if content_model.metadata.title else None
            abstract = content_model.metadata.description.abstract if \
                content_model.metadata.description else None
            context['title'] = title,
            context['file_type_error'] = file_type_error,
            context['just_copied'] = just_copied,
            context['just_published'] = just_published,
            context['rights_allow_copy'] = rights_allow_copy,
            context['abstract'] = abstract,
            context['language'] = language,
            context['show_relations_section'] = show_relations_section(content_model),
            context['resource_creation_error'] = create_resource_error,
            context['tool_homepage_url'] = tool_homepage_url,

            return render(request, 'hs_resource_landing/index.html', context)
        else:

            # EDIT MODE

            can_change = content_model.can_change(request) # whether the user has permission to change the model
            if not can_change:
                raise PermissionDenied()

            grps_member_of = []
            groups = Group.objects.filter(gaccess__active=True).exclude(name="Hydroshare Author")
            # for each group set group dynamic attributes
            for g in groups:
                g.is_user_member = user in g.gaccess.members
                if g.is_user_member:
                    grps_member_of.append(g)
            try:
                citation_id = content_model.metadata.citation.first().id
            except:
                citation_id = None

            if extended_metadata_layout:  # default assignment of None handles the View mode case
                context['metadata_form'] = ExtendedMetadataForm(resource_mode='edit' if can_change else 'view',
                                                                extended_metadata_layout=extended_metadata_layout)

            context['title'] = content_model.metadata.title,
            context['topics_json'] = mark_safe(escapejs(json.dumps(topics))),
            context['czo_user'] = any("CZO National" in x.name for x in user.uaccess.communities),
            context['odm2_terms'] = list(ODM2Variable.all()),
            context['citation_id'] = citation_id,
            context['relation_source_types'] = tuple((type_value, type_display)
                                                     for type_value, type_display in Relation.SOURCE_TYPES
                                                     if type_value != 'isReplacedBy' and
                                                     type_value != 'isVersionOf' and
                                                     type_value != 'hasPart'),

            return render(request, 'hs_resource_landing/index.html', context)
