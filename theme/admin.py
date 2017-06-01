from django.contrib import admin
from django import forms
from django.contrib.auth.models import User

from mezzanine.core.admin import TabularDynamicInlineAdmin, SingletonAdmin, OwnableAdmin
from mezzanine.pages.admin import PageAdmin

from models import SiteConfiguration, HomePage, IconBox, UserQuota, QuotaMessage


class IconBoxInline(TabularDynamicInlineAdmin):
    model = IconBox
    extra = 5
    max_num = 5


class HomePageAdmin(PageAdmin):
    inlines = (IconBoxInline,)

class UserQuotaForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.all())
    class Meta:
        model = UserQuota
        fields = ['user', 'allocated_value', 'used_value', 'unit', 'zone']
        exclude = []

    def __init__(self, *args, **kwargs):
        super(UserQuotaForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.user_id:
            # change a record, user foreign key cannot be changed
            self.fields['user'].initial = self.instance.user
            self.fields['user'].widget.attrs['readonly'] = True
            self.fields['user'].widget.attrs['disabled'] = True

    # def clean_user(self):
    #     if self.instance.pk is None:
    #         return self.instance.user
    #     else:
    #         return self.cleaned_data['user']
    #
    def save(self, *args, **kwargs):
         instance = super(UserQuotaForm, self).save(commit=False)
         self.cleaned_data['user'].save()
         return instance

class QuotaAdmin(admin.ModelAdmin):
    model = UserQuota
    form = UserQuotaForm
    # list_select_related = True
    # list_editable = ('user',)
    #readonly_fields = ('user',)
    #add_fieldsets = (
    #    (None, {
    #        'classes': ('wide',),
    #        'fields': ('user',)}),
    #)
    list_display = ('user', 'allocated_value', 'used_value', 'unit', 'zone')
    list_filter = ('zone',)


admin.site.register(HomePage, HomePageAdmin)
admin.site.register(SiteConfiguration, SingletonAdmin)
admin.site.register(User, admin.ModelAdmin)
admin.site.register(UserQuota, QuotaAdmin)
admin.site.register(QuotaMessage, SingletonAdmin)
