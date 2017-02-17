from django.contrib.auth.models import Group, User
from django.test import TestCase

from hs_core import hydroshare
from hs_core.hydroshare import hs_bagit
from hs_core.tasks import create_bag_by_irods
from hs_core.models import GenericResource
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

    def tearDown(self):
        super(TestBagIt, self).tearDown()
        if self.test_res:
            self.test_res.delete()
        GenericResource.objects.all().delete()

    def test_create_bag(self):
        # the resource should have only one bags object
        self.assertEquals(self.test_res.bags.count(), 1)
        old_bag = self.test_res.bags.all().first()

        # this is the api call we are testing
        new_bag = hs_bagit.create_bag(self.test_res)

        # resource should have one new bags object
        self.assertEquals(self.test_res.bags.count(), 1)
        self.assertEquals(new_bag, self.test_res.bags.all().first())
        self.assertNotEquals(old_bag, new_bag)

    def test_create_bag_files(self):
        # this is the api call we are testing
        irods_storage_obj = hs_bagit.create_bag_files(self.test_res)
        print(type(irods_storage_obj))
        self.assertTrue(isinstance(irods_storage_obj, IrodsStorage))

    def test_create_bag_by_irods(self):
        try:
            # this is the api call we testing
            create_bag_by_irods(self.test_res.short_id)
        except Exception as ex:
            self.fail("create_bag_by_irods() raised exception.{}".format(ex.message))

    def test_delete_bag(self):
        # check we have one bag at this point
        self.assertEquals(self.test_res.bags.count(), 1)
        # this is the api we are testing
        hs_bagit.delete_bag(self.test_res)
        # resource should not have any bags
        self.assertEquals(self.test_res.bags.count(), 0)
