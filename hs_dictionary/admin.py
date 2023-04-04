from django.contrib import admin
from .models import University, UncategorizedTerm, SubjectArea


class UniversityAdmin(admin.ModelAdmin):
    list_display = ['name']


admin.site.register(University, UniversityAdmin)


class UncategorizedTermAdmin(admin.ModelAdmin):
    pass


admin.site.register(UncategorizedTerm, UncategorizedTermAdmin)


class SubjectAreaAdmin(admin.ModelAdmin):
    list_display = ['name']


admin.site.register(SubjectArea, SubjectAreaAdmin)
