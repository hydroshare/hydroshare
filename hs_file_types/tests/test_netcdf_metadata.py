import os

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TransactionTestCase
from rest_framework.exceptions import ValidationError as DRF_ValidationError

from hs_core import hydroshare
from hs_core.models import Coverage, ResourceFile
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core.views.utils import remove_folder, move_or_rename_file_or_folder
from hs_file_types.models import NetCDFLogicalFile, NetCDFFileMetaData, OriginalCoverage, Variable
from hs_file_types.enums import AggregationMetaFilePath
from .utils import (
    assert_netcdf_file_type_metadata,
    CompositeResourceTestMixin,
    get_path_with_no_file_extension,
)


class NetCDFFileTypeTest(MockIRODSTestCaseMixin, TransactionTestCase,
                         CompositeResourceTestMixin):
    def setUp(self):
        super(NetCDFFileTypeTest, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        test_file_base_path = 'hs_file_types/tests'
        self.res_title = "Testing NetCDF File Type"

        self.netcdf_file_name = 'netcdf_valid.nc'
        self.netcdf_file = f'{test_file_base_path}/{self.netcdf_file_name}'
        self.netcdf_invalid_file_name = 'netcdf_invalid.nc'
        self.netcdf_invalid_file = f'{test_file_base_path}/{self.netcdf_invalid_file_name}'
        self.netcdf_no_coverage_file_name = 'nc_no_spatial_ref.nc'
        self.netcdf_no_coverage_file = f'{test_file_base_path}/data/{self.netcdf_no_coverage_file_name}'
        self.netcdf_sphere_lambert_conformal_conic_file_name = 'sample.nc'
        self.netcdf_sphere_lambert_conformal_conic_file = \
            f'{test_file_base_path}/data/{self.netcdf_sphere_lambert_conformal_conic_file_name}'

    def test_create_aggregation_from_nc_file_1(self):
        # here we are using a valid nc file for setting it
        # to NetCDF file type which includes metadata extraction
        # the nc file in this case is at the root of the folder hierarchy

        self.create_composite_resource(self.netcdf_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no NetCDFLogicalFile object
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        base_file_name, _ = os.path.splitext(res_file.file_name)
        expected_res_file_folder_path = res_file.file_folder
        # set the nc file to NetCDF file type
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # test extracted metadata
        assert_netcdf_file_type_metadata(self, self.res_title,
                                         aggr_folder=expected_res_file_folder_path)
        # test file level keywords
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # test the metadata for the aggregation is in dirty state
        self.assertTrue(logical_file.metadata.is_dirty)
        # test that the update file (.nc file) state is false
        self.assertFalse(logical_file.metadata.is_update_file)
        self.assertEqual(len(logical_file.metadata.keywords), 1)
        self.assertEqual(logical_file.metadata.keywords[0], 'Snow water equivalent')
        # check that there are no required missing metadata for the netcdf aggregation
        self.assertEqual(len(logical_file.metadata.get_required_missing_elements()), 0)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_from_nc_file_2(self):
        # here we are using a valid nc file for setting it
        # to NetCDF file type which includes metadata extraction
        # the nc file in this case is not at the root of the folder hierarchy but in a folder

        self.create_composite_resource()
        new_folder = 'netcdf_aggr'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the nc file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.netcdf_file, upload_folder=new_folder)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no NetCDFLogicalFile object
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)

        # set the nc file to NetCDF file type
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # test extracted metadata
        assert_netcdf_file_type_metadata(self, self.res_title, aggr_folder=new_folder)
        # test file level keywords
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # test the metadata for the aggregation is in dirty state
        self.assertTrue(logical_file.metadata.is_dirty)
        # test that the update file (.nc file) state is false
        self.assertFalse(logical_file.metadata.is_update_file)
        self.assertEqual(len(logical_file.metadata.keywords), 1)
        self.assertEqual(logical_file.metadata.keywords[0], 'Snow water equivalent')
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_from_nc_file_3(self):
        # here we are using a valid nc file for setting it
        # to NetCDF file type which includes metadata extraction
        # the nc file in this case is not at the root of the folder hierarchy but in a folder. The
        # same folder contains another file that's not going part of the aggregation
        # location of the nc file before aggregation is created: /my_folder/netcdf_valid.nc
        # location of another file before aggregation is created: /my_folder/netcdf_invalid.nc
        # location of nc file after aggregation is created:
        # /my_folder/netcdf_valid.nc
        # location of another file after aggregation is created: /my_folder/netcdf_invalid.nc

        self.create_composite_resource()
        new_folder = 'my_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the nc file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.netcdf_file, upload_folder=new_folder)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no NetCDFLogicalFile object
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        # add another file to the same folder
        self.add_file_to_resource(file_to_add=self.netcdf_invalid_file, upload_folder=new_folder)
        self.assertEqual(self.composite_resource.files.all().count(), 2)

        # set the nc file to NetCDF file type
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        self.assertEqual(self.composite_resource.files.all().count(), 3)
        # test logical file/aggregation
        self.assertEqual(len(list(self.composite_resource.logical_files)), 1)
        logical_file = list(self.composite_resource.logical_files)[0]
        self.assertEqual(logical_file.files.count(), 2)
        base_nc_file_name, _ = os.path.splitext(self.netcdf_file_name)
        expected_file_folder = new_folder
        for res_file in logical_file.files.all():
            self.assertEqual(res_file.file_folder, expected_file_folder)
        self.assertTrue(isinstance(logical_file, NetCDFLogicalFile))
        self.assertTrue(logical_file.metadata, NetCDFLogicalFile)
        # test the metadata for the aggregation is in dirty state
        self.assertTrue(logical_file.metadata.is_dirty)
        # test that the update file (.nc file) state is false
        self.assertFalse(logical_file.metadata.is_update_file)

        # test the location of the file that's not part of the netcdf aggregation
        other_res_file = None
        for res_file in self.composite_resource.files.all():
            if not res_file.has_logical_file:
                other_res_file = res_file
                break
        self.assertEqual(other_res_file.file_folder, new_folder)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_from_nc_file_4(self):
        # here we are using a valid nc file for setting it
        # to NetCDF file type which includes metadata extraction
        # the nc file in this case is not at the root of the folder hierarchy but in a folder. The
        # same folder contains another folder
        # location nc file before aggregation is created: /my_folder/netcdf_valid.nc
        # location of another folder before aggregation is created: /my_folder/another_folder
        # location of nc file after aggregation is created:
        # /my_folder/netcdf_valid.nc

        self.create_composite_resource()
        new_folder = 'my_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        another_folder = '{}/another_folder'.format(new_folder)
        ResourceFile.create_folder(self.composite_resource, another_folder)
        # add the the nc file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.netcdf_file, upload_folder=new_folder)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no NetCDFLogicalFile object
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)

        # set the nc file to NetCDF file type
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        # test logical file/aggregation
        self.assertEqual(len(list(self.composite_resource.logical_files)), 1)
        logical_file = list(self.composite_resource.logical_files)[0]
        self.assertEqual(logical_file.files.count(), 2)
        base_nc_file_name, _ = os.path.splitext(self.netcdf_file_name)
        expected_file_folder = new_folder
        for res_file in logical_file.files.all():
            self.assertEqual(res_file.file_folder, expected_file_folder)
        self.assertTrue(isinstance(logical_file, NetCDFLogicalFile))
        self.assertTrue(logical_file.metadata, NetCDFLogicalFile)
        # test the metadata for the aggregation is in dirty state
        self.assertTrue(logical_file.metadata.is_dirty)
        # test that the update file (.nc file) state is false
        self.assertFalse(logical_file.metadata.is_update_file)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_from_nc_file_5(self):
        # here we are using a valid nc file for setting it
        # to NetCDF file type which includes metadata extraction
        # the nc file in this case has spatial reference with coordinate system of 'Sphere_Lambert_Conformal_Conic'
        # and we are testing that spatial coverage is computed from spatial reference as part of the metadata extraction

        self.create_composite_resource(self.netcdf_sphere_lambert_conformal_conic_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no NetCDFLogicalFile object
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        base_file_name, _ = os.path.splitext(res_file.file_name)
        # set the nc file to NetCDF file type
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # test computed spatial coverage
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # test the metadata for the aggregation is in dirty state
        self.assertTrue(logical_file.metadata.is_dirty)
        # test that the update file (.nc file) state is false
        self.assertFalse(logical_file.metadata.is_update_file)
        self.assertNotEqual(logical_file.metadata.originalCoverage, None)
        self.assertNotEqual(logical_file.metadata.spatial_coverage, None)
        # check that there are no required missing metadata for the netcdf aggregation
        self.assertEqual(len(logical_file.metadata.get_required_missing_elements()), 0)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_for_netcdf_resource_title(self):
        # here we are using a valid nc file for setting it
        # to NetCDF file type which includes metadata extraction
        # and testing that the resource title gets set with the
        # extracted metadata if the original title is 'untitled resource'

        self.res_title = 'untitled resource'
        self.create_composite_resource(self.netcdf_file)

        self.assertEqual(self.composite_resource.metadata.title.value, self.res_title)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no NetCDFLogicalFile object
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)

        # set the nc file to NetCDF file type
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # test resource title was updated with the extracted netcdf data
        res_title = "Snow water equivalent estimation at TWDEF site from Oct 2009 to June 2010"
        self.assertEqual(self.composite_resource.metadata.title.value, res_title)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_from_invalid_nc_file_1(self):
        # here we are using an invalid netcdf file for setting it
        # to netCDF file type which should fail

        self.create_composite_resource(self.netcdf_invalid_file)
        self._test_invalid_file()
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_from_invalid_nc_file_2(self):
        # here we are using a valid nc file for setting it
        # to NetCDF file type which already been previously set to this file type - should fail

        self.create_composite_resource(self.netcdf_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # set nc file to aggregation
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        # check that the nc resource file is associated with a logical file
        res_file = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, '.nc')[0]
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "NetCDFLogicalFile")

        # trying to set this nc file again to netcdf file type should raise
        # ValidationError
        with self.assertRaises(ValidationError):
            NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_aggregation_metadata_CRUD(self):
        # here we are using a valid nc file (has no spatial reference) for creating a NetCDF file type (aggregation)
        # then testing with metadata CRUD actions for the  aggregation

        self.create_composite_resource()
        new_folder = 'nc_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the nc file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.netcdf_no_coverage_file, upload_folder=new_folder)
        # create a NetCDFLogicalFile using the uploaded file
        res_file = self.composite_resource.files.first()
        self.assertEqual(NetCDFFileMetaData.objects.count(), 0)
        NetCDFLogicalFile.set_file_type(resource=self.composite_resource, user=self.user, file_id=res_file.id)

        self.assertEqual(NetCDFFileMetaData.objects.count(), 1)
        netcdf_logical_file = NetCDFLogicalFile.objects.first()

        # check that there are no required missing metadata for the netcdf aggregation
        self.assertEqual(len(netcdf_logical_file.metadata.get_required_missing_elements()), 0)

        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.logical_file_type_name, 'NetCDFLogicalFile')
        self.assertEqual(netcdf_logical_file.files.count(), 2)

        # create keywords - note it is possible to have duplicate keywords
        # appropriate view functions need to disallow duplicate keywords
        keywords = ['key-1', 'key-1', 'key-2']
        netcdf_logical_file.metadata.keywords = keywords
        netcdf_logical_file.metadata.save()
        self.assertEqual(len(keywords), len(netcdf_logical_file.metadata.keywords))
        for keyword in keywords:
            self.assertIn(keyword, netcdf_logical_file.metadata.keywords)

        # create OriginalCoverage element
        self.assertEqual(netcdf_logical_file.metadata.original_coverage, None)
        coverage_data = {'northlimit': 121.345, 'southlimit': 42.678, 'eastlimit': 123.789,
                         'westlimit': 40.789, 'units': 'meters'}
        netcdf_logical_file.metadata.create_element('OriginalCoverage', value=coverage_data)
        self.assertNotEqual(netcdf_logical_file.metadata.original_coverage, None)
        self.assertEqual(float(netcdf_logical_file.metadata.original_coverage.value['northlimit']),
                         121.345)

        # test updating OriginalCoverage is not allowed
        orig_coverage = netcdf_logical_file.metadata.original_coverage
        coverage_data = {'northlimit': 111.333, 'southlimit': 42.678, 'eastlimit': 123.789,
                         'westlimit': 40.789, 'units': 'meters'}
        with self.assertRaises(ValidationError):
            netcdf_logical_file.metadata.update_element('OriginalCoverage', orig_coverage.id,
                                                        value=coverage_data)
        # trying to create a 2nd OriginalCoverage element should raise exception
        with self.assertRaises(Exception):
            netcdf_logical_file.metadata.create_element('OriginalCoverage', value=coverage_data)

        # test that spatial coverage can be created
        # there should not be any spatial coverage for the netcdf file type
        self.assertEqual(netcdf_logical_file.metadata.spatial_coverage, None)
        coverage_data = {'projection': 'WGS 84 EPSG:4326', 'northlimit': 41.87,
                         'southlimit': 41.863,
                         'eastlimit': -111.505,
                         'westlimit': -111.511, 'units': 'meters'}
        # create spatial coverage
        netcdf_logical_file.metadata.create_element('Coverage', type="box", value=coverage_data)
        spatial_coverage = netcdf_logical_file.metadata.spatial_coverage
        self.assertEqual(float(spatial_coverage.value['northlimit']), 41.87)

        # test spatial coverage can't be updated when there is spatial reference coverage (original coverage)
        self.assertNotEqual(netcdf_logical_file.metadata.original_coverage, None)
        coverage_data = {'projection': 'WGS 84 EPSG:4326', 'northlimit': 41.87706,
                         'southlimit': 41.863,
                         'eastlimit': -111.505,
                         'westlimit': -111.511, 'units': 'meters'}

        with self.assertRaises(ValidationError):
            netcdf_logical_file.metadata.update_element('Coverage', element_id=spatial_coverage.id,
                                                        type="box", value=coverage_data)
        # create Variable element
        self.assertEqual(netcdf_logical_file.metadata.variables.count(), 2)
        variable_data = {'name': 'variable_name', 'type': 'Int', 'unit': 'deg F',
                         'shape': 'variable_shape'}
        netcdf_logical_file.metadata.create_element('Variable', **variable_data)
        self.assertEqual(netcdf_logical_file.metadata.variables.count(), 3)
        variable_names = [variable.name for variable in netcdf_logical_file.metadata.variables.all()]
        self.assertIn('variable_name', variable_names)
        # test that multiple Variable elements can be created
        variable_data = {'name': 'variable_name_2', 'type': 'Int', 'unit': 'deg F',
                         'shape': 'variable_shape_2'}
        netcdf_logical_file.metadata.create_element('Variable', **variable_data)
        self.assertEqual(netcdf_logical_file.metadata.variables.count(), 4)

        # test update Variable element
        variable = netcdf_logical_file.metadata.variables.first()
        variable_data = {'name': 'variable_name_updated', 'type': 'Int', 'unit': 'deg F',
                         'shape': 'variable_shape'}
        netcdf_logical_file.metadata.update_element('Variable', variable.id, **variable_data)
        variable = netcdf_logical_file.metadata.variables.get(id=variable.id)
        self.assertEqual(variable.name, 'variable_name_updated')
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_coverage_editing(self):
        """
        Here we are using a valid nc file for setting it
        to NetCDF file type which includes metadata extraction
        The nc file in this case is at the root of the folder hierarchy
        The file used here for creating a netcdf aggregation has spatial reference and spatial coverage
        gets computed from spatial reference
        Here we are testing that coverage can't be updated.
        """

        self.create_composite_resource(self.netcdf_file)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no NetCDFLogicalFile object
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        base_file_name, _ = os.path.splitext(res_file.file_name)
        expected_res_file_folder_path = res_file.file_folder
        # set the nc file to NetCDF file type
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # test extracted metadata
        assert_netcdf_file_type_metadata(self, self.res_title,
                                         aggr_folder=expected_res_file_folder_path)
        # test editing of coverage
        netcdf_logical_file = NetCDFLogicalFile.objects.first()
        self.assertNotEqual(netcdf_logical_file.metadata.original_coverage, None)
        self.assertNotEqual(netcdf_logical_file.metadata.spatial_coverage, None)
        # test that original coverage can't be updated
        orig_coverage = netcdf_logical_file.metadata.original_coverage
        coverage_data = {'northlimit': 111.333, 'southlimit': 42.678, 'eastlimit': 123.789,
                         'westlimit': 40.789, 'units': 'meters'}
        with self.assertRaises(ValidationError):
            netcdf_logical_file.metadata.update_element('OriginalCoverage', orig_coverage.id,
                                                        value=coverage_data)
        # test that spatial coverage can't be updated
        spatial_coverage = netcdf_logical_file.metadata.spatial_coverage
        coverage_data = {'projection': 'WGS 84 EPSG:4326', 'northlimit': 41.87706,
                         'southlimit': 41.863,
                         'eastlimit': -111.505,
                         'westlimit': -111.511, 'units': 'meters'}

        with self.assertRaises(ValidationError):
            netcdf_logical_file.metadata.update_element('Coverage', element_id=spatial_coverage.id,
                                                        type="box", value=coverage_data)

    def test_aggregation_metadata_on_logical_file_delete(self):
        # test that when the NetCDFLogicalFile instance is deleted
        # all metadata associated with it also get deleted

        self.create_composite_resource(self.netcdf_file)
        res_file = self.composite_resource.files.first()

        # extract metadata from the tif file
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test that we have one logical file of type NetCDFLogicalFile as a result
        # of metadata extraction
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        self.assertEqual(NetCDFFileMetaData.objects.count(), 1)

        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # test that we have the metadata elements
        # there should be 4 Coverage objects - 2 at the resource level and
        # the other 2 at the file type level
        self.assertEqual(Coverage.objects.count(), 4)
        self.assertEqual(self.composite_resource.metadata.coverages.all().count(), 2)
        self.assertEqual(logical_file.metadata.coverages.all().count(), 2)
        self.assertEqual(OriginalCoverage.objects.count(), 1)
        self.assertNotEqual(logical_file.metadata.originalCoverage, None)
        self.assertEqual(Variable.objects.count(), 5)
        self.assertEqual(logical_file.metadata.variables.all().count(), 5)

        # test the metadata for the aggregation is in dirty state
        self.assertTrue(logical_file.metadata.is_dirty)
        # test that the update file (.nc file) state is false
        self.assertFalse(logical_file.metadata.is_update_file)

        # delete the logical file
        logical_file.logical_delete(self.user)
        # test that we have no logical file of type NetCDFLogicalFile
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        self.assertEqual(NetCDFFileMetaData.objects.count(), 0)

        # test that all metadata deleted - there should be 2 resource level coverages
        self.assertEqual(self.composite_resource.metadata.coverages.all().count(), 2)
        self.assertEqual(Coverage.objects.count(), 2)
        self.assertEqual(OriginalCoverage.objects.count(), 0)
        self.assertEqual(Variable.objects.count(), 0)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_remove_aggregation(self):
        # test that when an instance NetCDFLogicalFile Type (aggregation) is deleted
        # all resource files associated with that aggregation is not deleted but the associated
        # metadata is deleted

        self.create_composite_resource(self.netcdf_file)
        nc_res_file = self.composite_resource.files.first()
        base_file_name, _ = os.path.splitext(nc_res_file.file_name)
        expected_folder_name = nc_res_file.file_folder

        # set the nc file to NetCDFLogicalFile aggregation
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, nc_res_file.id)

        # test that we have one logical file (aggregation) of type NetCDFLogicalFile
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        self.assertEqual(NetCDFFileMetaData.objects.count(), 1)
        logical_file = NetCDFLogicalFile.objects.first()
        self.assertEqual(logical_file.files.all().count(), 2)
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        self.assertEqual(set(self.composite_resource.files.all()),
                         set(logical_file.files.all()))

        # delete the aggregation (logical file) object using the remove_aggregation function
        # this should delete the system generated txt file when the netcdf logical file was created
        logical_file.remove_aggregation()
        # test there is no NetCDFLogicalFile object
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        # test there is no NetCDFFileMetaData object
        self.assertEqual(NetCDFFileMetaData.objects.count(), 0)
        # check the files associated with the aggregation not deleted
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        # check the file folder is not deleted
        nc_file = self.composite_resource.files.first()
        self.assertTrue(nc_file.file_name.endswith('.nc'))
        self.assertEqual(nc_file.file_folder, expected_folder_name)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_aggregation_metadata_on_resource_delete(self):
        # test that when the composite resource is deleted
        # all metadata associated with NetCDFLogicalFile Type is deleted

        self.create_composite_resource(self.netcdf_file)
        res_file = self.composite_resource.files.first()

        # extract metadata from the tif file
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test that we have one logical file of type NetCDFLogicalFile as a result
        # of metadata extraction
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        self.assertEqual(NetCDFFileMetaData.objects.count(), 1)

        # test that we have the metadata elements

        # there should be 4 Coverage objects - 2 at the resource level and
        # the other 2 at the file type level
        self.assertEqual(Coverage.objects.count(), 4)
        self.assertEqual(OriginalCoverage.objects.count(), 1)
        self.assertEqual(Variable.objects.count(), 5)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())

        # delete resource
        hydroshare.delete_resource(self.composite_resource.short_id)

        # test that we have no logical file of type NetCDFLogicalFile
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        self.assertEqual(NetCDFFileMetaData.objects.count(), 0)

        # test that all metadata deleted
        self.assertEqual(Coverage.objects.count(), 0)
        self.assertEqual(OriginalCoverage.objects.count(), 0)
        self.assertEqual(Variable.objects.count(), 0)

    def test_aggregation_metadata_on_file_delete(self):
        # test that when any resource file that is part of a NetCDFLogicalFile is deleted
        # all metadata associated with NetCDFLogicalFile is deleted
        # test for both .nc and .txt delete

        # test with deleting of 'nc' file
        self._test_file_metadata_on_file_delete(ext='.nc')

        # test with deleting of 'txt' file
        self._test_file_metadata_on_file_delete(ext='.txt')

    def test_aggregation_folder_delete(self):
        # when  a file is set to NetCDFLogicalFile type
        # system automatically creates folder using the name of the file
        # that was used to set the file type
        # Here we need to test that when that folder gets deleted, all files
        # in that folder gets deleted, the logicalfile object gets deleted and
        # the associated metadata objects get deleted

        self.create_composite_resource()
        new_folder = 'nc_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the nc file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.netcdf_file, upload_folder=new_folder)
        nc_res_file = self.composite_resource.files.first()
        base_file_name, _ = os.path.splitext(nc_res_file.file_name)
        expected_folder_name = nc_res_file.file_folder

        # extract metadata from the tif file
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, nc_res_file.id)

        # test that we have one logical file of type NetCDFLogicalFile as a result
        # of metadata extraction
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        # should have one NetCDFFileMetadata object
        self.assertEqual(NetCDFFileMetaData.objects.count(), 1)

        # there should be 2 content files
        self.assertEqual(self.composite_resource.files.count(), 2)
        # test that there are metadata associated with the logical file
        self.assertEqual(Coverage.objects.count(), 4)
        self.assertEqual(OriginalCoverage.objects.count(), 1)
        self.assertEqual(Variable.objects.count(), 5)

        # delete the folder for the logical file
        folder_path = "data/contents/{}".format(expected_folder_name)
        remove_folder(self.user, self.composite_resource.short_id, folder_path)
        # there should no content files
        self.assertEqual(self.composite_resource.files.count(), 0)

        # there should not be any netCDF logical file or metadata file
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        self.assertEqual(NetCDFFileMetaData.objects.count(), 0)

        # test that all metadata associated with the logical file got deleted - there still be
        # 2 resource level coverages
        self.assertEqual(self.composite_resource.metadata.coverages.all().count(), 2)
        self.assertEqual(Coverage.objects.count(), 2)
        self.assertEqual(OriginalCoverage.objects.count(), 0)
        self.assertEqual(Variable.objects.count(), 0)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_aggregation_file_rename(self):
        # test that a file can't renamed for any resource file
        # that's part of the NetCDF  logical file

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.netcdf_file)
        res_file = self.composite_resource.files.first()
        expected_folder_path = res_file.file_folder
        # create aggregation from the nc file
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # test renaming of files that are associated with aggregation raises exception
        self.assertEqual(self.composite_resource.files.count(), 2)

        for res_file in self.composite_resource.files.all():
            base_file_name, ext = os.path.splitext(res_file.file_name)
            self.assertEqual(res_file.file_folder, expected_folder_path)

            if expected_folder_path:
                src_path = 'data/contents/{0}/{1}'.format(expected_folder_path, res_file.file_name)
            else:
                src_path = 'data/contents/{}'.format(res_file.file_name)

            new_file_name = 'some_netcdf{}'.format(ext)

            self.assertNotEqual(res_file.file_name, new_file_name)
            if expected_folder_path:
                tgt_path = 'data/contents/{}/{}'.format(expected_folder_path, new_file_name)
            else:
                tgt_path = 'data/contents/{}'.format(new_file_name)

            with self.assertRaises(DRF_ValidationError):
                move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                              tgt_path)

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_aggregation_file_move(self):
        # test any resource file that's part of the NetCDF logical file can't be moved

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.netcdf_file)
        nc_res_file = self.composite_resource.files.first()

        # create the aggregation using the nc file
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, nc_res_file.id)
        # test renaming of files that are associated with raster LFO - which should raise exception
        self.assertEqual(self.composite_resource.files.count(), 2)
        res_file = self.composite_resource.files.first()
        expected_folder_path = nc_res_file.file_folder
        self.assertEqual(res_file.file_folder, expected_folder_path)
        new_folder = 'netcdf_aggr'
        ResourceFile.create_folder(self.composite_resource, new_folder)

        # moving any of the resource files to this new folder should raise exception
        tgt_path = 'data/contents/{}'.format(new_folder)
        for res_file in self.composite_resource.files.all():
            with self.assertRaises(DRF_ValidationError):
                src_path = os.path.join('data', 'contents', res_file.short_path)
                move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                              tgt_path)

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_aggregation_folder_rename(self):
        # test changes to aggregation name, aggregation metadata xml file path, and aggregation
        # resource map xml file path on folder (that contains netcdf aggregation) name change

        self.create_composite_resource()
        new_folder = 'netcdf_aggr'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the nc file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.netcdf_file, upload_folder=new_folder)
        nc_res_file = self.composite_resource.files.first()
        expected_folder_path = nc_res_file.file_folder

        # create aggregation from the nc file
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, nc_res_file.id)

        self.assertEqual(self.composite_resource.files.count(), 2)

        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, expected_folder_path)

        # test aggregation name
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.aggregation_name, nc_res_file.short_path)

        # test aggregation xml file paths
        nc_file_path = get_path_with_no_file_extension(nc_res_file.short_path)
        expected_meta_file_path = '{0}{1}'.format(nc_file_path, AggregationMetaFilePath.METADATA_FILE_ENDSWITH)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_file_path)

        expected_map_file_path = '{0}{1}'.format(nc_file_path, AggregationMetaFilePath.RESMAP_FILE_ENDSWITH)
        self.assertEqual(logical_file.map_short_file_path, expected_map_file_path)

        # test renaming folder
        src_path = 'data/contents/{}'.format(expected_folder_path)
        tgt_path = 'data/contents/{}_1'.format(expected_folder_path)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, '{}_1'.format(expected_folder_path))

        # test aggregation name update
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        nc_res_file.refresh_from_db()
        self.assertEqual(logical_file.aggregation_name, nc_res_file.short_path)

        # test aggregation xml file paths
        nc_file_path = get_path_with_no_file_extension(nc_res_file.short_path)
        expected_meta_file_path = '{0}{1}'.format(nc_file_path, AggregationMetaFilePath.METADATA_FILE_ENDSWITH)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_file_path)

        expected_map_file_path = '{0}{1}'.format(nc_file_path, AggregationMetaFilePath.RESMAP_FILE_ENDSWITH)
        self.assertEqual(logical_file.map_short_file_path, expected_map_file_path)

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_aggregation_parent_folder_rename(self):
        # test changes to aggregation name, aggregation metadata xml file path, and aggregation
        # resource map xml file path on aggregation folder parent folder name change

        self.create_composite_resource()
        new_folder = 'netcdf_aggr'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the nc file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.netcdf_file, upload_folder=new_folder)
        nc_res_file = self.composite_resource.files.first()
        aggregation_folder_name = new_folder

        # create aggregation from the nc file
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, nc_res_file.id)
        # test renaming of files that are associated with aggregation raises exception
        self.assertEqual(self.composite_resource.files.count(), 2)

        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, aggregation_folder_name)

        # test aggregation name
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.aggregation_name, nc_res_file.short_path)

        # test aggregation xml file paths
        nc_file_path = get_path_with_no_file_extension(nc_res_file.short_path)
        expected_meta_file_path = '{0}{1}'.format(nc_file_path, AggregationMetaFilePath.METADATA_FILE_ENDSWITH)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_file_path)

        expected_map_file_path = '{0}{1}'.format(nc_file_path, AggregationMetaFilePath.RESMAP_FILE_ENDSWITH)
        self.assertEqual(logical_file.map_short_file_path, expected_map_file_path)

        # create a folder to be the parent folder of the aggregation folder
        parent_folder = 'parent_folder'
        ResourceFile.create_folder(self.composite_resource, parent_folder)
        # move the aggregation folder to the parent folder
        src_path = 'data/contents/{}'.format(aggregation_folder_name)
        tgt_path = 'data/contents/{0}/{1}'.format(parent_folder, aggregation_folder_name)

        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        file_folder = '{}/{}'.format(parent_folder, aggregation_folder_name)
        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, file_folder)

        # renaming parent folder
        parent_folder_rename = 'parent_folder_1'
        src_path = 'data/contents/{}'.format(parent_folder)
        tgt_path = 'data/contents/{}'.format(parent_folder_rename)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        file_folder = '{}/{}'.format(parent_folder_rename, aggregation_folder_name)
        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, file_folder)

        # test aggregation name after folder rename
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        nc_res_file.refresh_from_db()
        self.assertEqual(logical_file.aggregation_name, nc_res_file.short_path)

        # test aggregation xml file paths after folder rename
        nc_file_path = get_path_with_no_file_extension(nc_res_file.short_path)
        expected_meta_file_path = '{0}{1}'.format(nc_file_path, AggregationMetaFilePath.METADATA_FILE_ENDSWITH)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_file_path)
        expected_map_file_path = '{0}{1}'.format(nc_file_path, AggregationMetaFilePath.RESMAP_FILE_ENDSWITH)
        self.assertEqual(logical_file.map_short_file_path, expected_map_file_path)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_aggregation_folder_move_1(self):
        # test changes to aggregation name, aggregation metadata xml file path, and aggregation
        # resource map xml file path on moving a folder that contains netcdf aggregation

        self.create_composite_resource()
        new_folder = 'netcdf_aggr'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the nc file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.netcdf_file, upload_folder=new_folder)
        nc_res_file = self.composite_resource.files.first()
        aggregation_folder_name = nc_res_file.file_folder

        # create aggregation from the nc file
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, nc_res_file.id)

        self.assertEqual(self.composite_resource.files.count(), 2)

        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, aggregation_folder_name)

        # create a folder to move the aggregation folder there
        parent_folder = 'parent_folder'
        ResourceFile.create_folder(self.composite_resource, parent_folder)
        # move the aggregation folder to the parent folder
        src_path = 'data/contents/{}'.format(aggregation_folder_name)
        tgt_path = 'data/contents/{0}/{1}'.format(parent_folder, aggregation_folder_name)

        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        file_folder = '{0}/{1}'.format(parent_folder, aggregation_folder_name)
        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, file_folder)

        # test aggregation name update
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        nc_res_file.refresh_from_db()
        self.assertEqual(logical_file.aggregation_name, nc_res_file.short_path)

        # test aggregation xml file paths
        nc_file_path = get_path_with_no_file_extension(nc_res_file.short_path)
        expected_meta_file_path = '{0}{1}'.format(nc_file_path, AggregationMetaFilePath.METADATA_FILE_ENDSWITH)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_file_path)

        expected_map_file_path = '{0}{1}'.format(nc_file_path, AggregationMetaFilePath.RESMAP_FILE_ENDSWITH)
        self.assertEqual(logical_file.map_short_file_path, expected_map_file_path)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_aggregation_folder_move_2(self):
        # test a folder can be moved into a folder that contains a netcdf aggregation

        self.create_composite_resource()
        new_folder = 'netcdf_aggr'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the nc file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.netcdf_file, upload_folder=new_folder)
        nc_res_file = self.composite_resource.files.first()
        aggregation_folder_name = new_folder

        # create aggregation from the nc file
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, nc_res_file.id)
        # create a folder to move into the aggregation folder
        folder_to_move = 'folder_to_move'
        ResourceFile.create_folder(self.composite_resource, folder_to_move)
        # move the folder_to_move into the aggregation folder
        src_path = 'data/contents/{}'.format(folder_to_move)
        tgt_path = 'data/contents/{}'.format(aggregation_folder_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_aggregation_folder_sub_folder_creation(self):
        # test a folder can be created inside a folder that contains a netcdf aggregation

        self.create_composite_resource()
        new_folder = 'netcdf_aggr'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the nc file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.netcdf_file, upload_folder=new_folder)
        nc_res_file = self.composite_resource.files.first()
        self.assertEqual(nc_res_file.file_folder, new_folder)

        # create aggregation from the nc file
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, nc_res_file.id)
        res_file = self.composite_resource.files.first()
        self.assertNotEqual(res_file.file_folder, None)
        # create a folder inside the aggregation folder
        new_folder = '{}/sub_folder'.format(res_file.file_folder)
        ResourceFile.create_folder(self.composite_resource, new_folder)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_file_move_to_aggregation_folder_allowed(self):
        # test a file can be moved into a folder that contains a netcdf aggregation

        self.create_composite_resource()
        new_folder = 'netcdf_aggr'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the nc file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.netcdf_file, upload_folder=new_folder)
        nc_res_file = self.composite_resource.files.first()
        self.assertEqual(nc_res_file.file_folder, new_folder)

        # create aggregation from the nc file
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, nc_res_file.id)
        res_file = self.composite_resource.files.first()
        self.assertNotEqual(res_file.file_folder, '')

        # add a file to the resource which will try to move into the aggregation folder
        res_file_to_move = self.add_file_to_resource(file_to_add=self.netcdf_invalid_file)
        src_path = os.path.join('data', 'contents', res_file_to_move.short_path)
        tgt_path = 'data/contents/{}'.format(res_file.file_folder)

        # move file to aggregation folder
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_upload_file_to_aggregation_folder_allowed(self):
        # test no file can be uploaded into a folder that represents an aggregation

        self.create_composite_resource()
        new_folder = 'netcdf_aggr'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the nc file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.netcdf_file, upload_folder=new_folder)
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.file_folder, new_folder)

        # create aggregation from the nc file
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()
        self.assertNotEqual(res_file.file_folder, '')

        # add a file to the resource at the aggregation folder
        self.add_file_to_resource(file_to_add=self.netcdf_invalid_file,
                                  upload_folder=res_file.file_folder)

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def _test_invalid_file(self):
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # trying to set this invalid tif file to NetCDF file type should raise
        # ValidationError
        with self.assertRaises(ValidationError):
            NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        # test that the invalid file did not get deleted
        self.assertEqual(self.composite_resource.files.all().count(), 1)

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

    def _test_file_metadata_on_file_delete(self, ext):

        self.create_composite_resource(self.netcdf_file)
        res_file = self.composite_resource.files.first()

        # extract metadata from the tif file
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test that we have one logical file of type NetCDFLogicalFile
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        self.assertEqual(NetCDFFileMetaData.objects.count(), 1)

        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # there should be 2 coverage elements - one spatial and the other one temporal
        self.assertEqual(logical_file.metadata.coverages.all().count(), 2)
        self.assertNotEqual(logical_file.metadata.spatial_coverage, None)
        self.assertNotEqual(logical_file.metadata.temporal_coverage, None)

        # there should be one original coverage
        self.assertNotEqual(logical_file.metadata.originalCoverage, None)
        # testing additional metadata element: variables
        self.assertEqual(logical_file.metadata.variables.all().count(), 5)

        # there should be 4 coverage objects - 2 at the resource level
        # and the other 2 at the file type level
        self.assertEqual(Coverage.objects.count(), 4)
        self.assertEqual(OriginalCoverage.objects.count(), 1)
        self.assertEqual(Variable.objects.count(), 5)

        # delete content file specified by extension (ext parameter)
        res_file = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, ext)[0]
        hydroshare.delete_resource_file(self.composite_resource.short_id,
                                        res_file.id,
                                        self.user)
        # test that we don't have logical file of type NetCDFLogicalFile Type
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        self.assertEqual(NetCDFFileMetaData.objects.count(), 0)

        # test that all metadata deleted - there should be still 2 resource level coverages
        self.assertEqual(self.composite_resource.metadata.coverages.all().count(), 2)
        self.assertEqual(Coverage.objects.count(), 2)
        self.assertEqual(OriginalCoverage.objects.count(), 0)
        self.assertEqual(Variable.objects.count(), 0)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_main_file(self):
        self.create_composite_resource(self.netcdf_file)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.has_logical_file, False)
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        self.assertEqual(1, NetCDFLogicalFile.objects.count())
        self.assertEqual(".nc", NetCDFLogicalFile.objects.first().get_main_file_type())
        self.assertEqual(self.netcdf_file_name,
                         NetCDFLogicalFile.objects.first().get_main_file.file_name)

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
