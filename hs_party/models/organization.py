from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group
from django.db import models
from mezzanine.pages.models import Page, RichText,Displayable
from mezzanine.core.fields import FileField, RichTextField
from mezzanine.core.models import Ownable
from mezzanine.generic.models import  Orderable
from mezzanine.generic.fields import KeywordsField
from hs_core.models import AbstractResource
from django.db.models.signals import  post_save
from datetime import date
from uuid import uuid4
from django.db.models.signals import post_save,pre_save,post_init
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist,ValidationError
from django.core.urlresolvers import reverse
from django.core.exceptions import NON_FIELD_ERRORS

from party import Party
from party_types import PartyEmailModel,\
    PartyGeolocation,PartyPhoneModel,\
    PartyLocationModel,ExternalIdentifierCodeList,\
    NameAliasType,AddressCodeList,PhoneCodeList,EmailCodeList
from person import Person


__author__ = 'valentin'

#=======================================================================================
# ORGANIZATION
# ======================================================================================
# make consistent with CUAHSI

class OrganizationCodeList(models.Model):
    # these are classes, so changing the model means you change this
    code = models.CharField(primary_key=True,verbose_name="Acronym for Organization Type", max_length=24, blank=False)
    name = models.CharField(verbose_name="Brief Name or Organization Type",max_length=255, blank=False)
    order = models.IntegerField(verbose_name="Optional Order", blank=True)
    url = models.CharField(verbose_name="Optional Url pointing to provider",max_length=255, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'hs_party'
    pass


class Organization(Displayable,Party):
    ORG_TYPES_CHOICES = (
    ("commercial", "Commercial/Professional")
    , ("university","University")
    , ("college", "College")
    , ("gov", "Government Organization")
    , ("nonprofit", "Non-profit Organization")
    , ("k12", "School  Kindergarten to 12th Grade")
    , ("cc", "Community College ")
    , ("other", "Other")
    , ("Unspecified", "Unspecified")
    )
    logoUrl = models.ImageField(blank=True, upload_to='orgLogos')
    #smallLogoUrl = models.ImageField()
    parentOrganization = models.ForeignKey('self', null=True,blank=True)
    organizationType = models.ForeignKey(OrganizationCodeList,)
    # externalIdentifiers from ExternalOrgIdentifiers
    specialities = KeywordsField()
    persons = models.ManyToManyField(Person, verbose_name="Organizations",
                                           through="OrganizationAssociation", blank=True, null=True,
                                           related_name="organizations",symmetrical=False
    ,)


    #businessAddress = models.CharField(max_length='100', blank=True, verbose_name="business Address", help_text="business Mailing or Street, if known")
    #businessTelephone = models.CharField(max_length='30', blank=True, verbose_name="business Telephone",help_text="business Telephone, if known")



    def get_businessAddress(self):
        paddr = self.mail_addresses.filter(address_type='primary')
        if (paddr):
            return paddr.first().address
        else:
            return None

    def set_businessAddress(self, value):
        paddr = self.mail_addresses.filter(address_type='primary')
        if (paddr):
            firstOne = paddr.first()
            firstOne.address = value
            firstOne.save()
        else:
            primaryType = AddressCodeList.objects.get(code='primary')
            address =  OrganizationLocation(address_type=primaryType,address=value)
            self.mail_addresses.add(address)
            self.save()

    businessAddress = property(get_businessAddress,set_businessAddress)


    def get_businessTelephone(self):
        phone1 = self.phone_numbers.filter(phone_type='primary')
        if (phone1):
            return phone1.first().phone_number
        else:
            return None


    def set_businessTelephone(self, value):
        phone1 = self.phone_numbers.filter(phone_type='primary')
        if (phone1):
            firstOne = phone1.first()
            firstOne.phone_number = value
            firstOne.save()
        else:
            primaryType = PhoneCodeList.objects.get(code='primary')
            phone =  OrganizationPhone(phone_type=primaryType,phone_number=value)
            self.phone_numbers.add(phone)
            self.save()

    businessTelephone = property(get_businessTelephone,set_businessTelephone)

    def get_businessEmail(self):
        paddr = self.email_addresses.filter(email_type='primary')
        if (paddr):
            return paddr.first().email
        else:
            return None

    def set_businessEmail(self, value):
        paddr = self.email_addresses.filter(email_type='primary')
        if (paddr):
            firstOne = paddr.first()
            firstOne.email = value
            firstOne.save()
        else:
            primaryType = EmailCodeList.objects.get(code='primary')
            address =  OrganizationEmail(email_type=primaryType,email=value)
            self.email_addresses.add(address)
            self.save()

    businessEmail = property(get_businessEmail,set_businessEmail)


    def get_absolute_url(self):
        return reverse('organization_detail', kwargs={'pk': self.pk})

    def __init__(self, *args, **kwargs):
        super(Organization, self).__init__(*args, **kwargs)
        nameField = self._meta.get_field('name')
        nameField.verbose_name="Organization Name"
        nameField.help_text="Organization Name"
        notesField = self._meta.get_field('notes')
        notesField.verbose_name="Description"
        notesField.help_text="Brief Description of organizaiton"
        urlField = self._meta.get_field('url')
        urlField.verbose_name="Web Page for Organization"
        urlField.help_text="Organizaiton web page"

    def __unicode__(self):
        return unicode(self.name)

    class Meta:
        app_label = 'hs_party'
    pass



class OrganizationEmail(PartyEmailModel):
    organization = models.ForeignKey(to=Organization, related_name="email_addresses", blank=True,null=True)

    class Meta:
        app_label = 'hs_party'

    def validate_unique(self, exclude=None):
        try:
            dupes = OrganizationEmail.objects.filter(organization=self.organization,email_type='primary')

            if (dupes.count() > 1):
                raise ValidationError(
                     {
                            NON_FIELD_ERRORS:
                            ("Only one primary type allowed ",)
                        }
                )
            else:
                return
        except ObjectDoesNotExist:
            return

    def save(self, *args, **kwargs):
        self.validate_unique()
        super(OrganizationEmail,self).save( *args, **kwargs)

    pass

class OrganizationLocation(PartyLocationModel):
    organization = models.ForeignKey(to=Organization, related_name="mail_addresses", blank=True,null=True)

    class Meta:
        app_label = 'hs_party'

    def validate_unique(self, exclude=None):
        try:
            dupes = OrganizationLocation.objects.filter(organization=self.organization,address_type='primary')

            if (dupes.count() > 1):
                raise ValidationError(
                     {
                            NON_FIELD_ERRORS:
                            ("Only one primary type allowed ",)
                        }
                )
            else:
                return
        except ObjectDoesNotExist:
            return

    def save(self, *args, **kwargs):
        self.validate_unique()
        super(OrganizationLocation,self).save( *args, **kwargs)


    pass

class OrganizationPhone(PartyPhoneModel):
    organization = models.ForeignKey(to=Organization, related_name="phone_numbers", blank=True,null=True)

    class Meta:
        app_label = 'hs_party'

    def validate_unique(self, exclude=None):
        try:
            dupes = OrganizationPhone.objects.filter(organization=self.organization,phone_type='primary')

            if (dupes.count() > 1):
                raise ValidationError(
                     {
                            NON_FIELD_ERRORS:
                            ("Only one primary type allowed ",)
                        }
                )
            else:
                return
        except ObjectDoesNotExist:
            return

    def save(self, *args, **kwargs):
        self.validate_unique()
        super(OrganizationPhone,self).save( *args, **kwargs)
    pass



class OrganizationName(NameAliasType):
    organization = models.ForeignKey(to=Organization, related_name="alternate_names", blank=True,null=True)

    class Meta:
        app_label = 'hs_party'
    pass


class ExternalOrgIdentifier(models.Model):
    organization = models.ForeignKey(to=Organization, related_name='externalIdentifiers')
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