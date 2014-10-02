from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group
from django.db import models
from mezzanine.pages.models import Page, RichText,Displayable
from mezzanine.core.fields import FileField, RichTextField
from mezzanine.core.models import Ownable
from mezzanine.generic.models import Keyword, Orderable
from hs_core.models import AbstractResource
from django.db.models.signals import  post_save
from datetime import date
from uuid import uuid4
from django.db.models.signals import post_save,pre_save,post_init
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist,ValidationError
from django.core.urlresolvers import reverse

from .party import Party
from .party_types import PartyEmailModel,PartyGeolocation,PartyPhoneModel,PartyLocationModel

from .activities import ActivitiesModel
from .person import Person
from .organization import Organization

__author__ = 'valentin'

class GroupAssociation( ActivitiesModel):
    # object to handle a person being in one or more organizations
    #organization = models.ForeignKey(Organization)
    uniqueCode = models.CharField(max_length=64,default=lambda: str(uuid4()),verbose_name="A unique code for the record", help_text="A unique code for the record")
    group = models.ForeignKey(Group)
    #person = models.ForeignKey(Person)
    person = models.ForeignKey(Person)
    beginDate = models.DateField(null=True,blank=True,verbose_name="begin date of associate, Empty is not know.")
    endDate = models.DateField(null=True,blank=True, verbose_name="End date of association. Empty if still with group")
    positionName = models.CharField(verbose_name="Position, empty is not known", blank=True,max_length='100')

    def __unicode__(self):
        if (self.beginDate):

            if (self.endDate):
                range=u' [%s, %s]' % (self.beginDate,self.endDate)
            else:
                range=u' [%s]' % (self.beginDate)
        else:
            range=''

        if (self.jobTitle):
            title = ' ,' + self.jobTitle

        return u'%s (%s%s%s)' % (self.person.name, self.group.name,title,range)

    class Meta:
        app_label = 'hs_party'