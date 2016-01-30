__author__ = 'tonycastronova'

from django.contrib.auth.models import Group
from django.test import TestCase

from hs_core.hydroshare import resource
from hs_core.hydroshare import users

# iRODS mocking has not been used here as we want to test bag creation which needs
# interaction with iRODS


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

        self.res = resource.create_resource(
            'GenericResource',
            self.user,
            'My Test Resource'
            )

    def test_get_resource(self):
        # function to test: hydroshare.get_resource() which returns a Bags object (not the actual bag file)
        # TODO: Don't see any useful way of using the hydroshare.get_resource() function
        # One can't do much with a Bags object. For downloading a bag we are using resource.bag_url.
        # So it is better that we delete the get_resource() function and remove this test
        
        res_bag = resource.get_resource(self.res.short_id)
        self.assertTrue(res_bag is not None)
