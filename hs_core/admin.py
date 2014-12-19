from mezzanine.pages.admin import PageAdmin
from django.contrib.gis import admin
from .models import *
from dublincore.models import QualifiedDublinCoreElement

class InlineDublinCoreMetadata(generic.GenericTabularInline):
    model = QualifiedDublinCoreElement

class InlineResourceFiles(generic.GenericTabularInline):
    model = ResourceFile

class GenericResourceAdmin(PageAdmin):
    inlines = PageAdmin.inlines + [InlineDublinCoreMetadata, InlineResourceFiles]

admin.site.register(GenericResource, GenericResourceAdmin)
