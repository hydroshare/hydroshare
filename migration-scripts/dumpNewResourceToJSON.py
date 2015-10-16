# This script dumps HydroShare resource uuid to primary id mapping into new_resources.json to be used   
# to ingest the auxiliary resource data back into new system for manual migration purpose. This script 
# should be run in the new system to be migrated to.
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

django.setup()

generic_res_objs = list(GenericResource.objects.all())
netcdf_res_objs = list(NetcdfResource.objects.all())
raster_res_objs = list(RasterResource.objects.all())
timeseries_res_objs = list(TimeSeriesResource.objects.all())
mi_res_objs = list(ModelInstanceResource.objects.all())
mp_res_objs = list(ModelProgramResource.objects.all())
refts_res_objs = list(RefTimeSeries.objects.all())
tool_res_objs = list(ToolResource.objects.all())

all_objs = generic_res_objs + netcdf_res_objs + raster_res_objs + timeseries_res_objs + mi_res_objs + mp_res_objs + refts_res_objs + tool_res_objs
data = serializers.serialize("json", all_objs, fields=('short_id', 'resource_type'), indent=4)
out = open("new_resources.json", "w")

out.write(data)
out.close()
