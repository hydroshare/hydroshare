from ..models.person import Person, OtherNames,UserCodeList

__author__ = 'valentin'

FIRST1='first'
FIRST2='me'

LAST1="last"
LAST2='You'

NAME1='{0} {1}' % (FIRST1,LAST1)
NAME2='{0} {1}' % (FIRST2,LAST2)

ALTNAME1='Alt 1'

def PersonCore():
    return Person.objects.create(givenName=FIRST1, familyName=LAST1, name=NAME1)


def PersonUnsaved():
    aPerson = Person.objects.create(givenName=FIRST2, familyName=LAST2, name=NAME2)
    OtherNames.objects.create(persons=aPerson, otherName="abcd", annotation="other")
    OtherNames.objects.create(persons=aPerson, otherName="def", annotation="other")
    return aPerson

def PersonOne():
    aPerson = PersonUnsaved()
    aPerson.save()
    return aPerson

def PersonUnsavedDupe():
    aPerson = Person.objects.create(givenName=FIRST2, familyName=LAST2, name=NAME2)
    OtherNames.objects.create(persons=aPerson, otherName=NAME1, annotation="other")
    OtherNames.objects.create(persons=aPerson, otherName=ALTNAME1, annotation="other")
    return aPerson

