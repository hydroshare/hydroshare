from mezzanine.pages.admin import PageAdmin
from django.contrib.gis import admin
from .models import *

# admin.site.register(MyResource, PageAdmin)


admin.site.register(RasterResource, PageAdmin)