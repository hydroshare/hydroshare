from django.db import models
from haystack.signals import RealtimeSignalProcessor
from haystack.exceptions import NotHandled
import logging
import types
from haystack.query import SearchQuerySet
from haystack.utils import get_identifier

logger = logging.getLogger(__name__)


class HydroRealtimeSignalProcessor(RealtimeSignalProcessor):

    """
    Customized for the fact that all indexed resources are subclasses of BaseResource.

    Notes:
    1. RealtimeSignalProcessor already plumbs in all class updates. We might want to be more specific.
    2. The class sent to this is a subclass of BaseResource, or another class.
    3. Thus, we want to capture cases in which it is an appropriate instance, and respond.
    """

    def handle_save(self, sender, instance, **kwargs):
        """
        Given an individual model instance, determine which backends the
        update should be sent to & update the object on those backends.
        """
        from hs_core.models import BaseResource
        from hs_access_control.models import ResourceAccess

        if isinstance(instance, BaseResource):
            logger.debug("realtime SOLR index of %s invoked", instance.short_id)
            if hasattr(instance, 'raccess') and hasattr(instance, 'metadata'):
                # work around for failure of super(BaseResource, instance) to work properly.
                # this always succeeds because this is a post-save object action.
                newinstance = BaseResource.objects.get(pk=instance.pk)
                newsender = BaseResource
                using_backends = self.connection_router.for_write(instance=newinstance)
                for using in using_backends:
                    # if object is public/discoverable or becoming public/discoverable, index it
                    if instance.raccess.public or instance.raccess.discoverable:
                        logger.debug("realtime SOLR indexing %s", newinstance.short_id)
                        try:
                            index = self.connections[using].get_unified_index().get_index(newsender)
                            index.update_object(newinstance, using=using)
                        except NotHandled:
                            logger.exception("Failure: changes to %s with short_id %s not added to Solr Index.", str(type(instance)), newinstance.short_id)
                    # if object is private or becoming private, delete from index
                    else:
                        logger.debug("realtime SOLR removing %s from index", newinstance.short_id)
                        try:
                            index = self.connections[using].get_unified_index().get_index(newsender)
                            index.remove_object(newinstance, using=using)
                        except NotHandled:
                            logger.exception("Failure: delete of %s with short_id %s failed.", str(type(instance)), newinstance.short_id)

        elif isinstance(instance, ResourceAccess):
            # automatically a BaseResource; just call the routine on it.
            newinstance = instance.resource
            newsender = BaseResource
            logger.debug("realtime SOLR recursing to index %s", newinstance.short_id)
            self.handle_save(newsender, newinstance)


    def handle_delete(self, sender, instance, **kwargs):
        """
        Given an individual model instance, determine which backends the
        delete should be sent to & delete the object on those backends.
        """
        from hs_core.models import BaseResource
        from hs_access_control.models import ResourceAccess

        # only delete the SOLR instance when the raccess field is recursively deleted.
        # At this point, the resource still exists.
        # Thus, the BaseResource is literally available and can be unindexed.
        # Trying to delete as a result of deleting the Resource fails, because
        # it is not possible to recover the BaseResource object.
        if isinstance(instance, ResourceAccess):
            newinstance = instance.resource # automatically a BaseResource
            newsender = BaseResource
            logger.debug("realtime SOLR index of %s invoked", newinstance.short_id)
            # self.handle_delete(newsender, newinstance)
            using_backends = self.connection_router.for_write(instance=newinstance)
            for using in using_backends:
                try:
                    index = self.connections[using].get_unified_index().get_index(newsender)
                    index.remove_object(newinstance, using=using)
                except NotHandled:
                    logger.exception("Failure: delete of %s with short_id %s failed.", str(type(instance)), newinstance.short_id)
