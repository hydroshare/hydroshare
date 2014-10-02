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

class CodeListType(models.Model):
    # these are classes, so changing the model means you change this
    code = models.CharField(primary_key=True,verbose_name="Code Choice Item", max_length=24, blank=False)
    name = models.CharField(verbose_name="Brief Name of Choice Item",max_length=255, blank=False)
    order = models.IntegerField(verbose_name="Optional Order", blank=True)
    url = models.CharField(verbose_name="Optional Url pointing to provider",max_length=255, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        app_label = 'hs_party'

######
# address
#########

class AddressCodeList(CodeListType):

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'hs_party'

class PartyLocationModel(models.Model):
    #ID = models.AutoField(primary_key=True)
    ADDRESS_TYPE_CHOICES = (
        ("mailing", "Mailing Address. For mail. Can be a PO Box"),
    ("street", "Street Address. "),
    ("shipping","Shipping Address. Address where packages are shipped to"),
    ("office","Office Address. For a person, includes details of the office number")
    )
    address = models.TextField(verbose_name="Multi-line Address",)
    address_type = models.ForeignKey(AddressCodeList,
                                     verbose_name="Type of Address",default='mailing')

    class Meta:
        abstract = True
        app_label = 'hs_party'

####
# addres/contact
###
class PhoneCodeList(CodeListType):
    # these are classes, so changing the model means you change this
    # code = models.CharField(primary_key=True,verbose_name="Code Choice Item", max_length=24, blank=False)
    # name = models.CharField(verbose_name="Brief Name of Choice Item",max_length=255, blank=False)
    # order = models.IntegerField(verbose_name="Optional Order", blank=True)
    # url = models.CharField(verbose_name="Optional Url pointing to provider",max_length=255, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'hs_party'

class PartyPhoneModel(models.Model):
    PHONE_TYPE_CHOICES = (("main", "Main Line for a company"),
                            ("office", "Office Phone Number"),
                            ("cell", "Cell Phone. "),
                            ("fax", "Fax"),
                            ("other", "Other Phone Numbe"),
    )
    phone_number = models.CharField(verbose_name="Office or main phone number", blank=False,max_length='30')
    phone_type = models.ForeignKey(PhoneCodeList, blank=True,default='other')

    class Meta:
        abstract = True
        app_label = 'hs_party'


class EmailCodeList(CodeListType):
    # these are classes, so changing the model means you change this
    # code = models.CharField(primary_key=True,verbose_name="Code Choice Item", max_length=24, blank=False)
    # name = models.CharField(verbose_name="Brief Name of Choice Item",max_length=255, blank=False)
    # order = models.IntegerField(verbose_name="Optional Order", blank=True)
    # url = models.CharField(verbose_name="Optional Url pointing to provider",max_length=255, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'hs_party'


class PartyEmailModel(models.Model):
    ADDRESS_TYPE_CHOICES = (("work", "Work Email"),
                            ("personal", "personal email"),
                            ("mailing_list", "email for a mailing list. Use for groups "),
                            ("support", "Support email"),
                            ("other", "Other email"),
    )
    email = models.CharField(verbose_name="Email", blank=True,max_length='30')
    email_type = models.ForeignKey(EmailCodeList,verbose_name="Email type", blank=True, default='other')

    class Meta:
        abstract = True
        app_label = 'hs_party'
#####
# address/location
class PartyGeolocation(models.Model):
    name = models.CharField(max_length=100)
    geonamesUrl = models.URLField(verbose_name="URL of Geonames reference")
    # add geolocation
    class Meta:
        abstract = True
        app_label = 'hs_party'

class City(PartyGeolocation):
    def __init__(self, *args, **kwargs):
        super(City, self).__init__(*args, **kwargs)
        City._meta.get_field('name').verbose_name ="City"

    class Meta:
        app_label = 'hs_party'
    pass

class Region(PartyGeolocation):
    def __init__(self, *args, **kwargs):
        super(Region, self).__init__(*args, **kwargs)
        Region._meta.get_field('name').verbose_name ="State or Region"

    class Meta:
        app_label = 'hs_party'
    pass

class Country(PartyGeolocation):
    def __init__(self, *args, **kwargs):
        super(Country, self).__init__(*args, **kwargs)
        Country._meta.get_field('name').verbose_name ="Country"

    class Meta:
        app_label = 'hs_party'
    pass

##########
# IDENTIFIER SUPPORT
##########
class ExternalIdentifierCodeList(CodeListType):
    # these are classes, so changing the model means you change this
    # code = models.CharField(primary_key=True, verbose_name="Code Choice Item", max_length=24, blank=False)
    # name = models.CharField(verbose_name="Brief Name of Choice Item",max_length=255, blank=False)
    # order = models.IntegerField(verbose_name="Optional Order", blank=True)
    # url = models.CharField(verbose_name="Optional Url pointing to provider",max_length=255, blank=True)
    def __unicode__(self):
        return self.name
    class Meta:
        app_label = 'hs_party'


class NameAliasCodeList(CodeListType):
    # these are classes, so changing the model means you change this
    # code = models.CharField(primary_key=True,verbose_name="Code Choice Item", max_length=24, blank=False)
    # name = models.CharField(verbose_name="Brief Name of Choice Item",max_length=255, blank=False)
    # order = models.IntegerField(verbose_name="Optional Order", blank=True)
    # url = models.CharField(verbose_name="Optional Url pointing to provider",max_length=255, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'hs_party'

class NameAliasType(models.Model):
    #ID = models.AutoField(primary_key=True)
    # relation will show in Party as otherNames
    otherName = models.CharField(verbose_name="Other Name or alias",max_length='255',blank=True)
    ANNOTATION_TYPE_CHOICE = (
        ("change", "Name Change"),
        ("citation", "Publishing Alias"),
        ("fullname", "Full Name variation"),
        ("other", "other type of alias")
    )
    annotation = models.ForeignKey(NameAliasCodeList,verbose_name="type of alias",max_length='10')



    class Meta:
        """Meta Class for your model."""
        abstract = True
        app_label = 'hs_party'