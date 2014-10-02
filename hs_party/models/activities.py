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


class ActivitiesModel(models.Model):
    '''
    this is a base class for users associated with
     Organizations (associations)
     Workshops
     Citations -- not yet implemented. should be separate
    '''
    createdDate = models.DateField(auto_now_add=True)

    class Meta:
        abstract = True
        app_label = 'hs_party'
    pass