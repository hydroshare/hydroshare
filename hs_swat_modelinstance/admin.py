__author__ = 'Mohamed Morsy'
from mezzanine.pages.admin import PageAdmin

from django.contrib import admin

from hs_swat_modelinstance.models import SWATModelInstanceResource

admin.site.register(SWATModelInstanceResource, PageAdmin)