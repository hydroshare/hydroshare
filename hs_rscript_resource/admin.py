# Register your models here.
from django.contrib.gis import admin

from mezzanine.pages.admin import PageAdmin

from .models import RScriptResource

admin.site.register(RScriptResource, PageAdmin)