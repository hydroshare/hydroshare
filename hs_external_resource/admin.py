from django.contrib.gis import admin
from .models import ExternalResource

admin.site.unregister(ExternalResource)
