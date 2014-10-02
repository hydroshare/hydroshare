from copy import deepcopy
from mezzanine.pages.admin import PageAdmin
from mezzanine.core.admin import DisplayableAdmin, TabularDynamicInlineAdmin, OwnableAdmin,StackedDynamicInlineAdmin
from django.contrib import admin
from django.contrib.admin import ModelAdmin,StackedInline
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from django.forms import ModelForm
from .models import *

class PersonInline(admin.TabularInline):
    model = Person

class PersonAddressInline(admin.TabularInline):
    model = PersonLocation
    extra = 1

class PersonEmailInline(admin.TabularInline):
    model = PersonEmail
    extra = 1

class PersonIdentifiersInline(admin.StackedInline):
    model = PersonExternalIdentifier
    extra = 1

class PersonOtherNamesInline(admin.TabularInline):
    model = OtherName
    extra = 1

class PersonPhoneInline(admin.TabularInline):
    model = PersonPhone
    extra = 1

#####
# Org
# #####
#person_extra_fieldsets = ((None, {"fields": ("dob",)}),)

class OrgInline (admin.StackedInline):
    model = Organization
    list_display = ('name',"organizationType")

class OrgAddressInline(admin.TabularInline):
    model = OrganizationLocation
    extra = 1

class OrgEmailInline(admin.TabularInline):
    model = OrganizationEmail
    extra = 1

class OrgIdentifiersInline(admin.StackedInline):
    model = ExternalOrgIdentifier
    extra = 1

class OrgOtherNamesInline(admin.TabularInline):
    model = OrganizationName
    extra = 1

class OrgPhoneInline(admin.TabularInline):
    model = OrganizationPhone
    extra = 1

class PersonAssociationInline(StackedDynamicInlineAdmin):
    model = Organization.persons.through
    extra = 0
#    inlines = (OrgInline)

class OrganizationTypeInline(admin.TabularInline):
    model = OrganizationCodeList
    list_display = ('code',"name")

#class OrganizationAdmin( ModelAdmin):
class OrganizationAdmin(DisplayableAdmin):
    model = Organization
    search_fields = ['name',]
    readonly_fields = ["uniqueCode",]
    inlines = (OrgOtherNamesInline,
               OrgEmailInline,
               OrgIdentifiersInline,
               OrgAddressInline,
               OrgPhoneInline,)
    #inlines = (PersonAssociationInline,)
    list_display = ("id","name","organizationType")
    list_display_links = ("id",)
    list_editable = ()
    ordering = ("name",)
    fieldsets = (
       (None, {
           "fields": ("uniqueCode","name","organizationType","parentOrganization","url"),
               }),
        ("Advanced", {
           "fields": ("specialities","notes",),
               }),
   )

    #fieldsets = deepcopy(PageAdmin.fieldsets) #+ person_extra_fieldsets
    pass



class UserTypeInline(admin.TabularInline):
    model = UserCodeList
    list_display = ('code',"name")

class PersonAdmin(DisplayableAdmin):
    model = Person
    search_fields = [ "name" , ]
    inlines = (PersonOtherNamesInline,
               PersonIdentifiersInline,
               PersonEmailInline,
               PersonAddressInline,
               PersonPhoneInline, )# OrgInline)
    list_display = ("id","name","primaryOrganizationRecord",)
    list_display_links = ("id",)
    list_editable = ()
    readonly_fields = ["uniqueCode",]
    ordering = ("name",)
    fieldsets = (
        (None, {
            "fields": ("uniqueCode","givenName","familyName","name","jobTitle","primaryOrganizationRecord",),
                }),
        ("Contact", {
           "fields": ("primaryAddress","primaryTelephone"),
               }),
        ("Personal", {
           "fields": ("url","notes",),
               }),
    )
    #filter_horizontal = ('organizations',)
    pass

admin.site.register(Organization, OrganizationAdmin)

admin.site.register(Person, PersonAdmin)


admin.site.register(OrganizationAssociation)

admin.site.register(UserCodeList)
admin.site.register(OrganizationCodeList)
admin.site.register(PhoneCodeList)
admin.site.register(AddressCodeList)
admin.site.register(EmailCodeList)
admin.site.register(ExternalIdentifierCodeList)
admin.site.register(NameAliasCodeList)


class GroupInlineAdmin(admin.TabularInline):
    model = Group



class PersonInline(admin.TabularInline):
    model = Person
    list_display = ('name',"familyName","givenName",)





