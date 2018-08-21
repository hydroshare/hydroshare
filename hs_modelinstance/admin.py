from django.contrib import admin
from hs_modelinstance.models import ModelInstanceResource

admin.site.unregister(ModelInstanceResource)
