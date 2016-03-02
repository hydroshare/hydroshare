from mezzanine.pages.admin import PageAdmin
from django.contrib.gis import admin
from ga_resources.models import *
from django.forms import ModelForm
from django import forms

class RenderedLayerAdminForm(ModelForm):
   data_resource = forms.ModelChoiceField(queryset=DataResource.objects.order_by('slug'))
   default_style = forms.ModelChoiceField(queryset=Style.objects.order_by('slug'))
   styles = forms.ModelMultipleChoiceField(queryset=Style.objects.order_by('slug'))

   class Meta:
      model = RenderedLayer
      fields = ['data_resource', 'default_style', 'default_class', 'styles', 'public', 'owner']

class RenderedLayerAdmin(PageAdmin):
   form = RenderedLayerAdminForm

# TODO add prepopulated fields to all models with slug fields.
# class ArticleAdmin(admin.ModelAdmin):
#   prepopulated_fields = {"slug": ("title",)}


#class OSMPageAdmin(admin.OSMGeoAdmin):
#    fieldsets = deepcopy(PageAdmin.fieldsets)

#class DataResourceAdmin(admin.OSMGeoAdmin):
#    fieldsets = deepcopy(PageAdmin.fieldsets) + ((None, {"fields" : (
#        'content',
#        "resource_file", "resource_url", "resource_irods_env", "resource_irods_file",
#        "time_represented","perform_caching","cache_ttl","data_cache","bounding_box","kind","driver"
#    )}),)

admin.site.register(CatalogPage, PageAdmin)
#admin.site.register(Verb, PageAdmin)
admin.site.register(DataResource, PageAdmin)
admin.site.register(ResourceGroup, PageAdmin)
admin.site.register(OrderedResource)

admin.site.register(RelatedResource, PageAdmin)

admin.site.register(RenderedLayer, RenderedLayerAdmin)
admin.site.register(Style, PageAdmin)
