import os

from django.test import TestCase
from django.contrib.auth.models import Group

from hs_core import hydroshare


class TestHideOldVersions(TestCase):
    def setUp(self):
        super(TestHideOldVersions, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        # create a user who is the owner of the resource to be versioned
        self.owner = hydroshare.create_account(
            'owner@gmail.edu',
            username='owner',
            first_name='owner_firstname',
            last_name='owner_lastname',
            superuser=False,
            groups=[]
        )
        # create a composite resource
        self.version0 = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.owner,
            title='Test Composite Resource'
        )
        test_file1 = open('test1.txt', 'w')
        test_file1.write("Test text file in test1.txt")
        test_file1.close()
        test_file2 = open('test2.txt', 'w')
        test_file2.write("Test text file in test2.txt")
        test_file2.close()
        self.test_file1 = open('test1.txt', 'rb')
        self.test_file2 = open('test2.txt', 'rb')
        hydroshare.add_resource_files(self.version0.short_id, self.test_file1, self.test_file2)

        # make one version
        self.version1 = hydroshare.create_empty_resource(self.version0.short_id, self.owner)
        self.version1 = hydroshare.create_new_version_resource(self.version0, self.version1, self.owner)

        # and then make a version of that
        self.version2 = hydroshare.create_empty_resource(self.version1.short_id, self.owner)
        self.version2 = hydroshare.create_new_version_resource(self.version1, self.version2, self.owner)

    def tearDown(self):
        super(TestHideOldVersions, self).tearDown()
        self.test_file1.close()
        os.remove(self.test_file1.name)
        self.test_file2.close()
        os.remove(self.test_file2.name)

    def test_show_discoverable(self):
        self.version0.raccess.discoverable = True
        self.version0.raccess.save()
        self.assertTrue(self.version0.show_in_discover)
        self.assertFalse(self.version1.show_in_discover)
        self.assertFalse(self.version2.show_in_discover)

        self.version1.raccess.discoverable = True
        self.version1.raccess.save()
        self.assertFalse(self.version0.show_in_discover)
        self.assertTrue(self.version1.show_in_discover)
        self.assertFalse(self.version2.show_in_discover)

        self.version2.raccess.discoverable = True
        self.version2.raccess.save()
        self.assertFalse(self.version0.show_in_discover)
        self.assertFalse(self.version1.show_in_discover)
        self.assertTrue(self.version2.show_in_discover)

    def test_show_discoverable_2(self):
        self.version2.raccess.discoverable = True
        self.version2.raccess.save()
        self.assertFalse(self.version0.show_in_discover)
        self.assertFalse(self.version1.show_in_discover)
        self.assertTrue(self.version2.show_in_discover)

        # test chaining: if 1,2 are True, then show 2
        self.version1.raccess.discoverable = True
        self.version1.raccess.save()
        self.assertFalse(self.version0.show_in_discover)
        self.assertFalse(self.version1.show_in_discover)
        self.assertTrue(self.version2.show_in_discover)

        # if 0,1,2 are True, then show 2
        self.version0.raccess.discoverable = True
        self.version0.raccess.save()
        self.assertFalse(self.version0.show_in_discover)
        self.assertFalse(self.version1.show_in_discover)
        self.assertTrue(self.version2.show_in_discover)
