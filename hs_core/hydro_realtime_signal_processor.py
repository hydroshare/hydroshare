from django.db import models
from haystack.signals import RealtimeSignalProcessor
from haystack.exceptions import NotHandled
from haystack.query import SearchQuerySet
from haystack.utils import get_identifier
from hs_core.models import BaseResource, CoreMetaData, AbstractMetaDataElement
from hs_access_control.models import ResourceAccess
import logging
import types

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
            if hasattr(instance, 'raccess') and hasattr(instance, 'metadata'): 
                # work around for failure of super(BaseResource, instance) to work properly.
                # this always succeeds because this is a post-save object action. 
                newinstance = BaseResource.objects.get(pk=instance.pk)
                newsender = BaseResource
                using_backends = self.connection_router.for_write(instance=newinstance)
                for using in using_backends:
                    # if object is public/discoverable or becoming public/discoverable, index it 
                    # test whether the object should be exposed. 
                    if instance.show_in_discover: 
                        try:
                            index = self.connections[using].get_unified_index().get_index(newsender)
                            index.update_object(newinstance, using=using)
                        except NotHandled:
                            logger.exception("Failure: changes to %s with short_id %s not added to Solr Index.", 
                                             str(type(instance)), newinstance.short_id)


                    # if object is private or becoming private, delete from index
                    else:  # not to be shown in discover
                        try:
                            index = self.connections[using].get_unified_index().get_index(newsender)
                            index.remove_object(newinstance, using=using)
                        except NotHandled:
                            logger.exception("Failure: delete of %s with short_id %s failed.", 
                                             str(type(instance)), newinstance.short_id)

        elif isinstance(instance, ResourceAccess):
            # automatically a BaseResource; just call the routine on it. 
            newinstance = instance.resource
            self.handle_save(BaseResource, newinstance)

        elif isinstance(instance, CoreMetaData): 
            try: 
                newinstance = BaseResource.objects.get(metadata=instance)
                self.handle_save(BaseResource, newinstance)
            except Exception: 
                pass
        
        elif isinstance(instance, AbstractMetaDataElement):
            try: 
                # resolve the BaseResource corresponding to the metadata element. 
                # this works regardless of the type of the metadata element. 
                # fields used here are the union of all fields in the metadata element
                newinstance = BaseResource.objects.get(Q(metadata__title=instance) |
                                                       Q(metadata__description=instance) |
                                                       Q(metadata__creators=instance) |
                                                       Q(metadata__contributors=instance) |
                                                       Q(metadata__citation=instance) |
                                                       Q(metadata__dates=instance) |
                                                       Q(metadata__coverages=instance) |
                                                       Q(metadata__formats=instance) |
                                                       Q(metadata__identifiers=instance) |
                                                       Q(metadata__language=instance) |
                                                       Q(metadata__subjects=instance) |
                                                       Q(metadata__sources=instance) |
                                                       Q(metadata__relations=instance) |
                                                       Q(metadata__rights=instance) |
                                                       Q(metadata__type=instance) |
                                                       Q(metadata__publisher=instance) |
                                                       Q(metadata__funding_agencies=instance) |
                                                       Q(metadata__variables=instance) |
                                                       Q(metadata__sites=instance) |
                                                       Q(metadata__methods=instance) |
                                                       Q(metadata__quality_levels=instance) |
                                                       Q(metadata__datasources=instance) |
                                                       Q(metadata__time_series_results=instance) |
                                                       Q(metadata__variables=instance) |
                                                       Q(metadata__fieldinformations=instance))
                self.handle_save(BaseResource, newinstance)
            except Exception:  # don't report missing resource 
                pass

        else:  # could be extended metadata element
            try: 
                newinstance = BaseResource.objects.get(extra_metadata=instance)
                self.handle_save(BaseResource, newinstance)
            except Exception: 
                pass
                
    def handle_delete(self, sender, instance, **kwargs):
        """ do not delete anything when this is called. """
        pass
