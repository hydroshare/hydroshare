import logging

from django.conf import settings
from django.db import models
from hs_core.models import Date, BaseResource
from hs_access_control.models import ResourceAccess
from haystack.exceptions import NotHandled
from haystack.signals import BaseSignalProcessor

logger = logging.getLogger(__name__)


class HydroRealtimeSignalProcessor(BaseSignalProcessor):
    """
    Notes:
    1. We assume everytime metadata is updated the modified datetime is updated
    2. ResourceAccess does not update the modified datetime (it is not scientific metadata)
    """

    def setup(self):
        if not getattr(settings, "DISABLE_HAYSTACK", False):
            models.signals.post_save.connect(self.handle_update, sender=Date)
            models.signals.post_save.connect(self.handle_access, sender=ResourceAccess)

    def teardown(self):
        if not getattr(settings, "DISABLE_HAYSTACK", False):
            models.signals.post_save.disconnect(self.handle_update, sender=Date)
            models.signals.post_save.disconnect(self.handle_access, sender=ResourceAccess)

    def handle_update(self, sender, instance, **kwargs):
        try:
            # resolve the BaseResource corresponding to the metadata element.
            newbase = instance.metadata.resource
            index_resource(self, newbase)
        except Exception as e:
            logger.exception("{} exception: {}".format(type(instance), str(e)))

    def handle_access(self, sender, instance, **kwargs):
        try:
            newbase = instance.resource
            index_resource(self, newbase)
        except Exception as e:
            logger.exception("{} exception: {}".format(type(instance), str(e)))


def index_resource(signal_processor, instance: BaseResource):
    if hasattr(instance, 'raccess') and hasattr(instance, 'metadata'):
        # work around for failure of super(BaseResource, instance) to work properly.
        # this always succeeds because this is a post-save object action.
        newbase = BaseResource.objects.get(pk=instance.pk)
        newsender = BaseResource
        using_backends = signal_processor.connection_router.for_write(instance=newbase)
        for using in using_backends:
            # if object is public/discoverable or becoming public/discoverable, index it
            # test whether the object should be exposed.
            if instance.show_in_discover:
                try:
                    index = signal_processor.connections[using].get_unified_index().get_index(newsender)
                    index.update_object(newbase, using=using)
                except NotHandled:
                    logger.exception("Failure: changes to %s with short_id %s not added to Solr Index.",
                                     str(type(instance)), newbase.short_id)

            # if object is private or becoming private, delete from index
            else:  # not to be shown in discover
                try:
                    index = signal_processor.connections[using].get_unified_index().get_index(newsender)
                    index.remove_object(newbase, using=using)
                except NotHandled:
                    logger.exception("Failure: delete of %s with short_id %s failed.",
                                     str(type(instance)), newbase.short_id)
