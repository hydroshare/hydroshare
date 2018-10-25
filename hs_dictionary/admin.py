from django.contrib import admin
from .models import University, UncategorizedTerm


class UniversityAdmin(admin.ModelAdmin):
    pass


class UncategorizedTermAdmin(admin.ModelAdmin):
    pass


admin.site.register(UncategorizedTerm, UncategorizedTermAdmin)
admin.site.register(University, UniversityAdmin)
