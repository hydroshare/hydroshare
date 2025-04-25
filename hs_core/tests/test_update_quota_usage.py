import os
from django.http.response import Http404
from django.test import TestCase
from django.contrib.auth.models import User, Group
from theme.models import UserQuota
from hs_access_control.models import PrivilegeCodes
from hs_composite_resource.models import CompositeResource
from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.views.utils import create_folder, move_or_rename_file_or_folder, zip_folder, \
    unzip_file, remove_folder, get_default_admin_user
from hs_core.tasks import create_bag_by_s3


class UpdateQuotaUsageTestCase(TestCase):
    def setUp(self):
        self.username = 'testuser'
        self.hs_internal_zone = 'hydroshare'
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'test_user@email.com',
            username=self.username,
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[self.group]
        )
        self.user2 = hydroshare.create_account(
            'test_user2@email.com',
            username='testuser2',
            first_name='some_first_name2',
            last_name='some_last_name2',
            superuser=False,
            groups=[self.group]
        )
        self.unit = 'GB'
        self.single_file_size = 27  # in bytes

        # create files
        self.n1 = "test1.txt"
        self.n2 = "test2.txt"
        self.n3 = "test3.txt"

        test_file = open(self.n1, 'w')
        test_file.write("Test text file in test1.txt")
        test_file.close()

        test_file = open(self.n2, 'w')
        test_file.write("Test text file in test2.txt")
        test_file.close()

        test_file = open(self.n3, 'w')
        test_file.write("Test text file in test3.txt")
        test_file.close()

        # open files for read and upload
        self.myfile1 = open(self.n1, "rb")
        self.myfile2 = open(self.n2, "rb")
        self.myfile3 = open(self.n3, "rb")

        self.res = hydroshare.create_resource(resource_type='CompositeResource',
                                              owner=self.user,
                                              title='My Test Resource ' * 10,
                                              edit_users=[self.user2],
                                              keywords=('a', 'b', 'c'))

        self.res.metadata.create_element("description", abstract="new abstract for the resource " * 10)

    def tearDown(self):
        super(UpdateQuotaUsageTestCase, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        BaseResource.objects.all().delete()
        Group.objects.all().delete()
        self.myfile1.close()
        os.remove(self.myfile1.name)
        self.myfile2.close()
        os.remove(self.myfile2.name)
        self.myfile3.close()
        os.remove(self.myfile3.name)

    def convert_gb_to_bytes(self, gb):
        return gb * 1024 * 1024 * 1024

    def test_adding_file_increase_quota(self):
        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        self.assertEqual(user_quota.data_zone_value, 0)
        self.assertEqual(0, self.res.size)

        # add files
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        # resource should have 3 files
        self.assertEqual(self.res.files.all().count(), 3)
        expected = self.single_file_size * 3
        # assert math.isclose(expected, self.res.size, rel_tol=1e-5)
        self.assertAlmostEqual(expected, self.res.size, places=5)

        user_quota.refresh_from_db()
        self.assertNotEqual(user_quota.data_zone_value, 0)

        # Assert that the used values have been updated correctly
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertAlmostEqual(dz, expected, places=5)

    def test_deleting_file_decrease_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)
        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        user_quota.refresh_from_db()
        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)

        # Delete a file from the resource
        hydroshare.resource.delete_resource_file(self.res.short_id, self.n1, self.user)

        # Assert that the file has been deleted
        self.assertEqual(self.res.files.all().count(), 2)
        expected = 2 * self.single_file_size
        # assert math.isclose(expected, self.res.size, rel_tol=1e-5)
        self.assertAlmostEqual(expected, self.res.size, places=5)

        # Assert that the quota has been updated correctly
        user_quota.refresh_from_db()
        expected = initial_quota_value - self.single_file_size
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        # assert math.isclose(user_quota.data_zone_value, expected, rel_tol=1e-5)
        self.assertAlmostEqual(dz, expected, places=5)

    def test_zipping_files_increase_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)

        create_folder(self.res.short_id, 'data/contents/sub_test_dir')
        move_or_rename_file_or_folder(self.user, self.res.short_id,
                                      'data/contents/' + self.n1,
                                      'data/contents/sub_test_dir/' + self.n1)

        # Zip the files in the resource
        zip_folder(self.user, self.res.short_id, 'data/contents/sub_test_dir', 'sub_test_dir.zip', False)

        # Assert that the resource has added a single zip file
        self.assertEqual(self.res.files.all().count(), 4)

        # Assert that the resource size has increased
        self.assertGreater(self.res.size, self.single_file_size * 3)

        # Assert that the quota has been updated correctly
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        size_of_zip = 215
        expected = self.single_file_size * 3 + size_of_zip
        self.assertAlmostEqual(dz, expected, places=5)

    def test_unzipping_files_increase_quota(self):
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3,
                                               folder='test')
        zip_folder(self.user, self.res.short_id, 'data/contents/test', 'test.zip', bool_remove_original=False)

        # now delete the folder
        folder_path = "data/contents/test"
        remove_folder(self.user, self.res.short_id, folder_path)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)

        # Unzip the files in the resource
        unzip_file(self.user, self.res.short_id, 'data/contents/test.zip', bool_remove_original=False)

        # Assert that the resource has the original files + 1
        self.assertEqual(self.res.files.all().count(), 4)

        # Assert that the quota has been updated correctly
        user_quota.refresh_from_db()
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        expected = initial_quota_value + 3 * self.single_file_size
        # assert math.isclose(user_quota.data_zone_value, expected, rel_tol=1e-5)
        self.assertAlmostEqual(dz, expected, places=5)

    def test_moving_files_doesnt_alter_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)

        # Move a file in the resource
        rename = self.n1 + '_moved'
        move_or_rename_file_or_folder(self.user, self.res.short_id,
                                      'data/contents/' + self.n1,
                                      'data/contents/' + rename)

        # Assert that the resource has the original files
        self.assertEqual(self.res.files.all().count(), 3)

        # Assert that the quota has not been updated
        user_quota.refresh_from_db()
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, initial_quota_value)

    def test_renaming_files_doesnt_alter_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)

        # Rename a file in the resource
        move_or_rename_file_or_folder(self.user, self.res.short_id,
                                      'data/contents/' + self.n1,
                                      'data/contents/' + 'renamed_' + self.n1)

        # Assert that the resource has the original files
        self.assertEqual(self.res.files.all().count(), 3)

        # Assert that the quota has not been updated
        user_quota.refresh_from_db()
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, initial_quota_value)

    def test_creating_folder_doesnt_alter_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)

        # Create a folder in the resource
        create_folder(self.res.short_id, 'data/contents/test_folder')

        # Assert that the resource has the original files
        self.assertEqual(self.res.files.all().count(), 3)

        # Assert that the quota has not been updated
        user_quota.refresh_from_db()
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, initial_quota_value)

    def test_deleting_folder_not_decrease_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)

        # Create a folder in the resource
        create_folder(self.res.short_id, 'data/contents/test_folder')

        # Assert that the resource has the original files
        self.assertEqual(self.res.files.all().count(), 3)

        # Assert that the quota has not been updated
        user_quota.refresh_from_db()
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, initial_quota_value)

        # now delete the folder
        folder_path = "data/contents/test_folder"
        remove_folder(self.user, self.res.short_id, folder_path)

        # Assert that the resource has the original files
        self.assertEqual(self.res.files.all().count(), 3)

        # Assert that the quota has not been updated
        user_quota.refresh_from_db()
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, initial_quota_value)

    def test_moving_folder_doesnt_alter_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)

        # Create a folder in the resource
        create_folder(self.res.short_id, 'data/contents/test_folder')

        # Assert that the resource has the original files
        self.assertEqual(self.res.files.all().count(), 3)

        # Assert that the quota has not been updated
        user_quota.refresh_from_db()
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, initial_quota_value)

        # Move the folder in the resource
        move_or_rename_file_or_folder(self.user, self.res.short_id,
                                      'data/contents/test_folder',
                                      'data/contents/test_folder_new')

        # Assert that the resource has the original files
        self.assertEqual(self.res.files.all().count(), 3)

        # Assert that the quota has not been updated
        user_quota.refresh_from_db()
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, initial_quota_value)

    def test_renaming_folder_doesnt_alter_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)

        # Create a folder in the resource
        create_folder(self.res.short_id, 'data/contents/test_folder')

        # Assert that the resource has the original files
        self.assertEqual(self.res.files.all().count(), 3)

        # Assert that the quota has not been updated
        user_quota.refresh_from_db()
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, initial_quota_value)

        # Rename the folder in the resource
        move_or_rename_file_or_folder(self.user, self.res.short_id,
                                      'data/contents/test_folder',
                                      'data/contents/renamed_test_folder')

        # Assert that the resource has the original files
        self.assertEqual(self.res.files.all().count(), 3)

        # Assert that the quota has not been updated
        user_quota.refresh_from_db()
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, initial_quota_value)

    def test_change_quota_holder_alters_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertAlmostEqual(initial_quota_value, 3 * self.single_file_size, places=5)

        # change the quota holder
        # first add user2 as owner
        self.user.uaccess.share_resource_with_user(self.res, self.user2, PrivilegeCodes.OWNER)
        self.res.set_quota_holder(self.user, self.user2)

        # Assert that the quota holder has been updated
        self.res.refresh_from_db()
        self.assertEqual(self.res.raccess.owners.all().count(), 2)
        self.assertEqual(self.res.quota_holder, self.user2)

        # Assert that the quota has been updated
        user_quota.refresh_from_db()
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertAlmostEqual(dz, 0, places=5)

        # assert that the new quota holder has the correct quota
        user_quota2 = UserQuota.objects.get(user=self.user2, zone=self.hs_internal_zone)
        dz2 = self.convert_gb_to_bytes(user_quota2.data_zone_value)
        self.assertAlmostEqual(dz2, initial_quota_value, places=5)

    def test_delete_resource_reduces_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)

        # assert that the initial quota value is correct
        self.assertAlmostEqual(initial_quota_value, self.single_file_size * 3, places=5)

        # Delete the resource
        self.assertTrue(BaseResource.objects.filter(short_id=self.res.short_id).exists())
        hydroshare.delete_resource(self.res.short_id)
        self.assertEqual(BaseResource.objects.count(), 0)

        # Assert that the resource has been deleted
        with self.assertRaises(Http404):
            hydroshare.get_resource_by_shortkey(self.res.short_id)

        # assert that the user no longer owns any resources
        self.assertEqual(self.user.uaccess.owned_resources.count(), 0)

        # Assert that the user is not the quota holder for any resources
        self.assertEqual(BaseResource.objects.filter(quota_holder=self.user).count(), 0)

        # Assert that the quota has been updated
        user_quota.refresh_from_db()
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertAlmostEqual(dz, 0, places=5)

    def test_copying_resource_doubles_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertAlmostEqual(initial_quota_value, 3 * self.single_file_size, places=5)

        new_res = hydroshare.create_empty_resource(self.res.short_id,
                                                   self.user,
                                                   action='copy')
        # test to make sure the new copied empty resource has no content files
        self.assertEqual(new_res.files.all().count(), 0)
        # Copy the resource
        new_res = hydroshare.copy_resource(self.res, new_res)

        # test the new copied resource has the same resource type as the original resource
        self.assertTrue(isinstance(new_res, CompositeResource))

        # Assert that the copied resource has files
        self.assertEqual(new_res.files.all().count(), 3)

        # Assert that the copied resource has the same size as the original resource
        self.assertEqual(new_res.size, self.res.size)

        # Assert that the user is the quota holder for both resources
        self.assertEqual(new_res.quota_holder, self.user)
        self.assertEqual(self.res.quota_holder, self.user)

        # Assert that the quota has been updated
        user_quota.refresh_from_db()
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertAlmostEqual(dz, initial_quota_value * 2, places=5)

    def test_version_resource_doubles_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertAlmostEqual(initial_quota_value, 3 * self.single_file_size, places=5)

        # Version the resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.res.short_id, self.user
        )
        # test to make sure the new copied empty resource has no content files
        self.assertEqual(new_composite_resource.files.all().count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 2)
        new_composite_resource = hydroshare.create_new_version_resource(
            self.res, new_composite_resource, self.user
        )
        self.assertEqual(
            self.res.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.res.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 3)
        self.assertEqual(self.single_file_size * 3, new_composite_resource.size)

        # test the new copied resource has the same resource type as the original resource
        self.assertTrue(isinstance(new_composite_resource, CompositeResource))

        # Assert that the user is the quota holder for both resources
        self.assertEqual(new_composite_resource.quota_holder, self.user)
        self.assertEqual(self.res.quota_holder, self.user)

        # Assert that the quota has been updated
        user_quota.refresh_from_db()
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertAlmostEqual(dz, initial_quota_value * 2, places=5)

    def test_publish_resource_decreases_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertAlmostEqual(initial_quota_value, 3 * self.single_file_size, places=5)

        # there should not be published date type metadata element
        self.assertFalse(self.res.metadata.dates.filter(type='published').exists())

        admin_user = get_default_admin_user()
        hydroshare.submit_resource_for_review(pk=self.res.short_id, user=self.user)

        # publish resource
        hydroshare.publish_resource(user=admin_user, pk=self.res.short_id)
        self.pub_res = hydroshare.get_resource_by_shortkey(self.res.short_id)

        # test publish state
        self.assertTrue(
            self.pub_res.raccess.published,
            msg='The resource is not published'
        )

        # Assert that the quota has been updated
        user_quota.refresh_from_db()
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertAlmostEqual(dz, 0, places=5)

    def test_adding_zipped_bag_not_increase_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertAlmostEqual(initial_quota_value, 3 * self.single_file_size, places=5)

        # create the zipped bag
        status = create_bag_by_s3(self.res.short_id)
        self.assertTrue(status)

        # Assert that the resource has the original files
        self.assertEqual(self.res.files.all().count(), 3)

        # Assert that the quota has not been updated
        user_quota.refresh_from_db()
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertAlmostEqual(dz, initial_quota_value, places=5)
