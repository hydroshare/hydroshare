from django.db import models
from django.contrib.auth.models import User
from hs_core.models import BaseResource
from django.db import transaction

import logging
logger = logging.getLogger(__name__)

class Upload(models.Model):
    ''' all in-progress uploads '''
    user = models.ForeignKey(User, null=True, editable=False)
    resource = models.ForeignKey(BaseResource, null=True, editable=False)
    path = models.TextField(null=True, editable=False)
    tempfile = models.TextField(null=True, editable=False)
    size = models.IntegerField(null=True, editable=False)
    uploaded = models.IntegerField(null=True, editable=False)

    class Meta:  # don't let two downloads of the same file occur at the same time.
        unique_together = ('resource', 'path')

    @classmethod
    def create(cls, user, resource, path, tempfile, size):
        try: 
            object = cls.objects.create(user=user,
                                        resource=resource,
                                        path=path,
                                        tempfile=tempfile, 
                                        size=size)
            logger.debug("starting upload for {}: {}/{} ({})"
                         .format(user, resource, path, tempfile))
            return object
        except Exception as e: 
            logger.debug(e)
            return None

    @classmethod
    def update(cls, user, resource, path, uploaded): 
        try: 
            object = cls.objects.get(user=user, resource=resource, path=path)
            object.uploaded=uploaded
            object.save()
            logger.debug("updating upload for {}: {}/{} ({}) bytes={}"
                         .format(user, resource, path, tempfile, uploaded))
            return object
        except Exception as e: 
            logger.debug(e)
            return None

    @classmethod
    def remove(cls, user, resource, path, filename):
        try: 
            cls.objects.get(user=user, resource=resource, path=path).delete()
            logger.debug("terminating upload for {}: {}/{}/{}"
                         .format(user, resource, path, filename, tempfile, uploaded))
            return True
        except Exception as e: 
            logger.debug(e)
            return False
