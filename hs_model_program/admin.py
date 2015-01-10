#from mezzanine.pages.admin import PageAdmin
#from django.contrib.gis import admin
#from .models import *

#admin.site.register(HydroProgramResource, PageAdmin)

from django.contrib import admin
from .models import *

admin.site.register(HydroProgramResource)



