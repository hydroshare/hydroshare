__author__ = 'Pabitra'
from django.test import TestCase
from django.contrib.auth.models import User
from hs_core import hydroshare
from hs_core.models import GenericResource

class TestResourceModifiedAPI(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        User.objects.all().delete()
        GenericResource.objects.all().delete()
        pass

    def test_resource_modified(self):
        # create a user to be used for creating the resource
        user_creator = hydroshare.create_account(
            'creator@usu.edu',
            username='creator',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )
        resource_changed_by = hydroshare.create_account(
            'pabitra.dash@usu.edu',
            username='pkdash',
            first_name='Pabitra',
            last_name='Dash',
            superuser=False,
            groups=[]
        )

        # create a resource
        resource = hydroshare.create_resource('GenericResource', user_creator, 'My resource')

        # get the number of bags currently exists for the resource
        resource_bag_count_old = resource.bags.all().count()

        # set the resource last changed by a different user - this is the api call we are testing
        hydroshare.utils.resource_modified(resource, resource_changed_by)

        # get the number of bags the resource have now
        resource_bag_count_new = resource.bags.all().count()

        # test that the resource last changed by is the same user that we passed into our api call
        self.assertEqual(resource_changed_by, resource.last_changed_by)

        # test that the resource last changed by is not the same user that originally created the resource
        self.assertNotEqual(user_creator, resource.last_changed_by)

        # test the number of bags the resource has after the resource got updated is one more than what the resource
        # had prior to the update
        self.assertEqual(resource_bag_count_new, resource_bag_count_old + 1)