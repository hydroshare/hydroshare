from django.db import models
from django.contrib.auth.models import User
from hs_core.models import BaseResource
from django.db import transaction


class Upload(models.Model):
    ''' all in-progress uploads '''
    user = models.ForeignKey(User, null=True, editable=False)
    resource = models.ForeignKey(BaseResource, null=True, editable=False)
    path = models.TextField(null=True, editable=False)
    filename = models.TextField(null=True, editable=False)
    tempfile = models.TextField(null=True, editable=False)
    size = models.IntegerField(null=True, editable=False)
    uploaded = models.IntegerField(null=True, editable=False)

    class Meta:  # don't let two downloads of the same file occur at the same time.
        unique_together = ('resource', 'path', 'filename')

    @classmethod
    def create_or_update(cls, status, user, resource, path, filename,
                         tempfile, size=None, uploaded=None):

        with transaction.atomic():
            record, create = cls.objects.get_or_create(defaults={'user': user,
                                                                 'resource': resource,
                                                                 'path': path,
                                                                 'filename': filename},
                                                       size=size, uploaded=uploaded,
                                                       tempfile=tempfile)
            if not create:
                # These can arrive out of order: take maximum.
                if uploaded > record.uploaded:
                    record.uploaded = uploaded
                if size is not None and record.size is None:
                    record.size = size
                record.save()
