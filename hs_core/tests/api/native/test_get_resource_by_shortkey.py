__author__ = 'Pabitra'

import unittest

from django.contrib.auth.models import User, Group

from hs_core import hydroshare
from hs_core.models import GenericResource


class TestGetResourceByShortkeyAPI(unittest.TestCase):
    def setUp(self):
        self.hydroshare_author_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        pass

    def tearDown(self):
        self.user_creator.uaccess.delete()
        User.objects.all().delete()
        self.hydroshare_author_group.delete()
        GenericResource.objects.all().delete()


    def test_get_resource_by_shortkey(self):
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
        resource = hydroshare.create_resource(
            'GenericResource',
            self.user_creator,
            'My Test Resource'
        )

        # do the test of the api
        self.assertEqual(
            resource,
            hydroshare.get_resource_by_shortkey(resource.short_id)
        )
