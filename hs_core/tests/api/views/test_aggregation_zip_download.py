import json
import os

from django.contrib.auth.models import Group
from django.core.files.uploadedfile import UploadedFile
from django.urls import reverse
from rest_framework import status

from django_s3.views import download
from hs_core import hydroshare
from hs_core.hydroshare import resource_file_add_process
from hs_core.models import ResourceFile
from hs_core.testing import MockS3TestCaseMixin, ViewTestCase
from hs_core.views.utils import move_or_rename_file_or_folder
from hs_file_types.models import GeoRasterLogicalFile


class TestAggregationZipDownload(MockS3TestCaseMixin, ViewTestCase):
    def setUp(self):
        super(TestAggregationZipDownload, self).setUp()
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
            resource_type='CompositeResource',
            owner=self.user,
            title='Resource Aggregation zip download Testing'
        )
        self.raster_file_path_1 = 'hs_core/tests/data/cea.tif'
        self.raster_file_path_2 = 'hs_core/tests/data/cea with spaces.tif'

    def tearDown(self):
        self.resource.delete()
        super(TestAggregationZipDownload, self).tearDown()

    def test_aggregation_download_as_zip_1(self):
        """test we can download an aggregation that is inside a folder - aggregation path contains no spaces"""
        self._test_aggregation_download_zip(folder="raster_aggregation", raster_file=self.raster_file_path_1)

    def test_aggregation_download_as_zip_2(self):
        """test we can download an aggregation that is inside a folder (folder name contains spaces) - aggregation path
        contains spaces"""
        self._test_aggregation_download_zip(folder="raster aggregation", raster_file=self.raster_file_path_1)

    def test_aggregation_download_as_zip_3(self):
        """test we can download an aggregation that is at the root of the resource - aggregation path
        contains no spaces"""
        self._test_aggregation_download_zip(folder="", raster_file=self.raster_file_path_1)

    def test_aggregation_download_as_zip_4(self):
        """test we can download an aggregation that is at the root of the resource - aggregation path
        contains spaces due to the spaces in the uploaded tif file name"""
        self._test_aggregation_download_zip(folder="", raster_file=self.raster_file_path_2, auto_aggregate=False)

    def test_aggregation_download_as_zip_5(self):
        """test we can download an aggregation that is inside a folder - aggregation path
        contains spaces due to the spaces in the uploaded tif file name and spaces in the name of the folder"""
        self._test_aggregation_download_zip(folder="raster aggregation", raster_file=self.raster_file_path_2,
                                            auto_aggregate=False)

    def _test_aggregation_download_zip(self, folder, raster_file, auto_aggregate=True):
        aggr_folder = folder
        if folder:
            ResourceFile.create_folder(resource=self.resource, folder=aggr_folder)

        # there should be no raster aggregation
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)

        # upload a tif file to create a raster aggregation
        tif_file_obj = open(raster_file, "rb")
        uploaded_file = UploadedFile(file=tif_file_obj,
                                     name=os.path.basename(tif_file_obj.name))
        resource_file_add_process(resource=self.resource, files=(uploaded_file,), folder=aggr_folder, user=self.user,
                                  auto_aggregate=auto_aggregate)

        if not auto_aggregate:
            # rename the uploaded file to create spaces in the file name
            base_path = "data/contents"
            if folder:
                base_path = f"{base_path}/{folder}"
            res_file = self.resource.files.first()
            src_path = f'{base_path}/{res_file.file_name}'
            file_name_non_preferred = 'tif file name with spaces.tif'
            tgt_path = f'{base_path}/{file_name_non_preferred}'
            move_or_rename_file_or_folder(self.user, self.resource.short_id, src_path, tgt_path)
            GeoRasterLogicalFile.set_file_type(resource=self.resource, file_id=res_file.id, user=self.user)

        # there should be 1 raster aggregation
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        raster_aggr = GeoRasterLogicalFile.objects.first()

        # download the raster aggregation as a zip file
        aggr_main_file = raster_aggr.get_main_file
        aggr_main_file_path = aggr_main_file.storage_path
        url_params = {'path': aggr_main_file_path}
        url = reverse('django_s3_download', kwargs=url_params)
        url = f"{url}?zipped=True&aggregation=True"
        request = self.factory.get(url)
        request.user = self.user

        self.add_session_to_request(request)
        response = download(request, path=aggr_main_file.storage_path)
        # check that the download request was successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        # check that a task id was generated
        task_id = response_json["task_id"]
        self.assertTrue(len(task_id) > 0, msg='ensure a task_id is returned for async zipping')
        # verify the download path
        download_path = response_json["download_path"]
        self.assertTrue(download_path.endswith(f"{aggr_main_file_path}.zip"))
