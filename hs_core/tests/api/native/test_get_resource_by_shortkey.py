__author__ = 'Pabitra'
from django.test import TestCase
from django.contrib.auth.models import User
from hs_core import hydroshare
from hs_core.models import GenericResource

class TestGetResourceByShortkeyAPI(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        User.objects.all().delete()
        GenericResource.objects.all().delete()
        pass


    def test_get_resource_by_shortkey(self):
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
        resource = GenericResource.objects.create(
            user=user_creator,
            title='My resource',
            creator=user_creator,
            last_changed_by=user_creator,
            doi='doi1000100010001'
        )

        # do the test of the api
        self.assertEqual(
            resource,
            hydroshare.get_resource_by_shortkey(resource.short_id)
        )