import os
import tempfile
import shutil

from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError

from rest_framework.exceptions import ValidationError as DRF_ValidationError

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.models import Coverage
from hs_core.hydroshare.utils import resource_post_create_actions
from hs_core.views.utils import remove_folder, move_or_rename_file_or_folder

from hs_app_netCDF.models import OriginalCoverage, Variable
from hs_file_types.models import NetCDFLogicalFile, NetCDFFileMetaData, GenericLogicalFile
from utils import assert_netcdf_file_type_metadata


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
            title='Test NetCDF File Type Metadata'
        )

        self.temp_dir = tempfile.mkdtemp()
        self.netcdf_file_name = 'netcdf_valid.nc'
        self.netcdf_file = 'hs_file_types/tests/{}'.format(self.netcdf_file_name)

        target_temp_netcdf_file = os.path.join(self.temp_dir, self.netcdf_file_name)
        shutil.copy(self.netcdf_file, target_temp_netcdf_file)
        self.netcdf_file_obj = open(target_temp_netcdf_file, 'r')

        self.netcdf_invalid_file_name = 'netcdf_invalid.nc'
        self.netcdf_invalid_file = 'hs_file_types/tests/{}'.format(self.netcdf_invalid_file_name)

        target_temp_netcdf_invalid_file = os.path.join(self.temp_dir, self.netcdf_invalid_file_name)
        shutil.copy(self.netcdf_invalid_file, target_temp_netcdf_invalid_file)

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

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no NetCDFLogicalFile object
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)

        # set the nc file to NetCDF file type
        NetCDFLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        # test extracted metadata
        res_title = 'Test NetCDF File Type Metadata'
        assert_netcdf_file_type_metadata(self, res_title)
        # test file level keywords
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(len(logical_file.metadata.keywords), 1)
        self.assertEqual(logical_file.metadata.keywords[0], 'Snow water equivalent')
        self.composite_resource.delete()

    def test_set_file_type_to_netcdf_resource_title(self):
        # here we are using a valid nc file for setting it
        # to NetCDF file type which includes metadata extraction
        # and testing that the resource title gets set with the
        # extracted metadata if the original title is 'untitled resource'

        self.netcdf_file_obj = open(self.netcdf_file, 'r')
        self._create_composite_resource(title='untitled resource')

        self.assertEqual(self.composite_resource.metadata.title.value, 'untitled resource')
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no NetCDFLogicalFile object
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)

        # set the nc file to NetCDF file type
        NetCDFLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        # test resource title was updated with the extracted netcdf data
        res_title = "Snow water equivalent estimation at TWDEF site from Oct 2009 to June 2010"
        self.assertEqual(self.composite_resource.metadata.title.value, res_title)

        self.composite_resource.delete()

    def test_set_file_type_to_necdf_invalid_file(self):
        # here we are using an invalid netcdf file for setting it
        # to netCDF file type which should fail
        self.netcdf_file_obj = open(self.netcdf_invalid_file, 'r')
        self._create_composite_resource()
        self._test_invalid_file()
        self.composite_resource.delete()

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
        netcdf_logical_file.add_resource_file(res_file)

        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.logical_file_type_name, 'NetCDFLogicalFile')
        self.assertEqual(netcdf_logical_file.files.count(), 1)

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
        coverage_data = {'northlimit': '121.345', 'southlimit': '42.678', 'eastlimit': '123.789',
                         'westlimit': '40.789', 'units': 'meters'}
        netcdf_logical_file.metadata.create_element('OriginalCoverage', value=coverage_data)
        self.assertNotEqual(netcdf_logical_file.metadata.original_coverage, None)
        self.assertEqual(netcdf_logical_file.metadata.original_coverage.value['northlimit'],
                         '121.345')

        # test updating OriginalCoverage element
        orig_coverage = netcdf_logical_file.metadata.original_coverage
        coverage_data = {'northlimit': '111.333', 'southlimit': '42.678', 'eastlimit': '123.789',
                         'westlimit': '40.789', 'units': 'meters'}
        netcdf_logical_file.metadata.update_element('OriginalCoverage', orig_coverage.id,
                                                    value=coverage_data)
        self.assertEqual(netcdf_logical_file.metadata.original_coverage.value['northlimit'],
                         '111.333')

        # trying to create a 2nd OriginalCoverage element should raise exception
        with self.assertRaises(Exception):
            netcdf_logical_file.metadata.create_element('OriginalCoverage', value=coverage_data)

        # trying to update bounding box values with non-numeric values
        # (e.g., 'north_limit' key with a non-numeric value) should raise exception
        coverage_data = {'northlimit': '121.345a', 'southlimit': '42.678', 'eastlimit': '123.789',
                         'westlimit': '40.789', 'units': 'meters'}
        with self.assertRaises(ValidationError):
            netcdf_logical_file.metadata.update_element('OriginalCoverage', orig_coverage.id,
                                                        value=coverage_data)
        # test creating spatial coverage
        # there should not be any spatial coverage for the netcdf file type
        self.assertEqual(netcdf_logical_file.metadata.spatial_coverage, None)
        coverage_data = {'projection': 'WGS 84 EPSG:4326', 'northlimit': '41.87',
                         'southlimit': '41.863',
                         'eastlimit': '-111.505',
                         'westlimit': '-111.511', 'units': 'meters'}
        # create spatial coverage
        netcdf_logical_file.metadata.create_element('Coverage', type="box", value=coverage_data)
        spatial_coverage = netcdf_logical_file.metadata.spatial_coverage
        self.assertEqual(spatial_coverage.value['northlimit'], 41.87)

        # test updating spatial coverage
        coverage_data = {'projection': 'WGS 84 EPSG:4326', 'northlimit': '41.87706',
                         'southlimit': '41.863',
                         'eastlimit': '-111.505',
                         'westlimit': '-111.511', 'units': 'meters'}
        netcdf_logical_file.metadata.update_element('Coverage', element_id=spatial_coverage.id,
                                                    type="box", value=coverage_data)
        spatial_coverage = netcdf_logical_file.metadata.spatial_coverage
        self.assertEqual(spatial_coverage.value['northlimit'], 41.87706)

        # create Variable element
        self.assertEqual(netcdf_logical_file.metadata.variables.count(), 0)
        variable_data = {'name': 'variable_name', 'type': 'Int', 'unit': 'deg F',
                         'shape': 'variable_shape'}
        netcdf_logical_file.metadata.create_element('Variable', **variable_data)
        self.assertEqual(netcdf_logical_file.metadata.variables.count(), 1)
        self.assertEqual(netcdf_logical_file.metadata.variables.first().name, 'variable_name')

        # test that multiple Variable elements can be created
        variable_data = {'name': 'variable_name_2', 'type': 'Int', 'unit': 'deg F',
                         'shape': 'variable_shape_2'}
        netcdf_logical_file.metadata.create_element('Variable', **variable_data)
        self.assertEqual(netcdf_logical_file.metadata.variables.count(), 2)

        # test update Variable element
        variable = netcdf_logical_file.metadata.variables.first()
        variable_data = {'name': 'variable_name_updated', 'type': 'Int', 'unit': 'deg F',
                         'shape': 'variable_shape'}
        netcdf_logical_file.metadata.update_element('Variable', variable.id, **variable_data)
        variable = netcdf_logical_file.metadata.variables.get(id=variable.id)
        self.assertEqual(variable.name, 'variable_name_updated')

        self.composite_resource.delete()

    def test_file_metadata_on_logical_file_delete(self):
        # test that when the NetCDFLogicalFile instance is deleted
        # all metadata associated with it also get deleted
        self.netcdf_file_obj = open(self.netcdf_file, 'r')
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()

        # extract metadata from the tif file
        NetCDFLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)

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

        self.composite_resource.delete()

    def test_remove_aggregation(self):
        # test that when an instance NetCDFLogicalFile Type (aggregation) is deleted
        # all resource files associated with that aggregation is not deleted but the associated
        # metadata is deleted
        self.netcdf_file_obj = open(self.netcdf_file, 'r')
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()

        # set the nc file to NetCDFLogicalFile aggregation
        NetCDFLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)

        # test that we have one logical file (aggregation) of type NetCDFLogicalFile
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        self.assertEqual(NetCDFFileMetaData.objects.count(), 1)
        logical_file = NetCDFLogicalFile.objects.first()
        self.assertEqual(logical_file.files.all().count(), 2)
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        self.assertEqual(set(self.composite_resource.files.all()),
                         set(logical_file.files.all()))

        # delete the aggregation (logical file) object using the remove_aggregation function
        logical_file.remove_aggregation()
        # test there is no NetCDFLogicalFile object
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        # test there is no NetCDFFileMetaData object
        self.assertEqual(NetCDFFileMetaData.objects.count(), 0)
        # check the files associated with the aggregation not deleted
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        # check the file folder is not deleted
        for f in self.composite_resource.files.all():
            self.assertEqual(f.file_folder, 'netcdf_valid')
        self.composite_resource.delete()

    def test_file_metadata_on_resource_delete(self):
        # test that when the composite resource is deleted
        # all metadata associated with NetCDFFileType is deleted
        self.netcdf_file_obj = open(self.netcdf_file, 'r')
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()

        # extract metadata from the tif file
        NetCDFLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)

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

        # delete resource
        hydroshare.delete_resource(self.composite_resource.short_id)

        # test that we have no logical file of type NetCDFLogicalFile
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        self.assertEqual(NetCDFFileMetaData.objects.count(), 0)

        # test that all metadata deleted
        self.assertEqual(Coverage.objects.count(), 0)
        self.assertEqual(OriginalCoverage.objects.count(), 0)
        self.assertEqual(Variable.objects.count(), 0)

    def test_file_metadata_on_file_delete(self):
        # test that when any file in NetCDFLogicalFile is deleted
        # all metadata associated with NetCDFLogicalFile is deleted
        # test for both .nc and .txt delete

        # test with deleting of 'nc' file
        self._test_file_metadata_on_file_delete(ext='.nc')

        # test with deleting of 'txt' file
        self._test_file_metadata_on_file_delete(ext='.txt')

    def test_netcdf_file_type_folder_delete(self):
        # when  a file is set to NetCDFLogicalFile type
        # system automatically creates folder using the name of the file
        # that was used to set the file type
        # Here we need to test that when that folder gets deleted, all files
        # in that folder gets deleted, the logicalfile object gets deleted and
        # the associated metadata objects get deleted
        self.netcdf_file_obj = open(self.netcdf_file, 'r')
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()

        # extract metadata from the tif file
        NetCDFLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)

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
        folder_path = "data/contents/netcdf_valid"
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

        self.composite_resource.delete()

    def test_file_rename_or_move(self):
        # test that file can't be moved or renamed for any resource file
        # that's part of the NetCDF logical file object (LFO)

        self.netcdf_file_obj = open(self.netcdf_file, 'r')
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()

        # extract metadata from the tif file
        NetCDFLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        # test renaming of files that are associated with netcdf LFO - which should raise exception
        self.assertEqual(self.composite_resource.files.count(), 2)
        src_path = 'data/contents/netcdf_valid/netcdf_valid.nc'
        tgt_path = "data/contents/netcdf_valid/netcdf_valid_1.nc"
        with self.assertRaises(DRF_ValidationError):
            move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                          tgt_path)
        src_path = 'data/contents/netcdf_valid/netcdf_valid_header_info.txt'
        tgt_path = 'data/contents/netcdf_valid/netcdf_valid_header_info_1.txt'
        with self.assertRaises(DRF_ValidationError):
            move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                          tgt_path)
        # test moving the files associated with netcdf LFO
        src_path = 'data/contents/netcdf_valid/netcdf_valid.nc'
        tgt_path = 'data/contents/netcdf_valid_1/netcdf_valid.nc'
        with self.assertRaises(DRF_ValidationError):
            move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                          tgt_path)
        src_path = 'data/contents/netcdf_valid/netcdf_valid_header_info.txt'
        tgt_path = 'data/contents/netcdf_valid_1/netcdf_valid_header_info.txt'
        with self.assertRaises(DRF_ValidationError):
            move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                          tgt_path)

        self.composite_resource.delete()

    def _create_composite_resource(self, title='Test NetCDF File Type Metadata'):
        uploaded_file = UploadedFile(file=self.netcdf_file_obj,
                                     name=os.path.basename(self.netcdf_file_obj.name))
        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title=title,
            files=(uploaded_file,)
        )

        # set the generic logical file as part of resource post create signal
        resource_post_create_actions(resource=self.composite_resource, user=self.user,
                                     metadata=self.composite_resource.metadata)

    def _test_invalid_file(self):
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # trying to set this invalid tif file to NetCDF file type should raise
        # ValidationError
        with self.assertRaises(ValidationError):
            NetCDFLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)

        # test that the invalid file did not get deleted
        self.assertEqual(self.composite_resource.files.all().count(), 1)

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

    def _test_file_metadata_on_file_delete(self, ext):
        self.netcdf_file_obj = open(self.netcdf_file, 'r')
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()

        # extract metadata from the tif file
        NetCDFLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)

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
        # testing extended metadata element: variables
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
        self.assertEqual (self.composite_resource.metadata.coverages.all().count(), 2)
        self.assertEqual(Coverage.objects.count(), 2)
        self.assertEqual(OriginalCoverage.objects.count(), 0)
        self.assertEqual(Variable.objects.count(), 0)

        self.composite_resource.delete()
