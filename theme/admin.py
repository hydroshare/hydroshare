from django.contrib import admin
from django import forms
from django.contrib.auth.models import User

from mezzanine.core.admin import TabularDynamicInlineAdmin
from mezzanine.utils.admin import SingletonAdmin

from .models import SiteConfiguration, HomePage, IconBox, UserQuota, QuotaMessage, QuotaRequest


class IconBoxInline(TabularDynamicInlineAdmin):
    model = IconBox
    extra = 5
    max_num = 5


class UserQuotaForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.exclude(is_superuser=True).exclude(is_active=False))

    class Meta:
        model = UserQuota
        fields = ['allocated_value',]
        readonly_fields = ['zone', 'unit', 'user_zone_value', 'data_zone_value',]

    def save(self, *args, **kwargs):
        instance = super(UserQuotaForm, self).save(commit=False)
        instance.user = self.cleaned_data['user']
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

    list_display = ('user', 'allocated_value', 'used_value', 'user_zone_value', 'data_zone_value', 'unit', 'zone')
    list_filter = ('zone',)

    readonly_fields = ('user', 'user_zone_value', 'data_zone_value',)
    search_fields = ('user__username',)

    def get_form(self, request, obj=None, **kwargs):
        # use a customized form class when adding a UserQuota object so that
        # the foreign key user field is available for selection.
        if obj is None:
            return UserQuotaForm
        else:
            return super(QuotaAdmin, self).get_form(request, obj, **kwargs)


admin.site.register(HomePage)
admin.site.register(SiteConfiguration, SingletonAdmin)
admin.site.register(UserQuota, QuotaAdmin)
admin.site.register(QuotaRequest, QuotaRequestAdmin)
admin.site.register(QuotaMessage, SingletonAdmin)
