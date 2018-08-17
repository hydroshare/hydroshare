# Register your models here.
from django.contrib.gis import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from .models import ToolResource, ToolMetaData, AppHomePageUrl, \
    HelpPageUrl, TestingProtocolUrl, SourceCodeUrl, IssuesPageUrl, \
    MailingListUrl, Roadmap, ShowOnOpenWithList


class InlineAppHomePageUrlAdmin(GenericTabularInline):
    verbose_name_plural = "App Home Page URL"
    model = AppHomePageUrl
    max_num = 1
    extra = 1


class InlineRoadmapAdmin(GenericTabularInline):
    verbose_name_plural = "Roadmap"
    model = Roadmap
    max_num = 1
    extra = 1


class InlineShowOnOpenWithListAdmin(GenericTabularInline):
    verbose_name_plural = "Show on 'Open With' List"
    model = ShowOnOpenWithList
    max_num = 1
    extra = 1


class InlineMailingListUrlAdmin(GenericTabularInline):
    verbose_name_plural = "Mailing List URL"
    model = MailingListUrl
    max_num = 1
    extra = 1


class InlineIssuesPageUrlAdmin(GenericTabularInline):
    verbose_name_plural = "Issues Page URL"
    model = IssuesPageUrl
    max_num = 1
    extra = 1


class InlineSourceCodeUrldmin(GenericTabularInline):
    verbose_name_plural = "Source Code URL"
    model = SourceCodeUrl
    max_num = 1
    extra = 1


class InlineTestingProtocolUrlAdmin(GenericTabularInline):
    verbose_name_plural = "Testing Protocol URL"
    model = TestingProtocolUrl
    max_num = 1
    extra = 1


class InlineHelpPageUrl(GenericTabularInline):
    verbose_name_plural = "Help Page URL"
    model = HelpPageUrl
    max_num = 1
    extra = 1


class ToolMetaDataAdmin(admin.ModelAdmin):
    fields = ['approved']

    inlines = [InlineAppHomePageUrlAdmin, InlineHelpPageUrl, InlineIssuesPageUrlAdmin,
               InlineSourceCodeUrldmin, InlineTestingProtocolUrlAdmin,
               InlineMailingListUrlAdmin, InlineRoadmapAdmin, InlineShowOnOpenWithListAdmin]

    def has_add_permission(self, request):
        return False


admin.site.register(ToolMetaData, ToolMetaDataAdmin)
