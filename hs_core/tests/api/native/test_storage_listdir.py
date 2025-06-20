import os
import shutil
import tempfile

from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.test import TestCase

from django_s3.exceptions import SessionException
from django_s3.utils import (
    is_metadata_json_file,
    is_metadata_xml_file,
    is_schema_json_file,
    is_schema_json_values_file,
)

from hs_core import hydroshare
from hs_core.hydroshare.utils import add_file_to_resource
from hs_core.models import BaseResource
from hs_core.testing import MockS3TestCaseMixin
from hs_core.views.utils import create_folder


class TestS3StorageListDir(MockS3TestCaseMixin, TestCase):
    """Test cases for S3Storage.listdir() method and related utility functions."""

    def setUp(self):
        super(TestS3StorageListDir, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        self.res = hydroshare.create_resource(
            'CompositeResource',
            self.user,
            'test resource for listdir',
        )

        # Create test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = {
            'regular1.txt': 'Test content 1',
            'regular2.txt': 'Test content 2',
            'test_meta.xml': '<metadata>test</metadata>',
            'test_resmap.xml': '<resmap>test</resmap>',
            'hs_user_metadata.json': '{"test": "metadata"}',
            'model.hs_user_metadata.json': '{"test": "metadata_endswith"}',
            'model_schema.json': '{"schema": "test"}',
            'model_schema_values.json': '{"values": "test"}'
        }

        # Create actual test files
        for filename, content in self.test_files.items():
            filepath = os.path.join(self.temp_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)

    def tearDown(self):
        super(TestS3StorageListDir, self).tearDown()
        # Clean up test files
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

        # Clean up database
        self.res.delete()
        BaseResource.objects.all().delete()

    def test_listdir_with_resource_files(self):
        """Test listdir function with files uploaded to a resource."""

        # Add test files to the resource
        for filename in ['regular1.txt', 'regular2.txt']:
            filepath = os.path.join(self.temp_dir, filename)
            file_to_upload = UploadedFile(file=open(filepath, 'rb'),
                                          name=os.path.basename(filepath))
            add_file_to_resource(self.res, file_to_upload)

        # Get storage instance
        storage = self.res.get_s3_storage()
        resource_path = self.res.file_path

        # Test basic listdir functionality
        directories, files, file_sizes = storage.listdir(resource_path)

        # Verify files are listed
        self.assertIn('regular1.txt', files)
        self.assertIn('regular2.txt', files)
        self.assertEqual(len(files), 2)
        self.assertEqual(len(file_sizes), 2)

        # Verify no directories at root level initially
        self.assertEqual(len(directories), 0)

        # Verify file sizes are reasonable
        for size in file_sizes:
            self.assertGreater(size, 0)

    def test_listdir_with_folders(self):
        """Test listdir function with folders."""

        # Create a folder in the resource
        create_folder(self.res.short_id, 'data/contents/test_folder')

        # Add a file to the folder
        filepath = os.path.join(self.temp_dir, 'regular1.txt')
        file_to_upload = UploadedFile(file=open(filepath, 'rb'),
                                      name=os.path.basename(filepath))
        add_file_to_resource(self.res, file_to_upload, folder='test_folder')

        # Get storage instance
        storage = self.res.get_s3_storage()
        resource_path = self.res.file_path

        # Test listdir on root
        directories, files, file_sizes = storage.listdir(resource_path)

        # Verify folder is listed
        self.assertIn('test_folder', directories)
        # There should be no files at root level
        self.assertEqual(len(files), 0)
        self.assertEqual(len(file_sizes), 0)

        # Test listdir on the folder
        folder_path = os.path.join(resource_path, 'test_folder')
        directories, files, file_sizes = storage.listdir(folder_path)

        # Verify file is in the folder
        self.assertIn('regular1.txt', files)
        # Verify no directories in the folder
        self.assertEqual(len(directories), 0)
        self.assertEqual(len(files), 1)
        self.assertEqual(len(file_sizes), 1)

    def test_listdir_with_metadata_filtering(self):
        """Test listdir function with metadata file filtering."""

        # Add regular files and simulate metadata files
        regular_files = ['regular1.txt', 'regular2.txt']
        for filename in regular_files:
            filepath = os.path.join(self.temp_dir, filename)
            with open(filepath, 'w') as f:
                f.write(f'Test content for {filename}')
            uploaded_file = UploadedFile(file=open(filepath, 'rb'), name=filename)
            add_file_to_resource(self.res, uploaded_file)

        # Get storage instance
        storage = self.res.get_s3_storage()
        resource_path = self.res.file_path

        # Test listdir without metadata filtering
        directories, files, file_sizes = storage.listdir(resource_path, remove_metadata=False)

        # Should include all files
        for filename in regular_files:
            self.assertIn(filename, files)

        # Verify basic structure
        # There should be no directories in the root
        self.assertEqual(len(directories), 0)
        self.assertEqual(len(files), len(regular_files))
        self.assertEqual(len(file_sizes), len(regular_files))

        # Test listdir with metadata filtering
        directories_filtered, files_filtered, file_sizes_filtered = storage.listdir(
            resource_path, remove_metadata=True
        )

        # Should still include regular files (metadata filtering doesn't affect regular files)
        for filename in regular_files:
            self.assertIn(filename, files_filtered)

        # The filtered and unfiltered results should be the same for regular files
        self.assertEqual(set(files), set(files_filtered))
        self.assertEqual(len(directories), len(directories_filtered))
        self.assertEqual(len(file_sizes), len(file_sizes_filtered))

    def test_listdir_nonexistent_path(self):
        """Test listdir function with nonexistent path."""
        storage = self.res.get_s3_storage()

        # Test with a path that doesn't exist within the resource
        resource_path = self.res.file_path
        nonexistent_path = os.path.join(resource_path, 'nonexistent_folder')
        with self.assertRaises(SessionException):
            storage.listdir(nonexistent_path)

    def test_listdir_with_simulated_metadata_files(self):
        """Test listdir function with simulated metadata files by directly saving to S3."""

        # Add regular files to the resource
        regular_files = ['regular1.txt', 'regular2.txt']
        for filename in regular_files:
            filepath = os.path.join(self.temp_dir, filename)
            file_to_upload = UploadedFile(file=open(filepath, 'rb'),
                                          name=os.path.basename(filepath))
            add_file_to_resource(self.res, file_to_upload)

        # Get storage instance
        storage = self.res.get_s3_storage()
        resource_path = self.res.file_path

        # Directly save metadata files to S3 (as they would be generated by the system)
        metadata_files = {
            'test_meta.xml': '<metadata>test metadata</metadata>',
            'test_resmap.xml': '<resmap>test resmap</resmap>',
            'hs_user_metadata.json': '{"test": "user metadata"}',
            'model.hs_user_metadata.json': '{"test": "model metadata"}',
            'model_schema.json': '{"schema": "test schema"}',
            'model_schema_values.json': '{"values": "test values"}'
        }

        for meta_filename, content in metadata_files.items():
            to_file_name = os.path.join(resource_path, meta_filename)
            content_file = ContentFile(content.encode('utf-8'))
            # Save the metadata file directly to S3
            storage.save(to_file_name, content_file)

        # Test listdir without metadata filtering
        directories, files, file_sizes = storage.listdir(resource_path, remove_metadata=False)

        # Should include all files (regular + metadata)
        all_expected_files = regular_files + list(metadata_files.keys())
        for filename in all_expected_files:
            self.assertIn(filename, files)

        self.assertEqual(len(files), len(all_expected_files))
        self.assertEqual(len(file_sizes), len(all_expected_files))

        # Test listdir with metadata files filtering
        directories_filtered, files_filtered, file_sizes_filtered = storage.listdir(
            resource_path, remove_metadata=True
        )

        # Should only include regular files (metadata files should be filtered out)
        for filename in regular_files:
            self.assertIn(filename, files_filtered)

        # Metadata files should be filtered out
        for filename in metadata_files.keys():
            if (
                is_metadata_xml_file(filename)
                or is_metadata_json_file(filename)
                or is_schema_json_file(filename)
                or is_schema_json_values_file(filename)
            ):
                self.assertNotIn(filename, files_filtered)

        # Verify filtering worked - should have fewer files after filtering
        self.assertLess(len(files_filtered), len(files))
        self.assertEqual(len(files_filtered), len(regular_files))
        self.assertEqual(len(directories), len(directories_filtered))
        # The filtered list should only contain regular files
        self.assertEqual(len(files_filtered), len(regular_files))
        self.assertLessEqual(len(file_sizes_filtered), len(files_filtered))

    def test_listdir_metadata_filtering_comprehensive(self):
        """Test comprehensive metadata filtering with various file types."""

        # Add regular files to the resource
        regular_files = ['data.txt', 'results.csv', 'image.png']
        for filename in regular_files:
            filepath = os.path.join(self.temp_dir, filename)
            with open(filepath, 'w') as f:
                f.write(f'Content of {filename}')
            file_to_upload = UploadedFile(file=open(filepath, 'rb'),
                                          name=os.path.basename(filepath))
            add_file_to_resource(self.res, file_to_upload)

        # Get storage instance
        storage = self.res.get_s3_storage()
        resource_path = self.res.file_path

        # Create a set of metadata files directly in S3
        metadata_test_cases = {
            # XML metadata files
            'aggregation_meta.xml': '<metadata>aggregation metadata</metadata>',
            'aggregation_resmap.xml': '<resmap>aggregation resmap</resmap>',
            'dataset_meta.xml': '<metadata>dataset metadata</metadata>',
            'model_resmap.xml': '<resmap>model resmap</resmap>',

            # JSON metadata files
            'hs_user_metadata.json': '{"user": "metadata"}',
            'timeseries.hs_user_metadata.json': '{"timeseries": "metadata"}',
            'netcdf.hs_user_metadata.json': '{"netcdf": "metadata"}',

            # Schema files
            'model_schema.json': '{"schema": "definition"}',
            'instance_schema.json': '{"schema": "instance"}',

            # Schema values files
            'model_schema_values.json': '{"values": "model"}',
            'instance_schema_values.json': '{"values": "instance"}',

            # Regular files that should NOT be filtered
            'user_data.json': '{"data": "user"}',
            'config.xml': '<config>settings</config>',
            'schema.txt': 'schema documentation',
            'metadata.txt': 'metadata documentation'
        }

        # Save all test files directly to S3
        for filename, content in metadata_test_cases.items():
            to_file_name = os.path.join(resource_path, filename)
            content_file = ContentFile(content.encode('utf-8'))
            storage.save(to_file_name, content_file)

        # Test listdir without filtering
        directories, files, file_sizes = storage.listdir(resource_path, remove_metadata=False)

        # Should include all files
        all_files = regular_files + list(metadata_test_cases.keys())
        self.assertEqual(len(files), len(all_files))
        # Verify no directories at root level
        self.assertEqual(len(directories), 0)
        self.assertEqual(len(file_sizes), len(all_files))

        # Test listdir with filtering
        directories_filtered, files_filtered, file_sizes_filtered = storage.listdir(
            resource_path, remove_metadata=True
        )

        # Count expected files after filtering
        expected_after_filtering = regular_files + [
            'user_data.json',  # Regular JSON file
            'config.xml',      # Regular XML file
            'schema.txt',      # Regular text file
            'metadata.txt'     # Regular text file
        ]

        # Verify regular files are still present
        for filename in expected_after_filtering:
            self.assertIn(filename, files_filtered)

        # Verify metadata files are filtered out
        filtered_out_files = [
            'aggregation_meta.xml',
            'aggregation_resmap.xml',
            'dataset_meta.xml',
            'model_resmap.xml',
            'hs_user_metadata.json',
            'timeseries.hs_user_metadata.json',
            'netcdf.hs_user_metadata.json',
            'model_schema.json',
            'instance_schema.json',
            'model_schema_values.json',
            'instance_schema_values.json'
        ]

        for filename in filtered_out_files:
            self.assertNotIn(filename, files_filtered)

        # Verify counts
        self.assertEqual(len(files_filtered), len(expected_after_filtering))
        self.assertLess(len(files_filtered), len(files))
        # There should be no directories in the root
        self.assertEqual(len(directories_filtered), 0)
        self.assertEqual(len(file_sizes_filtered), len(expected_after_filtering))

    def test_metadata_file_detection_functions(self):
        """Test the metadata file detection helper functions."""

        # Test XML metadata detection (files ending with _meta.xml or _resmap.xml)
        self.assertTrue(is_metadata_xml_file('test_meta.xml'))
        self.assertTrue(is_metadata_xml_file('test_resmap.xml'))
        self.assertTrue(is_metadata_xml_file('folder/test_meta.xml'))
        self.assertTrue(is_metadata_xml_file('folder/test_resmap.xml'))
        self.assertFalse(is_metadata_xml_file('regular_file.xml'))
        self.assertFalse(is_metadata_xml_file('test_metadata.xml'))
        self.assertFalse(is_metadata_xml_file('test.txt'))

        # Test JSON metadata detection (files ending with .hs_user_metadata.json or named hs_user_metadata.json)
        self.assertTrue(is_metadata_json_file('hs_user_metadata.json'))
        self.assertTrue(is_metadata_json_file('test.hs_user_metadata.json'))
        self.assertTrue(is_metadata_json_file('folder/hs_user_metadata.json'))
        self.assertTrue(is_metadata_json_file('folder/test.hs_user_metadata.json'))
        self.assertFalse(is_metadata_json_file('regular_file.json'))
        self.assertFalse(is_metadata_json_file('user_metadata.json'))
        self.assertFalse(is_metadata_json_file('test.txt'))

        # Test schema JSON detection (files ending with _schema.json)
        self.assertTrue(is_schema_json_file('test_schema.json'))
        self.assertTrue(is_schema_json_file('folder/test_schema.json'))
        self.assertTrue(is_schema_json_file('my_model_schema.json'))
        self.assertFalse(is_schema_json_file('schema.json'))
        self.assertFalse(is_schema_json_file('test.txt'))

        # Test schema values JSON detection (files ending with _schema_values.json)
        self.assertTrue(is_schema_json_values_file('test_schema_values.json'))
        self.assertTrue(is_schema_json_values_file('folder/test_schema_values.json'))
        self.assertTrue(is_schema_json_values_file('my_model_schema_values.json'))
        self.assertFalse(is_schema_json_values_file('regular_values.json'))
        self.assertFalse(is_schema_json_values_file('schema_values.json'))
        self.assertFalse(is_schema_json_values_file('test.txt'))
