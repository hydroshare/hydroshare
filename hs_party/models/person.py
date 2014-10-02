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
from django.core.exceptions import NON_FIELD_ERRORS
from django.core.urlresolvers import reverse

from party import Party
from party_types import PartyEmailModel,PartyGeolocation,\
    PartyPhoneModel,PartyLocationModel,\
    ExternalIdentifierCodeList,\
    NameAliasType, AddressCodeList,PhoneCodeList,EmailCodeList



__author__ = 'valentin'


#======================================================================================
# PERSON
# note: Hydroshare User is near end of document
#======================================================================================


class Person(Displayable,Party):

    # name is the only required field: Science spec
    # fields from vcard.
    givenName = models.CharField(max_length='125', verbose_name="First or Given Name") # given+family =name of party needs to be 255
    familyName = models.CharField(max_length='125', verbose_name="Last or Family Name") # given+family =name of party needs to be 255
    jobTitle = models.CharField(max_length='100', blank=True, verbose_name="Position or Job Title")
    # This makes a full org record required.
    # Should this be just a text field?
    #organization = models.ForeignKey(Organization, null=True) # one to many

    #cellPhone = models.CharField(verbose_name="Cell Phone", blank=True,max_length='30')  # sciencebase
    # do we want some adviser field.
    #primaryOrganizationName = models.CharField(max_length='100', blank=True, verbose_name="Primary Organization", help_text="Primary Organization, if known")
    #primaryAddress = models.CharField(max_length='100', blank=True, verbose_name="Primary Address", help_text="Primary Mailing or Street, if known")
    #primaryTelephone = models.CharField(max_length='30', blank=True, verbose_name="Primary Telephone",help_text="Primary Telephone, if known")
    primaryOrganizationRecord = models.ForeignKey('Organization',  verbose_name="Primary Organization",
                                                  null=True, blank=True,related_name="+")

    #@property
    def get_primaryOrganizationName(self):
        return self.primaryOrganizationRecord.name

    primaryOrganizationName = property(get_primaryOrganizationName)

    #@property
    def get_primaryAddress(self):
        paddr = self.mail_addresses.filter(address_type='primary')
        if (paddr):
            return paddr.first().address
        else:
            return None

   # @primaryAddress.setter
    def set_primaryAddress(self, value):
        paddr = self.mail_addresses.filter(address_type='primary')
        if (paddr):
            firstOne = paddr.first()
            firstOne.address = value
            firstOne.save()
        else:
            primaryType = AddressCodeList.objects.get(code='primary')
            address =  PersonLocation(address_type=primaryType,address=value)
            self.mail_addresses.add(address)
            self.save()

    primaryAddress = property(get_primaryAddress,set_primaryAddress)


    def get_primaryTelephone(self):
        phone1 = self.phone_numbers.filter(phone_type='primary')
        if (phone1):
            return phone1.first().phone_number
        else:
            return None


    def set_primaryTelephone(self, value):
        phone1 = self.phone_numbers.filter(phone_type='primary')
        if (phone1):
            firstOne = phone1.first()
            firstOne.phone_number = value
            firstOne.save()
        else:
            primaryType = PhoneCodeList.objects.get(code='primary')
            phone =  PersonPhone(phone_type=primaryType,phone_number=value)
            self.phone_numbers.add(phone)
            self.save()

    primaryTelephone = property(get_primaryTelephone,set_primaryTelephone)

    def get_primaryEmail(self):
        paddr = self.email_addresses.filter(email_type='primary')
        if (paddr):
            return paddr.first().email
        else:
            return None

    def set_primaryEmail(self, value):
        paddr = self.email_addresses.filter(email_type='primary')
        if (paddr):
            firstOne = paddr.first()
            firstOne.email = value
            firstOne.save()
        else:
            primaryType = EmailCodeList.objects.get(code='primary')
            address =  PersonEmail(email_type=primaryType,email=value)
            self.email_addresses.add(address)
            self.save()

    primaryEmail = property(get_primaryEmail,set_primaryEmail)

    def get_absolute_url(self):
        return reverse('person_detail', kwargs={'pk': self.pk})

    def __init__(self, *args, **kwargs):
        super(Person, self).__init__(*args, **kwargs)
        nameField = self._meta.get_field('name')
        nameField.verbose_name="Name of Person"
        nameField.help_text="Name You would like to be displayed"
        notesField = self._meta.get_field('notes')
        notesField.verbose_name="Short Bio"
        notesField.help_text="Short Biography"
        urlField = self._meta.get_field('url')
        urlField.verbose_name="Personal Web Page"
        urlField.help_text="Web page that describes you, or your work"



    def create(self, *args, **kwargs):
        if (self.name is None):
            if self.givenName is not None and self.familyName is not None:
                  self.name = self.givenName + ' ' + self.familyName
            else:
                if self.givenName is not None:
                  self.name = self.givenName
                else:
                    if self.familyName is not None:
                        self.name =  self.familyName
        super(Person,self).save(*args,**kwargs)

    # override save to use the model validatons... if you use a form, then these are run automatically
    def save(self, *args, **kwargs):
        self.clean_name()
        self.validate_unique()
        super(Person,self).save( *args, **kwargs)

    def validate_unique(self, exclude=None):
        try:
            dupname = Person.objects.filter(name=self.name)

            if (dupname.count() > 1):
                raise ValidationError(
                     {
                            "name":
                            ("Name is a not unique. ",)
                        }
                )
            person = dupname.first()
            if (person):
                if (person.pk == self.pk):
                    return
                self.name = self.name + "_1"
                raise ValidationError(
                     {
                            "name":
                            ("Name is a not unique. ",)
                    }
                )
        except ObjectDoesNotExist:
            return

    def clean_name(self):
        super(Person, self).clean()
        p = self
        if (not self.name):
            if self.givenName  and self.familyName :
                self.name = '{1} {0}'.format( self.familyName,  self.givenName,)
            else:
                if self.givenName:
                  self.name = self.givenName
                else:
                    if self.familyName:
                        self.name =  self.familyName
                    else:
                        raise ValidationError(
                            {
                            NON_FIELD_ERRORS:
                            ("Family Name, or Given Name must be provided",)
                            }
                        )
    def clean_phone_numbers(self):
        super(Person, self).clean()
        p = self
        if (not self.phone_numbers):
            primaryNumbers = self.phone_numbers.filter(phone_type='primary')
            if (primaryNumbers.count() >1):
                raise ValidationError(
                    {
                    "phone_numbers":
                    ("There can only be one primary phone number",)
                    }
                )

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'hs_party'

    pass


