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
from hs_app_timeseries.models import TimeSeriesResource, Site, Variable, Method, ProcessingLevel, TimeSeriesResult


class TestTimeSeriesMetaData(MockIRODSTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(TestTimeSeriesMetaData, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        self.resTimeSeries = hydroshare.create_resource(
            resource_type='TimeSeriesResource',
            owner=self.user,
            title='Test Time Series Resource'
        )

        self.temp_dir = tempfile.mkdtemp()
        self.odm2_sqlite_file_name = 'ODM2_valid.sqlite'
        self.odm2_sqlite_file = 'hs_app_timeseries/tests/{}'.format(self.odm2_sqlite_file_name)
        target_temp_sqlite_file = os.path.join(self.temp_dir, self.odm2_sqlite_file_name)
        shutil.copy(self.odm2_sqlite_file, target_temp_sqlite_file)
        self.odm2_sqlite_file_obj = open(target_temp_sqlite_file, 'r')

        self.odm2_sqlite_bad_file_name = 'ODM2_invalid.sqlite'
        self.odm2_sqlite_bad_file = 'hs_app_timeseries/tests/{}'.format(self.odm2_sqlite_bad_file_name)
        target_temp_bad_sqlite_file = os.path.join(self.temp_dir, self.odm2_sqlite_bad_file_name)
        shutil.copy(self.odm2_sqlite_bad_file, target_temp_bad_sqlite_file)
        self.odm2_sqlite_bad_file_obj = open(target_temp_bad_sqlite_file, 'r')

        temp_text_file = os.path.join(self.temp_dir, 'ODM2.txt')
        text_file = open(temp_text_file, 'w')
        text_file.write("ODM2 records")
        self.text_file_obj = open(temp_text_file, 'r')

    def tearDown(self):
        super(TestTimeSeriesMetaData, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_allowed_file_types(self):
        # test allowed file type is '.sqlite'
        self.assertIn('.sqlite', TimeSeriesResource.get_supported_upload_file_types())
        self.assertEquals(len(TimeSeriesResource.get_supported_upload_file_types()), 1)

        # there should not be any content file
        self.assertEquals(self.resTimeSeries.files.all().count(), 0)

        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        # trying to add a text file to this resource should raise exception
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files, user=self.user,
                                                extract_metadata=False)

        # trying to add sqlite file should pass the file add pre process check
        files = [UploadedFile(file=self.odm2_sqlite_bad_file_obj, name=self.odm2_sqlite_bad_file_name)]
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files, user=self.user,
                                            extract_metadata=False)

        # should raise file validation error even though the file gets added to the resource
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_process(resource=self.resTimeSeries, files=files, user=self.user,
                                            extract_metadata=False)

        # there should 1 content file
        self.assertEquals(self.resTimeSeries.files.all().count(), 1)

        # file pre add process should raise validation error if we try to add a 2nd file when the resource has
        # already one content file
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files, user=self.user,
                                                extract_metadata=False)

        # delete the content file
        hydroshare.delete_resource_file(self.resTimeSeries.short_id, self.odm2_sqlite_bad_file_name, self.user)

        # there should no content file
        self.assertEquals(self.resTimeSeries.files.all().count(), 0)

        # use a valid ODM2 sqlite which should pass both the file pre add check post add check
        files = [UploadedFile(file=self.odm2_sqlite_file_obj, name=self.odm2_sqlite_file_name)]
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resTimeSeries, files=files, user=self.user,
                                        extract_metadata=False)

        # there should one content file
        self.assertEquals(self.resTimeSeries.files.all().count(), 1)

    def test_metadata_extraction_on_resource_creation(self):
        # passing the file object that points to the temp dir doesn't work - create_resource throws error
        # open the file from the fixed file location
        self.odm2_sqlite_file_obj = open(self.odm2_sqlite_file, 'r')

        self.resTimeSeries = hydroshare.create_resource(
            resource_type='TimeSeriesResource',
            owner=self.user,
            title='My Test TimeSeries Resource',
            files=(self.odm2_sqlite_file_obj,)
            )
        utils.resource_post_create_actions(resource=self.resTimeSeries, user=self.user, metadata=[])

        self._test_metadata_extraction()

    def test_metadata_extraction_on_content_file_add(self):
        # test the core metadata at this point
        self.assertEquals(self.resTimeSeries.metadata.title.value, 'Test Time Series Resource')

        # there shouldn't any abstract element
        self.assertEquals(self.resTimeSeries.metadata.description, None)

        # there shouldn't any coverage element
        self.assertEquals(self.resTimeSeries.metadata.coverages.all().count(), 0)

        # there shouldn't any format element
        self.assertEquals(self.resTimeSeries.metadata.formats.all().count(), 0)

        # there shouldn't any subject element
        self.assertEquals(self.resTimeSeries.metadata.subjects.all().count(), 0)

        # there shouldn't any contributor element
        self.assertEquals(self.resTimeSeries.metadata.contributors.all().count(), 0)

        # check that there are no extended metadata elements at this point
        self.assertEquals(self.resTimeSeries.metadata.site, None)
        self.assertEquals(self.resTimeSeries.metadata.variable, None)
        self.assertEquals(self.resTimeSeries.metadata.method, None)
        self.assertEquals(self.resTimeSeries.metadata.processing_level, None)
        self.assertEquals(self.resTimeSeries.metadata.time_series_result, None)

        # adding a valid ODM2 sqlite file should generate some core metadata and all extended metadata
        files = [UploadedFile(file=self.odm2_sqlite_file_obj, name=self.odm2_sqlite_file_name)]
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resTimeSeries, files=files, user=self.user,
                                        extract_metadata=True)

        self._test_metadata_extraction()

    def test_metadata_on_content_file_delete(self):
        # test that metadata is not deleted (except format element) on content file deletion
        # adding a valid ODM2 sqlite file should generate some core metadata and all extended metadata
        files = [UploadedFile(file=self.odm2_sqlite_file_obj, name=self.odm2_sqlite_file_name)]
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resTimeSeries, files=files, user=self.user,
                                        extract_metadata=True)

        # there should one content file
        self.assertEquals(self.resTimeSeries.files.all().count(), 1)

        # there should be one format element
        self.assertEquals(self.resTimeSeries.metadata.formats.all().count(), 1)

        # delete content file that we added above
        hydroshare.delete_resource_file(self.resTimeSeries.short_id, self.odm2_sqlite_file_name, self.user)
        # there should no content file
        self.assertEquals(self.resTimeSeries.files.all().count(), 0)

        # test the core metadata at this point
        self.assertNotEquals(self.resTimeSeries.metadata.title, None)

        # there should be an abstract element
        self.assertNotEquals(self.resTimeSeries.metadata.description, None)

        # there should be one creator element
        self.assertEquals(self.resTimeSeries.metadata.creators.all().count(), 1)

        # there should be one contributor element
        self.assertEquals(self.resTimeSeries.metadata.contributors.all().count(), 1)

        # there should be 2 coverage element -  point type and period type
        self.assertEquals(self.resTimeSeries.metadata.coverages.all().count(), 2)
        self.assertEquals(self.resTimeSeries.metadata.coverages.all().filter(type='point').count(), 1)
        self.assertEquals(self.resTimeSeries.metadata.coverages.all().filter(type='period').count(), 1)
        # there should be no format element
        self.assertEquals(self.resTimeSeries.metadata.formats.all().count(), 0)
        # there should be one subject element
        self.assertEquals(self.resTimeSeries.metadata.subjects.all().count(), 1)

        # testing extended metadata elements
        self.assertNotEquals(self.resTimeSeries.metadata.site, None)
        self.assertNotEquals(self.resTimeSeries.metadata.variable, None)
        self.assertNotEquals(self.resTimeSeries.metadata.method, None)
        self.assertNotEquals(self.resTimeSeries.metadata.processing_level, None)
        self.assertNotEquals(self.resTimeSeries.metadata.time_series_result, None)

    def test_metadata_delete_on_resource_delete(self):
        # generate metadata by adding a valid odm2 sqlite file
        files = [UploadedFile(file=self.odm2_sqlite_file_obj, name=self.odm2_sqlite_file_name)]
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resTimeSeries, files=files, user=self.user,
                                        extract_metadata=True)

        # before resource delete
        core_metadata_obj = self.resTimeSeries.metadata
        self.assertEquals(CoreMetaData.objects.all().count(), 1)
        # there should be Creator metadata objects
        self.assertTrue(Creator.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Contributor metadata objects
        self.assertTrue(Contributor.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Identifier metadata objects
        self.assertTrue(Identifier.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Type metadata objects
        self.assertTrue(Type.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Source metadata objects
        self.assertFalse(Source.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Relation metadata objects
        self.assertFalse(Relation.objects.filter(object_id=core_metadata_obj.id).exists())
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
        # there should be Site metadata objects
        self.assertTrue(Site.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Variable metadata objects
        self.assertTrue(Variable.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Method metadata objects
        self.assertTrue(Method.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be ProcessingLevel metadata objects
        self.assertTrue(ProcessingLevel.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be TimeSeriesResult metadata objects
        self.assertTrue(TimeSeriesResult.objects.filter(object_id=core_metadata_obj.id).exists())

        # delete resource
        hydroshare.delete_resource(self.resTimeSeries.short_id)
        self.assertEquals(CoreMetaData.objects.all().count(), 0)

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
        # there should be no Site metadata objects
        self.assertFalse(Site.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Variable metadata objects
        self.assertFalse(Variable.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Method metadata objects
        self.assertFalse(Method.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no ProcessingLevel metadata objects
        self.assertFalse(ProcessingLevel.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no TimeSeriesResult metadata objects
        self.assertFalse(TimeSeriesResult.objects.filter(object_id=core_metadata_obj.id).exists())

    def test_extended_metadata_CRUD(self):
        # create
        self.assertEquals(self.resTimeSeries.metadata.site, None)
        self.resTimeSeries.metadata.create_element('site', site_code='LR_WaterLab_AA',
                                                   site_name='Logan River at the Utah Water Research Laboratory '
                                                             'west bridge', elevation_m=1414, elevation_datum='EGM96',
                                                   site_type='Stream')

        site_element = self.resTimeSeries.metadata.site
        self.assertEquals(site_element.site_code, 'LR_WaterLab_AA')
        self.assertEquals(site_element.site_name, 'Logan River at the Utah Water Research Laboratory west bridge')
        self.assertEquals(site_element.elevation_m, 1414)
        self.assertEquals(site_element.elevation_datum, 'EGM96')
        self.assertEquals(site_element.site_type, 'Stream')

        # multiple site elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            self.resTimeSeries.metadata.create_element('site', site_code='LR_WaterLab_BB',
                                                       site_name='Logan River at the Utah Water Research Laboratory '
                                                                 'west bridge', elevation_m=1515,
                                                       elevation_datum='EGM97', site_type='Stream Flow')

        self.assertEquals(self.resTimeSeries.metadata.variable, None)
        self.resTimeSeries.metadata.create_element('variable', variable_code='ODO', variable_name='Oxygen, dissolved',
                                                   variable_type='Concentration', no_data_value=-9999,
                                                   variable_definition='Concentration of oxygen gas dissolved in '
                                                                       'water.', speciation='Not Applicable')

        variable_element = self.resTimeSeries.metadata.variable
        self.assertEquals(variable_element.variable_code, 'ODO')
        self.assertEquals(variable_element.variable_name, 'Oxygen, dissolved')
        self.assertEquals(variable_element.variable_type, 'Concentration')
        self.assertEquals(variable_element.no_data_value, -9999)
        self.assertEquals(variable_element.variable_definition, 'Concentration of oxygen gas dissolved in water.')
        self.assertEquals(variable_element.speciation, 'Not Applicable')

        # multiple variable elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            self.resTimeSeries.metadata.create_element('variable', variable_code='ODO-2', variable_name='Oxygen',
                                                       variable_type='Concentration', no_data_value=-9999,
                                                       variable_definition='Concentration of oxygen gas dissolved in '
                                                                           'water.', speciation='Applicable')

        self.assertEquals(self.resTimeSeries.metadata.method, None)
        self.resTimeSeries.metadata.create_element('method', method_code=59, method_name='Optical DO',
                                                   method_type='Instrument deployment',
                                                   method_description='Dissolved oxygen concentration measured '
                                                                      'optically using a YSI EXO multi-parameter water '
                                                                      'quality sonde.',
                                                   method_link='http://www.exowater.com')

        method_element = self.resTimeSeries.metadata.method
        self.assertEquals(method_element.method_code, 59)
        self.assertEquals(method_element.method_name, 'Optical DO')
        self.assertEquals(method_element.method_type, 'Instrument deployment')
        method_desc = 'Dissolved oxygen concentration measured optically using a YSI EXO multi-parameter water ' \
                      'quality sonde.'
        self.assertEquals(method_element.method_description, method_desc)
        self.assertEquals(method_element.method_link, 'http://www.exowater.com')

        # multiple method elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            self.resTimeSeries.metadata.create_element('method', method_code=591, method_name='Optical DO1',
                                                       method_type='Instrument deployment',
                                                       method_description='Dissolved oxygen concentration measured '
                                                                          'optically using a YSI EXO-1 multi-parameter '
                                                                          'water quality sonde.',
                                                       method_link='http://www.ex-water.com')

        self.assertEquals(self.resTimeSeries.metadata.processing_level, None)
        exp_text = """Raw and unprocessed data and data products that have not undergone quality control.
        Depending on the variable, data type, and data transmission system, raw data may be available within seconds
        or minutes after the measurements have been made. Examples include real time precipitation, streamflow and
        water quality measurements."""
        self.resTimeSeries.metadata.create_element('processinglevel', processing_level_code=0, definition='Raw data',
                                                   explanation=exp_text)

        proc_level_element = self.resTimeSeries.metadata.processing_level
        self.assertEquals(proc_level_element.processing_level_code, 0)
        self.assertEquals(proc_level_element.definition, 'Raw data')
        self.assertEquals(proc_level_element.explanation, exp_text)

        # multiple processing level elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            self.resTimeSeries.metadata.create_element('processinglevel', processing_level_code=10, definition='data',
                                                       explanation=exp_text + ' Updated.')

        self.assertEquals(self.resTimeSeries.metadata.time_series_result, None)
        self.resTimeSeries.metadata.create_element('timeseriesresult', units_type='Concentration',
                                                   units_name='milligrams per liter', units_abbreviation='mg/L',
                                                   status='Complete', sample_medium='Surface water', value_count=11283,
                                                   aggregation_statistics="Average")

        ts_result_element = self.resTimeSeries.metadata.time_series_result
        self.assertEquals(ts_result_element.units_type, 'Concentration')
        self.assertEquals(ts_result_element.units_name, 'milligrams per liter')
        self.assertEquals(ts_result_element.units_abbreviation, 'mg/L')
        self.assertEquals(ts_result_element.status, 'Complete')
        self.assertEquals(ts_result_element.sample_medium, 'Surface water')
        self.assertEquals(ts_result_element.value_count, 11283)
        self.assertEquals(ts_result_element.aggregation_statistics, 'Average')

        # multiple timeseries result elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            self.resTimeSeries.metadata.create_element('timeseriesresult', units_type='Concentration-1',
                                                       units_name='milligrams per gallon', units_abbreviation='mg/GL',
                                                       status='Incomplete', sample_medium='Fresh water',
                                                       value_count=11111, aggregation_statistics="Mean")

        # update
        self.resTimeSeries.metadata.update_element('site', self.resTimeSeries.metadata.site.id,
                                                   site_code='LR_WaterLab_BB',
                                                   site_name='Logan River at the Utah WRL '
                                                             'west bridge', elevation_m=1515, elevation_datum='EGM97',
                                                   site_type='Stream flow')

        site_element = self.resTimeSeries.metadata.site
        self.assertEquals(site_element.site_code, 'LR_WaterLab_BB')
        self.assertEquals(site_element.site_name, 'Logan River at the Utah WRL west bridge')
        self.assertEquals(site_element.elevation_m, 1515)
        self.assertEquals(site_element.elevation_datum, 'EGM97')
        self.assertEquals(site_element.site_type, 'Stream flow')

        self.resTimeSeries.metadata.update_element('variable', self.resTimeSeries.metadata.variable.id,
                                                   variable_code='ODO-1', variable_name='H2O dissolved',
                                                   variable_type='Concentration-1', no_data_value=-999,
                                                   variable_definition='Concentration of oxygen dissolved in '
                                                                       'water.', speciation='Applicable')

        variable_element = self.resTimeSeries.metadata.variable
        self.assertEquals(variable_element.variable_code, 'ODO-1')
        self.assertEquals(variable_element.variable_name, 'H2O dissolved')
        self.assertEquals(variable_element.variable_type, 'Concentration-1')
        self.assertEquals(variable_element.no_data_value, -999)
        self.assertEquals(variable_element.variable_definition, 'Concentration of oxygen dissolved in water.')
        self.assertEquals(variable_element.speciation, 'Applicable')

        method_desc = 'Dissolved oxygen concentration measured optically using a YSI EXO multi-parameter water ' \
                      'quality sonde-1.'
        self.resTimeSeries.metadata.update_element('method', self.resTimeSeries.metadata.method.id, method_code=69,
                                                   method_name='Optical DO-1',
                                                   method_type='Instrument deployment-1',
                                                   method_description=method_desc,
                                                   method_link='http://www.ex-water.com')

        method_element = self.resTimeSeries.metadata.method
        self.assertEquals(method_element.method_code, 69)
        self.assertEquals(method_element.method_name, 'Optical DO-1')
        self.assertEquals(method_element.method_type, 'Instrument deployment-1')

        self.assertEquals(method_element.method_description, method_desc)
        self.assertEquals(method_element.method_link, 'http://www.ex-water.com')

        self.resTimeSeries.metadata.update_element('processinglevel', self.resTimeSeries.metadata.processing_level.id,
                                                   processing_level_code=9, definition='data',
                                                   explanation=exp_text + 'some more text')

        proc_level_element = self.resTimeSeries.metadata.processing_level
        self.assertEquals(proc_level_element.processing_level_code, 9)
        self.assertEquals(proc_level_element.definition, 'data')
        self.assertEquals(proc_level_element.explanation, exp_text + 'some more text')

        self.resTimeSeries.metadata.update_element('timeseriesresult',
                                                   self.resTimeSeries.metadata.time_series_result.id,
                                                   units_type='Concentration-1',
                                                   units_name='milligrams per GL', units_abbreviation='mg/GL',
                                                   status='Incomplete', sample_medium='Fresh water', value_count=11211,
                                                   aggregation_statistics="Mean")

        ts_result_element = self.resTimeSeries.metadata.time_series_result
        self.assertEquals(ts_result_element.units_type, 'Concentration-1')
        self.assertEquals(ts_result_element.units_name, 'milligrams per GL')
        self.assertEquals(ts_result_element.units_abbreviation, 'mg/GL')
        self.assertEquals(ts_result_element.status, 'Incomplete')
        self.assertEquals(ts_result_element.sample_medium, 'Fresh water')
        self.assertEquals(ts_result_element.value_count, 11211)
        self.assertEquals(ts_result_element.aggregation_statistics, 'Mean')

        # delete
        # extended metadata deletion is not allowed - should raise exception
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.delete_element('site', self.resTimeSeries.metadata.site.id)

        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.delete_element('variable',
                                                       self.resTimeSeries.metadata.variable.id)

        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.delete_element('method', self.resTimeSeries.metadata.method.id)

        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.delete_element('processinglevel',
                                                       self.resTimeSeries.metadata.processing_level.id)
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.delete_element('timeseriesresult',
                                                       self.resTimeSeries.metadata.time_series_result.id)

    def test_get_xml(self):
        # add a valid odm2 sqlite file to generate metadata
        files = [UploadedFile(file=self.odm2_sqlite_file_obj, name=self.odm2_sqlite_file_name)]
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resTimeSeries, files=files, user=self.user,
                                        extract_metadata=True)

        # test if xml from get_xml() is well formed
        ET.fromstring(self.resTimeSeries.metadata.get_xml())

    def test_multiple_content_files(self):
        self.assertFalse(TimeSeriesResource.can_have_multiple_files())

    def test_public_or_discoverable(self):
        self.assertFalse(self.resTimeSeries.has_required_content_files())
        self.assertFalse(self.resTimeSeries.metadata.has_all_required_elements())
        self.assertFalse(self.resTimeSeries.can_be_public_or_discoverable)

        # adding a valid ODM2 sqlite file should generate required core metadata and all extended metadata
        files = [UploadedFile(file=self.odm2_sqlite_file_obj, name=self.odm2_sqlite_file_name)]
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resTimeSeries, files=files, user=self.user,
                                        extract_metadata=True)

        self.assertTrue(self.resTimeSeries.has_required_content_files())
        self.assertTrue(self.resTimeSeries.metadata.has_all_required_elements())
        self.assertTrue(self.resTimeSeries.can_be_public_or_discoverable)

    def _test_metadata_extraction(self):
        # there should one content file
        self.assertEquals(self.resTimeSeries.files.all().count(), 1)

        # there should be one contributor element
        self.assertEquals(self.resTimeSeries.metadata.contributors.all().count(), 1)

        # test core metadata after metadata extraction
        extracted_title = "Water temperature in the Little Bear River at Mendon Road near Mendon, UT"
        self.assertEquals(self.resTimeSeries.metadata.title.value, extracted_title)

        # there should be an abstract element
        self.assertNotEquals(self.resTimeSeries.metadata.description, None)
        extracted_abstract = "This dataset contains observations of water temperature in the Little Bear River at " \
                             "Mendon Road near Mendon, UT. Data were recorded every 30 minutes. The values were " \
                             "recorded using a HydroLab MS5 multi-parameter water quality sonde connected to a " \
                             "Campbell Scientific datalogger. Values represent quality controlled data that have " \
                             "undergone quality control to remove obviously bad data."
        self.assertEquals(self.resTimeSeries.metadata.description.abstract, extracted_abstract)

        # there should be 2 coverage element -  point type and period type
        self.assertEquals(self.resTimeSeries.metadata.coverages.all().count(), 2)
        self.assertEquals(self.resTimeSeries.metadata.coverages.all().filter(type='point').count(), 1)
        self.assertEquals(self.resTimeSeries.metadata.coverages.all().filter(type='period').count(), 1)

        point_coverage = self.resTimeSeries.metadata.coverages.all().filter(type='point').first()
        self.assertEquals(point_coverage.value['projection'], 'Unknown')
        self.assertEquals(point_coverage.value['units'], 'Decimal degrees')
        self.assertEquals(point_coverage.value['east'], -111.946402)
        self.assertEquals(point_coverage.value['north'], 41.718473)

        temporal_coverage = self.resTimeSeries.metadata.coverages.all().filter(type='period').first()
        self.assertEquals(parser.parse(temporal_coverage.value['start']).date(), parser.parse('01/01/2008').date())
        self.assertEquals(parser.parse(temporal_coverage.value['end']).date(), parser.parse('01/31/2008').date())

        # there should be one format element
        self.assertEquals(self.resTimeSeries.metadata.formats.all().count(), 1)
        format_element = self.resTimeSeries.metadata.formats.all().first()
        self.assertEquals(format_element.value, 'application/sqlite')

        # there should be one subject element
        self.assertEquals(self.resTimeSeries.metadata.subjects.all().count(), 1)
        subj_element = self.resTimeSeries.metadata.subjects.all().first()
        self.assertEquals(subj_element.value, 'Temperature')

        # testing extended metadata elements
        self.assertNotEquals(self.resTimeSeries.metadata.site, None)
        self.assertEquals(self.resTimeSeries.metadata.site.site_code, 'USU-LBR-Mendon')
        site_name = 'Little Bear River at Mendon Road near Mendon, Utah'
        self.assertEquals(self.resTimeSeries.metadata.site.site_name, site_name)
        self.assertEquals(self.resTimeSeries.metadata.site.elevation_m, 1345)
        self.assertEquals(self.resTimeSeries.metadata.site.elevation_datum, 'NGVD29')
        self.assertEquals(self.resTimeSeries.metadata.site.site_type, 'Stream')

        self.assertNotEquals(self.resTimeSeries.metadata.variable, None)
        self.assertEquals(self.resTimeSeries.metadata.variable.variable_code, 'USU36')
        self.assertEquals(self.resTimeSeries.metadata.variable.variable_name, 'Temperature')
        self.assertEquals(self.resTimeSeries.metadata.variable.variable_type, 'Water Quality')
        self.assertEquals(self.resTimeSeries.metadata.variable.no_data_value, -9999)
        self.assertEquals(self.resTimeSeries.metadata.variable.variable_definition, None)
        self.assertEquals(self.resTimeSeries.metadata.variable.speciation, 'Not Applicable')

        self.assertNotEquals(self.resTimeSeries.metadata.method, None)
        self.assertEquals(self.resTimeSeries.metadata.method.method_code, 28)
        method_name = 'Quality Control Level 1 Data Series created from raw QC Level 0 data using ODM Tools.'
        self.assertEquals(self.resTimeSeries.metadata.method.method_name, method_name)
        self.assertEquals(self.resTimeSeries.metadata.method.method_type, 'Instrument deployment')
        method_des = 'Quality Control Level 1 Data Series created from raw QC Level 0 data using ODM Tools.'
        self.assertEquals(self.resTimeSeries.metadata.method.method_description, method_des)
        self.assertEquals(self.resTimeSeries.metadata.method.method_link, None)

        self.assertNotEquals(self.resTimeSeries.metadata.processing_level, None)
        self.assertEquals(self.resTimeSeries.metadata.processing_level.processing_level_code, 1)
        self.assertEquals(self.resTimeSeries.metadata.processing_level.definition, 'Quality controlled data')
        explanation = 'Quality controlled data that have passed quality assurance procedures such as ' \
                      'routine estimation of timing and sensor calibration or visual inspection and removal ' \
                      'of obvious errors. An example is USGS published streamflow records following parsing ' \
                      'through USGS quality control procedures.'
        self.assertEquals(self.resTimeSeries.metadata.processing_level.explanation, explanation)

        self.assertNotEquals(self.resTimeSeries.metadata.time_series_result, None)
        self.assertEquals(self.resTimeSeries.metadata.time_series_result.units_type, 'Temperature')
        self.assertEquals(self.resTimeSeries.metadata.time_series_result.units_name, 'degree celsius')
        self.assertEquals(self.resTimeSeries.metadata.time_series_result.units_abbreviation, 'degC')
        self.assertEquals(self.resTimeSeries.metadata.time_series_result.status, 'Unknown')
        self.assertEquals(self.resTimeSeries.metadata.time_series_result.sample_medium, 'Surface Water')
        self.assertEquals(self.resTimeSeries.metadata.time_series_result.value_count, 1441)
        self.assertEquals(self.resTimeSeries.metadata.time_series_result.aggregation_statistics, 'Average')