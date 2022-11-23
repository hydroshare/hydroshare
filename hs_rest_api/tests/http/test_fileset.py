import tempfile

from django.urls import reverse
from hs_file_types.tests.utils import CompositeResourceTestMixin

from hs_core.models import ResourceFile
from hs_core.tests.api.rest.base import HSRESTTestCase
from hs_file_types.models import FileSetLogicalFile


class TestFileSetEndpoint(HSRESTTestCase, CompositeResourceTestMixin):

    def setUp(self):
        super(TestFileSetEndpoint, self).setUp()

        self.temp_dir = tempfile.mkdtemp()
        self.resources_to_delete = []

        self.res_title = "Test Generic File Type"
        self.logical_file_type_name = "FileSetLogicalFile"
        base_file_path = 'hs_file_types/tests/{}'
        self.generic_file_name = 'generic_file.txt'
        self.generic_file = base_file_path.format(self.generic_file_name)

    def test_fileset_create_remove(self):
        """Test that we can create a fileset aggregation from a folder that contains one file and remove the
        aggregation through the api"""

        self.create_composite_resource()
        new_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=new_folder)
        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # file has a folder
        self.assertEqual(res_file.file_folder, new_folder)
        # check that the resource file is not part of an aggregation
        self.assertEqual(res_file.has_logical_file, False)
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)
        # set folder to fileset logical file type (aggregation)

        set_type_url = reverse('set_file_type_public', kwargs={"pk": self.composite_resource.short_id,
                                                               "file_path": "",
                                                               "hs_file_type": "FileSet"})
        self.client.post(set_type_url, data={"folder_path": new_folder})
        res_file = self.composite_resource.files.first()
        # file has the same folder
        self.assertEqual(res_file.file_folder, new_folder)
        self.assertEqual(res_file.logical_file_type_name, self.logical_file_type_name)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        # aggregation dataset name should be same as the folder name
        self.assertEqual(res_file.logical_file.dataset_name, new_folder)

        remove_agg_url = reverse('remove_aggregation_public', kwargs={"resource_id": self.composite_resource.short_id,
                                                                      "file_path": new_folder,
                                                                      "hs_file_type": "FileSetLogicalFile"})
        self.client.post(remove_agg_url)
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)
        self.assertEqual(self.composite_resource.files.all().count(), 1)

        self.composite_resource.delete()

    def test_fileset_create_delete(self):
        """Test that we can create a fileset aggregation from a folder that contains one file and delete the
        aggregation through the api"""

        self.create_composite_resource()
        new_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=new_folder)
        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # file has a folder
        self.assertEqual(res_file.file_folder, new_folder)
        # check that the resource file is not part of an aggregation
        self.assertEqual(res_file.has_logical_file, False)
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)
        # set folder to fileset logical file type (aggregation)

        set_type_url = reverse('set_file_type_public', kwargs={"pk": self.composite_resource.short_id,
                                                               "file_path": "",
                                                               "hs_file_type": "FileSet"})
        self.client.post(set_type_url, data={"folder_path": new_folder})
        res_file = self.composite_resource.files.first()
        # file has the same folder
        self.assertEqual(res_file.file_folder, new_folder)
        self.assertEqual(res_file.logical_file_type_name, self.logical_file_type_name)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        # aggregation dataset name should be same as the folder name
        self.assertEqual(res_file.logical_file.dataset_name, new_folder)

        delete_agg_url = reverse('delete_aggregation_public', kwargs={"resource_id": self.composite_resource.short_id,
                                                                      "file_path": new_folder,
                                                                      "hs_file_type": "FileSetLogicalFile"})
        self.client.delete(delete_agg_url)
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)
        self.assertEqual(self.composite_resource.files.all().count(), 0)

        self.composite_resource.delete()
