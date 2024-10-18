from django.contrib import admin

from .models import SubjectArea, UncategorizedTerm, University


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(UncategorizedTerm)
class UncategorizedTermAdmin(admin.ModelAdmin):
    pass


@admin.register(SubjectArea)
class SubjectAreaAdmin(admin.ModelAdmin):
    list_display = ['name']
