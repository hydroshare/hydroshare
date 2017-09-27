# Register your models here.
from django.contrib.gis import admin

from mezzanine.pages.admin import PageAdmin

from .models import ToolResource, ToolMetaData


class ToolMetaDataAdmin(admin.ModelAdmin):
    model = ToolMetaData
    fields = ['approved']


admin.site.register(ToolMetaData, ToolMetaDataAdmin)
admin.site.register(ToolResource, PageAdmin)
