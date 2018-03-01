from django.contrib import admin

from .models import PublicationQueue


class PublicationQueueAdmin(admin.ModelAdmin):
    fields = (('resource',), 'status', 'note')
    readonly_fields = ('resource',)

admin.site.register(PublicationQueue, PublicationQueueAdmin)