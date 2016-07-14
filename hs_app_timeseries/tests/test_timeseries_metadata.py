import os
import tempfile
import shutil
from dateutil import parser

from xml.etree import ElementTree as ET

from django.test import TransactionTestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.contrib.auth.models import Group

from hs_core import hydroshare
from hs_core.hydroshare import utils
from hs_core.models import CoreMetaData, Creator, Contributor, Coverage, Rights, Title, Language, \
    Publisher, Identifier, Type, Subject, Description, Date, Format, Relation, Source
from hs_core.testing import MockIRODSTestCaseMixin
from hs_app_timeseries.models import TimeSeriesResource, Site, Variable, Method, ProcessingLevel, \
    TimeSeriesResult, CVVariableType, CVVariableName, CVSpeciation, CVElevationDatum, CVSiteType, \
    CVMethodType, CVUnitsType, CVStatus, CVMedium, CVAggregationStatistic, TimeSeriesMetaData


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
        self.odm2_sqlite_file_name = 'ODM2_Multi_Site_One_Variable.sqlite'
        self.odm2_sqlite_file = 'hs_app_timeseries/tests/{}'.format(self.odm2_sqlite_file_name)
        target_temp_sqlite_file = os.path.join(self.temp_dir, self.odm2_sqlite_file_name)
        shutil.copy(self.odm2_sqlite_file, target_temp_sqlite_file)
        self.odm2_sqlite_file_obj = open(target_temp_sqlite_file, 'r')

        self.odm2_sqlite_bad_file_name = 'ODM2_invalid.sqlite'
        self.odm2_sqlite_bad_file = 'hs_app_timeseries/tests/{}'.format(
            self.odm2_sqlite_bad_file_name)
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
        self.assertEqual(len(TimeSeriesResource.get_supported_upload_file_types()), 1)

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

        # file pre add process should raise validation error if we try to add a 2nd file when the
        # resource has already has one content file
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files,
                                                user=self.user, extract_metadata=False)

    def test_metadata_extraction_on_resource_creation(self):
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

        self._test_metadata_extraction()

    def test_metadata_extraction_on_content_file_add(self):
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

        # adding a valid ODM2 sqlite file should generate some core metadata and all extended
        # metadata
        files = [UploadedFile(file=self.odm2_sqlite_file_obj, name=self.odm2_sqlite_file_name)]
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files,
                                            user=self.user, extract_metadata=False)

        utils.resource_file_add_process(resource=self.resTimeSeries, files=files, user=self.user,
                                        extract_metadata=True)

        self._test_metadata_extraction()

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
        self.assertEqual(core_metadata_obj.cv_mediums.all().count(), 17)
        self.assertEqual(CVMedium.objects.all().count(), 17)
        self.assertEqual(core_metadata_obj.cv_aggregation_statistics.all().count(), 17)
        self.assertEqual(CVAggregationStatistic.objects.all().count(), 17)

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
                                                   site_type='Stream')

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
                                                   processing_level_code=0,
                                                   definition='Raw data',
                                                   explanation=exp_text)

        proc_level_element = self.resTimeSeries.metadata.processing_levels.all().first()
        self.assertEqual(len(proc_level_element.series_ids), 1)
        self.assertIn('a456789-89yughys', proc_level_element.series_ids)
        self.assertEqual(proc_level_element.processing_level_code, 0)
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

        site_element = self.resTimeSeries.metadata.sites.all().first()
        self.assertEqual(site_element.site_code, 'LR_WaterLab_BB')
        self.assertEqual(site_element.site_name, 'Logan River at the Utah WRL west bridge')
        self.assertEqual(site_element.elevation_m, 1515)
        self.assertEqual(site_element.elevation_datum, 'EGM97')
        self.assertEqual(site_element.site_type, 'Stream flow')
        self.assertEqual(site_element.is_dirty, True)

        # the 'is_dirty' flag of metadata be True
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

        self.assertEqual(self.resTimeSeries.metadata.is_dirty, True)

        self.resTimeSeries.metadata.update_element(
            'processinglevel', self.resTimeSeries.metadata.processing_levels.all().first().id,
            processing_level_code=9, definition='data', explanation=exp_text + 'some more text')

        proc_level_element = self.resTimeSeries.metadata.processing_levels.all().first()
        self.assertEqual(proc_level_element.processing_level_code, 9)
        self.assertEqual(proc_level_element.definition, 'data')
        self.assertEqual(proc_level_element.explanation, exp_text + 'some more text')
        self.assertEqual(proc_level_element.is_dirty, True)

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

        # at this point the is_dirty be set to false
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, False)
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
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, True)

        # rest metadata is_dirty to false
        TimeSeriesMetaData.objects.filter(id=self.resTimeSeries.metadata.id).update(is_dirty=False)

        # at this point the is_dirty must be false for metadata
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, False)

        # test 'is_dirty' with update of the Variable element
        variable = self.resTimeSeries.metadata.variables.all().first()
        self.assertEqual(variable.is_dirty, False)
        # now update the variable element
        self.resTimeSeries.metadata.update_element('variable', variable.id,
                                                   variable_code='USU37',
                                                   variable_name=variable.variable_name,
                                                   varaiable_type=variable.variable_type,
                                                   no_data_value=variable.no_data_value,
                                                   speciation=variable.speciation)

        variable = self.resTimeSeries.metadata.variables.filter(id=variable.id).first()
        self.assertEqual(variable.is_dirty, True)
        # at this point the is_dirty must be true for metadata
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, True)
        # reset metadata is_dirty to false
        TimeSeriesMetaData.objects.filter(id=self.resTimeSeries.metadata.id).update(is_dirty=False)

        # at this point the is_dirty must be false for metadata
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, False)

        # test 'is_dirty' with update of the Method element
        method = self.resTimeSeries.metadata.methods.all().first()
        self.assertEqual(method.is_dirty, False)
        # now update the method element
        self.resTimeSeries.metadata.update_element('method', variable.id,
                                                   method_code='30',
                                                   method_name=method.method_name,
                                                   method_type=method.method_type,
                                                   description=method.method_description,
                                                   method_link=method.method_link)

        method = self.resTimeSeries.metadata.methods.filter(id=method.id).first()
        self.assertEqual(method.is_dirty, True)
        # at this point the is_dirty must be true
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, True)
        # reset metadata is_dirty to false
        TimeSeriesMetaData.objects.filter(id=self.resTimeSeries.metadata.id).update(is_dirty=False)

        # at this point the is_dirty must be false for metadata
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
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, True)
        # reset metadata is_dirty to false
        TimeSeriesMetaData.objects.filter(id=self.resTimeSeries.metadata.id).update(is_dirty=False)

        # at this point the is_dirty must be false for metadata
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
        self.assertEqual(self.resTimeSeries.metadata.is_dirty, True)
        # reset metadata is_dirty to false
        TimeSeriesMetaData.objects.filter(id=self.resTimeSeries.metadata.id).update(is_dirty=False)
        # at this point the is_dirty must be false for metadata
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

        # there should be 17 CV_Medium records
        self.assertEqual(self.resTimeSeries.metadata.cv_mediums.all().count(), 17)
        # now update the timeseriesresult element with a new term for sample medium
        self.resTimeSeries.metadata.update_element('timeseriesresult', ts_result.id,
                                                   sample_medium="Sample medium-1"
                                                   )
        # check the auto generated term
        self.assertIn('sampleMedium_1', [s_medium.term for s_medium in
                                         self.resTimeSeries.metadata.cv_mediums.all()])

        # there should be 18 CV_Medium records
        self.assertEqual(self.resTimeSeries.metadata.cv_mediums.all().count(), 18)

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

    def test_get_xml(self):
        # add a valid odm2 sqlite file to generate metadata
        files = [UploadedFile(file=self.odm2_sqlite_file_obj, name=self.odm2_sqlite_file_name)]
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files,
                                            user=self.user, extract_metadata=False)

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

        # adding a valid ODM2 sqlite file should generate required core metadata and all
        # extended metadata
        files = [UploadedFile(file=self.odm2_sqlite_file_obj, name=self.odm2_sqlite_file_name)]
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=files,
                                            user=self.user, extract_metadata=False)

        utils.resource_file_add_process(resource=self.resTimeSeries, files=files, user=self.user,
                                        extract_metadata=True)

        self.assertTrue(self.resTimeSeries.has_required_content_files())
        self.assertTrue(self.resTimeSeries.metadata.has_all_required_elements())
        self.assertTrue(self.resTimeSeries.can_be_public_or_discoverable)

    def _test_metadata_extraction(self):
        # there should one content file
        self.assertEqual(self.resTimeSeries.files.all().count(), 1)

        # there should be one contributor element
        self.assertEqual(self.resTimeSeries.metadata.contributors.all().count(), 1)

        # test core metadata after metadata extraction
        extracted_title = "Water temperature data from the Little Bear River, UT"
        self.assertEqual(self.resTimeSeries.metadata.title.value, extracted_title)

        # there should be an abstract element
        self.assertNotEqual(self.resTimeSeries.metadata.description, None)
        extracted_abstract = "This dataset contains time series of observations of water " \
                             "temperature in the Little Bear River, UT. Data were recorded every " \
                             "30 minutes. The values were recorded using a HydroLab MS5 " \
                             "multi-parameter water quality sonde connected to a Campbell " \
                             "Scientific datalogger."

        self.assertEqual(self.resTimeSeries.metadata.description.abstract.strip(),
                          extracted_abstract)

        # there should be 2 coverage element -  point type and period type
        self.assertEqual(self.resTimeSeries.metadata.coverages.all().count(), 2)
        self.assertEqual(self.resTimeSeries.metadata.coverages.all().filter(type='box').count(), 1)
        self.assertEqual(self.resTimeSeries.metadata.coverages.all().filter(
            type='period').count(), 1)

        box_coverage = self.resTimeSeries.metadata.coverages.all().filter(type='box').first()
        self.assertEqual(box_coverage.value['projection'], 'Unknown')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(box_coverage.value['northlimit'], 41.718473)
        self.assertEqual(box_coverage.value['eastlimit'], -111.799324)
        self.assertEqual(box_coverage.value['southlimit'], 41.495409)
        self.assertEqual(box_coverage.value['westlimit'], -111.946402)

        temporal_coverage = self.resTimeSeries.metadata.coverages.all().filter(
            type='period').first()
        self.assertEqual(parser.parse(temporal_coverage.value['start']).date(),
                          parser.parse('01/01/2008').date())
        self.assertEqual(parser.parse(temporal_coverage.value['end']).date(),
                          parser.parse('01/31/2008').date())

        # there should be one format element
        self.assertEqual(self.resTimeSeries.metadata.formats.all().count(), 1)
        format_element = self.resTimeSeries.metadata.formats.all().first()
        self.assertEqual(format_element.value, 'application/sqlite')

        # there should be one subject element
        self.assertEqual(self.resTimeSeries.metadata.subjects.all().count(), 1)
        subj_element = self.resTimeSeries.metadata.subjects.all().first()
        self.assertEqual(subj_element.value, 'Temperature')

        # there should be a total of 7 timeseries
        self.assertEqual(self.resTimeSeries.metadata.time_series_results.all().count(), 7)

        # testing extended metadata elements

        # test 'site' - there should be 7 sites
        self.assertEqual(self.resTimeSeries.metadata.sites.all().count(), 7)
        # each site be associated with one series id
        for site in self.resTimeSeries.metadata.sites.all():
            self.assertEqual(len(site.series_ids), 1)

        # test the data for a specific site
        site = self.resTimeSeries.metadata.sites.filter(site_code='USU-LBR-Paradise').first()
        self.assertNotEqual(site, None)
        site_name = 'Little Bear River at McMurdy Hollow near Paradise, Utah'
        self.assertEqual(site.site_name, site_name)
        self.assertEqual(site.elevation_m, 1445)
        self.assertEqual(site.elevation_datum, 'NGVD29')
        self.assertEqual(site.site_type, 'Stream')

        # test 'variable' - there should be 1 variable element
        self.assertEqual(self.resTimeSeries.metadata.variables.all().count(), 1)
        variable = self.resTimeSeries.metadata.variables.all().first()
        # there should be 7 series ids associated with this one variable
        self.assertEqual(len(variable.series_ids), 7)
        # test the data for a variable
        self.assertEqual(variable.variable_code, 'USU36')
        self.assertEqual(variable.variable_name, 'Temperature')
        self.assertEqual(variable.variable_type, 'Water Quality')
        self.assertEqual(variable.no_data_value, -9999)
        self.assertEqual(variable.variable_definition, None)
        self.assertEqual(variable.speciation, 'Not Applicable')

        # test 'method' - there should be 1 method element
        self.assertEqual(self.resTimeSeries.metadata.methods.all().count(), 1)
        method = self.resTimeSeries.metadata.methods.all().first()
        # there should be 7 series ids associated with this one method element
        self.assertEqual(len(method.series_ids), 7)
        self.assertEqual(method.method_code, '28')
        method_name = 'Quality Control Level 1 Data Series created from raw QC Level 0 data ' \
                      'using ODM Tools.'
        self.assertEqual(method.method_name, method_name)
        self.assertEqual(method.method_type, 'Instrument deployment')
        method_des = 'Quality Control Level 1 Data Series created from raw QC Level 0 data ' \
                     'using ODM Tools.'
        self.assertEqual(method.method_description, method_des)
        self.assertEqual(method.method_link, None)

        # test 'processing_level' - there should be 1 processing_level element
        self.assertEqual(self.resTimeSeries.metadata.processing_levels.all().count(), 1)
        proc_level = self.resTimeSeries.metadata.processing_levels.all().first()
        # there should be 7 series ids associated with this one element
        self.assertEqual(len(proc_level.series_ids), 7)
        self.assertEqual(proc_level.processing_level_code, 1)
        self.assertEqual(proc_level.definition, 'Quality controlled data')
        explanation = 'Quality controlled data that have passed quality assurance procedures ' \
                      'such as routine estimation of timing and sensor calibration or visual ' \
                      'inspection and removal of obvious errors. An example is USGS published ' \
                      'streamflow records following parsing through USGS quality control ' \
                      'procedures.'
        self.assertEqual(proc_level.explanation, explanation)

        # test 'timeseries_result' - there should be 7 timeseries_result element
        self.assertEqual(self.resTimeSeries.metadata.time_series_results.all().count(), 7)
        ts_result = self.resTimeSeries.metadata.time_series_results.filter(
            series_ids__contains=['182d8fa3-1ebc-11e6-ad49-f45c8999816f']).first()
        self.assertNotEqual(ts_result, None)
        # there should be only 1 series id associated with this element
        self.assertEqual(len(ts_result.series_ids), 1)
        self.assertEqual(ts_result.units_type, 'Temperature')
        self.assertEqual(ts_result.units_name, 'degree celsius')
        self.assertEqual(ts_result.units_abbreviation, 'degC')
        self.assertEqual(ts_result.status, 'Unknown')
        self.assertEqual(ts_result.sample_medium, 'Surface Water')
        self.assertEqual(ts_result.value_count, 1441)
        self.assertEqual(ts_result.aggregation_statistics, 'Average')

        # test for CV lookup tables
        # there should be 23 CV_VariableType records
        self.assertEqual(self.resTimeSeries.metadata.cv_variable_types.all().count(), 23)
        # there should be 805 CV_VariableName records
        self.assertEqual(self.resTimeSeries.metadata.cv_variable_names.all().count(), 805)
        # there should be 145 CV_Speciation records
        self.assertEqual(self.resTimeSeries.metadata.cv_speciations.all().count(), 145)
        # there should be 51 CV_SiteType records
        self.assertEqual(self.resTimeSeries.metadata.cv_site_types.all().count(), 51)
        # there should be 5 CV_ElevationDatum records
        self.assertEqual(self.resTimeSeries.metadata.cv_elevation_datums.all().count(), 5)
        # there should be 25 CV_MethodType records
        self.assertEqual(self.resTimeSeries.metadata.cv_method_types.all().count(), 25)
        # there should be 179 CV_UnitsType records
        self.assertEqual(self.resTimeSeries.metadata.cv_units_types.all().count(), 179)
        # there should be 4 CV_Status records
        self.assertEqual(self.resTimeSeries.metadata.cv_statuses.all().count(), 4)
        # there should be 17 CV_Medium records
        self.assertEqual(self.resTimeSeries.metadata.cv_mediums.all().count(), 17)
        # there should be 17 CV_aggregationStatistics records
        self.assertEqual(self.resTimeSeries.metadata.cv_aggregation_statistics.all().count(), 17)
