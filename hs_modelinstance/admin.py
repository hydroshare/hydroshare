from mezzanine.pages.admin import PageAdmin

from django.contrib import admin

from hs_modelinstance.models import ModelInstanceResource

admin.site.register(ModelInstanceResource, PageAdmin)
