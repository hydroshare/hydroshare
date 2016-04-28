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

    # def handle_save(self, sender, instance, **kwargs):
    #     """
    #     Given an individual model instance, determine which backends the
    #     update should be sent to & update the object on those backends.
    #     """
    #     from hs_core.models import BaseResource
    #     from hs_access_control.models import ResourceAccess
    #
    #     logger.debug("at handle update: type of instance is "+str(type(instance)))
    #
    #     if isinstance(instance, BaseResource):
    #         logger.debug("isinstance:" + str(type(instance)))
    #         newinstance = super(BaseResource, instance)
    #         newsender = BaseResource
    #         using_backends = self.connection_router.for_write(instance=newinstance)
    #         for using in using_backends:
    #             try:
    #                 index = self.connections[using].get_unified_index().get_index(newsender)
    #                 index.update_object(newinstance, using=using)
    #             except NotHandled:
    #                 # TODO: log failures
    #                 pass
    #
    #     elif isinstance(instance, ResourceAccess):
    #         newinstance = instance.resource # automatically a BaseResource
    #         newsender = BaseResource
    #         using_backends = self.connection_router.for_write(instance=newinstance)
    #         for using in using_backends:
    #
    #             try:
    #                 index = self.connections[using].get_unified_index().get_index(newsender)
    #                 index.update_object(newinstance, using=using)
    #             except NotHandled:
    #                 # TODO: log failures
    #                 pass
    #
    #     else:
    #         # log failures
    #         pass


    def handle_delete(self, sender, instance, **kwargs):
        """
        Given an individual model instance, determine which backends the
        delete should be sent to & delete the object on those backends.
        """
        logger.debug("at handle delete: type of instance is "+str(type(instance)))
        from hs_core.models import BaseResource
        from hs_access_control.models import ResourceAccess

        if isinstance(instance, BaseResource):
            newinstance = super(BaseResource, instance)
            newsender = BaseResource
            using_backends = self.connection_router.for_write(instance=newinstance)
            for using in using_backends:
                try:
                    index = self.connections[using].get_unified_index().get_index(newsender)
                    index.remove_object(newinstance, using=using)
                except NotHandled:
                    # TODO: log failures 
                    pass

        elif isinstance(instance, ResourceAccess):
            newinstance = instance.resource # automatically a BaseResource
            newsender = BaseResource
            using_backends = self.connection_router.for_write(instance=newinstance)
            for using in using_backends:

                try:
                    index = self.connections[using].get_unified_index().get_index(newsender)
                    index.remove_object(newinstance, using=using)
                except NotHandled:
                    # TODO: log failures
                    pass

        else: 
            # log failures 
            pass 
