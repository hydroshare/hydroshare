from django.test import TestCase
from django.contrib.auth import get_user_model
#from django_webtest import WebTest
from ..models.organization import Organization
from ..models.person import Person, OtherName,UserCodeList,PersonEmail,PersonPhone,PersonLocation
from ..models.party_types import NameAliasCodeList,AddressCodeList,PhoneCodeList,EmailCodeList
from django.core.exceptions import ObjectDoesNotExist,ValidationError



__author__ = 'valentin'
FIRST1='first'
FIRST2='me'

LAST1='last'
LAST2='You'

NAME1="{0} {1}".format(FIRST1, LAST1)
NAME2="{0} {1}".format( FIRST2, LAST2)

ALTNAME1='Alt 1'
ALTNAME2='Alt2'

def otherNameAliasType():
   return NameAliasCodeList.objects.get(code='other')

def PersonCore():
    return Person(givenName=FIRST1, familyName=LAST1, name=NAME1)


def PersonBasic():
    aPerson = Person(givenName=FIRST2, familyName=LAST2, name=NAME2)
    aPerson.save()
    OtherName.objects.create(persons=aPerson, otherName=ALTNAME2, annotation=otherNameAliasType())
    OtherName.objects.create(persons=aPerson, otherName=ALTNAME1, annotation=otherNameAliasType())
    PersonEmail.objects.create(person=aPerson,email='me@example.com' )
    PersonPhone.objects.create(person=aPerson,phone_number="1234567890" )
    PersonLocation.objects.create(person=aPerson,address="somestreet address" )
    return aPerson

def PersonOne():
    aPerson = PersonCore()
    aPerson.save()
    return aPerson

def PersonTwo():
    aPerson = PersonBasic()

    return aPerson

def PersonUnsavedDupe():
    aPerson = Person(givenName=FIRST2, familyName=LAST2, name=NAME2)

    return aPerson

# courtesy method for other classes
def AddPeople():
    return {PersonOne(),
    PersonTwo()}



