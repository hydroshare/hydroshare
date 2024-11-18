import json
import os
from http import HTTPStatus

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import UploadedFile
from django.test import RequestFactory, TransactionTestCase
from django.urls import reverse

from hs_composite_resource.views import check_aggregation_files_to_sync
from hs_core import hydroshare
from hs_core.hydroshare import add_file_to_resource, create_resource
from hs_core.testing import MockIRODSTestCaseMixin
from hs_file_types.models import NetCDFLogicalFile, TimeSeriesLogicalFile


class AggregationFilesToUpdateViewFunctionTest(MockIRODSTestCaseMixin, TransactionTestCase,):
    def setUp(self):
        super(AggregationFilesToUpdateViewFunctionTest, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        test_file_base_path = 'hs_composite_resource/tests/data'
        self.res_title = "Testing Aggregation Files to Sync View Function"

        self.netcdf_file_name = 'netcdf_valid.nc'
        self.netcdf_file = f'{test_file_base_path}/{self.netcdf_file_name}'
        self.sqlite_file_name = 'ODM2_Multi_Site_One_Variable.sqlite'
        test_file_base_path = 'hs_file_types/tests/data'
        self.sqlite_file = f'{test_file_base_path}/{self.sqlite_file_name}'
        self.factory = RequestFactory()

    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()
        self.composite_resource.delete()
        super(AggregationFilesToUpdateViewFunctionTest, self).tearDown()

    def test_aggregation_files_to_update(self):
        """
        Testing the view function check_aggregation_files_to_sync that checks if there are files in netcdf or timeseries
        aggregations that need to be updated due to metadata changes by the user
        """

        # test for netcdf aggregation
        self.create_composite_resource(self.netcdf_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        nc_res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(nc_res_file.has_logical_file, False)

        # check that there is no NetCDFLogicalFile object
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)

        # set the nc file to NetCDF file type
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, nc_res_file.id)
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        nc_res_file.refresh_from_db()
        nc_logical_file = nc_res_file.logical_file
        # test that the update file (.nc file) state is false
        self.assertFalse(nc_logical_file.metadata.is_update_file)
        # test the view function
        url_params = {'resource_id': self.composite_resource.short_id}
        url = reverse('aggregation_files_to_sync', kwargs=url_params)
        request = self.factory.post(url)
        request.user = self.user
        # this is the view function we are testing
        response = check_aggregation_files_to_sync(request, resource_id=self.composite_resource.short_id)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_data['status'], 'SUCCESS')
        self.assertEqual(response_data['files_to_sync']['nc_files'], [])
        self.assertEqual(response_data['files_to_sync']['ts_files'], [])
        # set the is_update_file flag to True for the netcdf aggregation
        nc_logical_file.metadata.is_update_file = True
        nc_logical_file.metadata.save()
        # test the view function
        response = check_aggregation_files_to_sync(request, resource_id=self.composite_resource.short_id)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_data['status'], 'SUCCESS')
        self.assertEqual(response_data['files_to_sync']['nc_files'], [self.netcdf_file_name])
        self.assertEqual(response_data['files_to_sync']['ts_files'], [])

        # test for time series aggregation
        sqlite_file = self.add_file_to_resource(file_to_add=self.sqlite_file)
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 0)
        # set the sqlite file to time series file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, sqlite_file.id)
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 1)
        sqlite_file.refresh_from_db()
        ts_logical_file = sqlite_file.logical_file
        # test that the update file (.sqlite file) state is false
        self.assertFalse(ts_logical_file.metadata.is_update_file)
        # test the view function
        response = check_aggregation_files_to_sync(request, resource_id=self.composite_resource.short_id)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_data['status'], 'SUCCESS')
        self.assertEqual(response_data['files_to_sync']['nc_files'], [self.netcdf_file_name])
        self.assertEqual(response_data['files_to_sync']['ts_files'], [])
        # set the is_update_file flag to True for the time series aggregation
        ts_logical_file.metadata.is_update_file = True
        ts_logical_file.metadata.save()
        # test the view function
        response = check_aggregation_files_to_sync(request, resource_id=self.composite_resource.short_id)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_data['status'], 'SUCCESS')
        self.assertEqual(response_data['files_to_sync']['nc_files'], [self.netcdf_file_name])
        self.assertEqual(response_data['files_to_sync']['ts_files'], [self.sqlite_file_name])

    def create_composite_resource(self, file_to_upload=[], auto_aggregate=False, folder=''):
        if isinstance(file_to_upload, str):
            file_to_upload = [file_to_upload]
        files = []
        full_paths = {}
        for file_name in file_to_upload:
            file_obj = open(file_name, 'rb')
            if folder:
                full_paths[file_obj] = os.path.join(folder, file_name)
            uploaded_file = UploadedFile(file=file_obj, name=os.path.basename(file_obj.name))
            files.append(uploaded_file)
        self.composite_resource = create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title=self.res_title,
            files=files,
            auto_aggregate=auto_aggregate,
            full_paths=full_paths
        )

    def add_file_to_resource(self, file_to_add, upload_folder=''):
        file_to_upload = UploadedFile(file=open(file_to_add, 'rb'),
                                      name=os.path.basename(file_to_add))

        new_res_file = add_file_to_resource(
            self.composite_resource, file_to_upload, folder=upload_folder, check_target_folder=True,
            save_file_system_metadata=True
        )
        return new_res_file
