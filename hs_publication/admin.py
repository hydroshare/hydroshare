from django.contrib import admin

from .models import PublicationQueue


class PublicationQueueAdmin(admin.ModelAdmin):
    pass

admin.site.register(PublicationQueue, PublicationQueueAdmin)