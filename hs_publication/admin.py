from django.contrib import admin
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

from .models import PublicationQueue


class PublicationQueueAdmin(admin.ModelAdmin):
    fields = ('resource_link', 'status', 'note')
    readonly_fields = ('resource_link',)

    list_display = ("resource", "status", "note",)
    list_filter = ('status',)

    def resource_link(self, instance):
        return mark_safe('<a href="/resource/{}">{}</a>'.format(
            instance.resource.short_id,
            instance.resoruce.metadata.title[0].value
        ))

    resource_link.allow_tags = True

admin.site.register(PublicationQueue, PublicationQueueAdmin)