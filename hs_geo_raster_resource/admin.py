from django.contrib.gis import admin
from .models import RasterResource

admin.site.unregister(RasterResource)
