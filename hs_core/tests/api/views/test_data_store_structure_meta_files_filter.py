import json
import os
from io import StringIO

from django.contrib.auth.models import Group
from django.core.files.base import ContentFile

from hs_core import hydroshare
from hs_core.hydroshare.utils import add_file_to_resource
from hs_core.testing import MockS3TestCaseMixin, ViewTestCase
from hs_core.views.resource_folder_hierarchy import data_store_structure
from hs_file_types.enums import AggregationMetaFilePath


class TestDataStoreStructureMetaFilesFilter(MockS3TestCaseMixin, ViewTestCase):
    def setUp(self):
        super(TestDataStoreStructureMetaFilesFilter, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.username = 'john'
        self.password = 'jhmypassword'
        self.user = hydroshare.create_account(
            'john@gmail.com',
            username=self.username,
            first_name='John',
            last_name='Clarson',
            superuser=False,
            password=self.password,
            groups=[]
        )
        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Resource for Metadata File Filtering for File Browsing'
        )

    def tearDown(self):
        super(TestDataStoreStructureMetaFilesFilter, self).tearDown()

    def test_metadata_file_filtering_at_resource_root(self):
        """Test that metadata files are filtered out at the resource root level"""

        # Get the storage instance
        istorage = self.composite_resource.get_s3_storage()

        # Create metadata files at resource root level by directly saving to S3
        resource_root_path = self.composite_resource.file_path

        # Create XML metadata files
        xml_metadata_content = '<?xml version="1.0" encoding="UTF-8"?><metadata></metadata>'
        xml_resmap_content = '<?xml version="1.0" encoding="UTF-8"?><resmap></resmap>'

        # Save XML metadata files directly to S3
        xml_meta_file_path = os.path.join(resource_root_path, 'test_meta.xml')
        xml_resmap_file_path = os.path.join(resource_root_path, 'test_resmap.xml')

        istorage.save(xml_meta_file_path, StringIO(xml_metadata_content))
        istorage.save(xml_resmap_file_path, StringIO(xml_resmap_content))

        # Create JSON metadata files
        json_metadata_content = '{"metadata": "test"}'

        # Save JSON metadata files directly to S3
        json_meta_file_path = os.path.join(
            resource_root_path,
            AggregationMetaFilePath.METADATA_JSON_FILE_NAME.value
        )
        json_meta_file_endswith_path = os.path.join(
            resource_root_path,
            'test' + AggregationMetaFilePath.METADATA_JSON_FILE_ENDSWITH.value
        )

        istorage.save(json_meta_file_path, StringIO(json_metadata_content))
        istorage.save(json_meta_file_endswith_path, StringIO(json_metadata_content))

        # Create schema files
        schema_json_content = '{"schema": "test"}'
        schema_values_content = '{"values": "test"}'

        schema_json_file_path = os.path.join(
            resource_root_path,
            'test' + AggregationMetaFilePath.SCHEMA_JSON_FILE_ENDSWITH.value
        )
        schema_values_file_path = os.path.join(
            resource_root_path,
            'test' + AggregationMetaFilePath.SCHEAMA_JSON_VALUES_FILE_ENDSWITH.value
        )

        istorage.save(schema_json_file_path, StringIO(schema_json_content))
        istorage.save(schema_values_file_path, StringIO(schema_values_content))

        # Add a regular file that should NOT be filtered
        regular_file_content = 'This is a regular file'
        regular_file = ContentFile(regular_file_content.encode('utf-8'))
        regular_file.name = 'regular_file.txt'

        # Create a ResourceFile record for the regular file so it appears in the listing
        add_file_to_resource(
            self.composite_resource,
            regular_file,
            folder='',
            check_target_folder=True,
            save_file_system_metadata=True
        )

        # Call the data_store_structure view function
        post_data = {
            'res_id': self.composite_resource.short_id,
            'store_path': ''
        }

        request = self.factory.post('/_internal/data-store-structure/', data=post_data)
        request.user = self.user
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = data_store_structure(request)
        self.assertEqual(response.status_code, 200)

        # Parse the JSON response
        response_data = json.loads(response.content.decode())

        # Verify that only the regular file is in the response, metadata files should be filtered out
        files = response_data['files']
        file_names = [f['name'] for f in files]

        # Regular file should be present
        self.assertIn('regular_file.txt', file_names)

        # Metadata files should be filtered out
        self.assertNotIn('test_meta.xml', file_names)
        self.assertNotIn('test_resmap.xml', file_names)
        self.assertNotIn(AggregationMetaFilePath.METADATA_JSON_FILE_NAME.value, file_names)
        self.assertNotIn('test' + AggregationMetaFilePath.METADATA_JSON_FILE_ENDSWITH.value, file_names)
        self.assertNotIn('test' + AggregationMetaFilePath.SCHEMA_JSON_FILE_ENDSWITH.value, file_names)
        self.assertNotIn('test' + AggregationMetaFilePath.SCHEAMA_JSON_VALUES_FILE_ENDSWITH.value, file_names)

        # Should have only 1 file (the regular file)
        self.assertEqual(len(files), 1)

        hydroshare.delete_resource(self.composite_resource.short_id)

    def test_metadata_file_filtering_at_folder_level(self):
        """Test that metadata files are filtered out at the folder level"""

        # Get the storage instance
        istorage = self.composite_resource.get_s3_storage()

        # Create a folder
        folder_name = 'test_folder'
        folder_path = os.path.join(self.composite_resource.file_path, folder_name)

        # Create metadata files at folder level by directly saving to S3
        # Create XML metadata files
        xml_metadata_content = '<?xml version="1.0" encoding="UTF-8"?><metadata></metadata>'
        xml_resmap_content = '<?xml version="1.0" encoding="UTF-8"?><resmap></resmap>'

        # Save XML metadata files directly to S3 in the folder
        xml_meta_file_path = os.path.join(folder_path, 'folder_test_meta.xml')
        xml_resmap_file_path = os.path.join(folder_path, 'folder_test_resmap.xml')

        istorage.save(xml_meta_file_path, StringIO(xml_metadata_content))
        istorage.save(xml_resmap_file_path, StringIO(xml_resmap_content))

        # Create JSON metadata files in the folder
        json_metadata_content = '{"metadata": "test"}'

        json_meta_file_path = os.path.join(
            folder_path,
            AggregationMetaFilePath.METADATA_JSON_FILE_NAME.value
        )
        json_meta_file_endswith_path = os.path.join(
            folder_path,
            'folder_test' + AggregationMetaFilePath.METADATA_JSON_FILE_ENDSWITH.value
        )

        istorage.save(json_meta_file_path, StringIO(json_metadata_content))
        istorage.save(json_meta_file_endswith_path, StringIO(json_metadata_content))

        # Create schema files in the folder
        schema_json_content = '{"schema": "test"}'
        schema_values_content = '{"values": "test"}'

        schema_json_file_path = os.path.join(
            folder_path,
            'folder_test' + AggregationMetaFilePath.SCHEMA_JSON_FILE_ENDSWITH.value
        )
        schema_values_file_path = os.path.join(
            folder_path,
            'folder_test' + AggregationMetaFilePath.SCHEAMA_JSON_VALUES_FILE_ENDSWITH.value
        )

        istorage.save(schema_json_file_path, StringIO(schema_json_content))
        istorage.save(schema_values_file_path, StringIO(schema_values_content))

        # Add a regular file in the folder that should NOT be filtered
        regular_file_content = 'This is a regular file in folder'
        regular_file = ContentFile(regular_file_content.encode('utf-8'))
        regular_file.name = 'folder_regular_file.txt'

        # Create a ResourceFile record for the regular file so it appears in the listing
        add_file_to_resource(
            self.composite_resource,
            regular_file,
            folder=folder_name,
            check_target_folder=True,
            save_file_system_metadata=True
        )

        # Call the data_store_structure view function for the folder
        post_data = {
            'res_id': self.composite_resource.short_id,
            'store_path': folder_name
        }

        request = self.factory.post('/_internal/data-store-structure/', data=post_data)
        request.user = self.user
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = data_store_structure(request)
        self.assertEqual(response.status_code, 200)

        # Parse the JSON response
        response_data = json.loads(response.content.decode())

        # Verify that only the regular file is in the response, metadata files should be filtered out
        files = response_data['files']
        file_names = [f['name'] for f in files]

        # Regular file should be present
        self.assertIn('folder_regular_file.txt', file_names)

        # Metadata files should be filtered out
        self.assertNotIn('folder_test_meta.xml', file_names)
        self.assertNotIn('folder_test_resmap.xml', file_names)
        self.assertNotIn(AggregationMetaFilePath.METADATA_JSON_FILE_NAME.value, file_names)
        self.assertNotIn('folder_test' + AggregationMetaFilePath.METADATA_JSON_FILE_ENDSWITH.value, file_names)
        self.assertNotIn('folder_test' + AggregationMetaFilePath.SCHEMA_JSON_FILE_ENDSWITH.value, file_names)
        self.assertNotIn('folder_test' + AggregationMetaFilePath.SCHEAMA_JSON_VALUES_FILE_ENDSWITH.value, file_names)

        # Should have only 1 file (the regular file)
        self.assertEqual(len(files), 1)

        hydroshare.delete_resource(self.composite_resource.short_id)
