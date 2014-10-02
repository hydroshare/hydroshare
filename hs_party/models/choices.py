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

class ChoiceType(models.Model):
    # these are classes, so changing the model means you change this
    CHOICETYPE_CHOICE = (
                         ("ExternalOrgIdentifiers", "External Org Identifiers")
                         , ("UserDemographics", "User Demographics")
                         , ("Organization","Organization Type")
                         , ("PartyPhone", "page for project")
                         , ("PartyAddress", "Address")
                         , ("PartyEmail", "Address")
                         , ("ScholarExternalIdentifiers", "Scholar External Identifiers")
    )
    choiceType = models.CharField(choices=CHOICETYPE_CHOICE, verbose_name="Select Type of Choice", max_length=40)
    code = models.CharField(verbose_name="Code Choice Item", max_length=24, blank=False)
    name = models.CharField(verbose_name="Brief Name of Choice Item",max_length=255, blank=False)
    order = models.IntegerField(verbose_name="Optional Order", blank=True)
    url = models.CharField(verbose_name="Optional Url pointing to provider",max_length=255, blank=True)

    class Meta:
        app_label = 'hs_party'
