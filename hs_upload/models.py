from django.db import models
from django.contrib.auth.models import User
from hs_core.models import BaseResource


class Uploads(models.Model):
    ''' all in-progress uploads '''
    user = models.ForeignKey(User, editable=False, null=False),
    resource = models.ForeignKey(BaseResource, null=False, editable=False),
    directory = models.TextField(null=False, editable=False),
    filename = models.TextField(null=False, editable=False),
    tempfile = models.TextField(null=False, editable=False),
    size = models.IntegerField(null=False, editable=False),
    bytes_uploaded = models.IntegerField(null=False, editable=False)
