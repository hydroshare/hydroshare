from django.contrib.gis import admin
from .models import GeographicFeatureResource

admin.site.unregister(GeographicFeatureResource)
