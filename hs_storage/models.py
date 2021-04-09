"""
 This model stores interface information for a user to various forms of third-party storage. 
"""

from django.contrib.auth.models import User
from django.db import models


class UserStorageCreds(models.Model):
    """
    Labels of a user for a resource
    This model stores credentials for accounts for an individual user, by user. 
    For a user u, this is accessible as a set via u.creds
    """
    user = models.ForeignKey(User, null=False, editable=False,
                             related_name='creds',  # unused but must be defined and unique
                             help_text='user assigning a label',
                             on_delete=models.CASCADE)
    name = models.CharField(null=False, max_length=255)  # allows you to look something up
    json = models.TextField(null=False)  # connection information 
