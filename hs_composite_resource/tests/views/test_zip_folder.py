import json
import os
import shutil

from django.contrib.auth.models import Group
from django.core.files.uploadedfile import UploadedFile
from django.urls import reverse
from rest_framework import status

from hs_core import hydroshare
from hs_core.hydroshare import add_file_to_resource
from hs_core.models import ResourceFile
from hs_core.testing import MockIRODSTestCaseMixin, ViewTestCase
from hs_core.views.resource_folder_hierarchy import data_store_folder_zip
from hs_file_types.models import GenericLogicalFile, FileSetLogicalFile


class TestZipFolderViewFunctions(MockIRODSTestCaseMixin, ViewTestCase):
    def setUp(self):
        super(TestZipFolderViewFunctions, self).setUp()
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

        self.resource = hydroshare.create_resource(
            'CompositeResource',
            self.user,
            'My Test Resource'
        )

        # Make a text file
        self.txt_file_name = 'text.txt'
        self.txt_file_path = os.path.join(self.temp_dir, self.txt_file_name)
        txt = open(self.txt_file_path, 'w')
        txt.write("Hello World\n")
        txt.close()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        self.resource.delete()
        super(TestZipFolderViewFunctions, self).tearDown()

    def test_zip_folder_no_aggregation(self):
        """Here we are testing the view function 'data_store_folder_zip' for zipping a folder that contains
        no aggregation"""

        # create a folder
        new_folder = 'test_folder'
        ResourceFile.create_folder(self.resource, new_folder)
        # add the the text  file to the resource at the above folder
        self._add_file_to_resource(file_to_add=self.txt_file_path, upload_folder=new_folder)

        # prepare post data to zip the folder
        zip_file_name = 'test_folder.zip'
        post_data = {'res_id': self.resource.short_id,
                     'input_coll_path': new_folder,
                     'output_zip_file_name': zip_file_name
                     }
        url = reverse('zip_folder')
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = data_store_folder_zip(request, res_id=self.resource.short_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_content = json.loads(response.content.decode())
        self.assertEqual(json_content['name'], zip_file_name)

    def test_zip_folder_containing_aggregation(self):
        """Here we are testing the view function 'data_store_folder_zip' for zipping a folder that contains
        an aggregation"""

        # create a folder
        new_folder = 'test_folder'
        ResourceFile.create_folder(self.resource, new_folder)
        # add the the text  file to the resource at the above folder
        res_file = self._add_file_to_resource(file_to_add=self.txt_file_path, upload_folder=new_folder)
        # create a generic aggregation form the resource file
        GenericLogicalFile.set_file_type(self.resource, self.user, res_file.id)
        self.assertEqual(GenericLogicalFile.objects.count(), 1)
        logical_file = GenericLogicalFile.objects.first()
        expected_aggr_name = f"{new_folder}/{self.txt_file_name}"
        self.assertEqual(logical_file.aggregation_name, expected_aggr_name)

        # prepare post data to zip the folder
        zip_file_name = 'test_folder.zip'
        post_data = {'res_id': self.resource.short_id,
                     'input_coll_path': new_folder,
                     'output_zip_file_name': zip_file_name
                     }
        url = reverse('zip_folder')
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = data_store_folder_zip(request, res_id=self.resource.short_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_content = json.loads(response.content.decode())
        self.assertEqual(json_content['name'], zip_file_name)

    def test_zip_aggregation_folder(self):
        """Here we are testing the view function 'data_store_folder_zip' for zipping a folder that represents a
        fileset aggregation"""

        # create a folder
        new_folder = 'test_folder'
        ResourceFile.create_folder(self.resource, new_folder)
        # add the the text  file to the resource at the above folder
        self._add_file_to_resource(file_to_add=self.txt_file_path, upload_folder=new_folder)
        # create a fileset aggregation from the folder
        FileSetLogicalFile.set_file_type(self.resource, self.user, folder_path=new_folder)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        logical_file = FileSetLogicalFile.objects.first()
        self.assertEqual(logical_file.aggregation_name, new_folder)

        # prepare post data to zip the folder
        zip_file_name = 'test_folder.zip'
        post_data = {'res_id': self.resource.short_id,
                     'input_coll_path': new_folder,
                     'output_zip_file_name': zip_file_name
                     }
        url = reverse('zip_folder')
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = data_store_folder_zip(request, res_id=self.resource.short_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_content = json.loads(response.content.decode())
        self.assertEqual(json_content['name'], zip_file_name)

    def test_zip_folder_in_aggregation(self):
        """Here we are testing the view function 'data_store_folder_zip' for zipping a folder that is a sub-folder
        of a folder that represents a fileset aggregation"""

        # create a folder
        fs_folder = 'fs_folder'
        ResourceFile.create_folder(self.resource, fs_folder)
        # add the the text  file to the resource at the above folder
        self._add_file_to_resource(file_to_add=self.txt_file_path, upload_folder=fs_folder)
        # create a fileset aggregation from the folder
        FileSetLogicalFile.set_file_type(self.resource, self.user, folder_path=fs_folder)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        logical_file = FileSetLogicalFile.objects.first()
        self.assertEqual(logical_file.aggregation_name, fs_folder)
        self.assertEqual(logical_file.files.count(), 1)
        fs_child_folder = f"{fs_folder}/fs-child-folder"
        ResourceFile.create_folder(self.resource, fs_child_folder)
        # prepare post data to zip the folder
        zip_file_name = 'fs_child_folder.zip'
        post_data = {'res_id': self.resource.short_id,
                     'input_coll_path': fs_child_folder,
                     'output_zip_file_name': zip_file_name
                     }
        url = reverse('zip_folder')
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = data_store_folder_zip(request, res_id=self.resource.short_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_content = json.loads(response.content.decode())
        self.assertEqual(json_content['name'], zip_file_name)
        logical_file = FileSetLogicalFile.objects.first()
        # check the newly created zip file is part of the fileset aggregation
        self.assertEqual(logical_file.files.count(), 2)

    def _add_file_to_resource(self, file_to_add, upload_folder=''):
        file_to_upload = UploadedFile(file=open(file_to_add, 'rb'),
                                      name=os.path.basename(file_to_add))

        new_res_file = add_file_to_resource(
            self.resource, file_to_upload, folder=upload_folder, check_target_folder=True
        )
        return new_res_file
