from django.contrib.gis import admin
from .models import NetcdfResource

admin.site.unregister(NetcdfResource)
