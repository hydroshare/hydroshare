from django.db import models
from haystack.signals import RealtimeSignalProcessor
from haystack.exceptions import NotHandled
import logging
import types

logger = logging.getLogger(__name__)
logger.debug("load real time processor")


class HydroRealtimeSignalProcessor(RealtimeSignalProcessor):

    """ 
    Customized for the fact that the index is a subclass of BaseResource. 

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
        from hs_labels.models import ResourceLabels
    
        if isinstance(instance, BaseResource):
            logger.debug("update SOLR for " + str(type(instance)) + " with short_id " + instance.short_id)
            if hasattr(instance, 'raccess') and hasattr(instance, 'metadata'): 
                # work around for failure of super(BaseResource, instance) to work properly.
                # this always succeeds because this is a post-save object action. 
                newinstance = BaseResource.objects.get(pk=instance.pk)
                newsender = BaseResource
                using_backends = self.connection_router.for_write(instance=newinstance)
                for using in using_backends:
                    try:
                        index = self.connections[using].get_unified_index().get_index(newsender)
                        logger.debug("baseresource should_update is " + str(index.should_update(newinstance)))
                        index.update_object(newinstance, using=using)
                        index.update_object(newinstance, using=using)
                    except NotHandled:
                        logger.error("Changes to " + str(type(instance)) + " with short_id " + newinstance.short_id+ " not added to SOLR index")
            else: 
                logger.debug("Skipped premature change to " + str(type(instance)))
    
        elif isinstance(instance, ResourceAccess):
            # automatically a BaseResource
            newinstance = instance.resource 
            newsender = BaseResource
            self.handle_save(newsender, newinstance)

        # for all other objects, so far, there is nothing to do 
        else:
            logger.debug("Changes to " + str(type(instance)) + " excluded from SOLR index")
            pass

    def handle_delete(self, sender, instance, **kwargs):
        """
        Given an individual model instance, determine which backends the
        delete should be sent to & delete the object on those backends.
        """
        logger.debug("at handle delete: type of instance is "+str(type(instance)))
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
            # self.handle_delete(newsender, newinstance)
            using_backends = self.connection_router.for_write(instance=newinstance)
            for using in using_backends:
                try:
                    index = self.connections[using].get_unified_index().get_index(newsender)
                    index.remove_object(newinstance, using=using)
                except NotHandled:
                    # TODO: log failures
                    logger.debug("fail to delete the resource")

        else:
            # log failures
            logger.debug("skipped deleting resource type " + str(type(instance)) + " from SOLR index")
