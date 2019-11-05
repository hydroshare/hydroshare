from django.contrib.auth.models import Group
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

    def test_create_bag_files(self):
        # this is the api call we are testing
        irods_storage_obj = hs_bagit.create_bag_files(self.test_res)
        self.assertTrue(isinstance(irods_storage_obj, IrodsStorage))

    def test_bag_creation_and_deletion(self):
        status = create_bag_by_irods(self.test_res.short_id)
        self.assertTrue(status)
        hs_bagit.delete_files_and_bag(self.test_res)
        # resource should not have any bags
        istorage = self.test_res.get_irods_storage()
        bag_path = self.test_res.bag_path
        self.assertFalse(istorage.exists(bag_path))
