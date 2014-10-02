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

from party import Party


__author__ = 'valentin'

class Group(Displayable,Party):
    # externalIdentifiers from ExternalOrgIdentifiers
    specialities = Keyword()

    def __init__(self, *args, **kwargs):
        super(Group, self).__init__(*args, **kwargs)
        nameField = self._meta.get_field('name')
        nameField.verbose_name="Group Name"
        nameField.help_text="Group Name"
        notesField = self._meta.get_field('notes')
        notesField.verbose_name="Description"
        notesField.help_text="Brief Description of Group"
        urlField = self._meta.get_field('url')
        urlField.verbose_name="Web Page for Group"
        urlField.help_text="Group web page"

    class Meta:
        app_label = 'hs_party'