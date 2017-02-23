import os
import tempfile
import shutil

from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.hydroshare.utils import resource_post_create_actions

from hs_file_types.models import NetCDFLogicalFile, NetCDFFileMetaData, BaseLogicalFile


class NetCDFFileTypeMetaDataTest(MockIRODSTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(NetCDFFileTypeMetaDataTest, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Raster File Metadata'
        )

        self.temp_dir = tempfile.mkdtemp()
        self.netcdf_file_name = 'netcdf_valid.nc'
        self.netcdf_file = 'hs_file_types/tests/{}'.format(self.netcdf_file_name)

        target_temp_netcdf_file = os.path.join(self.temp_dir, self.netcdf_file_name)
        shutil.copy(self.netcdf_file, target_temp_netcdf_file)
        self.netcdf_file_obj = open(target_temp_netcdf_file, 'r')

    def tearDown(self):
        super(NetCDFFileTypeMetaDataTest, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_set_file_type_to_netcdf(self):
        # here we are using a valid nc file for setting it
        # to NetCDF file type which includes metadata extraction
        self.netcdf_file_obj = open(self.netcdf_file, 'r')
        self._create_composite_resource()

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is associated with BaseLogicalFile
        logical_file = res_file.logical_file_new
        self.assertNotEqual(logical_file, None)
        self.assertEqual(logical_file.logical_file_type, "GenericLogicalFile")
        self.assertEqual(BaseLogicalFile.objects.filter(
            logical_file_type='GenericLogicalFile').count(), 1)

        # check that there is one BaseLogicalFile object
        self.assertEqual(BaseLogicalFile.objects.count(), 1)
        self.assertTrue(isinstance(logical_file, BaseLogicalFile))
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)

        # set the nc file to NetCDF file type
        NetCDFLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        # check that there is one BaseLogicalFile object
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        self.assertEqual(BaseLogicalFile.objects.count(), 1)
        self.assertEqual(BaseLogicalFile.objects.filter(
            logical_file_type='NetCDFLogicalFile').count(), 1)
        self.assertEqual(BaseLogicalFile.objects.filter(
            logical_file_type='GenericLogicalFile').count(), 0)
        # There should be now 2 files
        self.assertEqual(self.composite_resource.files.count(), 2)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file_new
        # logical file should be associated with 2 files
        self.assertEqual(logical_file.files.all().count(), 2)

        # TODO: test extracted netcdf file type metadata

        # test deleting the logical file should delete all associated resource files
        logical_file.delete()
        self.assertEqual(BaseLogicalFile.objects.count(), 0)
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        self.assertEqual(self.composite_resource.files.count(), 0)

    def test_netcdf_metadata_CRUD(self):
        # here we are using a valid nc file for setting it
        # to NetCDF file type which includes metadata extraction
        self.netcdf_file_obj = open(self.netcdf_file, 'r')
        self._create_composite_resource()

        # make the netcdf file part of the NetCDFLogicalFile
        res_file = self.composite_resource.files.first()
        self.assertEqual(NetCDFFileMetaData.objects.count(), 0)
        netcdf_logical_file = NetCDFLogicalFile.create()
        self.assertEqual(NetCDFFileMetaData.objects.count(), 1)
        # netcdf_logical_file.add_resource_file(res_file)
        res_file.logical_file_new = netcdf_logical_file
        res_file.save()
        # self.assertEqual(res_file.logical_file_type_name, 'NetCDFLogicalFile')
        self.assertEqual(netcdf_logical_file.logical_file_type, 'NetCDFLogicalFile')
        self.assertEqual(netcdf_logical_file.files.count(), 1)

        # create OriginalCoverage element
        self.assertEqual(netcdf_logical_file.metadata.original_coverage, None)
        coverage_data = {'northlimit': '121.345', 'southlimit': '42.678', 'eastlimit': '123.789',
                         'westlimit': '40.789', 'units': 'meters'}
        netcdf_logical_file.metadata.create_element('OriginalCoverage', data=coverage_data)
        self.assertNotEqual(netcdf_logical_file.metadata.original_coverage, None)
        self.assertEqual(netcdf_logical_file.metadata.original_coverage.northlimit, '121.345')

        # test updating OriginalCoverage element
        orig_coverage = netcdf_logical_file.metadata.original_coverage
        coverage_data = {'northlimit': '111.333', 'southlimit': '42.678', 'eastlimit': '123.789',
                         'westlimit': '40.789', 'units': 'meters'}
        netcdf_logical_file.metadata.update_element(orig_coverage.id, data=coverage_data)
        self.assertEqual(netcdf_logical_file.metadata.original_coverage.northlimit, '111.333')

        # trying to create a 2nd OriginalCoverage element should raise exception
        with self.assertRaises(ValidationError):
            netcdf_logical_file.metadata.create_element('OriginalCoverage', data=coverage_data)

        # trying to update 'north_limit' key with a non-numeric value should raise exception
        coverage_data = {'northlimit': '121.345a', 'southlimit': '42.678', 'eastlimit': '123.789',
                         'westlimit': '40.789', 'units': 'meters'}
        with self.assertRaises(ValidationError):
            netcdf_logical_file.metadata.update_element(orig_coverage.id, data=coverage_data)

        # create Variable element
        self.assertEqual(netcdf_logical_file.metadata.variables.count(), 0)
        variable_data = {'name': 'variable_name', 'type': 'Int', 'unit': 'deg F',
                         'shape': 'variable_shape'}
        netcdf_logical_file.metadata.create_element('Variable', data=variable_data)
        self.assertEqual(netcdf_logical_file.metadata.variables.count(), 1)
        self.assertEqual(netcdf_logical_file.metadata.variables.first().name, 'variable_name')

        # test that multiple Variable elements can be created
        variable_data = {'name': 'variable_name_2', 'type': 'Int', 'unit': 'deg F',
                         'shape': 'variable_shape_2'}
        netcdf_logical_file.metadata.create_element('Variable', data=variable_data)
        self.assertEqual(netcdf_logical_file.metadata.variables.count(), 2)

        # test update Variable element
        variable = netcdf_logical_file.metadata.variables.first()
        variable_data = {'name': 'variable_name_updated', 'type': 'Int', 'unit': 'deg F',
                         'shape': 'variable_shape'}
        netcdf_logical_file.metadata.update_element(variable.id, data=variable_data)
        variable = netcdf_logical_file.metadata.variables.get(id=variable.id)
        self.assertEqual(variable.name, 'variable_name_updated')

    def _create_composite_resource(self):
        uploaded_file = UploadedFile(file=self.netcdf_file_obj,
                                     name=os.path.basename(self.netcdf_file_obj.name))
        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test NetCDF File Type Metadata',
            files=(uploaded_file,)
        )

        # set the logical file
        resource_post_create_actions(resource=self.composite_resource, user=self.user,
                                     metadata=self.composite_resource.metadata)
