
import os
import tempfile
import shutil
from dateutil import parser

from xml.etree import ElementTree as ET

from django.test import TransactionTestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.contrib.auth.models import Group
from django.db import IntegrityError

from hs_core import hydroshare
from hs_core.hydroshare import utils
from hs_core.models import CoreMetaData, Creator, Contributor, Coverage, Rights, Title, Language, \
    Publisher, Identifier, Type, Subject, Description, Date, Format, Relation, Source
from hs_core.testing import MockIRODSTestCaseMixin
from hs_app_netCDF.models import NetcdfResource,Variable, OriginalCoverage


class TestNetcdfMetaData(MockIRODSTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(TestNetcdfMetaData, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        self.resNetcdf= hydroshare.create_resource(
            resource_type='NetcdfResource',
            owner=self.user,
            title='Snow water equivalent estimation at TWDEF site from Oct 2009 to June 2010'
        )

        self.temp_dir = tempfile.mkdtemp()
        self.netcdf_file_name = 'netcdf_valid.nc'
        self.netcdf_file = 'hs_app_netCDF/tests/{}'.format(self.netcdf_file_name)
        target_temp_netcdf_file = os.path.join(self.temp_dir, self.netcdf_file_name)
        shutil.copy(self.netcdf_file, target_temp_netcdf_file)
        self.netcdf_file_obj = open(target_temp_netcdf_file, 'r')

        self.temp_dir = tempfile.mkdtemp()
        self.netcdf_file_name_crs = 'netcdf_valid_crs.nc'
        self.netcdf_file_crs = 'hs_app_netCDF/tests/{}'.format(self.netcdf_file_name_crs)
        target_temp_netcdf_file_crs = os.path.join(self.temp_dir, self.netcdf_file_name_crs)
        shutil.copy(self.netcdf_file_crs, target_temp_netcdf_file_crs)
        self.netcdf_file_obj_crs = open(target_temp_netcdf_file_crs, 'r')


        self.netcdf_bad_file_name = 'netcdf_invalid.nc'
        self.netcdf_bad_file = 'hs_app_netCDF/tests/{}'.format(self.netcdf_bad_file_name)
        target_temp_bad_netcdf_file = os.path.join(self.temp_dir, self.netcdf_bad_file_name)
        shutil.copy(self.netcdf_bad_file, target_temp_bad_netcdf_file)
        self.netcdf_bad_file_obj = open(target_temp_bad_netcdf_file, 'r')

        temp_text_file = os.path.join(self.temp_dir, 'netcdf_text.txt')
        text_file = open(temp_text_file, 'w')
        text_file.write("NetCDF records")
        self.text_file_obj = open(temp_text_file, 'r')

    def tearDown(self):
        super(TestNetcdfMetaData, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_allowed_file_types(self):
        # test allowed file type is '.nc'
        self.assertIn('.nc', NetcdfResource.get_supported_upload_file_types())
        self.assertEqual(len(NetcdfResource.get_supported_upload_file_types()), 1)

        # there should not be any content file
        self.assertEqual(self.resNetcdf.files.all().count(), 0)

        # trying to add a text file to this resource should raise exception
        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_pre_process(resource=self.resNetcdf, files=files, user=self.user,
                                                extract_metadata=False)

        # trying to add bad .nc file should raise file validation error
        files = [UploadedFile(file=self.netcdf_bad_file_obj, name=self.netcdf_bad_file_name)]
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_pre_process(resource=self.resNetcdf, files=files, user=self.user,
                                            extract_metadata=False)

        # trying to add valid .nc file should pass the file check
        files = [UploadedFile(file=self.netcdf_file_obj, name=self.netcdf_file_name)]
        utils.resource_file_add_pre_process(resource=self.resNetcdf, files=files, user=self.user,
                                            extract_metadata=False)
        utils.resource_file_add_process(resource=self.resNetcdf, files=files, user=self.user,
                                        extract_metadata=False)

        # there should be 2 content file: with ncdump file created by system
        self.assertEqual(self.resNetcdf.files.all().count(), 2)

        # file pre add process should raise validation error if we try to add a 2nd file when the resource has
        # already 2 content files
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_pre_process(resource=self.resNetcdf, files=files, user=self.user,
                                                extract_metadata=False)

    def test_metadata_extraction_on_resource_creation(self):
        # passing the file object that points to the temp dir doesn't work - create_resource throws error
        # open the file from the fixed file location
        files = [UploadedFile(file=self.netcdf_file_obj, name=self.netcdf_file_name)]
        _, _, metadata, _ = utils.resource_pre_create_actions(resource_type='NetcdfResource',
                                                                          resource_title='Snow water equivalent '
                                                                                         'estimation at TWDEF site '
                                                                                         'from Oct 2009 to June 2010',
                                                                          page_redirect_url_key=None,
                                                                          files=files,
                                                                          metadata=None,)

        self.resNetcdf = hydroshare.create_resource(
            'NetcdfResource',
            self.user,
            'Snow water equivalent estimation at TWDEF site from Oct 2009 to June 2010',
            files=files,
            metadata=metadata
            )

        self._test_metadata_extraction()

    def test_metadata_extraction_on_content_file_add(self):
        # test the core metadata at this point
        self.assertEqual(self.resNetcdf.metadata.title.value, 'Snow water equivalent estimation at TWDEF site from Oct 2009 to June 2010')

        # there shouldn't any abstract element
        self.assertEqual(self.resNetcdf.metadata.description, None)

        # there shouldn't any coverage element
        self.assertEqual(self.resNetcdf.metadata.coverages.all().count(), 0)

        # there shouldn't any format element
        self.assertEqual(self.resNetcdf.metadata.formats.all().count(), 0)

        # there shouldn't any subject element
        self.assertEqual(self.resNetcdf.metadata.subjects.all().count(), 0)

        # there shouldn't any contributor element
        self.assertEqual(self.resNetcdf.metadata.contributors.all().count(), 0)

        # there shouldn't any source element
        self.assertEqual(self.resNetcdf.metadata.sources.all().count(), 0)

        # there shouldn't any relation element
        self.assertEqual(self.resNetcdf.metadata.relations.all().filter(type='cites').count(), 0)

        # there should be 1 creator
        self.assertEqual(self.resNetcdf.metadata.creators.all().count(), 1)

        # there shouldn't any extended metadata
        self.assertEqual(self.resNetcdf.metadata.ori_coverage.all().count(), 0)
        self.assertEqual(self.resNetcdf.metadata.variables.all().count(), 0)

        # adding a valid netcdf file should generate some core metadata and all extended metadata
        files = [UploadedFile(file=self.netcdf_file_obj, name=self.netcdf_file_name)]
        utils.resource_file_add_pre_process(resource=self.resNetcdf, files=files, user=self.user,
                                            extract_metadata=False)
        utils.resource_file_add_process(resource=self.resNetcdf, files=files, user=self.user,
                                        extract_metadata=False)

        self._test_metadata_extraction()

    def test_metadata_on_content_file_delete(self):
        # test that some of the metadata is not deleted on content file deletion
        # adding a valid netcdf file should generate some core metadata and all extended metadata
        files = [UploadedFile(file=self.netcdf_file_obj, name=self.netcdf_file_name)]
        utils.resource_file_add_pre_process(resource=self.resNetcdf, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resNetcdf, files=files, user=self.user,
                                        extract_metadata=True)

        # there should be 1 content files
        self.assertEqual(self.resNetcdf.files.all().count(), 2)

        # there should be 1 format elements
        self.assertEqual(self.resNetcdf.metadata.formats.all().count(), 2)

        # delete content file that we added above
        hydroshare.delete_resource_file(self.resNetcdf.short_id, self.netcdf_file_name, self.user)

        # there should no content file
        self.assertEqual(self.resNetcdf.files.all().count(), 0)

        # there should be a title element
        self.assertNotEquals(self.resNetcdf.metadata.title, None)

        # there should be abstract element
        self.assertNotEquals(self.resNetcdf.metadata.description, None)

        # there should be 2 creator element
        self.assertEqual(self.resNetcdf.metadata.creators.all().count(), 2)

        # there should be 1 contributor element
        self.assertEqual(self.resNetcdf.metadata.contributors.all().count(), 1)

        # there should be no coverage element
        self.assertEqual(self.resNetcdf.metadata.coverages.all().count(), 0)

        # there should be no format element
        self.assertEqual(self.resNetcdf.metadata.formats.all().count(), 0)

        # there should be subject element
        self.assertNotEquals(self.resNetcdf.metadata.subjects.all().count(), 0)

        # testing extended metadata elements
        self.assertEqual(self.resNetcdf.metadata.ori_coverage.all().count(), 0)
        self.assertEqual(self.resNetcdf.metadata.variables.all().count(), 0)

    def test_metadata_delete_on_resource_delete(self):
        # adding a valid netcdf file should generate some core metadata and all extended metadata
        files = [UploadedFile(file=self.netcdf_file_obj, name=self.netcdf_file_name)]
        utils.resource_file_add_pre_process(resource=self.resNetcdf, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resNetcdf, files=files, user=self.user,
                                        extract_metadata=True)

        # before resource delete
        # resource core metadata
        core_metadata_obj = self.resNetcdf.metadata
        self.assertEqual(CoreMetaData.objects.all().count(), 1)
        # there should be Creator metadata objects
        self.assertTrue(Creator.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Contributor metadata objects
        self.assertTrue(Contributor.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Identifier metadata objects
        self.assertTrue(Identifier.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Type metadata objects
        self.assertTrue(Type.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Source metadata objects
        self.assertTrue(Source.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Relation metadata objects
        self.assertTrue(Relation.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Publisher metadata objects
        self.assertFalse(Publisher.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Title metadata objects
        self.assertTrue(Title.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Description (Abstract) metadata objects
        self.assertTrue(Description.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Date metadata objects
        self.assertTrue(Date.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Subject metadata objects
        self.assertTrue(Subject.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Coverage metadata objects
        self.assertTrue(Coverage.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Format metadata objects
        self.assertTrue(Format.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Language metadata objects
        self.assertTrue(Language.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Rights metadata objects
        self.assertTrue(Rights.objects.filter(object_id=core_metadata_obj.id).exists())

        # resource specific metadata
        # there should be original coverage metadata objects
        self.assertTrue(OriginalCoverage.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Variable metadata objects
        self.assertTrue(Variable.objects.filter(object_id=core_metadata_obj.id).exists())

        # delete resource
        hydroshare.delete_resource(self.resNetcdf.short_id)
        self.assertEqual(CoreMetaData.objects.all().count(), 0)

        # there should be no Creator metadata objects
        self.assertFalse(Creator.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Contributor metadata objects
        self.assertFalse(Contributor.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Identifier metadata objects
        self.assertFalse(Identifier.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Type metadata objects
        self.assertFalse(Type.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Source metadata objects
        self.assertFalse(Source.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Relation metadata objects
        self.assertFalse(Relation.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Publisher metadata objects
        self.assertFalse(Publisher.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Title metadata objects
        self.assertFalse(Title.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Description (Abstract) metadata objects
        self.assertFalse(Description.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Date metadata objects
        self.assertFalse(Date.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Subject metadata objects
        self.assertFalse(Subject.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Coverage metadata objects
        self.assertFalse(Coverage.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Format metadata objects
        self.assertFalse(Format.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Language metadata objects
        self.assertFalse(Language.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Rights metadata objects
        self.assertFalse(Rights.objects.filter(object_id=core_metadata_obj.id).exists())

        # resource specific metadata
        # there should be original coverage metadata objects
        self.assertFalse(OriginalCoverage.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Variable metadata objects
        self.assertFalse(Variable.objects.filter(object_id=core_metadata_obj.id).exists())

    def test_extended_metadata_CRUD(self):
        # create original coverage element
        self.assertEqual(self.resNetcdf.metadata.ori_coverage.all().count(), 0)
        value = {"northlimit": '12', "projection": "transverse_mercator", "units": "meter", "southlimit": '10',
                    "eastlimit": '23', "westlimit": '2'}
        self.resNetcdf.metadata.create_element('originalcoverage',
                                               value=value,
                                               projection_string_text='+proj=tmerc +lon_0=-111.0 '
                                                                      '+lat_0=0.0 +x_0=500000.0 +y_0=0.0 +k_0=0.9996',
                                               projection_string_type='Proj4 String'
                                               )

        ori_coverage = self.resNetcdf.metadata.ori_coverage.all().first()
        self.assertEqual(ori_coverage.value, value)
        self.assertEqual(ori_coverage.projection_string_text, '+proj=tmerc +lon_0=-111.0 +lat_0=0.0 +x_0=500000.0 '
                                                               '+y_0=0.0 +k_0=0.9996')
        self.assertEqual(ori_coverage.projection_string_type, 'Proj4 String')

        # multiple original coverage elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            self.resNetcdf.metadata.create_element('originalcoverage',
                                                   value=value,
                                                   projection_string_text='+proj=tmerc +lon_0=-111.0 '
                                                                          '+lat_0=0.0 +x_0=500000.0 +y_0=0.0 +k_0=0.9996',
                                                   projection_string_type='Proj4 String'
                                                   )
        # create variable element
        self.assertEqual(self.resNetcdf.metadata.variables.all().count(), 0)
        self.resNetcdf.metadata.create_element('variable', name='SWE', type='Float',
                                                   shape='y,x,time', unit='m',
                                                   missing_value='-9999', descriptive_name='Snow water equivalent',
                                                   method='model simulation of UEB')

        variable_element = self.resNetcdf.metadata.variables.all().first()
        self.assertEqual(variable_element.name, 'SWE')
        self.assertEqual(variable_element.type, 'Float')
        self.assertEqual(variable_element.shape, 'y,x,time')
        self.assertEqual(variable_element.unit, 'm')
        self.assertEqual(variable_element.missing_value, '-9999')
        self.assertEqual(variable_element.descriptive_name, 'Snow water equivalent')
        self.assertEqual(variable_element.method, 'model simulation of UEB')

        # multiple variable elements are allowed
        self.resNetcdf.metadata.create_element('variable', name='x', type='Float',
                                                   shape='x', unit='m',
                                                   descriptive_name='x coordinate of projection')
        self.assertEqual(self.resNetcdf.metadata.variables.all().count(), 2)

        # delete
        # variable deletion is not allowed
        with self.assertRaises(ValidationError):
            self.resNetcdf.metadata.delete_element('variable', self.resNetcdf.metadata.variables.all().filter(name='SWE').first().id)

        # update
        # update original coverage element
        value_2 = {"northlimit": '12.5', "projection": "transverse_mercator", "units": "meter", "southlimit": '10.5',
            "eastlimit": '23.5', "westlimit": '2.5'}
        self.resNetcdf.metadata.update_element('originalcoverage',
                                               ori_coverage.id,
                                               value=value_2,
                                               projection_string_text='2009',
                                               projection_string_type='EPSG Code'
                                               )
        ori_coverage = self.resNetcdf.metadata.ori_coverage.all().first()
        self.assertEqual(ori_coverage.value, value_2)
        self.assertEqual(ori_coverage.projection_string_text, '2009')
        self.assertEqual(ori_coverage.projection_string_type, 'EPSG Code')

        # update variable element
        variable = self.resNetcdf.metadata.variables.all().filter(name='SWE').first()
        self.resNetcdf.metadata.update_element('variable', variable.id,
                                                   name='SWE2', type='Double',
                                                   shape='y,x,time', unit='m',
                                                   missing_value='-999', descriptive_name='snow water equivalent',
                                                   method='model result of UEB')
        variable = self.resNetcdf.metadata.variables.all().filter(name='SWE2').first()  # need to refer to the variable again!
        self.assertEqual(variable.name, 'SWE2')
        self.assertEqual(variable.type, 'Double')
        self.assertEqual(variable.shape, 'y,x,time')
        self.assertEqual(variable.unit, 'm')
        self.assertEqual(variable.missing_value, '-999')
        self.assertEqual(variable.descriptive_name, 'snow water equivalent')
        self.assertEqual(variable.method, 'model result of UEB')

    def test_have_multiple_content_files(self):
        self.assertFalse(NetcdfResource.can_have_multiple_files())

    def test_can_upload_multiple_content_files(self):
        # only one file can be uploaded
        self.assertFalse(NetcdfResource.allow_multiple_file_upload())

    def test_public_or_discoverable(self):
        self.assertFalse(self.resNetcdf.has_required_content_files())
        self.assertFalse(self.resNetcdf.metadata.has_all_required_elements())
        self.assertFalse(self.resNetcdf.can_be_public_or_discoverable)

        # adding a valid netcdf file
        files = [UploadedFile(file=self.netcdf_file_obj, name=self.netcdf_file_name)]
        utils.resource_file_add_pre_process(resource=self.resNetcdf, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resNetcdf, files=files, user=self.user,
                                        extract_metadata=True)

        self.assertTrue(self.resNetcdf.has_required_content_files())
        self.assertTrue(self.resNetcdf.metadata.has_all_required_elements())
        self.assertTrue(self.resNetcdf.can_be_public_or_discoverable)

    def test_metadata_extraction_of_wkt_crs_on_resource_creation(self):
        files = [UploadedFile(file=self.netcdf_file_obj_crs, name=self.netcdf_file_name_crs)]
        _, _, metadata, _ = utils.resource_pre_create_actions(resource_type='NetcdfResource',
                                                                          resource_title='Snow water equivalent '
                                                                                         'estimation at TWDEF site '
                                                                                         'from Oct 2009 to June 2010',
                                                                          page_redirect_url_key=None,
                                                                          files=files,
                                                                          metadata=None,)

        self.resNetcdf = hydroshare.create_resource(
            'NetcdfResource',
            self.user,
            'Snow water equivalent estimation at TWDEF site from Oct 2009 to June 2010',
            files=files,
            metadata=metadata
            )

        self._test_metadata_extraction_wkt_crs()

    def test_metadata_extraction_of_wkt_crs_on_content_file_add(self):
        files = [UploadedFile(file=self.netcdf_file_obj_crs, name=self.netcdf_file_name_crs)]
        utils.resource_file_add_pre_process(resource=self.resNetcdf, files=files, user=self.user,
                                            extract_metadata=False)
        utils.resource_file_add_process(resource=self.resNetcdf, files=files, user=self.user,
                                        extract_metadata=False)

        self._test_metadata_extraction_wkt_crs()

    def _test_metadata_extraction_wkt_crs(self, create_res_mode=True):

        # testing extended metadata element: original coverage
        ori_coverage = self.resNetcdf.metadata.ori_coverage.all().first()
        self.assertNotEquals(ori_coverage, None)
        self.assertEqual(ori_coverage.value['northlimit'], '4662377.44692')
        self.assertEqual(ori_coverage.value['eastlimit'], '461939.019091')
        self.assertEqual(ori_coverage.value['southlimit'], '4612607.44692')
        self.assertEqual(ori_coverage.value['westlimit'], '432419.019091')
        self.assertEqual(ori_coverage.value['units'], 'Meter')
        self.assertEqual(ori_coverage.value['projection'], 'NAD83 / UTM zone 12N')

        self.assertEqual(ori_coverage.projection_string_type, 'WKT String')
        proj_text = 'PROJCS["NAD83 / UTM zone 12N",GEOGCS["NAD83",DATUM["North_American_Datum_1983",' \
                    'SPHEROID["GRS 1980",6378137,298.2572221010002,AUTHORITY["EPSG","7019"]],' \
                    'AUTHORITY["EPSG","6269"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],' \
                    'AUTHORITY["EPSG","4269"]],PROJECTION["Transverse_Mercator"],' \
                    'PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",-111],' \
                    'PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],' \
                    'PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AUTHORITY["EPSG","26912"]]'
        self.assertEqual(ori_coverage.projection_string_text, proj_text)
        self.assertEqual(ori_coverage.datum, 'North_American_Datum_1983')

    def _test_metadata_extraction(self, create_res_mode=True):
        # there should 2 content file
        self.assertEqual(self.resNetcdf.files.all().count(), 2)

        # test core metadata after metadata extraction
        extracted_title = "Snow water equivalent estimation at TWDEF site from Oct 2009 to June 2010"
        self.assertEqual(self.resNetcdf.metadata.title.value, extracted_title)

        # there should be an abstract element
        self.assertNotEquals(self.resNetcdf.metadata.description, None)
        extracted_abstract = "This netCDF data is the simulation output from Utah Energy Balance (UEB) model." \
                             "It includes the simulation result of snow water equivalent during the period " \
                             "Oct. 2009 to June 2010 for TWDEF site in Utah."
        self.assertEqual(self.resNetcdf.metadata.description.abstract, extracted_abstract)

        # there should be one source element
        self.assertEqual(self.resNetcdf.metadata.sources.all().count(), 1)

        # there should be one license element:
        self.assertNotEquals(self.resNetcdf.metadata.rights.statement, 1)

        # there should be one relation element
        self.assertEqual(self.resNetcdf.metadata.relations.all().filter(type='cites').count(), 1)

        # there should be 2 creator
        self.assertEqual(self.resNetcdf.metadata.creators.all().count(), 2)

        # there should be one contributor
        self.assertEqual(self.resNetcdf.metadata.contributors.all().count(), 1)

        # there should be 2 coverage element - box type and period type
        self.assertEqual(self.resNetcdf.metadata.coverages.all().count(), 2)
        self.assertEqual(self.resNetcdf.metadata.coverages.all().filter(type='box').count(), 1)
        self.assertEqual(self.resNetcdf.metadata.coverages.all().filter(type='period').count(), 1)

        box_coverage = self.resNetcdf.metadata.coverages.all().filter(type='box').first()
        self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(box_coverage.value['northlimit'], 41.867126409)
        self.assertEqual(box_coverage.value['eastlimit'], -111.505940368)
        self.assertEqual(box_coverage.value['southlimit'], 41.8639080745)
        self.assertEqual(box_coverage.value['westlimit'], -111.51138808)

        temporal_coverage = self.resNetcdf.metadata.coverages.all().filter(type='period').first()
        self.assertEqual(parser.parse(temporal_coverage.value['start']).date(), parser.parse('10/01/2009').date())
        self.assertEqual(parser.parse(temporal_coverage.value['end']).date(), parser.parse('05/30/2010').date())

        # there should be 2 format elements
        self.assertEqual(self.resNetcdf.metadata.formats.all().count(), 2)
        self.assertEqual(self.resNetcdf.metadata.formats.all().filter(value='text/plain').count(), 1)
        self.assertEqual(self.resNetcdf.metadata.formats.all().filter(value='application/x-netcdf').count(), 1)

        # there should be one subject element
        self.assertEqual(self.resNetcdf.metadata.subjects.all().count(), 1)
        subj_element = self.resNetcdf.metadata.subjects.all().first()
        self.assertEqual(subj_element.value, 'Snow water equivalent')

        # testing extended metadata element: original coverage
        ori_coverage = self.resNetcdf.metadata.ori_coverage.all().first()
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
        self.assertEqual(self.resNetcdf.metadata.variables.all().count(), 5)

        # test time variable
        var_time = self.resNetcdf.metadata.variables.all().filter(name='time').first()
        self.assertNotEquals(var_time, None)
        self.assertEqual(var_time.unit, 'hours since 2009-10-1 0:0:00 UTC')
        self.assertEqual(var_time.type, 'Float')
        self.assertEqual(var_time.shape, 'time')
        self.assertEqual(var_time.descriptive_name, 'time')

        # test x variable
        var_x = self.resNetcdf.metadata.variables.all().filter(name='x').first()
        self.assertNotEquals(var_x, None)
        self.assertEqual(var_x.unit, 'Meter')
        self.assertEqual(var_x.type, 'Float')
        self.assertEqual(var_x.shape, 'x')
        self.assertEqual(var_x.descriptive_name, 'x coordinate of projection')

        # test y variable
        var_y = self.resNetcdf.metadata.variables.all().filter(name='y').first()
        self.assertNotEquals(var_y, None)
        self.assertEqual(var_y.unit, 'Meter')
        self.assertEqual(var_y.type, 'Float')
        self.assertEqual(var_y.shape, 'y')
        self.assertEqual(var_y.descriptive_name, 'y coordinate of projection')

        # test SWE variable
        var_swe = self.resNetcdf.metadata.variables.all().filter(name='SWE').first()
        self.assertNotEquals(var_swe, None)
        self.assertEqual(var_swe.unit, 'm')
        self.assertEqual(var_swe.type, 'Float')
        self.assertEqual(var_swe.shape, 'y,x,time')
        self.assertEqual(var_swe.descriptive_name, 'Snow water equivalent')
        self.assertEqual(var_swe.method, 'model simulation of UEB model')
        self.assertEqual(var_swe.missing_value, '-9999')

        # test grid mapping variable
        var_grid = self.resNetcdf.metadata.variables.all().filter(name='transverse_mercator').first()
        self.assertNotEquals(var_grid, None)
        self.assertEqual(var_grid.unit, 'Unknown')
        self.assertEqual(var_grid.type, 'Unknown')
        self.assertEqual(var_grid.shape, 'Not defined')