class PersonTest(TestCase):
    fixtures =['initial_data.json']

    def setUp(self):

        self.person1=PersonOne()

        self.person2= PersonTwo()



    def test_Person(self):
        person1 = Person.objects.get(familyName=LAST1)

        self.assertEqual(person1.otherNames.count(), 0)

        person2 = Person.objects.get(familyName=LAST2)
        self.assertEqual(person2.otherNames.count(),2)
        self.assertEquals(person2.otherNames.get(otherName=ALTNAME1).annotation.code, 'other')
        self.assertIsNotNone(person2.uniqueCode)
        print("uuid:" + person2.uniqueCode)


    def test_otherNames(self):
        person1 = Person.objects.get(familyName=LAST1)
        person2 = Person.objects.get(familyName=LAST2)
        self.assertEqual(person1.otherNames.count(), 0)
        self.assertEqual(person2.otherNames.count(), 2)

    def test_name(self):
        person1 = Person.objects.get(familyName=LAST1)
        self.assertEqual(person1.name, NAME1)

    def test_dupecheck(self):
        person1 = Person(familyName=LAST1, givenName=FIRST1,name="Different Display Name")
        person2 = PersonUnsavedDupe()
        person1.save() # no error, diff display naame
        with self.assertRaises(ValidationError):
           #person1.validate_unique()
           person2.save() # should be an error

    def test_primaryAddress_get(self):
        person1 = Person.objects.get(name="Sandy Flume")

        addr = PersonLocation.objects.filter(person=person1,address_type__code='primary')
        self.assertEqual(addr.count(),1)
        self.assertEqual(addr.first().address, person1.primaryAddress)


    def test_primaryAddress_set(self):
        person1 = Person.objects.get(name="Sandy Flume")
        ADDRESS = "setNewAddress"
        person1.primaryAddress = ADDRESS
        self.assertEqual(ADDRESS, person1.primaryAddress)

        addr = PersonLocation.objects.filter(person=person1,address_type__code='primary')
        self.assertEqual(addr.count(),1)
        self.assertEqual(addr.first().address, person1.primaryAddress)

    def test_primaryAddress_addnew(self):
        self.assertIsNotNone(self.person1)
        self.assertFalse(self.person1.primaryAddress)
        ADDRESS = "setNewAddress"
        address_type = AddressCodeList.objects.get(code='primary')
        self.person1.primaryAddress = ADDRESS
        self.assertEqual(ADDRESS, self.person1.primaryAddress)

        addr = PersonLocation.objects.filter(person=self.person1,address_type__code='primary')
        self.assertEqual(addr.count(),1)
        self.assertEqual(addr.first().address, self.person1.primaryAddress)

    def test_primaryPhone_set(self):
        person1 = Person.objects.get(name="Sandy Flume")
        phone = "123-123-1345"
        person1.primaryTelephone = phone
        self.assertEqual(phone, person1.primaryTelephone)

        addr = PersonPhone.objects.filter(person=person1,phone_type__code='primary')
        self.assertEqual(addr.count(),1)
        self.assertEqual(addr.first().phone_number, person1.primaryTelephone)

    def test_primaryPhone_addnew(self):
        self.assertIsNotNone(self.person1)
        self.assertFalse(self.person1.primaryTelephone)
        phone = "123-123-1345"
        address_type = PhoneCodeList.objects.get(code='primary')
        self.person1.primaryTelephone = phone
        self.assertEqual(phone, self.person1.primaryTelephone)

        addr = PersonPhone.objects.filter(person=self.person1,phone_type__code='primary')
        self.assertEqual(addr.count(),1)
        self.assertEqual(addr.first().phone_number, self.person1.primaryTelephone)

    # set a primary phone, then try to add a second one.
    def test_primaryPhone_addSecond(self):
        self.assertIsNotNone(self.person1)
        self.assertFalse(self.person1.primaryTelephone)
        phone = "123-123-1345"
        address_type = PhoneCodeList.objects.get(code='primary')
        self.person1.primaryTelephone = phone
        self.assertEqual(phone, self.person1.primaryTelephone)

        addr = PersonPhone.objects.filter(person=self.person1,phone_type__code='primary')
        self.assertEqual(addr.count(),1)
        self.assertEqual(addr.first().phone_number, self.person1.primaryTelephone)


        with self.assertRaises(ValidationError):
            thirdOne = PersonPhone(phone_type=address_type,phone_number='001-000-1111')
            self.person1.phone_numbers.add(thirdOne)
            thirdOne.save()
            self.person1.save()

        with self.assertRaises(ValidationError):
            # test object create
            secondOne = PersonPhone.objects.create(person=self.person1,phone_type=address_type,phone_number='001-000-1111')


    def test_primaryTelephone_addnew(self):
        self.assertIsNotNone(self.person1)
        self.assertFalse(self.person1.primaryTelephone)
        ADDRESS = "setNewAddress"
        address_type = PhoneCodeList.objects.get(code='primary')
        self.person1.primaryTelephone = ADDRESS
        self.assertEqual(ADDRESS, self.person1.primaryTelephone)

        phones = PersonPhone.objects.filter(person=self.person1,phone_type__code='primary')
        self.assertEqual(phones.count(),1)
        self.assertEqual(phones.first().phone_number, self.person1.primaryTelephone)

    def test_primaryEmail_addnew(self):
        self.assertIsNotNone(self.person1)
        self.assertFalse(self.person1.primaryEmail)
        ADDRESS = "me@example.com"
        address_type = EmailCodeList.objects.get(code='primary')
        self.person1.primaryEmail = ADDRESS
        self.assertEqual(ADDRESS, self.person1.primaryEmail)

        phones = PersonEmail.objects.filter(person=self.person1,email_type__code='primary')
        self.assertEqual(phones.count(),1)
        self.assertEqual(phones.first().email, self.person1.primaryEmail)
    pass