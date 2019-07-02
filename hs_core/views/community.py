from __future__ import absolute_import

import json
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.utils.decorators import method_decorator
from django.utils.html import mark_safe, escapejs
from django.views.generic import TemplateView
from hs_communities.models import Topics

logger = logging.getLogger(__name__)


class TopicsView(TemplateView):
    template_name = 'pages/topics.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(TopicsView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        u = User.objects.get(pk=self.request.user.id)
        groups = Group.objects.filter(gaccess__active=True).exclude(name="Hydroshare Author")
        # for each group set group dynamic attributes
        for g in groups:
            g.is_user_member = u in g.gaccess.members
            g.join_request_waiting_owner_action = g.gaccess.group_membership_requests.filter(request_from=u).exists()
            g.join_request_waiting_user_action = g.gaccess.group_membership_requests.filter(invitation_to=u).exists()
            g.join_request = None
            if g.join_request_waiting_owner_action or g.join_request_waiting_user_action:
                g.join_request = g.gaccess.group_membership_requests.filter(request_from=u).first() or \
                                 g.gaccess.group_membership_requests.filter(invitation_to=u).first()

        topics = ["Air Temperature", "Barometric Pressure", "Chlorophyll", "Climate", "Diatoms", "Digital Elevation Model(DEM)",
         "Dissolved Organic Matter(DOM)", "Ecosystem model", "Electrical Conductivity", "Flux Tower", "Geology",
         "Geomorphology", "Geophysics", "GIS / Map Data", "Ground Penetrating Radar(GPR)", "Groundwater Chemistry",
         "Groundwater Depth", "Groundwater Temperatures", "Hydropedologic Properties", "Land Cover", "Land Use History",
         "LiDAR", "Lysimeter Water Samples Chemistry", "Matric Potential", "Meteorology", "Nutrient Fluxes",
         "Overland Water Chemistry", "Ozone", "Photographic Imagery", "Piezometer", "Precipitation",
         "Precipitation Chemistry", "Rainfall Chemistry", "Regolith Survey", "Reservoir Height", "Rock Moisture",
         "Sap Flow", "Sediment Transport", "Seismic Refraction", "Snow Depth", "Snow Pits", "Snow Survey",
         "Soil Biogeochemistry", "Soil Electrical Resistivity", "Soil Evapotranspiration", "Soil Gas",
         "Soil Geochemistry", "Soil Invertebrates", "Soil Microbes", "Soil Mineralogy", "Soil Moisture",
         "Soil Porewater Chemistry", "Soil Porosity", "Soil Redox Potential", "Soil Respiration", "Soil Survey",
         "Soil Temperature", "Soil Texture", "Soil Water", "Soil Water Chemistry", "Solar Radiation", "Stable Isotopes",
         "Stage", "Stream Ecology", "Stream Suspended Sediment", "Stream Water Chemistry", "Stream Water Temperatures",
         "Streamflow / Discharge", "Surface Water Chemistry", "Throughfall Chemistry", "Topographic Carbon Storage",
         "Tree Growth & Physiology", "Vegetation", "Water Potential", "Well Water Levels"]

        topic1 = Topics(name="Air Temp")


        return {
            'topics_json': mark_safe(escapejs(json.dumps(topics)))
        }
