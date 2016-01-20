__author__ = 'tonycastronova'

from unittest import TestCase

from django.contrib.auth.models import User, Group

from hs_core.hydroshare import resource
from hs_core.hydroshare import users


class TestGetResource(TestCase):
    def setUp(self):
        self.hydroshare_author_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = users.create_account(
            'test_user@email.com',
            username='sometestuser',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[])

        # get the user's id
        self.userid = User.objects.get(username=self.user).pk

        self.group = users.create_group(
            'MytestGroup',
            members=[self.user],
            owners=[self.user]
            )

        self.res = resource.create_resource(
            'GenericResource',
            self.user,
            'My Test Resource'
            )

    def tearDown(self):
        self.user.delete()
        self.group.delete()
        self.hydroshare_author_group.delete()
        self.res.delete()

    def test_get_resource(self):
        # function to test: hydroshare.get_resource() which returns a Bags object
        # TODO: I (Pabitra) don't see any useful way of using the hydroshare.get_resource() function
        # One can't do much with a Bags object. For downloading a bag we are using resource.bag_url.
        # So I suggest we delete the get_resource() function and remove this test
        
        res_bag = resource.get_resource(self.res.short_id)
        self.assertTrue(res_bag is not None)
