from django.contrib import admin

from mezzanine.core.admin import TabularDynamicInlineAdmin, SingletonAdmin
from mezzanine.pages.admin import PageAdmin

from models import SiteConfiguration, HomePage, IconBox, UserQuota, QuotaMessage


class IconBoxInline(TabularDynamicInlineAdmin):
    model = IconBox
    extra = 5
    max_num = 5


class HomePageAdmin(PageAdmin):
    inlines = (IconBoxInline,)


class QuotaAdmin(admin.ModelAdmin):
    list_display = ('user', 'allocated_value', 'used_value', 'unit', 'zone')
    list_filter = ('zone',)


admin.site.register(HomePage, HomePageAdmin)
admin.site.register(SiteConfiguration, SingletonAdmin)
admin.site.register(UserQuota, QuotaAdmin)
admin.site.register(QuotaMessage, SingletonAdmin)
