
from django.contrib import admin

from mezzanine.core.admin import TabularDynamicInlineAdmin, SingletonAdmin
from mezzanine.pages.admin import PageAdmin

from models import SiteConfiguration, HomePage, IconBox

admin.site.register(SiteConfiguration, SingletonAdmin)


class IconBoxInline(TabularDynamicInlineAdmin):
    model = IconBox
    extra = 5
    max_num = 5


class HomePageAdmin(PageAdmin):
    inlines = (IconBoxInline,)


admin.site.register(HomePage, HomePageAdmin)
