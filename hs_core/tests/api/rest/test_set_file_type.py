import os

from django.core.files.uploadedfile import UploadedFile

from rest_framework import status

from hs_core.hydroshare import resource
from hs_core.hydroshare.utils import resource_file_add_process
from hs_core.views.utils import create_folder, move_or_rename_file_or_folder

from .base import HSRESTTestCase


class TestSetFileTypeEndPoint(HSRESTTestCase):
    def setUp(self):
        super(TestSetFileTypeEndPoint, self).setUp()
        self.raster_file_name = 'cea.tif'
        self.raster_file_path = 'hs_core/tests/data/cea.tif'

        self.rtype = 'CompositeResource'
        self.title = 'My Test resource'
        self.resource = resource.create_resource(self.rtype,
                                                 self.user,
                                                 self.title)

        self.resources_to_delete.append(self.resource.short_id)

    def test_set_file_type_success_1(self):
        # here we will set the tif file to GeoRaster file type

        # resource should have no file at this point
        self.assertEqual(self.resource.files.count(), 0)
        # add the tif file to the composite resource
        tif_file_obj = open(self.raster_file_path, "r")
        uploaded_file = UploadedFile(file=tif_file_obj,
                                     name=os.path.basename(tif_file_obj.name))
        resource_file_add_process(resource=self.resource, files=(uploaded_file,), user=self.user,
                                  auto_aggregate=False)

        # resource should have one file at this point
        self.assertEqual(self.resource.files.count(), 1)
        res_file = self.resource.files.all().first()
        self.assertEqual(res_file.file_name, self.raster_file_name)

        # test the set file type endpoint
        url_template = "/hsapi/resource/{res_id}/functions/set-file-type/{file_path}/{file_type}/"
        set_file_type_url = url_template.format(res_id=self.resource.short_id,
                                                file_path=self.raster_file_name,
                                                file_type="GeoRaster")
        response = self.client.post(set_file_type_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_set_file_type_success_2(self):
        # here we will set the tif file (the file being not in root dir)to GeoRaster file type

        # resource should have no file at this point
        self.assertEqual(self.resource.files.count(), 0)
        # add the tif file to the composite resource
        tif_file_obj = open(self.raster_file_path, "r")
        uploaded_file = UploadedFile(file=tif_file_obj,
                                     name=os.path.basename(tif_file_obj.name))
        resource_file_add_process(resource=self.resource, files=(uploaded_file,), user=self.user,
                                  auto_aggregate=False)

        # resource should have one file at this point
        self.assertEqual(self.resource.files.count(), 1)
        res_file = self.resource.files.all().first()
        self.assertEqual(res_file.file_name, self.raster_file_name)

        create_folder(self.resource.short_id, 'data/contents/sub_test_dir')

        # move the first two files in file_name_list to the new folder
        move_or_rename_file_or_folder(self.user, self.resource.short_id,
                                      'data/contents/' + self.raster_file_name,
                                      'data/contents/sub_test_dir/' + self.raster_file_name)

        res_file = self.resource.files.all().first()
        self.assertEqual(res_file.short_path, "sub_test_dir/" + self.raster_file_name)
        # test the set file type endpoint
        url_template = "/hsapi/resource/{res_id}/functions/set-file-type/{file_path}/{file_type}/"

        set_file_type_url = url_template.format(res_id=self.resource.short_id,
                                                file_path=res_file.short_path,
                                                file_type="GeoRaster")
        response = self.client.post(set_file_type_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_set_file_type_failure_1(self):
        # here we will set the tif file to NetCDF file type which should fail

        # resource should have no file at this point
        self.assertEqual(self.resource.files.count(), 0)
        # add the tif file to the composite resource
        tif_file_obj = open(self.raster_file_path, "r")
        uploaded_file = UploadedFile(file=tif_file_obj,
                                     name=os.path.basename(tif_file_obj.name))
        resource_file_add_process(resource=self.resource, files=(uploaded_file,), user=self.user,
                                  auto_aggregate=False)
        # resource should have one file at this point
        self.assertEqual(self.resource.files.count(), 1)
        res_file = self.resource.files.all().first()
        self.assertEqual(res_file.file_name, self.raster_file_name)

        # test the set file type endpoint using a wrong file type (NetCDF)
        url_template = "/hsapi/resource/{res_id}/functions/set-file-type/{file_path}/{file_type}/"
        set_file_type_url = url_template.format(res_id=self.resource.short_id,
                                                file_path=self.raster_file_name,
                                                file_type="NetCDF")
        response = self.client.post(set_file_type_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_set_file_type_failure_2(self):
        # here we will set the tif file to GeoRaster file type with an invalid file path
        # which should fail

        # resource should have no file at this point
        self.assertEqual(self.resource.files.count(), 0)
        # add the tif file to the composite resource
        tif_file_obj = open(self.raster_file_path, "r")
        uploaded_file = UploadedFile(file=tif_file_obj,
                                     name=os.path.basename(tif_file_obj.name))
        resource_file_add_process(resource=self.resource, files=(uploaded_file,), user=self.user,
                                  auto_aggregate=False)
        # resource should have one file at this point
        self.assertEqual(self.resource.files.count(), 1)
        res_file = self.resource.files.all().first()
        self.assertEqual(res_file.file_name, self.raster_file_name)

        # test the set file type endpoint using a wrong file path
        url_template = "/hsapi/resource/{res_id}/functions/set-file-type/{file_path}/{file_type}/"
        file_path = os.path.join("no-such-folder", self.raster_file_name)
        set_file_type_url = url_template.format(res_id=self.resource.short_id,
                                                file_path=file_path,
                                                file_type="GeoRaster")
        response = self.client.post(set_file_type_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
