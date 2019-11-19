from django.contrib.gis import admin
from .models import CollectionResource

admin.site.unregister(CollectionResource)