class PersonEmail(PartyEmailModel):
    person = models.ForeignKey(to=Person, related_name="email_addresses",null=True,blank=True)

    class Meta:
        """Meta Class for your model."""
        app_label = 'hs_party'
    pass

class PersonLocation(PartyLocationModel):
    person = models.ForeignKey(to=Person, related_name="mail_addresses",null=True,blank=True)

    class Meta:
        """Meta Class for your model."""
        app_label = 'hs_party'
    def validate_unique(self, exclude=None):
        try:
            dupes = PersonLocation.objects.filter(person=self.person,address_type='primary')

            if (dupes.count() > 1):
                raise ValidationError(
                     {
                            NON_FIELD_ERRORS:
                            ("Only one primary. ",)
                        }
                )
            else:
                return
        except ObjectDoesNotExist:
            return

    def save(self, *args, **kwargs):
        self.validate_unique()
        super(PersonLocation,self).save( *args, **kwargs)
    pass

class PersonPhone(PartyPhoneModel):
    person = models.ForeignKey(to=Person, related_name="phone_numbers",null=True,blank=True)

    class Meta:
        """Meta Class for your model."""
        app_label = 'hs_party'

    def validate_unique(self, exclude=None):
        try:
            dupes = PersonPhone.objects.filter(person=self.person,phone_type='primary')

            if (dupes.count() > 1):
                raise ValidationError(
                     {
                            NON_FIELD_ERRORS:
                            ("Only one primary. ",)
                        }
                )
            else:
                return
        except ObjectDoesNotExist:
            return

    def save(self, *args, **kwargs):
        self.validate_unique()
        super(PersonPhone,self).save( *args, **kwargs)
    pass


