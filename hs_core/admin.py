from mezzanine.pages.admin import PageAdmin
from django.contrib.gis import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import *

class InlineResourceFiles(GenericTabularInline):
    model = ResourceFile

class GenericResourceAdmin(PageAdmin):
    inlines = PageAdmin.inlines + [InlineResourceFiles]

admin.site.register(GenericResource, GenericResourceAdmin)
