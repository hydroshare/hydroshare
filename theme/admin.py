from django import forms
from django.contrib import admin
from django.contrib.auth.models import User
from mezzanine.core.admin import TabularDynamicInlineAdmin
from mezzanine.utils.admin import SingletonAdmin

from .models import (HomePage, IconBox, QuotaMessage, QuotaRequest,
                     SiteConfiguration, UserQuota)


class IconBoxInline(TabularDynamicInlineAdmin):
    model = IconBox
    extra = 5
    max_num = 5


class UserQuotaForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.exclude(is_superuser=True).exclude(is_active=False))

    class Meta:
        model = UserQuota
        exclude = ['zone',]
        #readonly_fields = ['zone', 'unit', 'data_zone_value',]

    allocated_value = forms.FloatField()
    unit = forms.CharField()

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        if instance:
            kwargs['initial'] = {'allocated_value': instance.allocated_value,
                                 #'zone': instance.zone,
                                 'unit': instance.unit,
                                 'data_zone_value': instance.data_zone_value}
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        instance = super(UserQuotaForm, self).save(commit=False)
        instance.user = self.cleaned_data['user']
        instance.save_allocated_value(self.cleaned_data['allocated_value'], self.cleaned_data['unit'],)
        return instance


class QuotaRequestForm(forms.ModelForm):

    class Meta:
        model = QuotaRequest
        fields = "__all__"


class QuotaRequestAdmin(admin.ModelAdmin):
    model = QuotaRequest
    list_display = ('request_from', 'quota', 'date_requested', 'justification', 'storage', 'status')
    list_filter = ('status',)
    readonly_fields = ('request_from', 'quota', 'date_requested', 'justification')
    search_fields = ('request_from__username', 'justification')

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            return QuotaRequestForm
        else:
            return super(QuotaRequestAdmin, self).get_form(request, obj, **kwargs)


class QuotaAdmin(admin.ModelAdmin):
    model = UserQuota

    list_display = ('user', 'allocated_value', 'unit', 'zone')
    list_filter = ('zone',)

    readonly_fields = ('user', 'data_zone_value')
    search_fields = ('user__username',)

    def get_form(self, request, obj=None, **kwargs):
        # use a customized form class when adding a UserQuota object so that
        # the foreign key user field is available for selection.
        return UserQuotaForm


admin.site.register(HomePage)
admin.site.register(SiteConfiguration, SingletonAdmin)
admin.site.register(UserQuota, QuotaAdmin)
admin.site.register(QuotaRequest, QuotaRequestAdmin)
admin.site.register(QuotaMessage, SingletonAdmin)
