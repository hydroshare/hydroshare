from django.db import models
from django.contrib.auth.models import User
from hs_core.models import BaseResource

import logging
logger = logging.getLogger(__name__)


class Upload(models.Model):
    ''' track all in-progress uploads '''
    user = models.ForeignKey(User, null=True, editable=False)
    resource = models.ForeignKey(BaseResource, null=True, editable=False)
    path = models.TextField(null=True, editable=False)
    tempfile = models.TextField(null=True, editable=False)
    size = models.IntegerField(null=True, editable=False)
    # uploaded = models.IntegerField(null=True, editable=False)

    class Meta:  # don't let two downloads of the same file occur at the same time.
        unique_together = ('resource', 'path')

    @classmethod
    def create(cls, user, resource, path, size):
        """ start an upload """
        object = cls.objects.create(user=user,
                                    resource=resource,
                                    path=path,
                                    size=size)
        logger.debug("starting upload for {}: {}/{}"
                     .format(user, resource, path))
        return object

    @classmethod
    def exists(cls, resource, path):
        """ is an upload in progress? """
        return cls.objects.filter(resource=resource, path=path).exists()

    @classmethod
    def delete(cls, resource, path):
        """ terminate an upload """
        object = cls.objects.get(resource=resource, path=path)
        logger.debug("terminating upload for {}: {}/{}"
                     .format(object.user, resource, path))
        object.delete()
