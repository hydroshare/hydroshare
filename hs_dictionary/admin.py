from django.contrib import admin
from .models import University


class UniversityAdmin(admin.ModelAdmin):
    pass

admin.site.register(University, UniversityAdmin)