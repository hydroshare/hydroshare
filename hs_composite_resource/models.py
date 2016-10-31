# coding=utf-8
from django.db import models
from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor


class CompositeResource(BaseResource):
    objects = ResourceManager("CompositeResource")

    class Meta:
        verbose_name = 'Composite'
        proxy = True

    @property
    def can_be_public_or_discoverable(self):
        # TODO: This needs to be unit tested
        if not super(BaseResource, self).can_be_public_or_discoverable:
            return False
        for lf in self.logical_files:
            if not lf.metadata.has_all_required_elements():
                return False

        return True

# this would allow us to pick up additional form elements for the template before the template
# is displayed
processor_for(CompositeResource)(resource_processor)
