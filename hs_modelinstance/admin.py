#from mezzanine.pages.admin import PageAdmin
#from django.contrib.gis import admin
from django.contrib import admin
from .models import *

admin.site.register(ModelInstanceResource)
