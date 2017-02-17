import os
import tempfile
import shutil
from dateutil import parser

from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import UploadedFile

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.hydroshare.utils import resource_post_create_actions

from hs_file_types.models import NetCDFLogicalFile, NetCDFFileMetaData, GenericLogicalFile


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

        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
        # check that there is one GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

        # check that there is no NetCDFLogicalFile object
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)

        # set the nc file to NetCDF file type
        NetCDFLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        # check that there is one BaseLogicalFile object
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        # check that there is no GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

        # There should be now 2 files
        self.assertEqual(self.composite_resource.files.count(), 2)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        # logical file should be associated with 2 files
        self.assertEqual(logical_file.files.all().count(), 2)
        file_extensions = set([f.extension for f in logical_file.files.all()])
        self.assertIn('.nc', file_extensions)
        self.assertIn('.txt', file_extensions)

        # test extracted netcdf file type metadata
        self._test_netcdf_metadata_extraction()

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

        # trying to update 'north_limit' key with a non-numeric value should raise exception
        coverage_data = {'northlimit': '121.345a', 'southlimit': '42.678', 'eastlimit': '123.789',
                         'westlimit': '40.789', 'units': 'meters'}

        # ToDO: modify the create() and update() of OriginalCoverage to check for numerical values
        # of the bounding box limits then uncomment the following test
        # with self.assertRaises(Exception):
        #     netcdf_logical_file.metadata.update_element('OriginalCoverage', orig_coverage.id,
        #                                                 value=coverage_data)

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

    def _create_composite_resource(self):
        uploaded_file = UploadedFile(file=self.netcdf_file_obj,
                                     name=os.path.basename(self.netcdf_file_obj.name))
        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test NetCDF File Type Metadata',
            files=(uploaded_file,)
        )

        # set the generic logical file as part of resource post create signal
        resource_post_create_actions(resource=self.composite_resource, user=self.user,
                                     metadata=self.composite_resource.metadata)

    def _test_netcdf_metadata_extraction(self):

        # there should 2 content file
        self.assertEqual(self.composite_resource.files.all().count(), 2)

        # test core metadata after metadata extraction
        title = "Test NetCDF File Type Metadata"
        self.assertEqual(self.composite_resource.metadata.title.value, title)

        # there should be an abstract element
        self.assertNotEqual(self.composite_resource.metadata.description, None)
        extracted_abstract = "This netCDF data is the simulation output from Utah Energy " \
                             "Balance (UEB) model.It includes the simulation result " \
                             "of snow water equivalent during the period " \
                             "Oct. 2009 to June 2010 for TWDEF site in Utah."
        self.assertEqual(self.composite_resource.metadata.description.abstract, extracted_abstract)

        # there should be one source element
        self.assertEqual(self.composite_resource.metadata.sources.all().count(), 1)

        # there should be one license element:
        self.assertNotEquals(self.composite_resource.metadata.rights.statement, 1)

        # there should be one relation element
        self.assertEqual(self.composite_resource.metadata.relations.all().filter(type='cites').
                         count(), 1)

        # there should be 2 creator
        self.assertEqual(self.composite_resource.metadata.creators.all().count(), 2)

        # there should be one contributor
        self.assertEqual(self.composite_resource.metadata.contributors.all().count(), 1)

        # there should be 2 coverage element - box type and period type
        self.assertEqual(self.composite_resource.metadata.coverages.all().count(), 2)
        self.assertEqual(self.composite_resource.metadata.coverages.all().filter(type='box').
                         count(), 1)
        self.assertEqual(self.composite_resource.metadata.coverages.all().filter(type='period').
                         count(), 1)

        box_coverage = self.composite_resource.metadata.coverages.all().filter(type='box').first()
        self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(box_coverage.value['northlimit'], 41.867126409)
        self.assertEqual(box_coverage.value['eastlimit'], -111.505940368)
        self.assertEqual(box_coverage.value['southlimit'], 41.8639080745)
        self.assertEqual(box_coverage.value['westlimit'], -111.51138808)

        temporal_coverage = self.composite_resource.metadata.coverages.all().filter(
            type='period').first()
        self.assertEqual(parser.parse(temporal_coverage.value['start']).date(),
                         parser.parse('10/01/2009').date())
        self.assertEqual(parser.parse(temporal_coverage.value['end']).date(),
                         parser.parse('05/30/2010').date())

        # there should be 2 format elements
        self.assertEqual(self.composite_resource.metadata.formats.all().count(), 2)
        self.assertEqual(self.composite_resource.metadata.formats.all().
                         filter(value='text/plain').count(), 1)
        self.assertEqual(self.composite_resource.metadata.formats.all().
                         filter(value='application/x-netcdf').count(), 1)

        # test file type metadata
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # there should be one subject element
        self.assertEqual(len(logical_file.metadata.keywords), 1)
        subj_element = self.composite_resource.metadata.subjects.all().first()
        self.assertIn('Snow water equivalent', logical_file.metadata.keywords)

        # testing extended metadata element: original coverage
        ori_coverage = logical_file.metadata.originalCoverage
        self.assertNotEquals(ori_coverage, None)
        self.assertEqual(ori_coverage.projection_string_type, 'Proj4 String')
        proj_text = u'+proj=tmerc +y_0=0.0 +k_0=0.9996 +x_0=500000.0 +lat_0=0.0 +lon_0=-111.0'
        self.assertEqual(ori_coverage.projection_string_text, proj_text)
        self.assertEqual(ori_coverage.value['northlimit'], '4.63515e+06')
        self.assertEqual(ori_coverage.value['eastlimit'], '458010.0')
        self.assertEqual(ori_coverage.value['southlimit'], '4.63479e+06')
        self.assertEqual(ori_coverage.value['westlimit'], '457560.0')
        self.assertEqual(ori_coverage.value['units'], 'Meter')
        self.assertEqual(ori_coverage.value['projection'], 'transverse_mercator')

        # testing extended metadata element: variables
        self.assertEqual(logical_file.metadata.variables.all().count(), 5)

        # test time variable
        var_time = logical_file.metadata.variables.all().filter(name='time').first()
        self.assertNotEquals(var_time, None)
        self.assertEqual(var_time.unit, 'hours since 2009-10-1 0:0:00 UTC')
        self.assertEqual(var_time.type, 'Float')
        self.assertEqual(var_time.shape, 'time')
        self.assertEqual(var_time.descriptive_name, 'time')

        # test x variable
        var_x = logical_file.metadata.variables.all().filter(name='x').first()
        self.assertNotEquals(var_x, None)
        self.assertEqual(var_x.unit, 'Meter')
        self.assertEqual(var_x.type, 'Float')
        self.assertEqual(var_x.shape, 'x')
        self.assertEqual(var_x.descriptive_name, 'x coordinate of projection')

        # test y variable
        var_y = logical_file.metadata.variables.all().filter(name='y').first()
        self.assertNotEquals(var_y, None)
        self.assertEqual(var_y.unit, 'Meter')
        self.assertEqual(var_y.type, 'Float')
        self.assertEqual(var_y.shape, 'y')
        self.assertEqual(var_y.descriptive_name, 'y coordinate of projection')

        # test SWE variable
        var_swe = logical_file.metadata.variables.all().filter(name='SWE').first()
        self.assertNotEquals(var_swe, None)
        self.assertEqual(var_swe.unit, 'm')
        self.assertEqual(var_swe.type, 'Float')
        self.assertEqual(var_swe.shape, 'y,x,time')
        self.assertEqual(var_swe.descriptive_name, 'Snow water equivalent')
        self.assertEqual(var_swe.method, 'model simulation of UEB model')
        self.assertEqual(var_swe.missing_value, '-9999')

        # test grid mapping variable
        var_grid = logical_file.metadata.variables.all().\
            filter(name='transverse_mercator').first()
        self.assertNotEquals(var_grid, None)
        self.assertEqual(var_grid.unit, 'Unknown')
        self.assertEqual(var_grid.type, 'Unknown')
        self.assertEqual(var_grid.shape, 'Not defined')
