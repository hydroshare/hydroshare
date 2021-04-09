"""
 This model stores interface information for a user to various forms of third-party storage. 

 To use this, store each storage set of credentials as a nickname. 
 Then you can look this up for a User u as u.creds.get(nickname=n)

"""

from django.contrib.auth.models import User
from django.db import models


class ServiceCodes(object):
    """
    Service codes identify a file sharing service.
        * 1 or ServiceCodes.GOOGLE: google drive
        * 2 or ServiceCodes.DROPBOX: DropBox
        * 3 or ServiceCodes.BOX: Box
    """
    NONE = 0
    GOOGLE = 1
    DROPBOX = 2
    BOX = 3
    CHOICES = (
        (NONE, 'None'),
        (GOOGLE,  'Google'), 
        (DROPBOX, 'DropBox'),
        (BOX, 'Box')
    )
    # Names of privileges for printing
    NAMES = ('None', 'Google', 'DropBox', 'Box')

class UserStorageCreds(models.Model):
    """
    Labels of a user for a resource
    This model stores credentials for accounts for an individual user, by user. 
    For a user u, this is accessible as a set via u.creds
    """
    user = models.ForeignKey(User, null=False, editable=False,
                             related_name='creds',  # unused but must be defined and unique
                             help_text='user for this credential information',
                             on_delete=models.CASCADE)
    nickname = models.CharField(null=False, max_length=255)  # allows user to quickly specify a service
    username = models.CharField(null=False, max_length=255)  # username on remote service.
    servicecode =  models.IntegerField(choices=ServiceCodes.CHOICES,
                                       editable=False,
                                       default=ServiceCodes.NONE)
    json = models.TextField(null=False)  # connection information 
    class Meta: 
        unique_together = ('user', 'nickname')
