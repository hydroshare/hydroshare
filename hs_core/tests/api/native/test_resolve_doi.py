__author__ = 'Pabitra'
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from hs_core import hydroshare
from hs_core.models import GenericResource

class TestResolveDOIAPI(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        User.objects.all().delete()
        GenericResource.objects.all().delete()
        pass

    def test_resolve_doi(self):
        # create a user to be used for creating the resource
        user_creator = hydroshare.create_account(
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
            user_creator,
            'My Test Resource'
        )

        # test that the api call resolve_doi() returns the short_id of the resource when we pass the
        # resource doi in this api call
        self.assertEqual(new_resource.short_id, hydroshare.resolve_doi(new_resource.doi))

        # test the exception 'ObjectDoesNotExit' is raised when we make the api call
        # passing a random doi ( e.g., '123') that does not exist
        self.assertRaises(ObjectDoesNotExist, lambda : hydroshare.resolve_doi("123"))
