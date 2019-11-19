from django.contrib.gis import admin
from .models import ScriptResource

admin.site.unregister(ScriptResource)
