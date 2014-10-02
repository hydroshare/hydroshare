from django.contrib.contenttypes import generic
from mezzanine.pages.models import Page, RichText
from hs_core.models import AbstractResource, resource_processor, ResourceFile
from mezzanine.pages.page_processors import processor_for
from django.db import models
from django.contrib.contenttypes.models import ContentType


class ResourceAggregation(Page, AbstractResource, RichText):

        resources = generic.GenericRelation('resource_aggregation.Resource')

        def can_add(self, request):
                return AbstractResource.can_add(self, request)

        def can_change(self, request):
                return AbstractResource.can_change(self, request)

        def can_delete(self, request):
                return AbstractResource.can_delete(self, request)

        def can_view(self, request):
                return AbstractResource.can_view(self, request)

processor_for(ResourceAggregation)(resource_processor)

class Resource(models.Model):
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    resource_short_id = models.CharField(max_length=32, db_index=True)  # the short_id of the resource
    resource_description = models.CharField(max_length=5000, blank=True, default='')
