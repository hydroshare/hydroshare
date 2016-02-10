import unittest

from unittest import TestCase
from hs_core.hydroshare import resource, get_resource_by_shortkey
from hs_core.hydroshare import users
from hs_core import hydroshare
from hs_core.models import GenericResource
from django.contrib.auth.models import User, Group
import datetime as dt

# TODO: These unit tests can't be part of test run until the api being tested (hydroshare.update_resource()) is
# fixed first


class TestUpdateResource(TestCase):
    def setUp(self):
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = users.create_account(
            'test_user@email.com',
            username='mytestuser',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[self.group])

        # get the user's id
        self.userid = User.objects.get(username=self.user).pk

        self.group = users.create_group(
            'MyGroup',
            members=[self.user],
            owners=[self.user]
        )

        self.res = hydroshare.create_resource(
            'GenericResource',
            self.user,
            'My Test Resource'
        )

    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()
        GenericResource.objects.all().delete()

    @unittest.skip
    def test_update_resource_with_metadata(self):
        # Note: for detailed test for updating metadata - see 'test_update_metadata.py'
        # here we may just update one or 2 metadata elements. Focus should be updating the resource
        # with other data
        metadata_dict = [
            {'creator': {'name':'John Smith', 'email':'jsmith@gmail.com'}},
            {'creator': {'name':'Lisa Molley', 'email':'lmolley@gmail.com'}},
            {'contributor': {'name':'Kelvin Marshal', 'email':'kmarshal@yahoo.com',
                             'organization': 'Utah State University',
                             'profile_links': [{'type':'yahooProfile', 'url': 'http://yahoo.com/LH001'}]}},
            {'coverage': {'type':'period', 'value':{'name':'Name for period coverage' , 'start':'1/1/2000', 'end':'12/12/2012'}}},
            {'coverage': {'type':'point', 'value': {'name':'Name for point coverage', 'east':'56.45678', 'north':'12.6789'}}},
            {'format': {'value': 'txt/csv'}},
            {'format': {'value': 'zip'}},
            {'identifier': {'name':'someIdentifier', 'url':"http://some.org/001"}},
            {'language': {'code':'eng'}},
            {'relation': {'type':'isPartOf', 'value':'http://hydroshare.org/resource/001'}},
            {'rights': {'statement':'This is the rights statement for this resource', 'url':'http://rights.org/001'}},
            {'source': {'derived_from':'http://hydroshare.org/resource/0001'}},
            {'subject': {'value':'sub-1'}},
            {'subject': {'value':'sub-2'}},
            ]
        self.res = hydroshare.update_resource(
            pk=self.res.short_id,
            metadata = metadata_dict
        )

        # title element is recreated in the resource update api method
        self.assertEqual(self.res.metadata.title.value, 'My Test Resource', msg='resource title did not match')

        # resource description element is created in the resource signal handler
        self.assertEqual(self.res.metadata.description.abstract, 'My Test Resource')

        # the following 2 date elements should have been created in the resource creation signal handler
        self.assertEqual(self.res.metadata.dates.all().count(), 2, msg="Number of date elements not equal to 2.")
        self.assertIn('created', [dt.type for dt in self.res.metadata.dates.all()], msg="Date element type 'Created' does not exist")
        self.assertIn('modified', [dt.type for dt in self.res.metadata.dates.all()], msg="Date element type 'Modified' does not exist")

        # number of creators at this point should be 3 (2 we are creating here one is automatically generated in resource creation signal
        self.assertEqual(self.res.metadata.creators.all().count(), 3, msg='Number of creators not equal to 3')
        self.assertIn('John Smith', [cr.name for cr in self.res.metadata.creators.all()], msg="Creator 'John Smith' was not found")
        self.assertIn('Lisa Molley', [cr.name for cr in self.res.metadata.creators.all()], msg="Creator 'Lisa Molley' was not found")

        # number of contributors at this point should be 1
        self.assertEqual(self.res.metadata.contributors.all().count(), 1, msg='Number of contributors not equal to 1')

        # there should be now 2 coverage elements
        self.assertEqual(self.res.metadata.coverages.all().count(), 2, msg="Number of coverages not equal to 2.")

        # there should be now 2 format elements
        self.assertEqual(self.res.metadata.formats.all().count(), 2, msg="Number of format elements not equal to 2.")

        # there should be now 2 identifier elements ( 1 we rae creating her + 1 auto generated in the resource creation signal handler)
        self.assertEqual(self.res.metadata.identifiers.all().count(), 2, msg="Number of identifier elements not equal to 1.")

        self.assertEqual(self.res.metadata.language.code, 'eng', msg="Resource has a language that is not English.")

        self.assertEqual(self.res.metadata.relations.all().count(), 1,
                         msg="Number of source elements is not equal to 1")

        self.assertEqual(self.res.metadata.rights.statement, 'This is the rights statement for this resource', msg="Statement of rights did not match.")
        self.assertEqual(self.res.metadata.rights.url, 'http://rights.org/001', msg="URL of rights did not match.")

        self.assertEqual(self.res.metadata.sources.all().count(), 1, msg="Number of sources is not equal to 1.")
        self.assertIn('http://hydroshare.org/resource/0001',
                      [src.derived_from for src in self.res.metadata.sources.all()],
                      msg="Source element with derived from value of %s does not exist."
                          % 'http://hydroshare.org/resource/0001')

        # there should be 2 subject elements for this resource
        self.assertEqual(self.res.metadata.subjects.all().count(), 2, msg="Number of subject elements found not be 1.")
        self.assertIn('sub-1', [sub.value for sub in self.res.metadata.subjects.all()],
                      msg="Subject element with value of %s does not exist." % 'sub-1')
        self.assertIn('sub-2', [sub.value for sub in self.res.metadata.subjects.all()],
                      msg="Subject element with value of %s does not exist." % 'sub-1')
