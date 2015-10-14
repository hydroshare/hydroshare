# This script dumps all HydroShare ModelProgram resource-relevant data into modelprogramresource.json to be used to  
# ingest the auxiliary generic resource access control data back into new system for manual migration purpose.
# This script is most likely not needed, though, since we most likely do not need to dump resources by type
# but rather dump all resources with all types with single script.   
# Author: Hong Yi
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'hydroshare.settings'

import django
from django.core import serializers
from hs_model_program.models import ModelProgramResource 

django.setup()
data = serializers.serialize("json", ModelProgramResource.objects.all(), fields=('short_id', 'public', 'comments_count', 'rating_count', 'rating_average', 'rating_sum', 'user', 'creator', 'owners', 'view_users', 'edit_users'), indent=4)
out = open("modelprogramresource.json", "w")
out.write(data)
out.close()
