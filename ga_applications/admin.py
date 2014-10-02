from copy import deepcopy
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from mezzanine.pages import admin as pages_admin
from mezzanine.pages.admin import page_fieldsets
from .models import *

class LayersInline(admin.TabularInline):
    model = ApplicationLayer
    extra = 1


class ApplicationAdmin(ModelAdmin):
    inlines = (LayersInline,)

admin.site.register(Application, ApplicationAdmin)