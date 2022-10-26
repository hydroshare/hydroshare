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
    # TODO: [#4808] add geoconnex metadata to search index
    
    def handle_save(self, sender, instance, **kwargs):
        """
        Given an individual model instance, determine which backends the
        update should be sent to & update the object on those backends.
        """
        from hs_core.models import BaseResource, CoreMetaData, AbstractMetaDataElement
        from hs_access_control.models import ResourceAccess
        from hs_file_types.models import AbstractFileMetaData
        from django.contrib.postgres.fields import HStoreField


        if isinstance(instance, BaseResource):
            if hasattr(instance, 'raccess') and hasattr(instance, 'metadata'):
                # work around for failure of super(BaseResource, instance) to work properly.
                # this always succeeds because this is a post-save object action.
                newbase = BaseResource.objects.get(pk=instance.pk)
                newsender = BaseResource
                using_backends = self.connection_router.for_write(instance=newbase)
                for using in using_backends:
                    # if object is public/discoverable or becoming public/discoverable, index it
                    # test whether the object should be exposed.
                    if instance.show_in_discover:
                        try:
                            # TODO: 4808
                            index = self.connections[using].get_unified_index().get_index(newsender)
                            index.update_object(newbase, using=using)
                        except NotHandled:
                            logger.exception("Failure: changes to %s with short_id %s not added to Solr Index.",
                                             str(type(instance)), newbase.short_id)


                    # if object is private or becoming private, delete from index
                    else:  # not to be shown in discover
                        try:
                            index = self.connections[using].get_unified_index().get_index(newsender)
                            index.remove_object(newbase, using=using)
                        except NotHandled:
                            logger.exception("Failure: delete of %s with short_id %s failed.",
                                             str(type(instance)), newbase.short_id)

        elif isinstance(instance, ResourceAccess):
            # automatically a BaseResource; just call the routine on it.
            try:
                newbase = instance.resource
                self.handle_save(BaseResource, newbase)
            except Exception as e:
                logger.exception("{} exception: {}".format(type(instance), e))

        elif isinstance(instance, CoreMetaData):
            try:
                newbase = instance.resource
                self.handle_save(BaseResource, newbase)
            except Exception:
                logger.exception("{} exception: {}".format(type(instance), e))
        # TODO: 4808
        elif isinstance(instance, AbstractMetaDataElement):
            if isinstance(instance.metadata, AbstractFileMetaData):
                try:
                    # resolve the BaseResource corresponding to the metadata element in a logical logical.
                    newbase = instance.metadata.logical_file.resource
                    self.handle_save(BaseResource, newbase)
                except Exception as e:
                    logger.exception("{} exception: {}".format(type(instance), e))
            else:
                try:
                    # resolve the BaseResource corresponding to the metadata element.
                    newbase = instance.metadata.resource
                    self.handle_save(BaseResource, newbase)
                except Exception as e:
                    logger.exception("{} exception: {}".format(type(instance), e))

        elif isinstance(instance, HStoreField):
            try:
                newbase = BaseResource.objects.get(extra_metadata=instance)
                self.handle_save(BaseResource, newbase)
            except Exception as e:
                logger.exception("{} exception: {}".format(type(instance), e))

    def handle_delete(self, sender, instance, **kwargs):
        """
        Ignore delete events as this is accomplished separately. 
        """
        pass
