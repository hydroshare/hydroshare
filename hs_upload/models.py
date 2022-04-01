from django.db import models
from django.contrib.auth.models import User
from hs_core.models import BaseResource
from django.db import transaction

import logging
logger = logging.getLogger(__name__)


class Upload(models.Model):
    ''' track all in-progress uploads '''
    user = models.ForeignKey(User, null=True, editable=False)
    resource = models.ForeignKey(BaseResource, null=True, editable=False)
    path = models.TextField(null=True, editable=False)
    tempfile = models.TextField(null=True, editable=False)
    size = models.IntegerField(null=True, editable=False)
    uploaded = models.IntegerField(null=True, editable=False)

    class Meta:  # don't let two downloads of the same file occur at the same time.
        unique_together = ('resource', 'path')

    @classmethod
    def create(cls, user, resource, path, size):
        try:
            object = cls.objects.create(user=user,
                                        resource=resource,
                                        path=path,
                                        size=size)
            logger.debug("starting upload for {}: {}/{}"
                         .format(user, resource, path))
            return object
        except Exception as e:
            logger.debug(e)
            return None

    @classmethod
    def update(cls, resource, path, uploaded, tempfile):
        try:
            with transaction.atomic():
                object = cls.objects.get(resource=resource, path=path)
                if object.uploaded < uploaded:
                    object.uploaded = uploaded
                if object.tempfile is None:
                    object.tempfile = tempfile
                object.save()
            logger.debug("updating upload for {}: {}/{} ({}) bytes={}"
                         .format(object.user, resource, path, tempfile, uploaded))
            return object
        except Exception as e:
            logger.debug(e)
            return None

    @classmethod
    def remove(cls, resource, path):
        try:
            object = cls.objects.get(resource=resource, path=path)
            logger.debug("terminating upload for {}: {}/{}"
                         .format(object.user, resource, path))
            object.delete()
            return True
        except Exception as e:
            logger.debug(e)
            return False
