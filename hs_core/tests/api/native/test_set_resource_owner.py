import unittest

from django.test import TestCase
from django.contrib.auth.models import User
from hs_core import hydroshare
from hs_core.models import GenericResource

# TODO: the api being tested  here (hydroshare.set_resource_owner()) is not based on new access_control app. Since
# similar api is available in the access_control app, do we need a wrapper api in hs_core? If not then we should delete
# this test since access_control app has this test


class TestSetResourceOwnerAPI(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        User.objects.all().delete()
        GenericResource.objects.all().delete()
        pass

    @unittest.skip
    def test_set_resource_owner(self):
        # create a user to be used for creating the resource
        user_creator = hydroshare.create_account(
            'creator@usu.edu',
            username='creator',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        # create a user to be set as the resource owner
        user_owner = hydroshare.create_account(
            'pabitra.dash@usu.edu',
            username='pabitra',
            first_name='Pabitra',
            last_name='Dash',
            superuser=False,
            groups=[]
        )

        # create a user who is not a resource owner
        user_non_owner = hydroshare.create_account(
            'pkdash.reena@gmail.com',
            username='pkdash',
            first_name='Pabitra',
            last_name='Dash',
            superuser=False,
            groups=[]
        )

        # create a resource without any owner
        resource = GenericResource.objects.create(
            user=user_creator,
            title='My resource',
            creator=user_creator,
            last_changed_by=user_creator,
            doi='doi1000100010001'
        )

        # set the resource owner - this is the api we are testing
        hydroshare.set_resource_owner(resource.short_id, user_owner)

        # test that the user we set as the owner of the resource is one of the resource owners
        self.assertTrue(resource.owners.filter(pk=user_owner.pk).exists(),
                        msg='user_owner not one of the owners of this resource')


        self.assertFalse(resource.owners.filter(pk=user_non_owner.pk).exists(),
                        msg='user_non_owner is one of the owners of this resource')

        # test that there is only one resource owner at this point
        self.assertEqual(
            1,
            resource.owners.all().count(),
            msg="More than one resource owners found."
        )




