from django.contrib import admin
from django import forms
from django.contrib.auth.models import User

from mezzanine.core.admin import TabularDynamicInlineAdmin
from mezzanine.utils.admin import SingletonAdmin
#from mezzanine.pages.admin import PageAdmin

from models import SiteConfiguration, HomePage, IconBox, UserQuota, QuotaMessage


class IconBoxInline(TabularDynamicInlineAdmin):
    model = IconBox
    extra = 5
    max_num = 5


#class HomePageAdmin(PageAdmin):
#    PageAdmin.inlines = (IconBoxInline,)


class UserQuotaForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.exclude(is_superuser=True).exclude(is_active=False))

    class Meta:
        model = UserQuota
        fields = ['allocated_value', 'used_value', 'unit', 'zone']

    def save(self, *args, **kwargs):
        instance = super(UserQuotaForm, self).save(commit=False)
        instance.user = self.cleaned_data['user']
        return instance


class QuotaAdmin(admin.ModelAdmin):
    model = UserQuota

    list_display = ('user', 'allocated_value', 'used_value', 'unit', 'zone')
    list_filter = ('zone', 'user__username', )

    readonly_fields = ('user',)

    def get_form(self, request, obj=None, **kwargs):
        # use a customized form class when adding a UserQuota object so that
        # the foreign key user field is available for selection.
        if obj is None:
            return UserQuotaForm
        else:
            return super(QuotaAdmin, self).get_form(request, obj, **kwargs)


#admin.site.register(HomePage, HomePageAdmin)
admin.site.register(SiteConfiguration, SingletonAdmin)
admin.site.register(UserQuota, QuotaAdmin)
admin.site.register(QuotaMessage, SingletonAdmin)
