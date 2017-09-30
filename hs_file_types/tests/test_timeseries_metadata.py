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
from hs_core.hydroshare.utils import resource_post_create_actions
from hs_core.views.utils import remove_folder, move_or_rename_file_or_folder
from hs_app_timeseries.models import Site, Variable, Method, ProcessingLevel, TimeSeriesResult

from hs_file_types.models import TimeSeriesLogicalFile, GenericLogicalFile, TimeSeriesFileMetaData
from hs_file_types.models.timeseries import CVVariableType, CVVariableName, CVSpeciation, \
    CVSiteType, CVElevationDatum, CVMethodType, CVMedium, CVUnitsType, CVStatus, \
    CVAggregationStatistic
from utils import assert_time_series_file_type_metadata


class TimeSeriesFileTypeMetaDataTest(MockIRODSTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(TimeSeriesFileTypeMetaDataTest, self).setUp()
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
            title='Test Time series File Type Metadata'
        )

        self.temp_dir = tempfile.mkdtemp()
        self.sqlite_file_name = 'ODM2_Multi_Site_One_Variable.sqlite'
        self.sqlite_file = 'hs_file_types/tests/data/{}'.format(self.sqlite_file_name)

        target_temp_sqlite_file = os.path.join(self.temp_dir, self.sqlite_file_name)
        shutil.copy(self.sqlite_file, target_temp_sqlite_file)
        self.sqlite_file_obj = open(target_temp_sqlite_file, 'r')

        self.sqlite_invalid_file_name = 'ODM2_invalid.sqlite'
        self.sqlite_invalid_file = 'hs_file_types/tests/data/{}'.format(
            self.sqlite_invalid_file_name)

        target_temp_sqlite_invalid_file = os.path.join(self.temp_dir, self.sqlite_invalid_file_name)
        shutil.copy(self.sqlite_invalid_file, target_temp_sqlite_invalid_file)

    def tearDown(self):
        super(TimeSeriesFileTypeMetaDataTest, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_sqlite_set_file_type_to_timeseries(self):
        # here we are using a valid sqlite file for setting it
        # to TimeSeries file type which includes metadata extraction
        self.sqlite_file_obj = open(self.sqlite_file, 'r')
        self._create_composite_resource(title='Untitled Resource')

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
        # check that there is one GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

        # check that there is no TimeSeriesLogicalFile object
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 0)

        # set the sqlite file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        # test extracted metadata
        assert_time_series_file_type_metadata(self)
        # test file level keywords
        # res_file = self.composite_resource.files.first()
        # logical_file = res_file.logical_file
        # self.assertEqual(len(logical_file.metadata.keywords), 1)
        # self.assertEqual(logical_file.metadata.keywords[0], 'Snow water equivalent')
        self.composite_resource.delete()

    def test_set_file_type_to_sqlite_invalid_file(self):
        # here we are using an invalid sqlite file for setting it
        # to TimeSeries file type which should fail
        self.sqlite_file_obj = open(self.sqlite_invalid_file, 'r')
        self._create_composite_resource()
        self._test_invalid_file()
        self.composite_resource.delete()

    def test_sqlite_metadata_update(self):
        # here we are using a valid sqlite file for setting it
        # to TimeSeries file type which includes metadata extraction
        # then we are testing update of the file level metadata elements

        self.sqlite_file_obj = open(self.sqlite_file, 'r')
        self._create_composite_resource(title='Untitled Resource')

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
        # check that there is one GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

        # check that there is no TimeSeriesLogicalFile object
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 0)

        # set the sqlite file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        # test updating site element
        site = logical_file.metadata.sites.filter(site_code='USU-LBR-Paradise').first()
        self.assertNotEqual(site, None)
        site_name = 'Little Bear River at McMurdy Hollow near Paradise, Utah'
        self.assertEqual(site.site_name, site_name)
        self.assertEqual(site.elevation_m, 1445)
        self.assertEqual(site.elevation_datum, 'NGVD29')
        self.assertEqual(site.site_type, 'Stream')
        self.assertFalse(logical_file.metadata.is_dirty)

        site_name = 'Little Bear River at Logan, Utah'
        site_data = {'site_name': site_name, 'elevation_m': site.elevation_m,
                     'elevation_datum': site.elevation_datum, 'site_type': site.site_type}
        logical_file.metadata.update_element('Site', site.id, **site_data)
        site = logical_file.metadata.sites.filter(site_code='USU-LBR-Paradise').first()
        self.assertEqual(site.site_name, site_name)
        self.assertTrue(logical_file.metadata.is_dirty)

        # updating site lat/long should update the resource coverage as well as file level coverage
        box_coverage = self.composite_resource.metadata.coverages.all().filter(type='box').first()
        self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(box_coverage.value['northlimit'], 41.718473)
        self.assertEqual(box_coverage.value['eastlimit'], -111.799324)
        self.assertEqual(box_coverage.value['southlimit'], 41.495409)
        self.assertEqual(box_coverage.value['westlimit'], -111.946402)

        box_coverage = logical_file.metadata.spatial_coverage
        self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(box_coverage.value['northlimit'], 41.718473)
        self.assertEqual(box_coverage.value['eastlimit'], -111.799324)
        self.assertEqual(box_coverage.value['southlimit'], 41.495409)
        self.assertEqual(box_coverage.value['westlimit'], -111.946402)

        site_data['latitude'] = 40.7896
        logical_file.metadata.update_element('Site', site.id, **site_data)
        site = logical_file.metadata.sites.filter(site_code='USU-LBR-Paradise').first()
        self.assertEqual(site.latitude, 40.7896)

        # test that resource level coverage got updated
        box_coverage = self.composite_resource.metadata.coverages.all().filter(type='box').first()
        self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(box_coverage.value['northlimit'], 41.718473)
        self.assertEqual(box_coverage.value['eastlimit'], -111.799324)
        # this is the changed value for the southlimit as a result of changing the sit latitude
        self.assertEqual(box_coverage.value['southlimit'], 40.7896)
        self.assertEqual(box_coverage.value['westlimit'], -111.946402)

        # test that file level coverage got updated
        box_coverage = logical_file.metadata.spatial_coverage
        self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(box_coverage.value['northlimit'], 41.718473)
        self.assertEqual(box_coverage.value['eastlimit'], -111.799324)
        # this is the changed value for the southlimit as a result of changing the sit latitude
        self.assertEqual(box_coverage.value['southlimit'], 40.7896)
        self.assertEqual(box_coverage.value['westlimit'], -111.946402)

        logical_file.metadata.is_dirty = False
        logical_file.metadata.save()
        # test updating variable element
        variable = logical_file.metadata.variables.filter(variable_code='USU36').first()
        self.assertNotEqual(variable, None)
        self.assertEqual(variable.variable_name, 'Temperature')
        self.assertEqual(variable.variable_type, 'Water Quality')
        self.assertEqual(variable.no_data_value, -9999)
        self.assertEqual(variable.speciation, 'Not Applicable')
        self.assertEqual(variable.variable_definition, None)

        var_def = 'Concentration of oxygen dissolved in water.'
        variable_data = {'variable_definition': var_def}
        logical_file.metadata.update_element('Variable', variable.id, **variable_data)
        variable = logical_file.metadata.variables.filter(variable_code='USU36').first()
        self.assertEqual(variable.variable_definition, var_def)
        self.assertEqual(variable.variable_name, 'Temperature')
        self.assertEqual(variable.variable_type, 'Water Quality')
        self.assertEqual(variable.no_data_value, -9999)
        self.assertEqual(variable.speciation, 'Not Applicable')

        self.assertTrue(logical_file.metadata.is_dirty)
        logical_file.metadata.is_dirty = False
        logical_file.metadata.save()

        # test updating method element
        method = logical_file.metadata.methods.filter(method_code=28).first()
        self.assertNotEqual(method, None)
        self.assertEqual(method.method_name, 'Quality Control Level 1 Data Series created from raw '
                                             'QC Level 0 data using ODM Tools.')
        self.assertEqual(method.method_type, 'Instrument deployment')
        self.assertEqual(method.method_description, 'Quality Control Level 1 Data Series created '
                                                    'from raw QC Level 0 data using ODM Tools.')
        self.assertEqual(method.method_link, None)

        method_link = "http://somesite.com"
        method_data = {'method_link': method_link}
        logical_file.metadata.update_element('Method', method.id, **method_data)
        method = logical_file.metadata.methods.filter(method_code=28).first()
        self.assertNotEqual(method, None)
        self.assertEqual(method.method_name, 'Quality Control Level 1 Data Series created from raw '
                                             'QC Level 0 data using ODM Tools.')
        self.assertEqual(method.method_type, 'Instrument deployment')
        self.assertEqual(method.method_description, 'Quality Control Level 1 Data Series created '
                                                    'from raw QC Level 0 data using ODM Tools.')
        self.assertEqual(method.method_link, method_link)

        self.assertTrue(logical_file.metadata.is_dirty)
        logical_file.metadata.is_dirty = False
        logical_file.metadata.save()

        # test updating processing level element
        pro_level = logical_file.metadata.processing_levels.filter(processing_level_code=1).first()
        self.assertNotEqual(pro_level, None)
        self.assertEqual(pro_level.definition, 'Quality controlled data')
        explanation = 'Quality controlled data that have passed quality assurance procedures ' \
                      'such as routine estimation of timing and sensor calibration or visual ' \
                      'inspection and removal of obvious errors. An example is USGS published ' \
                      'streamflow records following parsing through USGS quality ' \
                      'control procedures.'
        self.assertEqual(pro_level.explanation, explanation)

        definition = "Uncontrolled data"
        pro_level_data = {'definition': definition}
        logical_file.metadata.update_element('ProcessingLevel', pro_level.id, **pro_level_data)
        pro_level = logical_file.metadata.processing_levels.filter(processing_level_code=1).first()
        self.assertNotEqual(pro_level, None)
        self.assertEqual(pro_level.definition, definition)
        explanation = 'Quality controlled data that have passed quality assurance procedures ' \
                      'such as routine estimation of timing and sensor calibration or visual ' \
                      'inspection and removal of obvious errors. An example is USGS published ' \
                      'streamflow records following parsing through USGS quality ' \
                      'control procedures.'
        self.assertEqual(pro_level.explanation, explanation)

        self.assertTrue(logical_file.metadata.is_dirty)
        logical_file.metadata.is_dirty = False
        logical_file.metadata.save()

        # test updating time series result element
        ts_result = logical_file.metadata.time_series_results.all().first()
        self.assertNotEqual(ts_result, None)
        self.assertEqual(ts_result.units_type, 'Temperature')
        self.assertEqual(ts_result.units_name, 'degree celsius')
        self.assertEqual(ts_result.units_abbreviation, 'degC')
        self.assertEqual(ts_result.status, 'Unknown')
        self.assertEqual(ts_result.sample_medium, 'Surface Water')
        self.assertEqual(ts_result.value_count, 1441)
        self.assertEqual(ts_result.aggregation_statistics, 'Average')

        ts_data = {'status': 'Complete'}
        logical_file.metadata.update_element('timeseriesresult', ts_result.id, **ts_data)
        ts_result = logical_file.metadata.time_series_results.all().first()
        self.assertNotEqual(ts_result, None)
        self.assertEqual(ts_result.units_type, 'Temperature')
        self.assertEqual(ts_result.units_name, 'degree celsius')
        self.assertEqual(ts_result.units_abbreviation, 'degC')
        self.assertEqual(ts_result.status, 'Complete')
        self.assertEqual(ts_result.sample_medium, 'Surface Water')
        self.assertEqual(ts_result.value_count, 1441)
        self.assertEqual(ts_result.aggregation_statistics, 'Average')
        self.assertTrue(logical_file.metadata.is_dirty)

        self.composite_resource.delete()

    def test_file_metadata_on_logical_file_delete(self):
        # test that when the TimeSeriesLogicalFile instance is deleted
        # all metadata associated with it also get deleted
        self.sqlite_file_obj = open(self.sqlite_file, 'r')
        self._create_composite_resource(title='Untitled Resource')

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # set the sqlite file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # file level metadata
        # there should be Site metadata objects
        self.assertTrue(Site.objects.count() > 0)
        # there should be Variable metadata objects
        self.assertTrue(Variable.objects.count() > 0)
        # there should be Method metadata objects
        self.assertTrue(Method.objects.count() > 0)
        # there should be ProcessingLevel metadata objects
        self.assertTrue(ProcessingLevel.objects.count() > 0)
        # there should be TimeSeriesResult metadata objects
        self.assertTrue(TimeSeriesResult.objects.count() > 0)

        # CV lookup data
        self.assertEqual(logical_file.metadata.cv_variable_types.all().count(), 23)
        self.assertEqual(CVVariableType.objects.all().count(), 23)
        self.assertEqual(logical_file.metadata.cv_variable_names.all().count(), 805)
        self.assertEqual(CVVariableName.objects.all().count(), 805)
        self.assertEqual(logical_file.metadata.cv_speciations.all().count(), 145)
        self.assertEqual(CVSpeciation.objects.all().count(), 145)
        self.assertEqual(logical_file.metadata.cv_elevation_datums.all().count(), 5)
        self.assertEqual(CVElevationDatum.objects.all().count(), 5)
        self.assertEqual(logical_file.metadata.cv_site_types.all().count(), 51)
        self.assertEqual(CVSiteType.objects.all().count(), 51)
        self.assertEqual(logical_file.metadata.cv_method_types.all().count(), 25)
        self.assertEqual(CVMethodType.objects.all().count(), 25)
        self.assertEqual(logical_file.metadata.cv_units_types.all().count(), 179)
        self.assertEqual(CVUnitsType.objects.all().count(), 179)
        self.assertEqual(logical_file.metadata.cv_statuses.all().count(), 4)
        self.assertEqual(CVStatus.objects.all().count(), 4)
        self.assertEqual(logical_file.metadata.cv_mediums.all().count(), 18)
        self.assertEqual(CVMedium.objects.all().count(), 18)
        self.assertEqual(logical_file.metadata.cv_aggregation_statistics.all().count(), 17)
        self.assertEqual(CVAggregationStatistic.objects.all().count(), 17)

        # delete the logical file
        logical_file.logical_delete(self.user)
        # test that we have no logical file of type TimeSeries
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 0)
        self.assertEqual(TimeSeriesFileMetaData.objects.count(), 0)

        # test that all file level metadata deleted
        # there should be no Site metadata objects
        self.assertTrue(Site.objects.count() == 0)
        # there should be no Variable metadata objects
        self.assertTrue(Variable.objects.count() == 0)
        # there should be no Method metadata objects
        self.assertTrue(Method.objects.count() == 0)
        # there should be no ProcessingLevel metadata objects
        self.assertTrue(ProcessingLevel.objects.count() == 0)
        # there should be no TimeSeriesResult metadata objects
        self.assertTrue(TimeSeriesResult.objects.count() == 0)

        # there should not be any CV type records
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

        self.composite_resource.delete()

    def test_timeseries_file_type_folder_delete(self):
        # when  a file is set to TimeSeriesLogicalFile type
        # system automatically creates folder using the name of the file
        # that was used to set the file type
        # Here we need to test that when that folder gets deleted, all files
        # in that folder gets deleted, the logicalfile object gets deleted and
        # the associated metadata objects get deleted
        self.sqlite_file_obj = open(self.sqlite_file, 'r')
        self._create_composite_resource(title='Untitled Resource')

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # set the sqlite file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # test that we have one logical file of type TimeSeries
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 1)
        self.assertEqual(TimeSeriesFileMetaData.objects.count(), 1)
        # delete the folder for the logical file
        folder_path = "data/contents/ODM2_Multi_Site_One_Variable"
        remove_folder(self.user, self.composite_resource.short_id, folder_path)
        # there should no content files
        self.assertEqual(self.composite_resource.files.count(), 0)

        # there should not be any timeseries logical file or metadata file
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 0)
        self.assertEqual(TimeSeriesFileMetaData.objects.count(), 0)
        # test that all file level metadata deleted
        # there should be no Site metadata objects
        self.assertTrue(Site.objects.count() == 0)
        # there should be no Variable metadata objects
        self.assertTrue(Variable.objects.count() == 0)
        # there should be no Method metadata objects
        self.assertTrue(Method.objects.count() == 0)
        # there should be no ProcessingLevel metadata objects
        self.assertTrue(ProcessingLevel.objects.count() == 0)
        # there should be no TimeSeriesResult metadata objects
        self.assertTrue(TimeSeriesResult.objects.count() == 0)

        # there should not be any CV type records
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

        self.composite_resource.delete()

    def test_file_metadata_on_file_delete(self):
        # test that when any file in TimeSeries logical file is deleted
        # all metadata associated with TimeSeriesLogicalFile is deleted
        # test for both .sqlite and .csv delete

        # test with deleting of 'sqlite' file
        self._test_file_metadata_on_file_delete(ext='.sqlite')

        # TODO:  test with deleting of 'csv' file - uncomment the following when we implement
        # csv file
        # self._test_file_metadata_on_file_delete(ext='.csv')

    def test_file_rename_or_move(self):
        # test that file can't be moved or renamed for any resource file
        # that's part of the TimeSeries logical file object (LFO)

        self.sqlite_file_obj = open(self.sqlite_file, 'r')
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()

        # extract metadata from the sqlite file
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)

        # test renaming of files that are associated with timeseries LFO - should raise exception
        self.assertEqual(self.composite_resource.files.count(), 1)

        base_path = "data/contents/ODM2_Multi_Site_One_Variable/{}"
        src_path = base_path.format('ODM2_Multi_Site_One_Variable.sqlite')
        tgt_path = base_path.format('ODM2_Multi_Site_One_Variable_1.sqlite')
        with self.assertRaises(DRF_ValidationError):
            move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                          tgt_path)
        # TODO: test for renaming csv file when we implement csv file

        # test moving the files associated with timeseries LFO
        tgt_path = 'data/contents/new_folder/ODM2_Multi_Site_One_Variable.sqlite'
        with self.assertRaises(DRF_ValidationError):
            move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                          tgt_path)

        # TODO: test for moving csv file when we implement csv file

        self.composite_resource.delete()

    def _test_file_metadata_on_file_delete(self, ext):
        self.sqlite_file_obj = open(self.sqlite_file, 'r')
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()
        # set the sqlite file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # test that we have one logical file of type TimeSeries
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 1)
        self.assertEqual(TimeSeriesFileMetaData.objects.count(), 1)
        # delete content file specified by extension (ext parameter)
        res_file = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, ext)[0]
        hydroshare.delete_resource_file(self.composite_resource.short_id,
                                        res_file.id,
                                        self.user)

        # test that we don't have any logical file of type TimeSeries
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 0)
        self.assertEqual(TimeSeriesFileMetaData.objects.count(), 0)

        # test that all file level metadata deleted
        # there should be no Site metadata objects
        self.assertTrue(Site.objects.count() == 0)
        # there should be no Variable metadata objects
        self.assertTrue(Variable.objects.count() == 0)
        # there should be no Method metadata objects
        self.assertTrue(Method.objects.count() == 0)
        # there should be no ProcessingLevel metadata objects
        self.assertTrue(ProcessingLevel.objects.count() == 0)
        # there should be no TimeSeriesResult metadata objects
        self.assertTrue(TimeSeriesResult.objects.count() == 0)

        # there should not be any CV type records
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

        self.composite_resource.delete()

    def _create_composite_resource(self, title='Test Time series File Type Metadata'):
        uploaded_file = UploadedFile(file=self.sqlite_file_obj,
                                     name=os.path.basename(self.sqlite_file_obj.name))

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

        # check that the resource file is associated with the generic logical file
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")

        # trying to set this invalid tif file to NetCDF file type should raise
        # ValidationError
        with self.assertRaises(ValidationError):
            TimeSeriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)

        # test that the invalid file did not get deleted
        self.assertEqual(self.composite_resource.files.all().count(), 1)

        # check that the resource file is not associated with generic logical file
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
