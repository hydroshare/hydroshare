import os
import sqlite3
import tempfile
import shutil

from xml.etree import ElementTree as ET

from django.test import TransactionTestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.contrib.auth.models import Group

from hs_core import hydroshare
from hs_core.hydroshare import utils
from hs_core.models import CoreMetaData, Creator, Contributor, Coverage, Rights, Title, Language, \
    Publisher, Identifier, Type, Subject, Description, Date, Format, Relation, Source
from hs_core.testing import MockIRODSTestCaseMixin, TestCaseCommonUtilities
from hs_app_timeseries.models import TimeSeriesResource, Site, Variable, Method, ProcessingLevel, \
    TimeSeriesResult, CVVariableType, CVVariableName, CVSpeciation, CVElevationDatum, CVSiteType, \
    CVMethodType, CVUnitsType, CVStatus, CVMedium, CVAggregationStatistic, TimeSeriesMetaData, \
    UTCOffSet


class TestTimeSeriesMetaData(MockIRODSTestCaseMixin, TestCaseCommonUtilities, TransactionTestCase):
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
        self.odm2_sqlite_file_name = 'ODM2_Multi_Site_One_Variable.sqlite'
        self.odm2_sqlite_file = 'hs_app_timeseries/tests/{}'.format(self.odm2_sqlite_file_name)
        target_temp_sqlite_file = os.path.join(self.temp_dir, self.odm2_sqlite_file_name)
        shutil.copy(self.odm2_sqlite_file, target_temp_sqlite_file)
        self.odm2_sqlite_file_obj = open(target_temp_sqlite_file, 'r')

        self.odm2_sqlite_missing_data_file_name = \
            'ODM2_multi_site_single_variable_missing_data.sqlite'
        self.odm2_sqlite_missing_data_file = 'hs_app_timeseries/tests/{}'.format(
            self.odm2_sqlite_missing_data_file_name)

        self.odm2_sqlite_bad_file_name = 'ODM2_invalid.sqlite'
        self.odm2_sqlite_bad_file = 'hs_app_timeseries/tests/{}'.format(
            self.odm2_sqlite_bad_file_name)
        target_temp_bad_sqlite_file = os.path.join(self.temp_dir, self.odm2_sqlite_bad_file_name)
        shutil.copy(self.odm2_sqlite_bad_file, target_temp_bad_sqlite_file)
        self.odm2_sqlite_bad_file_obj = open(target_temp_bad_sqlite_file, 'r')

        self.odm2_csv_file_name = 'ODM2_Multi_Site_One_Variable_Test.csv'
        self.odm2_csv_file = 'hs_app_timeseries/tests/{}'.format(self.odm2_csv_file_name)
        target_temp_csv_file = os.path.join(self.temp_dir, self.odm2_csv_file_name)
        shutil.copy(self.odm2_csv_file, target_temp_csv_file)
        self.odm2_csv_file_obj = open(target_temp_csv_file, 'r')

        temp_text_file = os.path.join(self.temp_dir, 'ODM2.txt')
        text_file = open(temp_text_file, 'w')
        text_file.write("ODM2 records")
        self.text_file_obj = open(temp_text_file, 'r')

    def tearDown(self):
        super(TestTimeSeriesMetaData, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_allowed_file_types(self):
        # test allowed file type are '.sqlite' and '.csv
        self.assertIn('.sqlite', TimeSeriesResource.get_supported_upload_file_types())
        self.assertIn('.csv', TimeSeriesResource.get_supported_upload_file_types())
        self.assertEqual(len(TimeSeriesResource.get_supported_upload_file_types()), 2)

        # there should not be any content file
        self.assertEqual(self.resTimeSeries.files.all().count(), 0)

        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        # trying to add a text file to this resource should raise exception
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files,
                                                user=self.user, extract_metadata=False)

        # trying to add sqlite file should pass the file add pre process check
        files = [UploadedFile(file=self.odm2_sqlite_bad_file_obj,
                              name=self.odm2_sqlite_bad_file_name)]
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files,
                                            user=self.user, extract_metadata=False)

        # should raise file validation error and the file will not be added to the resource
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_process(resource=self.resTimeSeries, files=files,
                                            user=self.user, extract_metadata=False)

        # there should not be aby content file
        self.assertEqual(self.resTimeSeries.files.all().count(), 0)

        # there should no content file
        self.assertEqual(self.resTimeSeries.files.all().count(), 0)

        # use a valid ODM2 sqlite which should pass both the file pre add check post add check
        files = [UploadedFile(file=self.odm2_sqlite_file_obj, name=self.odm2_sqlite_file_name)]
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files,
                                            user=self.user, extract_metadata=False)

        utils.resource_file_add_process(resource=self.resTimeSeries, files=files, user=self.user,
                                        extract_metadata=False)

        # there should one content file
        self.assertEqual(self.resTimeSeries.files.all().count(), 1)

    def test_file_pre_add_signal_handler(self):
        # test that trying to add a csv file or sqlite file
        # when the resource already has a csv file or sqlite file should fail

        # use a valid ODM2 sqlite which should pass both the file pre add check post add check
        files = [UploadedFile(file=self.odm2_sqlite_file_obj, name=self.odm2_sqlite_file_name)]
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files,
                                            user=self.user, extract_metadata=False)

        utils.resource_file_add_process(resource=self.resTimeSeries, files=files, user=self.user,
                                        extract_metadata=False)

        # trying add another sqlite file should fail in the pre_add signal handler
        files = [UploadedFile(file=self.odm2_sqlite_file_obj, name=self.odm2_sqlite_file_name)]
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files,
                                                user=self.user, extract_metadata=False)

        # trying add scv file should fail in the pre_add signal handler
        files = [UploadedFile(file=self.odm2_csv_file_obj, name=self.odm2_csv_file_name)]
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files,
                                                user=self.user)

        # delete sqlite file that we added above
        hydroshare.delete_resource_file(self.resTimeSeries.short_id, self.odm2_sqlite_file_name,
                                        self.user)

        # add a csv file -
        files = [UploadedFile(file=self.odm2_csv_file_obj, name=self.odm2_csv_file_name)]
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files,
                                            user=self.user)
        utils.resource_file_add_process(resource=self.resTimeSeries, files=files, user=self.user,
                                        extract_metadata=False)

        # trying add another sqlite file should fail in the pre_add signal handler
        files = [UploadedFile(file=self.odm2_sqlite_file_obj, name=self.odm2_sqlite_file_name)]
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files,
                                                user=self.user, extract_metadata=False)

        # trying add scv file should fail in the pre_add signal handler
        files = [UploadedFile(file=self.odm2_csv_file_obj, name=self.odm2_csv_file_name)]
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files,
                                                user=self.user)

    def test_metadata_extraction_from_sqlite_on_resource_creation_1(self):
        # passing the file object that points to the temp dir doesn't work - create_resource
        # throws error open the file from the fixed file location
        self.odm2_sqlite_file_obj = open(self.odm2_sqlite_file, 'r')

        self.resTimeSeries = hydroshare.create_resource(
            resource_type='TimeSeriesResource',
            owner=self.user,
            title='My Test TimeSeries Resource',
            files=(self.odm2_sqlite_file_obj,)
            )
        utils.resource_post_create_actions(resource=self.resTimeSeries, user=self.user, metadata=[])

        super(TestTimeSeriesMetaData, self).timeseries_metadata_extraction()

    def test_metadata_extraction_from_sqlite_on_resource_creation_2(self):
        # Here we are using a sqlite file that has data missing as specified in issue#2771

        files = [open(self.odm2_sqlite_missing_data_file, 'r')]

        self.resTimeSeries = hydroshare.create_resource(
            resource_type='TimeSeriesResource',
            owner=self.user,
            title='My Test TimeSeries Resource',
            files=files
            )
        utils.resource_post_create_actions(resource=self.resTimeSeries, user=self.user, metadata=[])

        # test that there are sites with data for site name
        self.assertTrue(self.resTimeSeries.metadata.sites.filter(site_name__isnull=False).exists())
        # test that there are sites with no data for site name
        self.assertTrue(self.resTimeSeries.metadata.sites.filter(site_name__isnull=True).exists())
        # test that there are time series results with data for status
        self.assertTrue(self.resTimeSeries.metadata.time_series_results.exclude(status="").exists())
        # test that there are time series results with no data for status
        self.assertTrue(self.resTimeSeries.metadata.time_series_results.filter(status="").exists())
        # test that the variable code can be more than 20 characters long
        variable = self.resTimeSeries.metadata.variables.filter(
            variable_code__startswith='USU36_').first()
        self.assertTrue(len(variable.variable_code) > 20)

    def test_metadata_extraction_on_sqlite_file_add(self):
        # resource creation with uploaded sqlite file
        # test the core metadata at this point
        self.assertEqual(self.resTimeSeries.metadata.title.value, 'Test Time Series Resource')

        # there shouldn't any abstract element
        self.assertEqual(self.resTimeSeries.metadata.description, None)

        # there shouldn't any coverage element
        self.assertEqual(self.resTimeSeries.metadata.coverages.all().count(), 0)

        # there shouldn't any format element
        self.assertEqual(self.resTimeSeries.metadata.formats.all().count(), 0)

        # there shouldn't any subject element
        self.assertEqual(self.resTimeSeries.metadata.subjects.all().count(), 0)

        # there shouldn't any contributor element
        self.assertEqual(self.resTimeSeries.metadata.contributors.all().count(), 0)

        # check that there are no extended metadata elements at this point
        self.assertEqual(self.resTimeSeries.metadata.sites.all().count(), 0)
        self.assertEqual(self.resTimeSeries.metadata.variables.all().count(), 0)
        self.assertEqual(self.resTimeSeries.metadata.methods.all().count(), 0)
        self.assertEqual(self.resTimeSeries.metadata.processing_levels.all().count(), 0)
        self.assertEqual(self.resTimeSeries.metadata.time_series_results.all().count(), 0)
        self.assertEqual(self.resTimeSeries.metadata.utc_offset, None)

        # adding a valid ODM2 sqlite file should generate some core metadata and all extended
        # metadata
        files = [UploadedFile(file=self.odm2_sqlite_file_obj, name=self.odm2_sqlite_file_name)]
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files,
                                            user=self.user, extract_metadata=False)

        utils.resource_file_add_process(resource=self.resTimeSeries, files=files, user=self.user,
                                        extract_metadata=True)

        super(TestTimeSeriesMetaData, self).timeseries_metadata_extraction()

    def test_metadata_on_content_file_delete(self):
        # test that metadata is NOT deleted (except format element) on content file deletion

        # adding a valid ODM2 sqlite file should generate some core metadata and all extended
        # metadata
        files = [UploadedFile(file=self.odm2_sqlite_file_obj, name=self.odm2_sqlite_file_name)]
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files,
                                            user=self.user, extract_metadata=False)

        utils.resource_file_add_process(resource=self.resTimeSeries, files=files, user=self.user,
                                        extract_metadata=True)

        # there should one content file
        self.assertEqual(self.resTimeSeries.files.all().count(), 1)

        # there should be one format element
        self.assertEqual(self.resTimeSeries.metadata.formats.all().count(), 1)

        # delete content file that we added above
        hydroshare.delete_resource_file(self.resTimeSeries.short_id, self.odm2_sqlite_file_name,
                                        self.user)
        # there should no content file
        self.assertEqual(self.resTimeSeries.files.all().count(), 0)

        # test the core metadata at this point
        self.assertNotEqual(self.resTimeSeries.metadata.title, None)

        # there should be an abstract element
        self.assertNotEqual(self.resTimeSeries.metadata.description, None)

        # there should be one creator element
        self.assertEqual(self.resTimeSeries.metadata.creators.all().count(), 1)

        # there should be one contributor element
        self.assertEqual(self.resTimeSeries.metadata.contributors.all().count(), 1)

        # there should be 2 coverage element -  point type and period type
        self.assertEqual(self.resTimeSeries.metadata.coverages.all().count(), 2)
        self.assertEqual(self.resTimeSeries.metadata.coverages.all().filter(type='box').count(), 1)
        self.assertEqual(self.resTimeSeries.metadata.coverages.all().filter(
            type='period').count(), 1)
        # there should be no format element
        self.assertEqual(self.resTimeSeries.metadata.formats.all().count(), 0)
        # there should be one subject element
        self.assertEqual(self.resTimeSeries.metadata.subjects.all().count(), 1)

        # testing extended metadata elements
        self.assertNotEqual(self.resTimeSeries.metadata.sites.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.variables.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.methods.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.processing_levels.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.time_series_results.all().count(), 0)

        self.assertNotEqual(self.resTimeSeries.metadata.cv_variable_names.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.cv_variable_types.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.cv_speciations.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.cv_site_types.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.cv_elevation_datums.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.cv_method_types.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.cv_statuses.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.cv_mediums.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.cv_aggregation_statistics.all().count(), 0)

    def test_metadata_delete_on_resource_delete(self):
        # all metadata should get deleted when the resource get deleted

        # generate metadata by adding a valid odm2 sqlite file
        files = [UploadedFile(file=self.odm2_sqlite_file_obj, name=self.odm2_sqlite_file_name)]
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files,
                                            user=self.user, extract_metadata=False)

        utils.resource_file_add_process(resource=self.resTimeSeries, files=files, user=self.user,
                                        extract_metadata=True)

        # before resource delete
        core_metadata_obj = self.resTimeSeries.metadata
        self.assertEqual(CoreMetaData.objects.all().count(), 1)
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

        # CV lookup data
        self.assertEqual(core_metadata_obj.cv_variable_types.all().count(), 23)
        self.assertEqual(CVVariableType.objects.all().count(), 23)
        self.assertEqual(core_metadata_obj.cv_variable_names.all().count(), 805)
        self.assertEqual(CVVariableName.objects.all().count(), 805)
        self.assertEqual(core_metadata_obj.cv_speciations.all().count(), 145)
        self.assertEqual(CVSpeciation.objects.all().count(), 145)
        self.assertEqual(core_metadata_obj.cv_elevation_datums.all().count(), 5)
        self.assertEqual(CVElevationDatum.objects.all().count(), 5)
        self.assertEqual(core_metadata_obj.cv_site_types.all().count(), 51)
        self.assertEqual(CVSiteType.objects.all().count(), 51)
        self.assertEqual(core_metadata_obj.cv_method_types.all().count(), 25)
        self.assertEqual(CVMethodType.objects.all().count(), 25)
        self.assertEqual(core_metadata_obj.cv_units_types.all().count(), 179)
        self.assertEqual(CVUnitsType.objects.all().count(), 179)
        self.assertEqual(core_metadata_obj.cv_statuses.all().count(), 4)
        self.assertEqual(CVStatus.objects.all().count(), 4)
        self.assertEqual(core_metadata_obj.cv_mediums.all().count(), 18)
        self.assertEqual(CVMedium.objects.all().count(), 18)
        self.assertEqual(core_metadata_obj.cv_aggregation_statistics.all().count(), 17)
        self.assertEqual(CVAggregationStatistic.objects.all().count(), 17)

        # add the UTCOffset element which is only relevant in case of resource having a csv file
        self.resTimeSeries.metadata.create_element('UTCOffset', value=-7.5,
                                                   series_ids=['yyi123', '789ghjk'])
        self.assertTrue(UTCOffSet.objects.filter(object_id=core_metadata_obj.id).exists())

        # delete resource
        hydroshare.delete_resource(self.resTimeSeries.short_id)
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

        # there should not be any UTCOffset element
        self.assertFalse(UTCOffSet.objects.filter(object_id=core_metadata_obj.id).exists())

        # check CV lookup tables are empty
        self.assertEqual(CVVariableType.objects.all().count(), 0)
        self.assertEqual(CVVariableName.objects.all().count(), 0)
        self.assertEqual(CVSpeciation.objects.all().count(), 0)
        self.assertEqual(CVElevationDatum.objects.all().count(), 0)
        self.assertEqual(CVSiteType.objects.all().count(), 0)
        self.assertEqual(CVMethodType.objects.all().count(), 0)
        self.assertEqual(CVUnitsType.objects.all().count(), 0)
        self.assertEqual(CVStatus.objects.all().count(), 0)
        self.assertEqual(CVMedium.objects.all().count(), 0)
        self.assertEqual(CVAggregationStatistic.objects.all().count(), 0)

    def test_extended_metadata_CRUD(self):
        # create
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, False)
        self.assertEqual(self.resTimeSeries.metadata.sites.all().count(), 0)
        self.resTimeSeries.metadata.create_element('site', series_ids=['a456789-89yughys'],
                                                   site_code='LR_WaterLab_AA',
                                                   site_name='Logan River at the Utah Water '
                                                             'Research Laboratory west bridge',
                                                   elevation_m=1414,
                                                   elevation_datum='EGM96',
                                                   site_type='Stream',
                                                   latitude=65.789,
                                                   longitude=120.56789)

        site_element = self.resTimeSeries.metadata.sites.all().first()
        self.assertEqual(len(site_element.series_ids), 1)
        self.assertIn('a456789-89yughys', site_element.series_ids)
        self.assertEqual(site_element.site_code, 'LR_WaterLab_AA')
        self.assertEqual(site_element.site_name, 'Logan River at the Utah Water Research '
                                                 'Laboratory west bridge')
        self.assertEqual(site_element.elevation_m, 1414)
        self.assertEqual(site_element.elevation_datum, 'EGM96')
        self.assertEqual(site_element.site_type, 'Stream')
        self.assertEqual(site_element.is_dirty, False)

        self.assertEqual(self.resTimeSeries.metadata.is_dirty, False)

        self.assertEqual(self.resTimeSeries.metadata.variables.all().count(), 0)
        self.resTimeSeries.metadata.create_element('variable', series_ids=['a456789-89yughys'],
                                                   variable_code='ODO',
                                                   variable_name='Oxygen, dissolved',
                                                   variable_type='Concentration',
                                                   no_data_value=-9999,
                                                   variable_definition='Concentration of oxygen '
                                                                       'gas dissolved in water.',
                                                   speciation='Not Applicable')

        variable_element = self.resTimeSeries.metadata.variables.all().first()
        self.assertEqual(len(variable_element.series_ids), 1)
        self.assertIn('a456789-89yughys', variable_element.series_ids)
        self.assertEqual(variable_element.variable_code, 'ODO')
        self.assertEqual(variable_element.variable_name, 'Oxygen, dissolved')
        self.assertEqual(variable_element.variable_type, 'Concentration')
        self.assertEqual(variable_element.no_data_value, -9999)
        self.assertEqual(variable_element.variable_definition, 'Concentration of oxygen gas '
                                                               'dissolved in water.')
        self.assertEqual(variable_element.speciation, 'Not Applicable')
        self.assertEqual(variable_element.is_dirty, False)

        self.assertEqual(self.resTimeSeries.metadata.is_dirty, False)

        self.assertEqual(self.resTimeSeries.metadata.methods.all().count(), 0)
        self.resTimeSeries.metadata.create_element('method', series_ids=['a456789-89yughys'],
                                                   method_code='Code59',
                                                   method_name='Optical DO',
                                                   method_type='Instrument deployment',
                                                   method_description='Dissolved oxygen '
                                                                      'concentration measured '
                                                                      'optically using a YSI EXO '
                                                                      'multi-parameter water '
                                                                      'quality sonde.',
                                                   method_link='http://www.exowater.com')

        method_element = self.resTimeSeries.metadata.methods.all().first()
        self.assertEqual(len(method_element.series_ids), 1)
        self.assertIn('a456789-89yughys', method_element.series_ids)
        self.assertEqual(method_element.method_code, 'Code59')
        self.assertEqual(method_element.method_name, 'Optical DO')
        self.assertEqual(method_element.method_type, 'Instrument deployment')
        method_desc = 'Dissolved oxygen concentration measured optically using a YSI EXO ' \
                      'multi-parameter water quality sonde.'
        self.assertEqual(method_element.method_description, method_desc)
        self.assertEqual(method_element.method_link, 'http://www.exowater.com')
        self.assertEqual(method_element.is_dirty, False)

        self.assertEqual(self.resTimeSeries.metadata.is_dirty, False)

        self.assertEqual(self.resTimeSeries.metadata.processing_levels.all().count(), 0)
        exp_text = """Raw and unprocessed data and data products that have not undergone quality
        control. Depending on the variable, data type, and data transmission system, raw data may
        be available within seconds or minutes after the measurements have been made. Examples
        include real time precipitation, streamflow and water quality measurements."""
        self.resTimeSeries.metadata.create_element('processinglevel',
                                                   series_ids=['a456789-89yughys'],
                                                   processing_level_code='0',
                                                   definition='Raw data',
                                                   explanation=exp_text)

        proc_level_element = self.resTimeSeries.metadata.processing_levels.all().first()
        self.assertEqual(len(proc_level_element.series_ids), 1)
        self.assertIn('a456789-89yughys', proc_level_element.series_ids)
        self.assertEqual(proc_level_element.processing_level_code, '0')
        self.assertEqual(proc_level_element.definition, 'Raw data')
        self.assertEqual(proc_level_element.explanation, exp_text)
        self.assertEqual(proc_level_element.is_dirty, False)

        self.assertEqual(self.resTimeSeries.metadata.is_dirty, False)

        self.assertEqual(self.resTimeSeries.metadata.time_series_results.all().count(), 0)
        self.resTimeSeries.metadata.create_element('timeseriesresult',
                                                   series_ids=['a456789-89yughys'],
                                                   units_type='Concentration',
                                                   units_name='milligrams per liter',
                                                   units_abbreviation='mg/L',
                                                   status='Complete',
                                                   sample_medium='Surface water',
                                                   value_count=11283,
                                                   aggregation_statistics="Average")

        ts_result_element = self.resTimeSeries.metadata.time_series_results.all().first()
        self.assertEqual(len(ts_result_element.series_ids), 1)
        self.assertIn('a456789-89yughys', ts_result_element.series_ids)
        self.assertEqual(ts_result_element.units_type, 'Concentration')
        self.assertEqual(ts_result_element.units_name, 'milligrams per liter')
        self.assertEqual(ts_result_element.units_abbreviation, 'mg/L')
        self.assertEqual(ts_result_element.status, 'Complete')
        self.assertEqual(ts_result_element.sample_medium, 'Surface water')
        self.assertEqual(ts_result_element.value_count, 11283)
        self.assertEqual(ts_result_element.aggregation_statistics, 'Average')
        self.assertEqual(ts_result_element.is_dirty, False)

        self.assertEqual(self.resTimeSeries.metadata.is_dirty, False)

        # update - updating of any element should set the is_dirty attribute of metadata to True
        self.resTimeSeries.metadata.update_element(
            'site', self.resTimeSeries.metadata.sites.all().first().id,
            site_code='LR_WaterLab_BB', site_name='Logan River at the Utah WRL west bridge',
            elevation_m=1515, elevation_datum='EGM97', site_type='Stream flow')

        self.assertEqual(self.resTimeSeries.metadata.sites.all().count(), 1)
        site_element = self.resTimeSeries.metadata.sites.all().first()
        self.assertEqual(site_element.site_code, 'LR_WaterLab_BB')
        self.assertEqual(site_element.site_name, 'Logan River at the Utah WRL west bridge')
        self.assertEqual(site_element.elevation_m, 1515)
        self.assertEqual(site_element.elevation_datum, 'EGM97')
        self.assertEqual(site_element.site_type, 'Stream flow')
        self.assertEqual(site_element.is_dirty, True)

        # the 'is_dirty' flag of metadata be True
        self.resTimeSeries.metadata.refresh_from_db()
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, True)

        self.resTimeSeries.metadata.update_element(
            'variable', self.resTimeSeries.metadata.variables.all().first().id,
            variable_code='ODO-1', variable_name='H2O dissolved',
            variable_type='Concentration-1', no_data_value=-999,
            variable_definition='Concentration of oxygen dissolved in water.',
            speciation='Applicable')

        variable_element = self.resTimeSeries.metadata.variables.all().first()
        self.assertEqual(variable_element.variable_code, 'ODO-1')
        self.assertEqual(variable_element.variable_name, 'H2O dissolved')
        self.assertEqual(variable_element.variable_type, 'Concentration-1')
        self.assertEqual(variable_element.no_data_value, -999)
        self.assertEqual(variable_element.variable_definition,
                         'Concentration of oxygen dissolved in water.')
        self.assertEqual(variable_element.speciation, 'Applicable')
        self.assertEqual(variable_element.is_dirty, True)
        self.resTimeSeries.metadata.refresh_from_db()
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, True)

        method_desc = 'Dissolved oxygen concentration measured optically using a YSI EXO ' \
                      'multi-parameter water quality sonde-1.'
        self.resTimeSeries.metadata.update_element(
            'method', self.resTimeSeries.metadata.methods.all().first().id,
            method_code='Code 69', method_name='Optical DO-1',
            method_type='Instrument deployment-1',
            method_description=method_desc, method_link='http://www.ex-water.com')

        method_element = self.resTimeSeries.metadata.methods.all().first()
        self.assertEqual(method_element.method_code, 'Code 69')
        self.assertEqual(method_element.method_name, 'Optical DO-1')
        self.assertEqual(method_element.method_type, 'Instrument deployment-1')

        self.assertEqual(method_element.method_description, method_desc)
        self.assertEqual(method_element.method_link, 'http://www.ex-water.com')
        self.assertEqual(method_element.is_dirty, True)
        self.resTimeSeries.metadata.refresh_from_db()
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, True)

        self.resTimeSeries.metadata.update_element(
            'processinglevel', self.resTimeSeries.metadata.processing_levels.all().first().id,
            processing_level_code='9', definition='data', explanation=exp_text + 'some more text')

        proc_level_element = self.resTimeSeries.metadata.processing_levels.all().first()
        self.assertEqual(proc_level_element.processing_level_code, '9')
        self.assertEqual(proc_level_element.definition, 'data')
        self.assertEqual(proc_level_element.explanation, exp_text + 'some more text')
        self.assertEqual(proc_level_element.is_dirty, True)

        self.resTimeSeries.metadata.refresh_from_db()
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, True)

        self.resTimeSeries.metadata.update_element(
            'timeseriesresult', self.resTimeSeries.metadata.time_series_results.all().first().id,
            units_type='Concentration-1',
            units_name='milligrams per GL', units_abbreviation='mg/GL', status='Incomplete',
            sample_medium='Fresh water', value_count=11211, aggregation_statistics="Mean")

        ts_result_element = self.resTimeSeries.metadata.time_series_results.all().first()
        self.assertEqual(ts_result_element.units_type, 'Concentration-1')
        self.assertEqual(ts_result_element.units_name, 'milligrams per GL')
        self.assertEqual(ts_result_element.units_abbreviation, 'mg/GL')
        self.assertEqual(ts_result_element.status, 'Incomplete')
        self.assertEqual(ts_result_element.sample_medium, 'Fresh water')
        self.assertEqual(ts_result_element.value_count, 11211)
        self.assertEqual(ts_result_element.aggregation_statistics, 'Mean')
        self.assertEqual(ts_result_element.is_dirty, True)

        self.resTimeSeries.metadata.refresh_from_db()
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, True)

        # delete
        # extended metadata deletion is not allowed - should raise exception
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.delete_element(
                'site', self.resTimeSeries.metadata.sites.all().first().id)

        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.delete_element(
                'variable', self.resTimeSeries.metadata.variables.all().first().id)

        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.delete_element(
                'method', self.resTimeSeries.metadata.methods.all().first().id)

        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.delete_element(
                'processinglevel', self.resTimeSeries.metadata.processing_levels.all().first().id)
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.delete_element(
                'timeseriesresult',
                self.resTimeSeries.metadata.time_series_results.all().first().id)

    def test_metadata_is_dirty_flag(self):
        # resource.metadata.is_dirty flag be set to True if any of the resource specific
        # metadata elements is updated

        # create a resource with uploded sqlite file
        self.odm2_sqlite_file_obj = open(self.odm2_sqlite_file, 'r')

        self.resTimeSeries = hydroshare.create_resource(
            resource_type='TimeSeriesResource',
            owner=self.user,
            title='My Test TimeSeries Resource',
            files=(self.odm2_sqlite_file_obj,)
            )
        utils.resource_post_create_actions(resource=self.resTimeSeries, user=self.user, metadata=[])

        # updating the core metadata element title should also set the metadata is_dirty to True
        title = self.resTimeSeries.metadata.title
        self.resTimeSeries.metadata.update_element('title', title.id, value="New Resource Title")
        # at this point the is_dirty be set to true
        self.resTimeSeries.metadata.refresh_from_db()
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, True)
        # reset metadata is_dirty to false
        TimeSeriesMetaData.objects.filter(id=self.resTimeSeries.metadata.id).update(is_dirty=False)

        # updating the core metadata element Description (Abstract) should also set the
        # metadata is_dirty to True
        description = self.resTimeSeries.metadata.description
        self.resTimeSeries.metadata.update_element('description', description.id,
                                                   value="New abstract")
        # at this point the is_dirty be set to trye
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, True)
        # reset metadata is_dirty to false
        TimeSeriesMetaData.objects.filter(id=self.resTimeSeries.metadata.id).update(is_dirty=False)

        # test with resource specific metadata elements
        site = self.resTimeSeries.metadata.sites.all().first()
        self.assertEqual(site.is_dirty, False)
        # now update the site element
        self.resTimeSeries.metadata.update_element('site', site.id,
                                                   site_code='LR_WaterLab_BB',
                                                   site_name='Logan River at the Utah WRL west '
                                                             'bridge',
                                                   elevation_m=1515,
                                                   elevation_datum=site.elevation_datum,
                                                   site_type=site.site_type)

        site = self.resTimeSeries.metadata.sites.filter(id=site.id).first()
        self.assertEqual(site.is_dirty, True)
        # at this point the is_dirty for metadata must be true
        self.resTimeSeries.metadata.refresh_from_db()
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, True)

        # rest metadata is_dirty to false
        TimeSeriesMetaData.objects.filter(id=self.resTimeSeries.metadata.id).update(is_dirty=False)

        # at this point the is_dirty must be false for metadata
        self.resTimeSeries.metadata.refresh_from_db()
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, False)

        # test 'is_dirty' with update of the Variable element
        variable = self.resTimeSeries.metadata.variables.all().first()
        self.assertEqual(variable.is_dirty, False)
        # now update the variable element
        self.resTimeSeries.metadata.update_element('variable', variable.id,
                                                   variable_code='USU37',
                                                   variable_name=variable.variable_name,
                                                   variable_type=variable.variable_type,
                                                   no_data_value=variable.no_data_value,
                                                   speciation=variable.speciation)

        variable = self.resTimeSeries.metadata.variables.filter(id=variable.id).first()
        self.assertEqual(variable.is_dirty, True)
        # at this point the is_dirty must be true for metadata
        self.resTimeSeries.metadata.refresh_from_db()
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, True)
        # reset metadata is_dirty to false
        TimeSeriesMetaData.objects.filter(id=self.resTimeSeries.metadata.id).update(is_dirty=False)

        # at this point the is_dirty must be false for metadata
        self.resTimeSeries.metadata.refresh_from_db()
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, False)

        # test 'is_dirty' with update of the Method element
        method = self.resTimeSeries.metadata.methods.all().first()
        self.assertEqual(method.is_dirty, False)
        # now update the method element
        self.resTimeSeries.metadata.update_element('method', variable.id,
                                                   method_code='30',
                                                   method_name=method.method_name,
                                                   method_type=method.method_type,
                                                   method_description=method.method_description,
                                                   method_link=method.method_link)

        method = self.resTimeSeries.metadata.methods.filter(id=method.id).first()
        self.assertEqual(method.is_dirty, True)
        # at this point the is_dirty must be true
        self.resTimeSeries.metadata.refresh_from_db()
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, True)
        # reset metadata is_dirty to false
        TimeSeriesMetaData.objects.filter(id=self.resTimeSeries.metadata.id).update(is_dirty=False)

        # at this point the is_dirty must be false for metadata
        self.resTimeSeries.metadata.refresh_from_db()
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, False)

        # test 'is_dirty' with update of the ProcessingLevel element
        proc_level = self.resTimeSeries.metadata.processing_levels.all().first()
        self.assertEqual(proc_level.is_dirty, False)
        # now update the processinglevel element
        self.resTimeSeries.metadata.update_element('processinglevel', proc_level.id,
                                                   processing_level_code='2')

        proc_level = self.resTimeSeries.metadata.processing_levels.filter(id=proc_level.id).first()
        self.assertEqual(proc_level.is_dirty, True)
        # at this point the is_dirty must be true
        self.resTimeSeries.metadata.refresh_from_db()
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, True)
        # reset metadata is_dirty to false
        TimeSeriesMetaData.objects.filter(id=self.resTimeSeries.metadata.id).update(is_dirty=False)

        # at this point the is_dirty must be false for metadata
        self.resTimeSeries.metadata.refresh_from_db()
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, False)

        # test 'is_dirty' with update of the TimeSeriesResult element
        ts_result = self.resTimeSeries.metadata.time_series_results.all().first()
        self.assertEqual(ts_result.is_dirty, False)
        # now update the timeseriesresult element
        self.resTimeSeries.metadata.update_element('timeseriesresult', ts_result.id,
                                                   value_count=1500
                                                   )

        ts_result = self.resTimeSeries.metadata.time_series_results.filter(id=ts_result.id).first()
        self.assertEqual(ts_result.is_dirty, True)
        # at this point the is_dirty must be true
        self.resTimeSeries.metadata.refresh_from_db()
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, True)
        # reset metadata is_dirty to false
        TimeSeriesMetaData.objects.filter(id=self.resTimeSeries.metadata.id).update(is_dirty=False)
        # at this point the is_dirty must be false for metadata
        self.resTimeSeries.metadata.refresh_from_db()
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, False)

    def test_cv_lookup_tables_for_new_terms(self):
        # Here we will test that when new CV terms are used for updating metadata elements,
        # there should be new records added to the corresponding CV table (Django db table)

        # create a resource with uploded sqlite file
        self.odm2_sqlite_file_obj = open(self.odm2_sqlite_file, 'r')

        self.resTimeSeries = hydroshare.create_resource(
            resource_type='TimeSeriesResource',
            owner=self.user,
            title='My Test TimeSeries Resource',
            files=(self.odm2_sqlite_file_obj,)
            )
        utils.resource_post_create_actions(resource=self.resTimeSeries, user=self.user, metadata=[])

        # test for CV lookup tables

        # there should be 23 CV_VariableType records
        self.assertEqual(self.resTimeSeries.metadata.cv_variable_types.all().count(), 23)
        # now update the variable element with a new term for the variable type
        variable = self.resTimeSeries.metadata.variables.all().first()
        self.resTimeSeries.metadata.update_element('variable', variable.id,
                                                   variable_type="Variable type-1"
                                                   )

        # check the auto generated term
        self.assertIn('variableType_1', [var_type.term for var_type in
                                         self.resTimeSeries.metadata.cv_variable_types.all()])

        # there should be 24 CV_VariableType records
        self.assertEqual(self.resTimeSeries.metadata.cv_variable_types.all().count(), 24)

        # there should be 805 CV_VariableName records
        self.assertEqual(self.resTimeSeries.metadata.cv_variable_names.all().count(), 805)
        # now update the variable element with a new term for the variable name
        self.resTimeSeries.metadata.update_element('variable', variable.id,
                                                   variable_name="Variable name-1"
                                                   )
        # check the auto generated term
        self.assertIn('variableName_1', [var_name.term for var_name in
                                         self.resTimeSeries.metadata.cv_variable_names.all()])
        # there should be 806 CV_VariableName records
        self.assertEqual(self.resTimeSeries.metadata.cv_variable_names.all().count(), 806)

        # there should be 145 CV_Speciation records
        self.assertEqual(self.resTimeSeries.metadata.cv_speciations.all().count(), 145)
        # now update the variable element with a new term for the speciation
        self.resTimeSeries.metadata.update_element('variable', variable.id,
                                                   speciation="Speciation name-1"
                                                   )
        # check the auto generated term
        self.assertIn('speciationName_1', [spec.term for spec in
                                           self.resTimeSeries.metadata.cv_speciations.all()])

        # there should be now 146 CV_Speciation records
        self.assertEqual(self.resTimeSeries.metadata.cv_speciations.all().count(), 146)

        # there should be 51 CV_SiteType records
        self.assertEqual(self.resTimeSeries.metadata.cv_site_types.all().count(), 51)
        site = self.resTimeSeries.metadata.sites.all().first()
        # now update the site element with a new term for the site type
        self.resTimeSeries.metadata.update_element('site', site.id,
                                                   site_type="Site type-1"
                                                   )
        # check the auto generated term
        self.assertIn('siteType_1', [site_type.term for site_type in
                                     self.resTimeSeries.metadata.cv_site_types.all()])

        # there should be 52 CV_SiteType records
        self.assertEqual(self.resTimeSeries.metadata.cv_site_types.all().count(), 52)

        # there should be 5 CV_ElevationDatum records
        self.assertEqual(self.resTimeSeries.metadata.cv_elevation_datums.all().count(), 5)
        # now update the site element with a new term for the elevation datum
        self.resTimeSeries.metadata.update_element('site', site.id,
                                                   elevation_datum="Elevation datum-1"
                                                   )
        # check the auto generated term
        self.assertIn('elevationDatum_1', [ele_datum.term for ele_datum in
                                           self.resTimeSeries.metadata.cv_elevation_datums.all()])

        # there should be 6 CV_ElevationDatum records
        self.assertEqual(self.resTimeSeries.metadata.cv_elevation_datums.all().count(), 6)

        # there should be 25 CV_MethodType records
        self.assertEqual(self.resTimeSeries.metadata.cv_method_types.all().count(), 25)
        method = self.resTimeSeries.metadata.methods.all().first()
        # now update the method element with a new term for the method type
        self.resTimeSeries.metadata.update_element('method', method.id,
                                                   method_type="Method type-1"
                                                   )

        # check the auto generated term
        self.assertIn('methodType_1', [method_type.term for method_type in
                                       self.resTimeSeries.metadata.cv_method_types.all()])
        # there should be 26 CV_MethodType records
        self.assertEqual(self.resTimeSeries.metadata.cv_method_types.all().count(), 26)

        # there should be 179 CV_UnitsType records
        self.assertEqual(self.resTimeSeries.metadata.cv_units_types.all().count(), 179)
        ts_result = self.resTimeSeries.metadata.time_series_results.all().first()
        # now update the timeseriesresult element with a new term for the units type
        self.resTimeSeries.metadata.update_element('timeseriesresult', ts_result.id,
                                                   units_type="Units type-1"
                                                   )
        # check the auto generated term
        self.assertIn('unitsType_1', [units_type.term for units_type in
                                      self.resTimeSeries.metadata.cv_units_types.all()])
        # there should be 180 CV_UnitsType records
        self.assertEqual(self.resTimeSeries.metadata.cv_units_types.all().count(), 180)

        # there should be 4 CV_Status records
        self.assertEqual(self.resTimeSeries.metadata.cv_statuses.all().count(), 4)
        # now update the timeseriesresult element with a new term for the status
        self.resTimeSeries.metadata.update_element('timeseriesresult', ts_result.id,
                                                   status="Status type-1"
                                                   )
        # check the auto generated term
        self.assertIn('statusType_1', [status_type.term for status_type in
                                       self.resTimeSeries.metadata.cv_statuses.all()])
        # there should be 5 CV_Status records
        self.assertEqual(self.resTimeSeries.metadata.cv_statuses.all().count(), 5)

        # there should be 18 CV_Medium records. sqlite file CV_Medium table
        # contains 17 records and one more is added as a result of creating TimeSeriesResult
        # element. The Results table has SampleMediumCV value that's is not in CV_Medium table
        # therefore an additional CVMedium metadata element is created
        self.assertEqual(self.resTimeSeries.metadata.cv_mediums.all().count(), 18)
        # now update the timeseriesresult element with a new term for sample medium
        self.resTimeSeries.metadata.update_element('timeseriesresult', ts_result.id,
                                                   sample_medium="Sample medium-1"
                                                   )
        # check the auto generated term
        self.assertIn('sampleMedium_1', [s_medium.term for s_medium in
                                         self.resTimeSeries.metadata.cv_mediums.all()])

        # there should be 19 CV_Medium records
        self.assertEqual(self.resTimeSeries.metadata.cv_mediums.all().count(), 19)

        # there should be 17 CV_aggregationStatistics records
        self.assertEqual(self.resTimeSeries.metadata.cv_aggregation_statistics.all().count(), 17)
        # now update the timeseriesresult element with a new term for aggregation statistics
        self.resTimeSeries.metadata.update_element('timeseriesresult', ts_result.id,
                                                   aggregation_statistics="Aggregation statistics-1"
                                                   )
        # check the auto generated term
        self.assertIn('aggregationStatistics_1',
                      [agg_stat.term for agg_stat in
                       self.resTimeSeries.metadata.cv_aggregation_statistics.all()])
        # there should be 18 CV_aggregationStatistics records
        self.assertEqual(self.resTimeSeries.metadata.cv_aggregation_statistics.all().count(), 18)

    def test_metadata_is_dirty_on_sqlfile_delete(self):
        # upon delete of the sqlite file, the 'is_dirty' attribute of the metadata object
        # should be set to False

        # there should not be any file in the resource
        self.assertEqual(self.resTimeSeries.files.all().count(), 0)
        self._upload_valid_sqlite_file()

        # there should be one file in the resource
        self.assertEqual(self.resTimeSeries.files.all().count(), 1)

        # editing a resource specific metadata should set the is_dirty attribute of metadata object
        # to True
        site = self.resTimeSeries.metadata.sites.all().first()
        self.assertEqual(site.is_dirty, False)
        # now update the site element
        self.resTimeSeries.metadata.update_element('site', site.id,
                                                   site_code='LR_WaterLab_BB',
                                                   site_name='Logan River at the Utah WRL west '
                                                             'bridge',
                                                   elevation_m=1515,
                                                   elevation_datum=site.elevation_datum,
                                                   site_type=site.site_type)

        site = self.resTimeSeries.metadata.sites.filter(id=site.id).first()
        self.assertEqual(site.is_dirty, True)
        # at this point the is_dirty for metadata must be true
        self.resTimeSeries.metadata.refresh_from_db()
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, True)

        # delete content file that we added above
        hydroshare.delete_resource_file(self.resTimeSeries.short_id, self.odm2_sqlite_file_name,
                                        self.user)
        # there should not be any file in the resource
        self.assertEqual(self.resTimeSeries.files.all().count(), 0)
        # at this point the is_dirty for metadata must be false
        self.resTimeSeries.metadata.refresh_from_db()
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, False)

    def test_metadata_is_dirty_on_csv_file_delete(self):
        # upon delete of the csv file, the 'is_dirty' attribute of the metadata object
        # should be set to False

        # there should not be any file in the resource
        self.assertEqual(self.resTimeSeries.files.all().count(), 0)

        # add csv file to the resource - it should automatically add the blank sqlite file
        self._upload_valid_csv_file()

        # there should be 2 files in the resource
        self.assertEqual(self.resTimeSeries.files.all().count(), 2)
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, False)

        # create a site element
        self.resTimeSeries.metadata.create_element('site', series_ids=['0'],
                                                   site_code='Temp_DegC_Mendon',
                                                   site_name='Logan River at the Utah Water '
                                                             'Research Laboratory west bridge',
                                                   elevation_m=1414,
                                                   elevation_datum='EGM96',
                                                   site_type='Stream',
                                                   latitude=65.789,
                                                   longitude=120.56789)

        # added site element should be dirty
        site = self.resTimeSeries.metadata.sites.all().first()
        self.assertEqual(site.is_dirty, True)
        # at this point the is_dirty for metadata must be true
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, True)

        # delete content file that we added above
        hydroshare.delete_resource_file(self.resTimeSeries.short_id, self.odm2_csv_file_name,
                                        self.user)

        # there should  be 1 file in the resource
        self.assertEqual(self.resTimeSeries.files.all().count(), 1)
        # at this point the is_dirty for metadata must be false
        self.resTimeSeries.metadata.refresh_from_db()
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, False)

    def test_has_sqlite_file(self):
        # here we are testing the property has_sqlite_file
        # the resource should not have a sqlite file at this point
        self.assertFalse(self.resTimeSeries.has_sqlite_file)
        # add a valid odm2 sqlite file
        self._upload_valid_sqlite_file()

        # the resource should have a sqlite file at this point
        self.assertTrue(self.resTimeSeries.has_sqlite_file)

    def test_has_csv_file(self):
        # here we are testing the property has_sqlite_file
        # the resource should not have a csv file at this point
        self.assertFalse(self.resTimeSeries.has_csv_file)
        # add a csv file
        self._upload_valid_csv_file()

        # the resource should have a sqlite file at this point
        self.assertTrue(self.resTimeSeries.has_csv_file)

    def test_get_xml(self):
        # add a valid odm2 sqlite file to generate metadata
        self._upload_valid_sqlite_file()

        # test if xml from get_xml() is well formed
        ET.fromstring(self.resTimeSeries.metadata.get_xml())

    def test_can_have_multiple_content_files(self):
        # timeseries resource can have multiple files (csv and sqlite)
        self.assertTrue(TimeSeriesResource.can_have_multiple_files())

    def test_can_upload_multiple_content_files(self):
        # only one file can be uploaded
        self.assertFalse(TimeSeriesResource.allow_multiple_file_upload())

    def test_public_or_discoverable(self):
        self.assertFalse(self.resTimeSeries.has_required_content_files())
        self.assertFalse(self.resTimeSeries.metadata.has_all_required_elements())
        self.assertFalse(self.resTimeSeries.can_be_public_or_discoverable)

        # adding a valid ODM2 sqlite file should generate required core metadata and all
        # extended metadata
        self._upload_valid_sqlite_file()

        self.assertTrue(self.resTimeSeries.has_required_content_files())
        self.assertTrue(self.resTimeSeries.metadata.has_all_required_elements())
        self.assertTrue(self.resTimeSeries.can_be_public_or_discoverable)

    def test_has_required_content_files(self):
        # test that sqlite file is the require content file

        self.assertFalse(self.resTimeSeries.has_required_content_files())

        # upload a sqlite file
        self._upload_valid_sqlite_file()
        self.assertTrue(self.resTimeSeries.has_required_content_files())

        # delete the sqlite file that was added above
        hydroshare.delete_resource_file(self.resTimeSeries.short_id, self.odm2_sqlite_file_name,
                                        self.user)

        self.assertFalse(self.resTimeSeries.has_required_content_files())

        # add a csv file which should add the blank sqlie file
        self._upload_valid_csv_file()
        self.assertTrue(self.resTimeSeries.has_required_content_files())

    def test_csv_file_upload(self):
        # adding a valid csv file should be successful
        # the resource metadata object will have the data column headings

        self.assertEqual(self.resTimeSeries.metadata.title.value, 'Test Time Series Resource')
        self._test_no_change_in_metadata()

        # there shouldn't any format element
        self.assertEqual(self.resTimeSeries.metadata.formats.all().count(), 0)

        # there shouldn't any coverage element
        self.assertEqual(self.resTimeSeries.metadata.coverages.all().count(), 0)

        # at this point the resource should not have any content files
        self.assertEqual(self.resTimeSeries.files.all().count(), 0)

        # at this point there should not be any series names associated with the metadata object
        self.assertEqual(len(self.resTimeSeries.metadata.series_names), 0)

        # add a valid csv file to the resource - this automatically add the blank sqlite file
        self._upload_valid_csv_file()

        # at this point the resource should have 2 content file
        self.assertEqual(self.resTimeSeries.files.all().count(), 2)

        csv_file = utils.get_resource_files_by_extension(self.resTimeSeries, '.csv')[0]

        _, csv_file_name, _ = utils.get_resource_file_name_and_extension(csv_file)
        self.assertEqual(csv_file_name, self.odm2_csv_file_name)

        # since the uploaded csv file has 2 data columns, the metadata should have 2 series names
        self.assertEqual(len(self.resTimeSeries.metadata.series_names), 2)
        csv_data_colum_names = set(['Temp_DegC_Mendon', 'Temp_DegC_Paradise'])
        self.assertEqual(set(self.resTimeSeries.metadata.series_names), csv_data_colum_names)

        # since the uploaded csv file has 2 data columns, the metadata should have
        # the attribute value_counts (dict) 2 elements
        self.assertEqual(len(self.resTimeSeries.metadata.value_counts), 2)
        self.assertEqual(set(self.resTimeSeries.metadata.value_counts.keys()), csv_data_colum_names)

        # there should be 20 data values for each series
        self.assertEqual(self.resTimeSeries.metadata.value_counts['Temp_DegC_Mendon'], '20')
        self.assertEqual(self.resTimeSeries.metadata.value_counts['Temp_DegC_Paradise'], '20')

        # metadata is deleted on csv file upload - therefore the title change
        self.assertEqual(self.resTimeSeries.metadata.title.value, 'Untitled resource')
        self._test_no_change_in_metadata()
        # there should be  2 format elements - since the resource has a csv file and a sqlite file
        self.assertEqual(self.resTimeSeries.metadata.formats.all().count(), 2)

        # there should be 1 coverage element of type period
        self.assertEqual(self.resTimeSeries.metadata.coverages.all().count(), 1)
        self.assertEqual(self.resTimeSeries.metadata.coverages.filter(type='period').count(), 1)
        self.assertEqual(self.resTimeSeries.has_csv_file, True)

    def test_invalid_csv_file(self):
        # This file contains invalid number of data column headings
        invalid_csv_file_name = 'Invalid_Headings_Test_1.csv'
        self._test_invalid_csv_file(invalid_csv_file_name)

        # This file missing a data column heading
        invalid_csv_file_name = 'Invalid_Headings_Test_2.csv'
        self._test_invalid_csv_file(invalid_csv_file_name)

        # This file has an additional data column heading
        invalid_csv_file_name = 'Invalid_Headings_Test_3.csv'
        self._test_invalid_csv_file(invalid_csv_file_name)

        # This file contains a duplicate data column heading
        invalid_csv_file_name = 'Invalid_Headings_Test_4.csv'
        self._test_invalid_csv_file(invalid_csv_file_name)

        # This file has no data column heading
        invalid_csv_file_name = 'Invalid_Headings_Test_5.csv'
        self._test_invalid_csv_file(invalid_csv_file_name)

        # This file has not a CSV file
        invalid_csv_file_name = 'Invalid_format_Test.csv'
        self._test_invalid_csv_file(invalid_csv_file_name)

        # This file has a bad datetime value
        invalid_csv_file_name = 'Invalid_Data_Test_1.csv'
        self._test_invalid_csv_file(invalid_csv_file_name)

        # This file has a bad data value (not numeric)
        invalid_csv_file_name = 'Invalid_Data_Test_2.csv'
        self._test_invalid_csv_file(invalid_csv_file_name)

        # This file is missing a data value
        invalid_csv_file_name = 'Invalid_Data_Test_3.csv'
        self._test_invalid_csv_file(invalid_csv_file_name)

        # This file has a additional data value
        invalid_csv_file_name = 'Invalid_Data_Test_4.csv'
        self._test_invalid_csv_file(invalid_csv_file_name)

        # This file has no data values
        invalid_csv_file_name = 'Invalid_Data_Test_5.csv'
        self._test_invalid_csv_file(invalid_csv_file_name)

    def test_file_delete_on_file_upload(self):
        # this is to test that if a CSV file is uploaded then if the resource contains a
        # sqlite file that sqlite file will be deleted automatically
        # similarly if a sqlite file is uploaded, then the existing csv file will be deleted

        # upload a sqlite file
        self._upload_valid_sqlite_file()

        # at this point the resource should have one content file
        self.assertEqual(self.resTimeSeries.files.all().count(), 1)
        self.assertEqual(self.resTimeSeries.has_sqlite_file, True)
        res_file = self.resTimeSeries.files.all().first()

        _, file_name, file_ext = utils.get_resource_file_name_and_extension(res_file)
        self.assertEqual(file_name, self.odm2_sqlite_file_name)

        # now uploading of a csv file should delete the above uploaded sqlite file and
        # add the blank sqlite file (ODM2.sqlite)
        self._upload_valid_csv_file()
        # at this point the resource should 2 content files
        self.assertEqual(self.resTimeSeries.files.all().count(), 2)
        self.assertEqual(self.resTimeSeries.has_csv_file, True)
        self.assertEqual(self.resTimeSeries.has_sqlite_file, True)

        # get the sqlite file and check its name is ODM2.sqlite
        self.assertEqual(len(utils.get_resource_files_by_extension(self.resTimeSeries,
                                                                   '.sqlite')), 1)
        sqlite_file = utils.get_resource_files_by_extension(self.resTimeSeries, '.sqlite')[0]
        _, sqlite_file_name, _ = utils.get_resource_file_name_and_extension(sqlite_file)
        self.assertEqual(sqlite_file_name, 'ODM2.sqlite')

        # now uploading a sqlite file should delete the above uploaded csv file
        # first delete the existing sqlite file before we can upload a sqlite file
        hydroshare.delete_resource_file(self.resTimeSeries.short_id, 'ODM2.sqlite', self.user)

        self._upload_valid_sqlite_file()
        # at this point the resource should have one content file
        self.assertEqual(self.resTimeSeries.files.all().count(), 1)
        self.assertEqual(self.resTimeSeries.has_csv_file, False)
        self.assertEqual(self.resTimeSeries.has_sqlite_file, True)

    def test_populating_blank_sqlite_file(self):
        # This case applies to csv file upload only

        # at this point a blank sqlite file can't be added by the system
        # a blank sqlite file can be added to the resource after uploading a csv file
        # and entering all required metadata
        self.assertEqual(self.resTimeSeries.can_add_blank_sqlite_file, False)

        # first add a valid csv file to the resource - this also should add the blank sqlite file
        self._upload_valid_csv_file()

        # resource should have a sqlite file at this point
        self.assertEqual(self.resTimeSeries.has_sqlite_file, True)
        # resource should have a csv file at this point
        self.assertEqual(self.resTimeSeries.has_csv_file, True)

        # test the sqlite file is blank at this point
        self._test_sqlite_file_is_blank()

        # test that the value_count is set
        self.assertEqual(len(self.resTimeSeries.metadata.value_counts), 2)

        # test that the resource does not have all the required metadata elements at this point
        self.assertEqual(self.resTimeSeries.metadata.has_all_required_elements(), False)

        # with the upload of a csv file a temporal coverage element should have been created
        self.assertEqual(self.resTimeSeries.metadata.coverages.all().filter(type='period').count(),
                         1)
        # add/update core metadata -required elements
        self.resTimeSeries.metadata.update_element('title', self.resTimeSeries.metadata.title.id,
                                                   value="Multi-Site One Variable Time Series")

        self.resTimeSeries.metadata.create_element('description', abstract='Testing CSV File')

        self.resTimeSeries.metadata.create_element('subject', value='CSV')

        # add a contributor with organization
        self.resTimeSeries.metadata.create_element('contributor', name='John Smith',
                                                   organization='Utah State University')

        # add resource specific metadata

        # there should be no coverage element of type spatial before a site element is added
        self.assertEqual(self.resTimeSeries.metadata.sites.all().count(), 0)
        self.assertEqual(self.resTimeSeries.metadata.coverages.exclude(type='period').count(), 0)

        # add 2 site elements (one for each data column of the uploaded csv file)

        # since there are 2 data columns the valid series ids are 0 and 1
        self.resTimeSeries.metadata.create_element('site', series_ids=['0'],
                                                   site_code='Temp_DegC_Mendon',
                                                   site_name='Logan River at the Utah Water '
                                                             'Research Laboratory west bridge',
                                                   elevation_m=1414,
                                                   elevation_datum='EGM96',
                                                   site_type='Stream',
                                                   latitude=65.789,
                                                   longitude=120.56789)

        # there should be 1 site element at this point
        self.assertEqual(self.resTimeSeries.metadata.sites.all().count(), 1)
        # at this point the resource level coverage element should have been automatically created
        # there should be 2 coverage elements -  1 point type and the other one is temporal
        self.assertEqual(self.resTimeSeries.metadata.coverages.all().count(), 2)
        self.assertEqual(self.resTimeSeries.metadata.coverages.all().filter(type='point').count(),
                         1)
        site = self.resTimeSeries.metadata.sites.first()
        point_cov = self.resTimeSeries.metadata.coverages.all().filter(type='point').first()
        self.assertEqual(site.latitude, point_cov.value['north'])
        self.assertEqual(site.longitude, point_cov.value['east'])
        self.assertEqual(len(site.series_ids), 1)
        self.assertEqual(site.series_ids[0], '0')

        # add the 2nd site element
        self.resTimeSeries.metadata.create_element('site', series_ids=['1'],
                                                   site_code='Temp_DegC_Paradise',
                                                   site_name='Logan River at the Utah Water '
                                                             'Research Laboratory west bridge',
                                                   elevation_m=1414,
                                                   elevation_datum='EGM96',
                                                   site_type='Stream',
                                                   latitude=85.789,
                                                   longitude=110.56789)

        # there should be 2 site element at this point
        self.assertEqual(self.resTimeSeries.metadata.sites.all().count(), 2)
        site_1 = self.resTimeSeries.metadata.sites.all()[0]
        site_2 = self.resTimeSeries.metadata.sites.all()[1]
        self.assertEqual(len(site_1.series_ids), 1)
        self.assertEqual(len(site_2.series_ids), 1)
        self.assertEqual(set(site_1.series_ids + site_2.series_ids), set(['0', '1']))

        # there should be 1 coverage element -  box type and total 2 coverage elements
        self.assertEqual(self.resTimeSeries.metadata.coverages.all().count(), 2)
        self.assertEqual(self.resTimeSeries.metadata.coverages.all().filter(type='box').count(),
                         1)

        box_coverage = self.resTimeSeries.metadata.coverages.all().filter(type='box').first()
        # projection should be auto set to 'WGS 84 EPSG:4326'
        self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(box_coverage.value['northlimit'], 85.789)
        self.assertEqual(box_coverage.value['eastlimit'], 120.56789)
        self.assertEqual(box_coverage.value['southlimit'], 65.789)
        self.assertEqual(box_coverage.value['westlimit'], 110.56789)

        # test that the resource still does not have the required metadata elements at this point
        self.assertEqual(self.resTimeSeries.metadata.has_all_required_elements(), False)

        # add one variable element
        self.resTimeSeries.metadata.create_element('variable', series_ids=['0'],
                                                   variable_code='USU37',
                                                   variable_name='Temperature',
                                                   variable_type='Climate',
                                                   no_data_value=-999,
                                                   speciation='Not Applicable')

        # there should be 1 variable element at this point
        self.assertEqual(self.resTimeSeries.metadata.variables.all().count(), 1)
        variable = self.resTimeSeries.metadata.variables.first()
        self.assertEqual(len(variable.series_ids), 1)
        self.assertEqual(variable.series_ids[0], '0')

        # test that the resource still does not have the required metadata elements at this point
        self.assertEqual(self.resTimeSeries.metadata.has_all_required_elements(), False)

        # associate the same variable element with series id  1
        variable = self.resTimeSeries.metadata.variables.first()
        self.resTimeSeries.metadata.update_element('variable', variable.id, series_ids=['0', '1'])
        variable = self.resTimeSeries.metadata.variables.first()
        self.assertEqual(len(variable.series_ids), 2)
        self.assertIn('0', variable.series_ids)
        self.assertIn('1', variable.series_ids)

        # add 2 method elements - one for each series
        self.resTimeSeries.metadata.create_element('method', series_ids=['0'],
                                                   method_code='MC-30',
                                                   method_name='Testing method-1',
                                                   method_type='Data collection',
                                                   method_description=''
                                                   )

        # there should be 1 method element at this point
        self.assertEqual(self.resTimeSeries.metadata.methods.all().count(), 1)
        method = self.resTimeSeries.metadata.methods.first()
        self.assertEqual(len(method.series_ids), 1)
        self.assertEqual(method.series_ids[0], '0')

        # test that the resource still does not have the required metadata elements at this point
        self.assertEqual(self.resTimeSeries.metadata.has_all_required_elements(), False)

        self.resTimeSeries.metadata.create_element('method', series_ids=['1'],
                                                   method_code='MC-40',
                                                   method_name='Testing method-2',
                                                   method_type='Data collection',
                                                   method_description=''
                                                   )
        # there should be 2 method elements at this point
        self.assertEqual(self.resTimeSeries.metadata.methods.all().count(), 2)
        method_1 = self.resTimeSeries.metadata.methods.all()[0]
        method_2 = self.resTimeSeries.metadata.methods.all()[1]
        self.assertEqual(len(method_1.series_ids), 1)
        self.assertEqual(len(method_2.series_ids), 1)
        self.assertEqual(set(method_1.series_ids + method_2.series_ids), set(['0', '1']))

        # test that the resource still does not have the required metadata elements at this point
        self.assertEqual(self.resTimeSeries.metadata.has_all_required_elements(), False)

        # add 1 processing level elements for the 2 series
        self.resTimeSeries.metadata.create_element('processinglevel', series_ids=['0', '1'],
                                                   processing_level_code='101')

        # there should be 1 processinglevel element at this point
        self.assertEqual(self.resTimeSeries.metadata.processing_levels.all().count(), 1)

        pro_level = self.resTimeSeries.metadata.processing_levels.first()
        self.assertEqual(len(pro_level.series_ids), 2)
        self.assertEqual(set(pro_level.series_ids), set(['0', '1']))

        # test that the resource still does not have the required metadata elements at this point
        self.assertEqual(self.resTimeSeries.metadata.has_all_required_elements(), False)

        # add 2 timeseries result element - one for each series
        # here the value for the param 'series_label' is the 1st data column heading
        self.resTimeSeries.metadata.create_element('timeseriesresult', series_ids=['0'],
                                                   units_type='Temperature',
                                                   units_name='Degree F',
                                                   units_abbreviation='degF',
                                                   status='Complete',
                                                   sample_medium='Air',
                                                   value_count=1550,
                                                   aggregation_statistics='Average',
                                                   series_label='Temp_DegC_Mendon'
                                                   )
        # there should be 1 timeseries result element at this point
        self.assertEqual(self.resTimeSeries.metadata.time_series_results.all().count(), 1)
        ts_result = self.resTimeSeries.metadata.time_series_results.first()
        self.assertEqual(len(ts_result.series_ids), 1)
        self.assertEqual(ts_result.series_ids[0], '0')

        # test that the resource still does not have the required metadata elements at this point
        self.assertEqual(self.resTimeSeries.metadata.has_all_required_elements(), False)

        # add a 2nd timeseries result element
        # here the value for the param 'series_label' is the 2nd data column heading
        self.resTimeSeries.metadata.create_element('timeseriesresult', series_ids=['1'],
                                                   units_type='Temperature',
                                                   units_name='Degree F',
                                                   units_abbreviation='degF',
                                                   status='Complete',
                                                   sample_medium='Air',
                                                   value_count=1200,
                                                   aggregation_statistics='Average',
                                                   series_label='Temp_DegC_Paradise'
                                                   )

        # there should be 2 timeseries result element at this point
        self.assertEqual(self.resTimeSeries.metadata.time_series_results.all().count(), 2)
        ts_result_1 = self.resTimeSeries.metadata.time_series_results.all()[0]
        ts_result_2 = self.resTimeSeries.metadata.time_series_results.all()[1]
        self.assertEqual(len(ts_result_1.series_ids), 1)
        self.assertEqual(len(ts_result_2.series_ids), 1)
        self.assertEqual(set(ts_result_1.series_ids + ts_result_2.series_ids), set(['0', '1']))

        # test that the resource still does not have the required metadata elements at this point
        self.assertEqual(self.resTimeSeries.metadata.has_all_required_elements(), False)

        # set the utc offset
        self.resTimeSeries.metadata.create_element('UTCOffset', value=-7.5)
        # there should be one UTCOffset element
        self.assertTrue(UTCOffSet.objects.filter(
            object_id=self.resTimeSeries.metadata.id).count(), 1)
        self.assertEqual(self.resTimeSeries.metadata.utc_offset.value, -7.5)

        # test that the resource has the required metadata elements at this point
        self.assertEqual(self.resTimeSeries.metadata.get_required_missing_elements(), [])
        self.assertEqual(self.resTimeSeries.metadata.has_all_required_elements(), True)

        # at this point it should be possible to update sqlite file
        self.assertEqual(self.resTimeSeries.can_update_sqlite_file, True)

        # test the sqlite file is still blank at this point
        self._test_sqlite_file_is_blank()

        # test populating of the blank sqlite file
        self.resTimeSeries.metadata.update_sqlite_file(self.user)

        # test that the sqlite file has now data
        self._test_sqlite_file_has_data()

        # test that the value_count is rest
        self.resTimeSeries.metadata.refresh_from_db()
        self.assertEqual(len(self.resTimeSeries.metadata.value_counts), 0)

        # test series_names is empty
        self.assertEqual(len(self.resTimeSeries.metadata.series_names), 0)

    def test_series_id_for_metadata_element_create(self):
        # this applies only to csv file upload

        # first add a valid csv file to the resource
        self._upload_valid_csv_file()

        # since there are 2 data columns the valid series ids are 0 and 1

        # test element 'Site'
        # using a series id of 2 should fail to create the element
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('site', series_ids=['2'],
                                                       site_code='LR_WaterLab_AA',
                                                       site_name='Logan River at the Utah Water '
                                                                 'Research Laboratory west bridge',
                                                       elevation_m=1414,
                                                       elevation_datum='EGM96',
                                                       site_type='Stream',
                                                       latitude=65.789,
                                                       longitude=120.56789)

        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('site', series_ids=['0', '1', '2'],
                                                       site_code='LR_WaterLab_AA',
                                                       site_name='Logan River at the Utah Water '
                                                                 'Research Laboratory west bridge',
                                                       elevation_m=1414,
                                                       elevation_datum='EGM96',
                                                       site_type='Stream',
                                                       latitude=65.789,
                                                       longitude=120.56789)

        # there should be no site element at this point
        self.assertEqual(self.resTimeSeries.metadata.sites.all().count(), 0)

        # test using 'selected_series_id'
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('site', selected_series_id='2',
                                                       site_code='LR_WaterLab_AA',
                                                       site_name='Logan River at the Utah Water '
                                                                 'Research Laboratory west bridge',
                                                       elevation_m=1414,
                                                       elevation_datum='EGM96',
                                                       site_type='Stream',
                                                       latitude=65.789,
                                                       longitude=120.56789)

        self.resTimeSeries.metadata.create_element('site', series_ids=['1'],
                                                   site_code='LR_WaterLab_AA',
                                                   site_name='Logan River at the Utah Water '
                                                             'Research Laboratory west bridge',
                                                   elevation_m=1414,
                                                   elevation_datum='EGM96',
                                                   site_type='Stream',
                                                   latitude=65.789,
                                                   longitude=120.56789)

        # there should be 1 site element at this point
        self.assertEqual(self.resTimeSeries.metadata.sites.all().count(), 1)
        site = self.resTimeSeries.metadata.sites.all()[0]
        self.assertEqual(len(site.series_ids), 1)
        self.assertEqual(site.series_ids, ['1'])

        self.resTimeSeries.metadata.create_element('site', selected_series_id='0',
                                                   site_code='LR_WaterLab_BB',
                                                   site_name='Logan River at the Utah Water '
                                                             'Research Laboratory west bridge',
                                                   elevation_m=1414,
                                                   elevation_datum='EGM96',
                                                   site_type='Stream',
                                                   latitude=65.789,
                                                   longitude=120.56789)

        # there should be 2 site elements at this point
        self.assertEqual(self.resTimeSeries.metadata.sites.all().count(), 2)
        site_1 = self.resTimeSeries.metadata.sites.all()[0]
        site_2 = self.resTimeSeries.metadata.sites.all()[1]
        self.assertEqual(len(site_1.series_ids), 1)
        self.assertEqual(len(site_2.series_ids), 1)
        self.assertEqual(set(site_1.series_ids + site_2.series_ids), set(['0', '1']))

        self.resTimeSeries.metadata.sites.all().delete()
        self.resTimeSeries.metadata.create_element('site', series_ids=['0', '1'],
                                                   site_code='LR_WaterLab_AA',
                                                   site_name='Logan River at the Utah Water '
                                                             'Research Laboratory west bridge',
                                                   elevation_m=1414,
                                                   elevation_datum='EGM96',
                                                   site_type='Stream',
                                                   latitude=65.789,
                                                   longitude=120.56789)
        # there should be 1 site element at this point
        self.assertEqual(self.resTimeSeries.metadata.sites.all().count(), 1)
        site = self.resTimeSeries.metadata.sites.first()
        self.assertEqual(len(site.series_ids), 2)
        self.assertEqual(set(site.series_ids), set(['0', '1']))

        # test update of Site element
        self.resTimeSeries.metadata.update_element('site', site.id, series_ids=['0'])
        self.assertEqual(self.resTimeSeries.metadata.sites.all().count(), 1)
        site = self.resTimeSeries.metadata.sites.first()
        self.assertEqual(len(site.series_ids), 1)
        self.assertEqual(site.series_ids, ['0'])

        self.resTimeSeries.metadata.update_element('site', site.id, selected_series_id='1')
        self.assertEqual(self.resTimeSeries.metadata.sites.all().count(), 1)
        site = self.resTimeSeries.metadata.sites.first()
        self.assertEqual(len(site.series_ids), 2)
        self.assertEqual(set(site.series_ids), set(['0', '1']))

        # test element 'Variable'

        # invalid series id: 2
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('variable', series_ids=['2'],
                                                       variable_code='USU37',
                                                       variable_name='Temperature',
                                                       variable_type='Climate',
                                                       no_data_value=-999,
                                                       speciation='Not Applicable')

        # there should be no variable element at this point
        self.assertEqual(self.resTimeSeries.metadata.variables.all().count(), 0)

        # invalid series id: 2
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('variable', series_ids=['0', '1', '2'],
                                                       variable_code='USU37',
                                                       variable_name='Temperature',
                                                       variable_type='Climate',
                                                       no_data_value=-999,
                                                       speciation='Not Applicable')
        # there should be no variable element at this point
        self.assertEqual(self.resTimeSeries.metadata.variables.all().count(), 0)

        # test using selected_series_id (invalid series id: 2)
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('variable', selected_series_id='2',
                                                       variable_code='USU37',
                                                       variable_name='Temperature',
                                                       variable_type='Climate',
                                                       no_data_value=-999,
                                                       speciation='Not Applicable')

        # there should be no variable element at this point
        self.assertEqual(self.resTimeSeries.metadata.variables.all().count(), 0)

        self.resTimeSeries.metadata.create_element('variable', series_ids=['0'],
                                                   variable_code='USU37',
                                                   variable_name='Temperature',
                                                   variable_type='Climate',
                                                   no_data_value=-999,
                                                   speciation='Not Applicable')

        # there should be 1 variable element at this point
        self.assertEqual(self.resTimeSeries.metadata.variables.all().count(), 1)
        variable = self.resTimeSeries.metadata.variables.first()
        self.assertEqual(len(variable.series_ids), 1)
        self.assertEqual(variable.series_ids, ['0'])

        self.resTimeSeries.metadata.create_element('variable', selected_series_id='1',
                                                   variable_code='USU38',
                                                   variable_name='Temperature',
                                                   variable_type='Climate',
                                                   no_data_value=-999,
                                                   speciation='Not Applicable')
        # there should be 2 variable elements at this point
        self.assertEqual(self.resTimeSeries.metadata.variables.all().count(), 2)
        variable_1 = self.resTimeSeries.metadata.variables.all()[0]
        variable_2 = self.resTimeSeries.metadata.variables.all()[1]
        self.assertEqual(len(variable_1.series_ids), 1)
        self.assertEqual(len(variable_2.series_ids), 1)
        self.assertEqual(set(variable_1.series_ids + variable_2.series_ids), set(['0', '1']))

        self.resTimeSeries.metadata.variables.all().delete()

        self.resTimeSeries.metadata.create_element('variable', series_ids=['0', '1'],
                                                   variable_code='USU37',
                                                   variable_name='Temperature',
                                                   variable_type='Climate',
                                                   no_data_value=-999,
                                                   speciation='Not Applicable')

        # there should be 1 variable element at this point
        self.assertEqual(self.resTimeSeries.metadata.variables.all().count(), 1)
        variable = self.resTimeSeries.metadata.variables.first()
        self.assertEqual(len(variable.series_ids), 2)
        self.assertEqual(set(variable.series_ids), set(['0', '1']))

        # test update of Variable element
        self.resTimeSeries.metadata.update_element('variable', variable.id, series_ids=['0'])
        variable = self.resTimeSeries.metadata.variables.first()
        self.assertEqual(len(variable.series_ids), 1)
        self.assertEqual(variable.series_ids, ['0'])

        self.resTimeSeries.metadata.update_element('variable', variable.id,
                                                   selected_series_id='1')
        variable = self.resTimeSeries.metadata.variables.first()
        self.assertEqual(len(variable.series_ids), 2)
        self.assertEqual(set(variable.series_ids), set(['0', '1']))

        # test element 'Method'
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('method', series_ids=['2'],
                                                       method_code='MC-30',
                                                       method_name='Testing method-1',
                                                       method_type='Data collection',
                                                       method_description=''
                                                       )

        # there should be no method element at this point
        self.assertEqual(self.resTimeSeries.metadata.methods.all().count(), 0)

        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('method', series_ids=['0', '1', '2'],
                                                       method_code='MC-30',
                                                       method_name='Testing method-1',
                                                       method_type='Data collection',
                                                       method_description=''
                                                       )
        # there should be no method element at this point
        self.assertEqual(self.resTimeSeries.metadata.methods.all().count(), 0)

        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('method', selected_series_id='2',
                                                       method_code='MC-30',
                                                       method_name='Testing method-1',
                                                       method_type='Data collection',
                                                       method_description=''
                                                       )

        # there should be no method element at this point
        self.assertEqual(self.resTimeSeries.metadata.methods.all().count(), 0)

        self.resTimeSeries.metadata.create_element('method', series_ids=['1'],
                                                   method_code='MC-30',
                                                   method_name='Testing method-1',
                                                   method_type='Data collection',
                                                   method_description=''
                                                   )

        # there should be 1 method element at this point
        self.assertEqual(self.resTimeSeries.metadata.methods.all().count(), 1)
        method = self.resTimeSeries.metadata.methods.first()
        self.assertEqual(len(method.series_ids), 1)
        self.assertEqual(method.series_ids, ['1'])

        self.resTimeSeries.metadata.create_element('method', selected_series_id='0',
                                                   method_code='MC-31',
                                                   method_name='Testing method-1',
                                                   method_type='Data collection',
                                                   method_description=''
                                                   )

        # there should be 2 method elements at this point
        self.assertEqual(self.resTimeSeries.metadata.methods.all().count(), 2)
        method_1 = self.resTimeSeries.metadata.methods.all()[0]
        method_2 = self.resTimeSeries.metadata.methods.all()[1]
        self.assertEqual(len(method_1.series_ids), 1)
        self.assertEqual(len(method_2.series_ids), 1)
        self.assertEqual(set(method_1.series_ids + method_2.series_ids), set(['0', '1']))

        self.resTimeSeries.metadata.methods.all().delete()

        self.resTimeSeries.metadata.create_element('method', series_ids=['0', '1'],
                                                   method_code='MC-30',
                                                   method_name='Testing method-1',
                                                   method_type='Data collection',
                                                   method_description=''
                                                   )

        # there should be 1 method element at this point
        self.assertEqual(self.resTimeSeries.metadata.methods.all().count(), 1)
        method = self.resTimeSeries.metadata.methods.first()
        self.assertEqual(len(method.series_ids), 2)
        self.assertEqual(set(method.series_ids), set(['0', '1']))

        # test update of Method element
        self.resTimeSeries.metadata.update_element('method', method.id, series_ids=['1'])
        method = self.resTimeSeries.metadata.methods.first()
        self.assertEqual(len(method.series_ids), 1)
        self.assertEqual(method.series_ids, ['1'])

        self.resTimeSeries.metadata.update_element('method', method.id, selected_series_id='0')
        method = self.resTimeSeries.metadata.methods.first()
        self.assertEqual(len(method.series_ids), 2)
        self.assertEqual(set(method.series_ids), set(['0', '1']))

        # test element "ProcessingLevel"
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('processinglevel', series_ids=['2'],
                                                       definition='pro level definition',
                                                       explanation='pro level explanation',
                                                       processing_level_code='101')

        # there should be no processinglevel element at this point
        self.assertEqual(self.resTimeSeries.metadata.processing_levels.all().count(), 0)

        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('processinglevel',
                                                       series_ids=['0', '1', '2'],
                                                       definition='pro level definition',
                                                       explanation='pro level explanation',
                                                       processing_level_code='101')

        # there should be no processinglevel element at this point
        self.assertEqual(self.resTimeSeries.metadata.processing_levels.all().count(), 0)

        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('processinglevel', selected_series_id='2',
                                                       definition='pro level definition',
                                                       explanation='pro level explanation',
                                                       processing_level_code='101')

        # there should be no processinglevel element at this point
        self.assertEqual(self.resTimeSeries.metadata.processing_levels.all().count(), 0)

        self.resTimeSeries.metadata.create_element('processinglevel', series_ids=['1'],
                                                   definition='pro level definition',
                                                   explanation='pro level explanation',
                                                   processing_level_code='101')

        # there should be 1 processinglevel element at this point
        self.assertEqual(self.resTimeSeries.metadata.processing_levels.all().count(), 1)
        pro_level = self.resTimeSeries.metadata.processing_levels.first()
        self.assertEqual(len(pro_level.series_ids), 1)
        self.assertEqual(pro_level.series_ids, ['1'])

        self.resTimeSeries.metadata.create_element('processinglevel', selected_series_id='0',
                                                   definition='pro level definition',
                                                   explanation='pro level explanation',
                                                   processing_level_code='102')

        # there should be 2 processinglevel element at this point
        self.assertEqual(self.resTimeSeries.metadata.processing_levels.all().count(), 2)
        pro_level_1 = self.resTimeSeries.metadata.processing_levels.all()[0]
        pro_level_2 = self.resTimeSeries.metadata.processing_levels.all()[1]
        self.assertEqual(len(pro_level_1.series_ids), 1)
        self.assertEqual(len(pro_level_2.series_ids), 1)
        self.assertEqual(set(pro_level_1.series_ids + pro_level_2.series_ids), set(['0', '1']))

        self.resTimeSeries.metadata.processing_levels.all().delete()
        self.resTimeSeries.metadata.create_element('processinglevel', series_ids=['1', '0'],
                                                   definition='pro level definition',
                                                   explanation='pro level explanation',
                                                   processing_level_code='101')

        # there should be 1 processinglevel element at this point
        self.assertEqual(self.resTimeSeries.metadata.processing_levels.all().count(), 1)
        pro_level = self.resTimeSeries.metadata.processing_levels.first()
        self.assertEqual(len(pro_level.series_ids), 2)
        self.assertEqual(set(pro_level.series_ids), set(['0', '1']))

        # test update of ProcessingLevel element
        self.resTimeSeries.metadata.update_element('processinglevel', pro_level.id,
                                                   series_ids=['1'])

        pro_level = self.resTimeSeries.metadata.processing_levels.first()
        self.assertEqual(len(pro_level.series_ids), 1)
        self.assertEqual(pro_level.series_ids, ['1'])

        self.resTimeSeries.metadata.update_element('processinglevel', pro_level.id,
                                                   selected_series_id='0')
        pro_level = self.resTimeSeries.metadata.processing_levels.first()
        self.assertEqual(len(pro_level.series_ids), 2)
        self.assertEqual(set(pro_level.series_ids), set(['0', '1']))

        # test element "TimeSeriesResult"
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('timeseriesresult', series_ids=['2'],
                                                       units_type='Temperature',
                                                       units_name='Degree F',
                                                       units_abbreviation='degF',
                                                       status='Complete',
                                                       sample_medium='Air',
                                                       value_count=1550,
                                                       aggregation_statistics='Average'
                                                       )
        # there should be no timeseriesresult element at this point
        self.assertEqual(self.resTimeSeries.metadata.time_series_results.all().count(), 0)

        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('timeseriesresult',
                                                       series_ids=['0', '1', '2'],
                                                       units_type='Temperature',
                                                       units_name='Degree F',
                                                       units_abbreviation='degF',
                                                       status='Complete',
                                                       sample_medium='Air',
                                                       value_count=1550,
                                                       aggregation_statistics='Average'
                                                       )
        # there should be no timeseriesresult element at this point
        self.assertEqual(self.resTimeSeries.metadata.time_series_results.all().count(), 0)

        # timeseriesresult element can' be assinged multiple series ids
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('timeseriesresult',
                                                       series_ids=['0', '1'],
                                                       units_type='Temperature',
                                                       units_name='Degree F',
                                                       units_abbreviation='degF',
                                                       status='Complete',
                                                       sample_medium='Air',
                                                       value_count=1550,
                                                       aggregation_statistics='Average'
                                                       )
        # there should be no timeseriesresult element at this point
        self.assertEqual(self.resTimeSeries.metadata.time_series_results.all().count(), 0)

        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('timeseriesresult', selected_series_id='2',
                                                       units_type='Temperature',
                                                       units_name='Degree F',
                                                       units_abbreviation='degF',
                                                       status='Complete',
                                                       sample_medium='Air',
                                                       value_count=1550,
                                                       aggregation_statistics='Average'
                                                       )
        # there should be no timeseriesresult element at this point
        self.assertEqual(self.resTimeSeries.metadata.time_series_results.all().count(), 0)

        self.resTimeSeries.metadata.create_element('timeseriesresult', series_ids=['1'],
                                                   units_type='Temperature',
                                                   units_name='Degree F',
                                                   units_abbreviation='degF',
                                                   status='Complete',
                                                   sample_medium='Air',
                                                   value_count=1550,
                                                   aggregation_statistics='Average'
                                                   )
        # there should be 1 timeseriesresult element at this point
        self.assertEqual(self.resTimeSeries.metadata.time_series_results.all().count(), 1)
        ts_result = self.resTimeSeries.metadata.time_series_results.first()
        self.assertEqual(len(ts_result.series_ids), 1)
        self.assertEqual(ts_result.series_ids, ['1'])

        self.resTimeSeries.metadata.create_element('timeseriesresult', selected_series_id='0',
                                                   units_type='Temperature',
                                                   units_name='Degree F',
                                                   units_abbreviation='degF',
                                                   status='Complete',
                                                   sample_medium='Air',
                                                   value_count=1550,
                                                   aggregation_statistics='Average'
                                                   )
        # there should be 2 timeseriesresult elements at this point
        self.assertEqual(self.resTimeSeries.metadata.time_series_results.all().count(), 2)
        ts_result_1 = self.resTimeSeries.metadata.time_series_results.all()[0]
        ts_result_2 = self.resTimeSeries.metadata.time_series_results.all()[1]
        self.assertEqual(len(ts_result_1.series_ids), 1)
        self.assertEqual(len(ts_result_2.series_ids), 1)
        self.assertEqual(set(ts_result_1.series_ids + ts_result_2.series_ids), set(['0', '1']))

        # test update of TimeSeriesResult element
        self.resTimeSeries.metadata.time_series_results.all().delete()

        # create a timeseriesresult element for series id '0'
        self.resTimeSeries.metadata.create_element('timeseriesresult', series_ids=['0'],
                                                   units_type='Temperature',
                                                   units_name='Degree F',
                                                   units_abbreviation='degF',
                                                   status='Complete',
                                                   sample_medium='Air',
                                                   value_count=1550,
                                                   aggregation_statistics='Average'
                                                   )

        ts_result = self.resTimeSeries.metadata.time_series_results.first()
        self.assertEqual(len(ts_result.series_ids), 1)
        self.assertEqual(ts_result.series_ids, ['0'])

        # update the series id to '1'
        self.resTimeSeries.metadata.update_element('timeseriesresult', ts_result.id,
                                                   series_ids=['1'])
        ts_result = self.resTimeSeries.metadata.time_series_results.first()
        self.assertEqual(len(ts_result.series_ids), 1)
        self.assertEqual(ts_result.series_ids, ['1'])

        # update the series id back to '0' - this time using the selected_series_id parameter
        self.resTimeSeries.metadata.update_element('timeseriesresult', ts_result.id,
                                                   selected_series_id='0')
        ts_result = self.resTimeSeries.metadata.time_series_results.first()
        self.assertEqual(len(ts_result.series_ids), 1)
        self.assertEqual(ts_result.series_ids, ['0'])

        # test only one UTCOffSet element can be created
        self.resTimeSeries.metadata.create_element('UTCOffset', value=-7.5)
        # there should be one UTCOffset element
        self.assertTrue(UTCOffSet.objects.filter(
            object_id=self.resTimeSeries.metadata.id).count(), 1)

        # trying to create a 2nd UTCOffSet element should raise exception
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('UTCOffset', value=-9.0)

    def test_element_duplicate_code(self):
        # this is to test that we can't create/update some of the resource specific
        # metadata elements with duplicate code

        # first add a csv file to the resource
        self._upload_valid_csv_file()

        # create a site element
        site_code = 'Temp_DegC_Mendon'
        self.resTimeSeries.metadata.create_element('site', series_ids=['0'],
                                                   site_code=site_code,
                                                   site_name='Logan River at the Utah Water '
                                                             'Research Laboratory west bridge',
                                                   elevation_m=1414,
                                                   elevation_datum='EGM96',
                                                   site_type='Stream',
                                                   latitude=65.789,
                                                   longitude=120.56789)

        # trying to create a 2nd site element with same site_code value should raise exception
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('site', series_ids=['1'],
                                                       site_code=site_code,
                                                       site_name='Logan River at Logan',
                                                       elevation_m=2025,
                                                       elevation_datum='EGM96',
                                                       site_type='Stream',
                                                       latitude=40.789,
                                                       longitude=130.1234)

        # there should be 1 site element at this point
        self.assertEqual(self.resTimeSeries.metadata.sites.all().count(), 1)

        # create 2nd site element with different site code
        self.resTimeSeries.metadata.create_element('site', series_ids=['1'],
                                                   site_code='Temp_DegC_Paradise',
                                                   site_name='Logan River at the Utah Water '
                                                             'Research Laboratory west bridge',
                                                   elevation_m=1414,
                                                   elevation_datum='EGM96',
                                                   site_type='Stream',
                                                   latitude=85.789,
                                                   longitude=110.56789)

        # there should be 2 site element at this point
        self.assertEqual(self.resTimeSeries.metadata.sites.all().count(), 2)

        site = self.resTimeSeries.metadata.sites.filter(site_code='Temp_DegC_Paradise').first()

        # trying to update the site element with duplicate site code should raise exception
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.update_element('site', site.id, site_code=site_code)

        # add a variable element
        variable_code = 'USU37'
        self.resTimeSeries.metadata.create_element('variable', series_ids=['0'],
                                                   variable_code=variable_code,
                                                   variable_name='Temperature',
                                                   variable_type='Climate',
                                                   no_data_value=-999,
                                                   speciation='Not Applicable')

        # trying to create a 2nd variable element with same variable_code value should raise
        # exception
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('variable', series_ids=['1'],
                                                       variable_code=variable_code,
                                                       variable_name='RH',
                                                       variable_type='Climate',
                                                       no_data_value=-888,
                                                       speciation='Not Applicable')

        # there should be 1 variable element at this point
        self.assertEqual(self.resTimeSeries.metadata.variables.all().count(), 1)

        # create 2nd variable with different variable_code
        self.resTimeSeries.metadata.create_element('variable', series_ids=['1'],
                                                   variable_code='VAR-101',
                                                   variable_name='RH',
                                                   variable_type='Climate',
                                                   no_data_value=-888,
                                                   speciation='Not Applicable')

        # there should be 2 variable elements at this point
        self.assertEqual(self.resTimeSeries.metadata.variables.all().count(), 2)

        variable = self.resTimeSeries.metadata.variables.filter(variable_code='VAR-101').first()

        # trying to update variable_code with duplicate value should raise exception
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.update_element('variable', variable.id,
                                                       variable_code=variable_code)

        # create a method element
        method_code = 'MC-30'
        self.resTimeSeries.metadata.create_element('method', series_ids=['0'],
                                                   method_code=method_code,
                                                   method_name='Testing method-1',
                                                   method_type='Data collection',
                                                   method_description=''
                                                   )
        # trying to create a 2nd method element with same method_code should raise exception
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('method', series_ids=['1'],
                                                       method_code=method_code,
                                                       method_name='Testing method-2',
                                                       method_type='Data collection-2',
                                                       method_description='description'
                                                       )
        # there should be 1 method element at this point
        self.assertEqual(self.resTimeSeries.metadata.methods.all().count(), 1)

        # create a 2nd method element with a different method_code
        self.resTimeSeries.metadata.create_element('method', series_ids=['1'],
                                                   method_code='MC-50',
                                                   method_name='Testing method-2',
                                                   method_type='Data collection-2',
                                                   method_description='description'
                                                   )
        # there should be 2 method element at this point
        self.assertEqual(self.resTimeSeries.metadata.methods.all().count(), 2)

        method = self.resTimeSeries.metadata.methods.filter(method_code='MC-50').first()
        # trying to update method_code with duplicate value should raise exception
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.update_element('method', method.id,
                                                       method_code=method_code)

        # add a processing level element
        self.resTimeSeries.metadata.create_element('processinglevel', series_ids=['0'],
                                                   processing_level_code='101')

        # creating a 2nd processinglevel element with same code should raise exception
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.create_element('processinglevel', series_ids=['1'],
                                                       processing_level_code='101')

        # there should be 1 processinglevel element at this point
        self.assertEqual(self.resTimeSeries.metadata.processing_levels.all().count(), 1)

        # create 2nd processinglevel element with a different code
        self.resTimeSeries.metadata.create_element('processinglevel', series_ids=['1'],
                                                   processing_level_code='105')

        # there should be 2 processinglevel element at this point
        self.assertEqual(self.resTimeSeries.metadata.processing_levels.all().count(), 2)

        pro_level = self.resTimeSeries.metadata.processing_levels.filter(
            processing_level_code='105').first()

        # trying to update with a duplicate code should raise exception
        with self.assertRaises(ValidationError):
            self.resTimeSeries.metadata.update_element('processinglevel', pro_level.id,
                                                       processing_level_code='101')

    def _upload_valid_csv_file(self):
        # first add a valid csv file to the resource
        files = [UploadedFile(file=self.odm2_csv_file_obj, name=self.odm2_csv_file_name)]

        utils.resource_file_add_process(resource=self.resTimeSeries, files=files, user=self.user)

    def _upload_valid_sqlite_file(self):
        # first add a valid csv file to the resource
        files = [UploadedFile(file=self.odm2_sqlite_file_obj, name=self.odm2_sqlite_file_name)]

        utils.resource_file_add_process(resource=self.resTimeSeries, files=files, user=self.user,
                                        extract_metadata=True)

    def _test_invalid_csv_file(self, invalid_csv_file_name):
        invalid_csv_file_obj = self._get_invalid_csv_file_obj(invalid_csv_file_name)

        # at this point the resource should not have any content files
        self.assertEqual(self.resTimeSeries.files.all().count(), 0)

        files = [UploadedFile(file=invalid_csv_file_obj, name=invalid_csv_file_name)]
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files,
                                            user=self.user)

        # the validation of csv happens during file_add_process - which should fail
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_process(resource=self.resTimeSeries, files=files,
                                            user=self.user)
        # at this point the resource should have one content file
        self.assertEqual(self.resTimeSeries.files.all().count(), 0)
        self.assertEqual(self.resTimeSeries.has_csv_file, False)

    def _get_invalid_csv_file_obj(self, invalid_csv_file_name):
        invalid_csv_file = 'hs_app_timeseries/tests/{}'.format(invalid_csv_file_name)
        target_temp_csv_file = os.path.join(self.temp_dir, invalid_csv_file_name)
        shutil.copy(invalid_csv_file, target_temp_csv_file)
        return open(target_temp_csv_file, 'r')

    def _test_no_change_in_metadata(self):
        # test the core metadata at this point

        # there shouldn't any abstract element
        self.assertEqual(self.resTimeSeries.metadata.description, None)

        # there shouldn't any subject element
        self.assertEqual(self.resTimeSeries.metadata.subjects.all().count(), 0)

        # there shouldn't any contributor element
        self.assertEqual(self.resTimeSeries.metadata.contributors.all().count(), 0)

        # check that there are no extended metadata elements at this point
        self.assertEqual(self.resTimeSeries.metadata.sites.all().count(), 0)
        self.assertEqual(self.resTimeSeries.metadata.variables.all().count(), 0)
        self.assertEqual(self.resTimeSeries.metadata.methods.all().count(), 0)
        self.assertEqual(self.resTimeSeries.metadata.processing_levels.all().count(), 0)
        self.assertEqual(self.resTimeSeries.metadata.time_series_results.all().count(), 0)

    def _test_sqlite_file_is_blank(self):
        sqlite_file_to_update = utils.get_resource_files_by_extension(self.resTimeSeries,
                                                                      ".sqlite")[0]
        # retrieve the sqlite file from iRODS and save it to temp directory
        temp_sqlite_file = utils.get_file_from_irods(sqlite_file_to_update)
        con = sqlite3.connect(temp_sqlite_file)
        with con:
            # get the records in python dictionary format
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT * FROM SamplingFeatures")
            query_result = cur.fetchone()
            self.assertEqual(query_result, None)

            cur.execute("SELECT * FROM SpatialReferences")
            query_result = cur.fetchone()
            self.assertEqual(query_result, None)

            cur.execute("SELECT * FROM Sites")
            query_result = cur.fetchone()
            self.assertEqual(query_result, None)

            cur.execute("SELECT * FROM Methods")
            query_result = cur.fetchone()
            self.assertEqual(query_result, None)

            cur.execute("SELECT * FROM Variables")
            query_result = cur.fetchone()
            self.assertEqual(query_result, None)

            cur.execute("SELECT * FROM Units")
            query_result = cur.fetchone()
            self.assertEqual(query_result, None)

            cur.execute("SELECT * FROM ProcessingLevels")
            query_result = cur.fetchone()
            self.assertEqual(query_result, None)

            cur.execute("SELECT * FROM People")
            query_result = cur.fetchone()
            self.assertEqual(query_result, None)

            cur.execute("SELECT * FROM Organizations")
            query_result = cur.fetchone()
            self.assertEqual(query_result, None)

            cur.execute("SELECT * FROM Affiliations")
            query_result = cur.fetchone()
            self.assertEqual(query_result, None)

            cur.execute("SELECT * FROM Actions")
            query_result = cur.fetchone()
            self.assertEqual(query_result, None)

            cur.execute("SELECT * FROM ActionBy")
            query_result = cur.fetchone()
            self.assertEqual(query_result, None)

            cur.execute("SELECT * FROM FeatureActions")
            query_result = cur.fetchone()
            self.assertEqual(query_result, None)

            cur.execute("SELECT * FROM Results")
            query_result = cur.fetchone()
            self.assertEqual(query_result, None)

            cur.execute("SELECT * FROM TimeSeriesResults")
            query_result = cur.fetchone()
            self.assertEqual(query_result, None)

            cur.execute("SELECT * FROM TimeSeriesResultValues")
            query_result = cur.fetchone()
            self.assertEqual(query_result, None)

            cur.execute("SELECT * FROM Datasets")
            query_result = cur.fetchone()
            self.assertEqual(query_result, None)

            cur.execute("SELECT * FROM DatasetsResults")
            query_result = cur.fetchone()
            self.assertEqual(query_result, None)

        if os.path.exists(temp_sqlite_file):
            shutil.rmtree(os.path.dirname(temp_sqlite_file))

    def _test_sqlite_file_has_data(self):
        sqlite_file_to_update = utils.get_resource_files_by_extension(self.resTimeSeries,
                                                                      ".sqlite")[0]
        # retrieve the sqlite file from iRODS and save it to temp directory
        temp_sqlite_file = utils.get_file_from_irods(sqlite_file_to_update)
        con = sqlite3.connect(temp_sqlite_file)
        record_count_query = "SELECT COUNT() FROM {}"
        with con:
            # get the records in python dictionary format
            con.row_factory = sqlite3.Row
            cur = con.cursor()

            cur.execute(record_count_query.format("SamplingFeatures"))
            record_count = cur.fetchone()[0]
            self.assertEqual(record_count, 2)

            # there should be 1 record in SpatialReferences table
            cur.execute(record_count_query.format("SpatialReferences"))
            record_count = cur.fetchone()[0]
            self.assertEqual(record_count, 1)

            # there should be 2 records in Sites table
            cur.execute(record_count_query.format("Sites"))
            record_count = cur.fetchone()[0]
            self.assertEqual(record_count, 2)

            # there should be 2 records in Methods table
            cur.execute(record_count_query.format("Methods"))
            record_count = cur.fetchone()[0]
            self.assertEqual(record_count, 2)

            # there should be 1 record in Variables table
            cur.execute(record_count_query.format("Variables"))
            record_count = cur.fetchone()[0]
            self.assertEqual(record_count, 1)

            # there should be 2 records in Units table
            cur.execute(record_count_query.format("Units"))
            record_count = cur.fetchone()[0]
            self.assertEqual(record_count, 2)

            # there should be 1 record in ProcessingLevel table
            cur.execute(record_count_query.format("ProcessingLevels"))
            record_count = cur.fetchone()[0]
            self.assertEqual(record_count, 1)

            # there should be 2 records in People table
            cur.execute(record_count_query.format("People"))
            record_count = cur.fetchone()[0]
            self.assertEqual(record_count, 2)

            # there should be 2 records in Organizations table
            cur.execute(record_count_query.format("Organizations"))
            record_count = cur.fetchone()[0]
            self.assertEqual(record_count, 2)

            # there should be 2 records in Affiliations table
            cur.execute(record_count_query.format("Affiliations"))
            record_count = cur.fetchone()[0]
            self.assertEqual(record_count, 2)

            # there should be 2 records in Actions table
            cur.execute(record_count_query.format("Actions"))
            record_count = cur.fetchone()[0]
            self.assertEqual(record_count, 2)

            # there should be 4 records in ActionBy table
            cur.execute(record_count_query.format("ActionBy"))
            record_count = cur.fetchone()[0]
            self.assertEqual(record_count, 4)

            # there should be 2 records in FeatureActions table
            cur.execute(record_count_query.format("FeatureActions"))
            record_count = cur.fetchone()[0]
            self.assertEqual(record_count, 2)

            # there should be 2 records in Results table
            cur.execute(record_count_query.format("Results"))
            record_count = cur.fetchone()[0]
            self.assertEqual(record_count, 2)

            # there should be 2 records in TimeSeriesResults table
            cur.execute(record_count_query.format("TimeSeriesResults"))
            record_count = cur.fetchone()[0]
            self.assertEqual(record_count, 2)

            # there should be 40 records in TimeSeriesResultValues table
            cur.execute(record_count_query.format("TimeSeriesResultValues"))
            record_count = cur.fetchone()[0]
            self.assertEqual(record_count, 40)

            # there should be 1 record in Datasets table
            cur.execute(record_count_query.format("Datasets"))
            record_count = cur.fetchone()[0]
            self.assertEqual(record_count, 1)

            # there should be 2 records in DatasetsResults table
            cur.execute(record_count_query.format("DatasetsResults"))
            record_count = cur.fetchone()[0]
            self.assertEqual(record_count, 2)

        if os.path.exists(temp_sqlite_file):
            shutil.rmtree(os.path.dirname(temp_sqlite_file))
