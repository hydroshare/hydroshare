# Register your models here.
from django.contrib.gis import admin

from mezzanine.pages.admin import PageAdmin

from .models import ToolResource

admin.site.register(ToolResource, PageAdmin)