from django.contrib.gis import admin

from mezzanine.pages.admin import PageAdmin

from .models import RefTimeSeriesResource

admin.site.register(RefTimeSeriesResource, PageAdmin)