
from django.contrib.auth.models import Group, User
from django.test import TestCase

from hs_core.hydroshare import resource, utils
from hs_core.hydroshare import users
from hs_core.models import BaseResource

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
            'CompositeResource',
            self.user,
            'My Test Resource'
        )

    def tearDown(self):
        super(TestGetResource, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        self.res.delete()
        BaseResource.objects.all().delete()

    def test_get_resource(self):
        # function to test: hydroshare.get_resource() which returns a Bags object (not the actual bag file)
        # TODO: Don't see any useful way of using the hydroshare.get_resource() function
        # One can't do much with a Bags object. For downloading a bag we are using resource.bag_url.
        # So it is better that we delete the get_resource() function and remove this test

        res = utils.get_resource_by_shortkey(self.res.short_id)
        self.assertTrue(res is not None)
