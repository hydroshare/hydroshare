__author__ = 'Pabitra'

import unittest

from django.contrib.auth.models import User, Group
from django.http import Http404

from hs_core import hydroshare
from hs_core.models import GenericResource


class TestResolveDOIAPI(unittest.TestCase):
    def setUp(self):
        self.hydroshare_author_group, _ = Group.objects.get_or_create(name='Hydroshare Author')

    def tearDown(self):
        self.user_creator.uaccess.delete()
        User.objects.all().delete()
        GenericResource.objects.all().delete()

    def test_resolve_doi(self):
        # create a user to be used for creating the resource
        self.user_creator = hydroshare.create_account(
            'creator@usu.edu',
            username='creator',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        # create a resource
        new_resource = hydroshare.create_resource(
            'GenericResource',
            self.user_creator,
            'My Test Resource'
        )

        # assign doi to the resource
        new_resource.doi = 'xyz'
        new_resource.save()
        # test that the api call resolve_doi() returns the short_id of the resource when we pass the
        # resource doi in this api call
        self.assertEqual(new_resource.short_id, hydroshare.resolve_doi(new_resource.doi))

        # test the exception 'Http404' is raised when we make the api call
        # passing a random doi ( e.g., '123') that does not exist
        with self.assertRaises(Http404):
            hydroshare.resolve_doi("123")
