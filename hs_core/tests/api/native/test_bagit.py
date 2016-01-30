from django.contrib.auth.models import Group, User
from django.test import TestCase

from hs_core import hydroshare
from hs_core.hydroshare import hs_bagit

from django_irods.storage import IrodsStorage


class TestBagIt(TestCase):
    def setUp(self):
        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = hydroshare.create_account(
            'test_user@email.com',
            username='mytestuser',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[self.hs_group]
        )

        # note: creating a resource calls the hs_bagit.create_bag() api
        self.test_res = hydroshare.create_resource(
            'GenericResource',
            self.user,
            'My Test Resource'
            )

    def test_create_bag(self):
        # the resource should have only one bags object
        self.assertEquals(self.test_res.bags.count(), 1)
        bag_first = self.test_res.bags.all().first()

        # this is the api call we are testing
        bag_second = hs_bagit.create_bag(self.test_res)

        # resource should have 2 bags objects
        self.assertEquals(self.test_res.bags.count(), 2)
        self.assertIn(bag_second, self.test_res.bags.all())
        self.assertIn(bag_first, self.test_res.bags.all())
        self.assertNotEquals(bag_first, bag_second)

    def test_create_bag_files(self):
        # this is the api call we are testing
        irods_storage_obj = hs_bagit.create_bag_files(self.test_res)
        self.assertTrue(isinstance(irods_storage_obj, IrodsStorage))

    def test_create_bag_by_irods(self):
        try:
            # this is the api call we testing
            hs_bagit.create_bag_by_irods(self.test_res.short_id)
        except Exception as ex:
            self.fail("create_bag_by_irods() raised exception.{}".format(ex.message))

    def test_delete_bag(self):
        # check we have one bag at this point
        self.assertEquals(self.test_res.bags.count(), 1)
        # this is the api we are testing
        hs_bagit.delete_bag(self.test_res)
        # resource should not have any bags
        self.assertEquals(self.test_res.bags.count(), 0)
