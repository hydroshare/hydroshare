from django.contrib.gis import admin
from .models import RefTimeSeriesResource

admin.site.unregister(RefTimeSeriesResource)
