# Register your models here.
from django.contrib.gis import admin

from mezzanine.pages.admin import PageAdmin

from .models import ToolResource, ToolMetaData


class ToolMetaDataAdmin(admin.ModelAdmin):
    model = ToolMetaData
    fields = ['approved']

    def has_add_permission(self, request):
        return False


admin.site.register(ToolMetaData, ToolMetaDataAdmin)
admin.site.register(ToolResource, PageAdmin)
