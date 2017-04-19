# Register your models here.
from django.contrib.gis import admin

from mezzanine.pages.admin import PageAdmin

from .models import ToolResource
from copy import deepcopy

author_extra_fieldsets = ((None, {"fields": ("approved",)}),)


class ToolAdmin(PageAdmin):
    fieldsets = deepcopy(PageAdmin.fieldsets) + author_extra_fieldsets

admin.site.register(ToolResource, ToolAdmin)
