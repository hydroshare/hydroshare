from django.contrib import admin
from hs_modflow_modelinstance.models import MODFLOWModelInstanceResource

admin.site.unregister(MODFLOWModelInstanceResource)
