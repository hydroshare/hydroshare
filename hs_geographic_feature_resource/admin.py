# Register your models here.
from mezzanine.pages.admin import PageAdmin
from django.contrib.gis import admin
from .models import *

admin.site.register(GeographicFeatureResource, PageAdmin)
