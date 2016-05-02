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

    def hydro_resource_is_present(self, instance): 
        """ 
        This returns True if a current resource is now present in Haystack, and False if not. 
        This -- in turn -- informs us as to whether to update and/or delete the object 
        """
        discoverable = SearchQuerySet().filter(id=get_identifier(instance)).count()
        if discoverable > 0:
            return True
        else:
            return False

    def handle_save(self, sender, instance, **kwargs):
        """
        Given an individual model instance, determine which backends the
        update should be sent to & update the object on those backends.
        """
        from hs_core.models import BaseResource
        from hs_access_control.models import ResourceAccess
    
        if isinstance(instance, BaseResource):
            if hasattr(instance, 'raccess') and hasattr(instance, 'metadata'): 
                # work around for failure of super(BaseResource, instance) to work properly.
                # this always succeeds because this is a post-save object action. 
                newinstance = BaseResource.objects.get(pk=instance.pk)
                newsender = BaseResource
                using_backends = self.connection_router.for_write(instance=newinstance)
                for using in using_backends:
                    # if object is public/discoverable or becoming public/discoverable, index it 
                    if instance.raccess.public or instance.raccess.discoverable: 
                        try:
                            index = self.connections[using].get_unified_index().get_index(newsender)
                            index.update_object(newinstance, using=using)
                        except NotHandled:
                            logger.error("Failure: changes to " + str(type(instance)) + " with short_id " + newinstance.short_id+ " not added to SOLR index")
                    # if object is private or becoming private, delete from index 
                    elif self.hydro_resource_is_present(newinstance):
                        try:
                            index = self.connections[using].get_unified_index().get_index(newsender)
                            index.remove_object(newinstance, using=using)
                        except NotHandled:
                            logger.error("Failure: delete of " + str(type(instance)) + " with short_id " + newinstance.short_id+ " failed.")

        elif isinstance(instance, ResourceAccess):
            # automatically a BaseResource; just call the routine on it. 
            newinstance = instance.resource
            newsender = BaseResource
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
            # self.handle_delete(newsender, newinstance)
            using_backends = self.connection_router.for_write(instance=newinstance)
            for using in using_backends:
                if self.hydro_resource_is_present(newinstance): 
                    try:
                        index = self.connections[using].get_unified_index().get_index(newsender)
                        index.remove_object(newinstance, using=using)
                    except NotHandled:
                        logger.error("Failure: delete of " + str(type(instance)) + " with short_id " + newinstance.short_id+ " failed.")
