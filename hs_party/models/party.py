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

__author__ = 'valentin'

class Party(models.Model):
    #ID = models.AutoField(primary_key=True )
    # not fully sure how to use name. USGS uses distinct LDAP Id's here.
    # change to uniqueID
    uniqueCode = models.CharField(max_length=64,default=lambda: str(uuid4()),verbose_name="A unique code for the record", help_text="A unique code for the record")
    name = models.CharField(verbose_name="Full name of Organization or Person", blank=False,max_length='255')
    url = models.URLField(verbose_name="Web Page of Organization or Person", blank=True,max_length='255')
    # MULTIPLE Emails
    #email = models.ForeignKey(PartyEmail, null=True)
    # is a description on Page, which Person, Organization, and Group inherit from
    #description = models.TextField(verbose_name="Detailed description of Organization or Biography of a Person", blank=True)
    #primaryLocation = models.ForeignKey(PartyLocation, null=True)
    notes = models.TextField(blank=True)
    createdDate = models.DateField(auto_now_add=True)
    lastUpdate = models.DateField(auto_now=True)


    def __init__(self, *args, **kwargs):
        super(Party, self).__init__(*args, **kwargs)
        if self.uniqueCode is  None:
            self.uniqueCode = str(uuid4())
        if not self.id:
            self.createdDate = date.today()
        self.lastUpdate = date.today()

    class Meta:
        #abstract = True # if abstract, then we cannot retrieve all party's from database
        app_label = 'hs_party'