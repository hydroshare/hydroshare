from django.db import models
from haystack.signals import RealtimeSignalProcessor
from haystack.exceptions import NotHandled
import logging
import types
from haystack.query import SearchQuerySet
from haystack.utils import get_identifier
from hs_core.models import SOLRQueue

logger = logging.getLogger(__name__)


def solr_update(instance): 
    """ Update a resource's SOLR record """
    # work around for failure of super(BaseResource, instance) to work properly.
    # this always succeeds because this is a post-save object action.
    newbase = BaseResource.objects.get(pk=instance.pk)
    newsender = BaseResource
    using_backends = self.connection_router.for_write(instance=newbase)
    for using in using_backends:
        logger.info('updating {}'.format(instance.short_id))
        try:
            index = self.connections[using].get_unified_index().get_index(newsender)
            index.update_object(newbase, using=using)
        except NotHandled:
            logger.exception("Failure: changes to %s with short_id %s not added to Solr Index.",
                             str(type(instance)), newbase.short_id)


def solr_delete(instance): 
    """ Delete a resource from SOLR before deleting from Django """
    logger.info('deleting {}'.format(instance.short_id))
    newbase = BaseResource.objects.get(pk=instance.pk)
    newsender = BaseResource
    using_backends = self.connection_router.for_write(instance=newbase)
    for using in using_backends:
        try:
            index = self.connections[using].get_unified_index().get_index(newsender)
            index.remove_object(newbase, using=using)
        except NotHandled:
            logger.exception("Failure: delete of %s with short_id %s failed.",
                             str(type(instance)), newbase.short_id)


def solr_batch_update(): 
    """ update SOLR for resources in the SOLRQueue """
    logger.info('starting batch update') 
    for instance in SOLRQueue.read_and_clear(): 
        logger.info('checking {}'.format(instance.short_id))
        if instance.show_in_discover:  # if object should be displayed now
            solr_update(instance)
        else:  # not to be shown in discover
            solr_delete(instance)


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
        from hs_core.models import BaseResource, CoreMetaData, AbstractMetaDataElement
        from hs_access_control.models import ResourceAccess
        from hs_file_types.models import AbstractFileMetaData
        from django.contrib.postgres.fields import HStoreField

        if isinstance(instance, BaseResource):
            if hasattr(instance, 'raccess') and hasattr(instance, 'metadata'):
                SOLRQueue.add(instance)

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
