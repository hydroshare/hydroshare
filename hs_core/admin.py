from mezzanine.pages.admin import PageAdmin
from django.contrib.gis import admin
from .models import *

class InlineResourceFiles(generic.GenericTabularInline):
    model = ResourceFile

class GenericResourceAdmin(PageAdmin):
    inlines = PageAdmin.inlines + [InlineResourceFiles]

admin.site.register(GenericResource, GenericResourceAdmin)