class PersonExternalIdentifier(models.Model):
    person = models.ForeignKey(to=Person, related_name='externalIdentifiers')
    IDENTIFIER_CHOICE = (
                         ("LOC", "Library of Congress")
                         , ("NSF", "National Science Foundation")
                         , ("linked","linked Data URL")
                         , ("twitter", "twitterHandle")
                         , ("ProjectPage", "page for project")
                         , ("other", "other")
    )
    identifierName = models.ForeignKey(ExternalIdentifierCodeList, verbose_name="User Identities",
                                      help_text="User identities from external sites",max_length='10')
    otherName = models.CharField(verbose_name="If other is selected, type of identifier", blank=True,max_length='255')
    identifierCode = models.CharField(verbose_name="Username or Identifier for site",max_length='255')
    createdDate = models.DateField(auto_now_add=True)
    # validation needed. if identifierName =='other' then otherName must be populated.

    class Meta:
        app_label = 'hs_party'


# class UserKeywords(models.Model):
#     person = models.ForeignKey(Person, related_name="keywords",)
#     keyword = models.CharField(max_length='100')
#     createdDate = models.DateField(auto_now_add=True)
#     pass

class UserCodeList(models.Model):
    # these are classes, so changing the model means you change this
    code = models.CharField(primary_key=True,verbose_name="Code Choice Item", max_length=24, blank=False)
    name = models.CharField(verbose_name="Brief Name of Choice Item",max_length=255, blank=False)
    order = models.IntegerField(verbose_name="Optional Order", blank=True)
    url = models.CharField(verbose_name="Optional Url pointing to provider",max_length=255, blank=True)

    def __unicode__(self):
        return self.name
    class Meta:
        """Meta Class for your model."""
        app_label = 'hs_party'


class OtherName(NameAliasType):
    #ID = models.AutoField(primary_key=True)
    # relation will show in Party as otherNames
    persons = models.ForeignKey(to=Person,related_name='otherNames' )
    # otherName = models.CharField(verbose_name="Other Name or alias",max_length='255')
    # ANNOTATION_TYPE_CHOICE = (
    #     ("change", "Name Change"),
    #     ("citation", "Publishing Alias"),
    #     ("fullname", "Full Name variation"),
    #     ("other", "other type of alias")
    # )
    # annotation = models.CharField(verbose_name="type of alias", default="other",max_length='10')



    class Meta:
        """Meta Class for your model."""
        app_label = 'hs_party'



# @receiver(pre_save, sender=Person)
# def person_name_check(sender, instance,  **kwargs):
#     p = instance
#     if (not p.name):
#         if p.givenName  and p.familyName :
#               p.name = '{1} {0}'.format( p.familyName,  p.givenName,)
#         else:
#             if p.givenName:
#               p.name = p.givenName
#             else:
#                 if p.familyName:
#                     p.name =  p.familyName
#                 else:
#                     raise ValidationError(
#                         {
#                         NON_FIELD_ERRORS:
#                         ("Family Name, or Given Name must be provided",)
#                     }
#                     )
#
#
#     try:
#         dupname = Person.objects.get(name=instance.name)
#
#         if (dupname):
#             if (dupname == p):
#                 return p
#             p.name = p.name + "_1"
#             raise ValidationError(
#                  {
#                         "name":
#                         ("Name is a not unique. ",)
#                     }
#             )
#     except ObjectDoesNotExist:
#
#         pass
#     return p

