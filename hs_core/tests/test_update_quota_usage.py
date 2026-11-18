import os
import uuid
from unittest.mock import PropertyMock, patch
from django.contrib.contenttypes.models import ContentType
from django.db import connection, transaction
from django.core.files.base import ContentFile
from django.http.response import Http404
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.contrib.auth.models import User, Group
from theme.models import UserQuota
from hs_access_control.models import PrivilegeCodes
from hs_composite_resource.models import CompositeResource
from hs_core import hydroshare
from hs_core.models import BaseResource, ResourceFile, ResourceSizeCache
from hs_core.hydroshare.resource import get_data_zone_usage
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
            username=self.username + uuid.uuid4().hex,  # to ensure unique bucket in minio
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[self.group]
        )
        self.user2 = hydroshare.create_account(
            'test_user2@email.com',
            username='testuser2' + uuid.uuid4().hex,
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
        BaseResource.objects.all().delete()
        Group.objects.all().delete()
        self.myfile1.close()
        os.remove(self.myfile1.name)
        self.myfile2.close()
        os.remove(self.myfile2.name)
        self.myfile3.close()
        os.remove(self.myfile3.name)
        User.objects.all().delete()

    def convert_gb_to_bytes(self, gb):
        return gb * 1024 * 1024 * 1024

    @patch.object(ResourceFile, 'calculate_size')
    def test_resource_size_cache_mutations(self, mock_calculate_size):
        first = ResourceFile.objects.create(content_object=self.res, resource_file='cache-test-first', _size=10)
        self.assertEqual(self.res.size, 10)
        self.assertEqual(get_data_zone_usage(self.user.username), 10)

        first._size = 15
        first.save(update_fields=['_size'])
        self.assertFalse(ResourceSizeCache.objects.filter(resource=self.res).exists())
        self.assertEqual(self.res.size, 15)

        second, third = ResourceFile.objects.bulk_create([
            ResourceFile(content_object=self.res, resource_file='cache-test-second', _size=20),
            ResourceFile(content_object=self.res, resource_file='cache-test-third', _size=-1),
        ])
        self.assertEqual(get_data_zone_usage(self.user.username), 35)
        self.assertTrue(ResourceSizeCache.objects.get(resource=self.res).has_unknown)

        def resolve_size(resource_file, resource=None, save=True):
            resource_file._size = 7
            if save:
                resource_file.save(update_fields=['_size'])

        with patch.object(ResourceFile, 'calculate_size', resolve_size):
            self.assertEqual(self.res.size, 42)
        self.assertFalse(ResourceSizeCache.objects.get(resource=self.res).has_unknown)

        second._size = 30
        third._size = 8
        ResourceFile.objects.bulk_update([second, third], ['_size'])
        self.assertEqual(get_data_zone_usage(self.user.username), 53)
        ResourceFile.objects.filter(pk=first.pk).update(_size=-1)
        self.assertEqual(get_data_zone_usage(self.user.username), 38)
        ResourceFile.objects.filter(pk__in=[first.pk, second.pk]).delete()
        self.assertEqual(self.res.size, 8)
        ResourceFile.objects.filter(pk=third.pk).delete()
        self.assertEqual(get_data_zone_usage(self.user.username), 0)

    @patch.object(ResourceFile, 'calculate_size')
    def test_resource_size_cache_respects_content_types_and_transactions(self, mock_calculate_size):
        resource_file = ResourceFile.objects.create(
            content_object=self.res, resource_file='cache-test-resource', _size=10,
        )
        other_file = ResourceFile.objects.create(
            content_type=ContentType.objects.get_for_model(User),
            object_id=self.res.pk, resource_file='cache-test-other', _size=4,
        )
        self.assertEqual(self.res.size, 10)
        self.assertEqual(get_data_zone_usage(self.user.username), 10)
        with self.assertNumQueries(3):
            self.assertEqual(get_data_zone_usage(self.user.username), 10)

        with transaction.atomic():
            ResourceFile.objects.filter(pk=resource_file.pk).update(_size=30)
            self.assertEqual(get_data_zone_usage(self.user.username), 30)
            transaction.set_rollback(True)
        self.assertEqual(get_data_zone_usage(self.user.username), 10)
        with override_settings(RESOURCE_SIZE_CACHE_ENABLED=False):
            self.assertEqual(get_data_zone_usage(self.user.username), 10)

        ResourceSizeCache.objects.filter(resource=self.res).delete()
        original_get_size_cache = BaseResource.get_size_cache

        def invalidate_after_refresh(resource):
            cache = original_get_size_cache(resource)
            ResourceSizeCache.objects.filter(resource_id=resource.pk).delete()
            return cache

        with patch.object(BaseResource, 'get_size_cache', invalidate_after_refresh):
            self.assertEqual(get_data_zone_usage(self.user.username), 10)
        ResourceFile.objects.filter(pk__in=[resource_file.pk, other_file.pk]).delete()

    @patch.object(ResourceFile, 'calculate_size')
    def test_warm_quota_cache_does_not_scan_resource_files(self, mock_calculate_size):
        resource_file = ResourceFile.objects.create(
            content_object=self.res, resource_file='cache-test-plan', _size=10,
        )
        self.assertEqual(get_data_zone_usage(self.user.username), 10)
        with CaptureQueriesContext(connection) as queries:
            self.assertEqual(get_data_zone_usage(self.user.username), 10)
        with connection.cursor() as cursor:
            cursor.execute('EXPLAIN (ANALYZE, FORMAT JSON) ' + queries.captured_queries[-1]['sql'])
            plan = cursor.fetchone()[0][0]['Plan']

        def subplans(node):
            found = [node] if node.get('Parent Relationship') == 'SubPlan' else []
            for child in node.get('Plans', []):
                found.extend(subplans(child))
            return found

        plans = subplans(plan)
        self.assertTrue(plans)
        self.assertTrue(all(node['Actual Loops'] == 0 for node in plans))
        ResourceFile.objects.filter(pk=resource_file.pk).delete()

    @patch.object(ResourceFile, 'calculate_size')
    def test_resource_size_cache_respects_quota_holder_and_published_status(self, mock_calculate_size):
        resource_file = ResourceFile.objects.create(
            content_object=self.res, resource_file='cache-test-quota-holder', _size=12,
        )
        self.assertEqual(get_data_zone_usage(self.user.username), 12)
        BaseResource.objects.filter(pk=self.res.pk).update(quota_holder=self.user2)
        self.assertEqual(get_data_zone_usage(self.user.username), 0)
        self.assertEqual(get_data_zone_usage(self.user2.username), 12)
        type(self.res.raccess).objects.filter(pk=self.res.raccess.pk).update(published=True)
        self.assertEqual(get_data_zone_usage(self.user2.username), 0)
        self.assertEqual(get_data_zone_usage(self.user2.username, include_published=True), 12)
        ResourceFile.objects.filter(pk=resource_file.pk).delete()

    @patch.object(ResourceFile, 'calculate_size')
    def test_resource_size_cache_reassign_and_instance_delete(self, mock_calculate_size):
        other = hydroshare.create_resource('CompositeResource', self.user2, 'Other resource')
        resource_file = ResourceFile.objects.create(
            content_object=self.res, resource_file='cache-test-reassign', _size=12,
        )
        self.assertEqual(self.res.size, 12)
        self.assertEqual(other.size, 0)
        resource_file.object_id = other.pk
        ResourceFile.objects.bulk_update([resource_file], ['object_id'])
        self.assertEqual(self.res.size, 0)
        self.assertEqual(other.size, 12)
        self.assertEqual(get_data_zone_usage(self.user.username), 0)
        self.assertEqual(get_data_zone_usage(self.user2.username), 12)
        with patch.object(ResourceFile, 'exists', new_callable=PropertyMock, return_value=False):
            resource_file.delete()
        self.assertEqual(other.size, 0)

    @override_settings(RESOURCE_SIZE_CACHE_ENABLED=False)
    @patch.object(ResourceFile, 'calculate_size')
    def test_resource_size_cache_disabled(self, mock_calculate_size):
        resource_file = ResourceFile.objects.create(
            content_object=self.res, resource_file='cache-test-disabled', _size=-1,
        )
        self.assertEqual(get_data_zone_usage(self.user.username), 0)

        def resolve_size(resource_file, resource=None, save=True):
            resource_file._size = 9
            resource_file.save(update_fields=['_size'])

        with patch.object(ResourceFile, 'calculate_size', resolve_size):
            self.assertEqual(self.res.size, 9)
        self.assertEqual(get_data_zone_usage(self.user.username), 9)
        self.assertFalse(ResourceSizeCache.objects.filter(resource=self.res).exists())
        ResourceFile.objects.filter(pk=resource_file.pk).delete()

    def test_upload_calculates_size_before_metadata_task(self):
        from hs_core.tasks import set_resource_files_system_metadata
        with patch('hs_core.tasks.set_resource_files_system_metadata.apply_async'):
            resource_file = hydroshare.resource.add_resource_files(
                self.res.short_id, self.myfile1, auto_aggregate=False,
            )[0]
        resource_file.refresh_from_db()
        self.assertEqual(resource_file._size, self.single_file_size)
        self.assertIsNotNone(resource_file.filesize_cache_updated)
        self.assertEqual(get_data_zone_usage(self.user.username), self.single_file_size)
        with patch.object(ResourceFile, 'calculate_size') as calculate:
            resource_file.save(update_fields=['file_folder'])
            resource_file.save()
            calculate.assert_not_called()
        set_resource_files_system_metadata.run(self.res.short_id)
        resource_file.refresh_from_db()
        self.assertIsNotNone(resource_file._modified_time)
        self.assertTrue(resource_file._checksum)

    def test_bulk_create_calculates_sizes(self):
        resource_files = [
            ResourceFile(content_object=self.res, resource_file='cache-bulk-first'),
            ResourceFile(content_object=self.res, resource_file='cache-bulk-second'),
        ]
        with patch.object(resource_files[0].resource_file.storage, 'size', side_effect=[11, 23]) as size:
            ResourceFile.objects.bulk_create(resource_files)
        self.assertEqual(size.call_count, 2)
        self.assertEqual(list(self.res.files.order_by('pk').values_list('_size', flat=True)), [11, 23])
        self.assertEqual(get_data_zone_usage(self.user.username), 34)
        self.res.files.all().delete()

    def test_bulk_create_uploads_before_calculating_sizes(self):
        resource_files = [
            ResourceFile(content_object=self.res, resource_file=ContentFile(b'first', name='bulk-first.txt')),
            ResourceFile(content_object=self.res, resource_file=ContentFile(b'second', name='bulk-second.txt')),
        ]
        ResourceFile.objects.bulk_create(resource_files)
        self.assertEqual(list(self.res.files.order_by('pk').values_list('_size', flat=True)), [5, 6])
        self.assertEqual(get_data_zone_usage(self.user.username), 11)

    def test_save_with_file_update_fields_recalculates_size(self):
        with patch('hs_core.tasks.set_resource_files_system_metadata.apply_async'):
            resource_file = hydroshare.resource.add_resource_files(
                self.res.short_id, self.myfile1, auto_aggregate=False,
            )[0]
        self.assertEqual(get_data_zone_usage(self.user.username), self.single_file_size)
        resource_file.resource_file = ContentFile(b'replacement', name='replacement.txt')
        resource_file.save(update_fields=['resource_file'])
        resource_file.refresh_from_db()
        self.assertEqual(resource_file._size, 11)
        self.assertEqual(get_data_zone_usage(self.user.username), 11)

    def test_linking_existing_s3_file_refreshes_size(self):
        from hs_core.views.utils import link_s3_file_to_django
        with patch('hs_core.tasks.set_resource_files_system_metadata.apply_async'):
            resource_file = hydroshare.resource.add_resource_files(
                self.res.short_id, self.myfile1, auto_aggregate=False,
            )[0]
        self.assertEqual(get_data_zone_usage(self.user.username), self.single_file_size)
        with patch.object(resource_file.resource_file.storage, 'size', return_value=42):
            linked = link_s3_file_to_django(self.res, resource_file.storage_path)
        linked.refresh_from_db()
        self.assertEqual(linked._size, 42)
        self.assertEqual(get_data_zone_usage(self.user.username), 42)

    def test_adding_file_increase_quota(self):
        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        # initial quota includes metadata files
        initial_quota_value = user_quota.data_zone_value
        self.assertEqual(0, self.res.size)

        # add files
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        # resource should have 3 files
        self.assertEqual(self.res.files.all().count(), 3)
        expected = self.single_file_size * 3
        # assert math.isclose(expected, self.res.size, rel_tol=1e-5)
        self.assertEqual(expected, self.res.size)

        self.assertNotEqual(user_quota.data_zone_value, initial_quota_value)

        # Assert that the used values have been updated correctly
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, expected)

    def test_deleting_file_decrease_quota(self):
        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)

        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)
        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)

        # Delete a file from the resource
        hydroshare.resource.delete_resource_file(self.res.short_id, self.n1, self.user)
        # Assert that the file has been deleted
        self.assertEqual(self.res.files.all().count(), 2)
        expected = 2 * self.single_file_size
        # assert math.isclose(expected, self.res.size, rel_tol=1e-5)
        self.assertAlmostEqual(expected, self.res.size, places=5)

        # Assert that the quota has been updated correctly
        expected = initial_quota_value - self.single_file_size + 130  # add 130 bytes for metadata file updates
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        # assert math.isclose(user_quota.data_zone_value, expected, rel_tol=1e-5)
        self.assertLess(dz, expected)

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
        size_of_zip = 213
        expected = self.single_file_size * 3 + size_of_zip
        self.assertEqual(dz, expected)

    def test_unzipping_files_increase_quota(self):
        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)

        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3,
                                               folder='test')
        zip_folder(self.user, self.res.short_id, 'data/contents/test', 'test.zip', bool_remove_original=False)

        # now delete the folder
        folder_path = "data/contents/test"
        remove_folder(self.user, self.res.short_id, folder_path)

        data_zone_value = user_quota.data_zone_value
        initial_quota_value = self.convert_gb_to_bytes(data_zone_value)

        # Unzip the files in the resource
        unzip_file(self.user, self.res.short_id, 'data/contents/test.zip', bool_remove_original=False)

        # Assert that the resource has the original files + 1
        self.assertEqual(self.res.files.all().count(), 4)

        # Assert that the quota has been updated correctly
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        expected = initial_quota_value + 3 * self.single_file_size
        # assert math.isclose(user_quota.data_zone_value, expected, rel_tol=1e-5)
        self.assertEqual(dz, expected)

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
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertAlmostEqual(dz, initial_quota_value, delta=1024)

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
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, initial_quota_value)

        # now delete the folder
        folder_path = "data/contents/test_folder"
        remove_folder(self.user, self.res.short_id, folder_path)

        # Assert that the resource has the original files
        self.assertEqual(self.res.files.all().count(), 3)

        # Assert that the quota has not been updated
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
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, initial_quota_value)

        # Move the folder in the resource
        move_or_rename_file_or_folder(self.user, self.res.short_id,
                                      'data/contents/test_folder',
                                      'data/contents/test_folder_new')

        # Assert that the resource has the original files
        self.assertEqual(self.res.files.all().count(), 3)

        # Assert that the quota has not been updated
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
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, initial_quota_value)

        # Rename the folder in the resource
        move_or_rename_file_or_folder(self.user, self.res.short_id,
                                      'data/contents/test_folder',
                                      'data/contents/renamed_test_folder')

        # Assert that the resource has the original files
        self.assertEqual(self.res.files.all().count(), 3)

        # Assert that the quota has not been updated
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, initial_quota_value)

    def test_change_quota_holder_alters_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        data_zone_value = user_quota.data_zone_value
        initial_quota_value = self.convert_gb_to_bytes(data_zone_value)
        self.assertEqual(initial_quota_value, 3 * self.single_file_size)

        # change the quota holder
        # first add user2 as owner
        self.user.uaccess.share_resource_with_user(self.res, self.user2, PrivilegeCodes.OWNER)
        self.res.set_quota_holder(self.user, self.user2)

        # Assert that the quota holder has been updated
        self.res.refresh_from_db()
        self.assertEqual(self.res.raccess.owners.all().count(), 2)
        self.assertEqual(self.res.quota_holder, self.user2)

        # Assert that the quota has been updated
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, 0)

        # assert that the new quota holder has the correct quota
        user_quota2 = UserQuota.objects.get(user=self.user2, zone=self.hs_internal_zone)
        dz2 = self.convert_gb_to_bytes(user_quota2.data_zone_value)
        self.assertEqual(dz2, initial_quota_value)

    def test_delete_resource_reduces_quota(self):
        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        data_zone_value = user_quota.data_zone_value
        initial_quota_value = self.convert_gb_to_bytes(data_zone_value)

        # assert that the initial quota value is correct
        self.assertEqual(initial_quota_value, self.single_file_size * 3)

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
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, 0)

    def test_copying_resource_doubles_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        data_zone_value = user_quota.data_zone_value
        initial_quota_value = self.convert_gb_to_bytes(data_zone_value)
        self.assertEqual(initial_quota_value, 3 * self.single_file_size)

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
        self.assertEqual(
            list(new_res.files.values_list('_size', flat=True)),
            [self.single_file_size] * 3,
        )
        self.assertEqual(get_data_zone_usage(self.user.username), initial_quota_value * 2)

        # Assert that the copied resource has the same size as the original resource
        self.assertEqual(new_res.size, self.res.size)

        # Assert that the user is the quota holder for both resources
        self.assertEqual(new_res.quota_holder, self.user)
        self.assertEqual(self.res.quota_holder, self.user)

        # Assert that the quota has been updated
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, initial_quota_value * 2)

    def test_version_resource_doubles_quota(self):
        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)

        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        # Retrieve the UserQuota object for the user
        data_zone_value = user_quota.data_zone_value
        initial_quota_value = self.convert_gb_to_bytes(data_zone_value)
        self.assertEqual(initial_quota_value, 3 * self.single_file_size)

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
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, initial_quota_value * 2)

    def test_publish_resource_decreases_quota(self):
        hydroshare.create_account(
            'publisher@email.com',
            username='published',
            first_name='some_first_name2',
            last_name='some_last_name2',
            superuser=False,
        )
        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)

        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        # Retrieve the UserQuota object for the user
        data_zone_value = user_quota.data_zone_value
        initial_quota_value = self.convert_gb_to_bytes(data_zone_value)
        self.assertEqual(initial_quota_value, 3 * self.single_file_size)

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
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, 0)

    def test_adding_zipped_bag_not_increase_quota(self):
        # Add files to the resource
        hydroshare.resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(self.single_file_size * 3, self.res.size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)
        initial_quota_value = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(initial_quota_value, 3 * self.single_file_size)

        # create the zipped bag
        status = create_bag_by_s3(self.res.short_id)
        self.assertTrue(status)

        # Assert that the resource has the original files
        self.assertEqual(self.res.files.all().count(), 3)

        # Assert that the quota has not been updated
        dz = self.convert_gb_to_bytes(user_quota.data_zone_value)
        self.assertEqual(dz, initial_quota_value)
