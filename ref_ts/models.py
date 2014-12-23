from mezzanine.pages.models import Page, RichText
from hs_core.models import AbstractResource, resource_processor
from mezzanine.pages.page_processors import processor_for
from django.db import models

class RefTimeSeries(Page, AbstractResource, RichText):

        class Meta:
                verbose_name = "Referenced HIS Time Series Resource"

        def extra_capabilities(self):
            return None

        reference_type = models.CharField(max_length=4, null=False, blank=True, default='')

        url = models.URLField(null=False, blank=True, default='',
                              verbose_name='Web Services Url')

        data_site_name = models.CharField(max_length=100, null=True, blank=True, default='',
                                verbose_name='Time Series Site Name')

        data_site_code = models.CharField(max_length=100, null=True, blank=True, default='',
                                verbose_name='Time Series Site Code')

        variable_name = models.CharField(max_length=100, null=True, blank=True, default='',
                                    verbose_name='Data Variable Name')

        variable_code = models.CharField(max_length=100, null=True, blank=True, default='',
                                    verbose_name='Data Variable Code')

        start_date = models.DateTimeField(null=True)

        end_date = models.DateTimeField(null=True)

        def can_add(self, request):
                return AbstractResource.can_add(self, request)

        def can_change(self, request):
                return AbstractResource.can_change(self, request)

        def can_delete(self, request):
                return AbstractResource.can_delete(self, request)

        def can_view(self, request):
                return AbstractResource.can_view(self, request)

processor_for(RefTimeSeries)(resource_processor)
