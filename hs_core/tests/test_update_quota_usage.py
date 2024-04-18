import os
import shutil
from django.test import TestCase
from django.contrib.auth.models import User, Group
from theme.models import UserQuota
from hs_core.tasks import update_quota_usage
from hs_core import hydroshare
from hs_core.views.utils import create_folder, move_or_rename_file_or_folder, zip_folder, \
    unzip_file


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

        self.res = hydroshare.resource.create_resource(resource_type='CompositeResource',
                                                       owner=self.user,
                                                       title='Test Resource',
                                                       metadata=[], )

    def tearDown(self):
        super(UpdateQuotaUsageTestCase, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        self.res.delete()
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
        expected = 81
        # assert math.isclose(expected, self.res.size, rel_tol=1e-5)
        self.assertAlmostEqual(expected, self.res.size, places=5)

        # update_quota_usage(self.username)

        user_quota.refresh_from_db()
        self.assertNotEqual(user_quota.data_zone_value, 0)

        # Assert that the used values have been updated correctly
        self.assertEqual(user_quota.user_zone_value, 0)
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertAlmostEqual(dz, expected, places=5)

    def test_deleting_file_decrease_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)
        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(81, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        user_quota.refresh_from_db()
        # TODO: need to update_quota...? This should get updated automatically
        update_quota_usage(self.username)
        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)

        # Delete a file from the resource
        hydroshare.resource.delete_resource_file(self.res.short_id, self.n1, self.user)

        # Assert that the file has been deleted
        self.assertEqual(self.res.files.all().count(), 2)
        expected = 81 - 27
        # assert math.isclose(expected, self.res.size, rel_tol=1e-5)
        self.assertAlmostEqual(expected, self.res.size, places=5)

        # Assert that the quota has been updated correctly
        user_quota.refresh_from_db()
        expected = initial_quota_value - 27
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        # assert math.isclose(user_quota.data_zone_value, expected, rel_tol=1e-5)
        self.assertAlmostEqual(dz, expected, places=5)

    def test_zipping_files_increase_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(81, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)

        create_folder(self.res.short_id, 'data/contents/sub_test_dir')
        move_or_rename_file_or_folder(self.user, self.res.short_id,
                                      'data/contents/' + self.n1,
                                      'data/contents/sub_test_dir/' + self.n1)

        # Zip the files in the resource
        zip_folder(self.user, self.res.short_id, 'data/contents/sub_test_dir', 'sub_test_dir.zip', False)

        # Assert that the resource has added a single zip file
        self.assertEqual(self.res.files.all().count(), 4)

        # Assert that the quota has been updated correctly
        user_quota.refresh_from_db()
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        expected = initial_quota_value + 54
        self.assertAlmostEqual(dz, expected, places=5)

    def test_unzipping_files_increase_quota(self):
        # Add a zip file to the resource
        zip_file = open('test.zip', 'wb')
        shutil.make_archive('test', 'zip', '.', self.n1, self.n2, self.n3)
        zip_file.close()
        zip_file = open('test.zip', 'rb')

        hydroshare.resource.add_resource_files(self.res.short_id, zip_file)
        zip_file.close()
        os.remove('test.zip')

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)

        # Unzip the files in the resource
        unzip_file(self.user, self.res.short_id, 'data/contents/test.zip', bool_remove_original=False)

        # Assert that the resource has the original files
        # TODO: actually 1 ??
        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.res.files.first().file_folder, '')

        # Assert that the quota has been updated correctly
        user_quota.refresh_from_db()
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        expected = initial_quota_value + 54
        # assert math.isclose(user_quota.data_zone_value, expected, rel_tol=1e-5)
        self.assertAlmostEqual(dz, expected, places=5)

    def test_moving_files_doesnt_alter_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(81, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)

        # Move a file in the resource
        move_or_rename_file_or_folder(self.user, self.res.short_id,
                                      'data/contents/' + self.n1,
                                      'data/contents/' + self.n1)

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
        self.assertEqual(81, self.res.size)

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
        self.assertEqual(81, self.res.size)

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

    def test_deleting_folder_decrease_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(81, self.res.size)

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

        # Delete the folder in the resource
        move_or_rename_file_or_folder(self.user, self.res.short_id,
                                      'data/contents/test_folder',
                                      'data/contents/test_folder')

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
        self.assertEqual(81, self.res.size)

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
                                      'data/contents/test_folder')

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
        self.assertEqual(81, self.res.size)

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
        self.assertEqual(81, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)

        # change the quota holder
        self.res.set_quota_holder(self.user2)

        # Assert that the resource has the original files
        self.assertEqual(self.res.files.all().count(), 3)

        # Assert that the quota has been updated
        user_quota.refresh_from_db()
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, 0)

        # assert that the new quota holder has the correct quota
        user_quota2 = UserQuota.objects.get(user=self.user2, zone=self.hs_internal_zone)
        dz2 = self.convert_gb_to_bytes(user_quota2.data_zone_value)
        self.assertEqual(dz2, initial_quota_value)
