__author__ = 'Mohamed Morsy'
from mezzanine.pages.admin import PageAdmin
from django.contrib import admin
from .models import *

admin.site.register(SWATModelInstanceResource, PageAdmin)