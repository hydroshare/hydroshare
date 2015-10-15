# This script dumps all HydroShare resource-relevant data into resource.json to be used to
# ingest the auxiliary resource access control data back into new system for manual migration purpose
# Author: Hong Yi
import os

os.environ.setdefault("PYTHONPATH", '/home/docker/hydroshare')
os.environ['DJANGO_SETTINGS_MODULE'] = 'hydroshare.settings'

import django
from django.core import serializers
from hs_core.models import GenericResource
from hs_app_netCDF.models import NetcdfResource
from hs_geo_raster_resource.models import RasterResource
from hs_app_timeseries.models import TimeSeriesResource
from hs_modelinstance.models import ModelInstanceResource
from hs_model_program.models import ModelProgramResource
from ref_ts.models import RefTimeSeries
from hs_tools_resource.models import ToolResource
from hs_swat_modelinstance.models import SWATModelInstanceResource

django.setup()

generic_res_objs = list(GenericResource.objects.all())
netcdf_res_objs = list(NetcdfResource.objects.all())
raster_res_objs = list(RasterResource.objects.all())
timeseries_res_objs = list(TimeSeriesResource.objects.all())
mi_res_objs = list(ModelInstanceResource.objects.all())
mp_res_objs = list(ModelProgramResource.objects.all())
refts_res_objs = list(RefTimeSeries.objects.all())
tool_res_objs = list(ToolResource.objects.all())
swat_inst_res_objs = list(SWATModelInstanceResource.objects.all())

all_objs = generic_res_objs + netcdf_res_objs + raster_res_objs + timeseries_res_objs + mi_res_objs + mp_res_objs + refts_res_objs + tool_res_objs + swat_inst_res_objs
data = serializers.serialize("json", all_objs, fields=('short_id', 'public', 'comments_count', 'rating_count', 'rating_average', 'rating_sum', 'user', 'creator', 'owners', 'view_users', 'edit_users'), indent=4)
out = open("resources.json", "w")

out.write(data)
out.close()
