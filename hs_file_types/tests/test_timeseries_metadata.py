import os

from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from rest_framework.exceptions import ValidationError as DRF_ValidationError

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.models import ResourceFile
from hs_core.views.utils import remove_folder, move_or_rename_file_or_folder
from hs_app_timeseries.models import Site, Variable, Method, ProcessingLevel, TimeSeriesResult

from hs_file_types.models import TimeSeriesLogicalFile, TimeSeriesFileMetaData
from hs_file_types.models.timeseries import CVVariableType, CVVariableName, CVSpeciation, \
    CVSiteType, CVElevationDatum, CVMethodType, CVMedium, CVUnitsType, CVStatus, \
    CVAggregationStatistic
from utils import assert_time_series_file_type_metadata, CompositeResourceTestMixin


class TimeSeriesFileTypeTest(MockIRODSTestCaseMixin, TransactionTestCase,
                             CompositeResourceTestMixin):
    def setUp(self):
        super(TimeSeriesFileTypeTest, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        self.res_title = 'Test Timeseries File Type'

        self.sqlite_file_name = 'ODM2_Multi_Site_One_Variable.sqlite'
        self.sqlite_file = 'hs_file_types/tests/data/{}'.format(self.sqlite_file_name)

        self.sqlite_invalid_file_name = 'ODM2_invalid.sqlite'
        self.sqlite_invalid_file = 'hs_file_types/tests/data/{}'.format(
            self.sqlite_invalid_file_name)

        self.odm2_csv_file_name = 'ODM2_Multi_Site_One_Variable_Test.csv'
        self.odm2_csv_file = 'hs_app_timeseries/tests/{}'.format(self.odm2_csv_file_name)

    def test_create_aggregation_from_sqlite_file_1(self):
        # here we are using a valid sqlite file for setting it
        # to TimeSeries file type which includes metadata extraction
        # here in this case the sqlite file is at the root of the folder hierarchy
        # location of the sqlite file before aggregation:
        # data/contents/ODM2_Multi_Site_One_Variable.sqlite
        # location of the sqlite file after aggregation:
        # data/contents/ODM2_Multi_Site_One_Variable/ODM2_Multi_Site_One_Variable.sqlite

        self.res_title = 'Untitled resource'
        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.sqlite_file)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file at this point
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no TimeSeriesLogicalFile object
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 0)

        # set the sqlite file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # test extracted metadata
        res_file = self.composite_resource.files.first()
        base_file_name, _ = os.path.splitext(res_file.file_name)
        expected_file_folder = base_file_name
        assert_time_series_file_type_metadata(self, expected_file_folder=expected_file_folder)

        self.composite_resource.delete()

    def test_create_aggregation_from_sqlite_file_2(self):
        # here we are using a valid sqlite file for setting it
        # to TimeSeries file type which includes metadata extraction
        # here in this case the sqlite file is in a folder
        # location of the sqlite file before aggregation:
        # timeseries_aggr/ODM2_Multi_Site_One_Variable.sqlite
        # location of the sqlite file after aggregation:
        # timeseries_aggr/ODM2_Multi_Site_One_Variable.sqlite

        self.res_title = 'Untitled resource'
        self.create_composite_resource()
        # create a folder to place the sqlite file in that folder before creating an
        # aggregation from the sqlite file

        new_folder = 'timeseries_aggr'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        self.add_file_to_resource(file_to_add=self.sqlite_file, upload_folder=new_folder)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file at this point
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no TimeSeriesLogicalFile object
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 0)

        # set the sqlite file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # test extracted metadata
        assert_time_series_file_type_metadata(self, expected_file_folder=new_folder)

        self.composite_resource.delete()

    def test_create_aggregation_from_sqlite_file_3(self):
        # here we are using a valid sqlite file for setting it
        # to TimeSeries file type which includes metadata extraction
        # here in this case the sqlite file is in a folder along with another file that is not
        # going to be part of the aggregation. In this case a new folder should be created to
        # represent the aggregation
        # location of the sqlite file before aggregation:
        # my_folder/ODM2_Multi_Site_One_Variable.sqlite
        # location of the additional file before aggregation:
        # my_folder/ODM2_invalid.sqlite
        # location of the sqlite file after aggregation:
        # my_folder/ODM2_Multi_Site_One_Variable/ODM2_Multi_Site_One_Variable.sqlite

        self.res_title = 'Untitled resource'
        self.create_composite_resource()
        # create a folder to place the sqlite file in that folder before creating an
        # aggregation from the sqlite file

        new_folder = 'my_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        self.add_file_to_resource(file_to_add=self.sqlite_file, upload_folder=new_folder)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # add another file to the same folder
        self.add_file_to_resource(file_to_add=self.sqlite_invalid_file, upload_folder=new_folder)
        self.assertEqual(self.composite_resource.files.all().count(), 2)

        # create and test aggregation to check that a new folder was created
        self._test_aggregation_folder_creation(res_file, new_folder)

    def test_create_aggregation_from_sqlite_file_4(self):
        # here we are using a valid sqlite file for setting it
        # to TimeSeries file type which includes metadata extraction
        # here in this case the sqlite file is in a folder which contains another folder
        # in this case a new folder should be created to represent the aggregation
        # location of the sqlite file before aggregation:
        # my_folder/ODM2_Multi_Site_One_Variable.sqlite
        # location of the additional folder before aggregation:
        # my_folder/another_folder
        # location of the sqlite file after aggregation:
        # my_folder/ODM2_Multi_Site_One_Variable/ODM2_Multi_Site_One_Variable.sqlite
        # location of the additional folder after aggregation:
        # my_folder/another_folder

        self.res_title = 'Untitled resource'
        self.create_composite_resource()
        # create a folder to place the sqlite file in that folder before creating an
        # aggregation from the sqlite file

        new_folder = 'my_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        another_folder = '{}/another_folder'.format(new_folder)
        ResourceFile.create_folder(self.composite_resource, another_folder)
        self.add_file_to_resource(file_to_add=self.sqlite_file, upload_folder=new_folder)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # create and test aggregation to check that a new folder was created
        self._test_aggregation_folder_creation(res_file, new_folder)

    def test_create_aggregation_from_CSV_file_1(self):
        # here we are using a valid CSV file for setting it
        # to TimeSeries file type which includes metadata extraction
        # here in this case the csv file at the root of the folder hierarchy

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.odm2_csv_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no TimeSeriesLogicalFile object
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 0)

        # set the CSV file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()
        base_file_name, _ = os.path.splitext(res_file.file_name)
        expected_file_folder = base_file_name
        self._test_CSV_aggregation(expected_aggr_folder=expected_file_folder)

        self.composite_resource.delete()

    def test_create_aggregation_from_CSV_file_2(self):
        # here we are using a valid CSV file for setting it
        # to TimeSeries file type which includes metadata extraction
        # here in this case the csv file in a folder

        self.create_composite_resource()
        new_folder = 'timeseries_aggr'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        self.add_file_to_resource(file_to_add=self.odm2_csv_file, upload_folder=new_folder)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no TimeSeriesLogicalFile object
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 0)

        # set the CSV file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        self._test_CSV_aggregation(expected_aggr_folder=new_folder)

        self.composite_resource.delete()

    def test_create_aggregation_from_sqlite_folder_1(self):
        # here we are testing that timeseries aggregation can be created from a folder that
        # contains a sqlite file

        self._test_create_aggregation_from_folder_sqlite(sqlite_folder_path='timeseries_aggr')

    def test_create_aggregation_from_sqlite_folder_2(self):
        # here we are testing that timeseries aggregation can be created from a folder that
        # contains a sqlite file. This folder has a parent folder

        self._test_create_aggregation_from_folder_sqlite(
            sqlite_folder_path='parent_folder/timeseries_aggr')

    def test_create_aggregation_from_CSV_folder_1(self):
        # here we are testing that timeseries aggregation can be created from a folder that
        # contains a csv file.

        self._test_create_aggregation_from_folder_CSV(csv_folder_path='timeseries_aggr')

    def test_create_aggregation_from_CSV_folder_2(self):
        # here we are testing that timeseries aggregation can be created from a folder that
        # contains a csv file. This folder has a parent folder

        self._test_create_aggregation_from_folder_CSV(
            csv_folder_path='parent_foldertimeseries_aggr')

    def test_create_aggregation_from_sqlite_invalid_file(self):
        # here we are using an invalid sqlite file for setting it
        # to TimeSeries file type which should fail

        self.create_composite_resource(self.sqlite_invalid_file)
        self._test_invalid_file()
        self.composite_resource.delete()

    def test_create_aggregation_from_csv_invalid_file(self):
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

    def test_aggregation_sqlite_metadata_update(self):
        # here we are using a valid sqlite file for setting it
        # to TimeSeries file type which includes metadata extraction
        # then we are testing update of the file level metadata elements

        self.res_title = 'Untitled Resource'
        self.create_composite_resource(file_to_upload=self.sqlite_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no TimeSeriesLogicalFile object
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 0)

        # set the sqlite file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
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

        # updating site lat/long should update only the file level (aggregation) coverage
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

        # test that resource level coverage did not get updated
        box_coverage = self.composite_resource.metadata.coverages.all().filter(type='box').first()
        self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(box_coverage.value['northlimit'], 41.718473)
        self.assertEqual(box_coverage.value['eastlimit'], -111.799324)
        self.assertEqual(box_coverage.value['southlimit'], 41.495409)
        self.assertEqual(box_coverage.value['westlimit'], -111.946402)

        # test that file level coverage got updated
        box_coverage = logical_file.metadata.spatial_coverage
        self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(box_coverage.value['northlimit'], 41.718473)
        self.assertEqual(box_coverage.value['eastlimit'], -111.799324)
        # this is the changed value for the southlimit as a result of changing the site latitude
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

    def test_aggregation_metadata_on_aggregation_delete(self):
        # test that when the TimeSeriesLogicalFile instance is deleted
        # all metadata associated with it also get deleted

        self.create_composite_resource(file_to_upload=self.sqlite_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # set the sqlite file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
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

    def test_remove_aggregation(self):
        # test that when an instance TimeSeriesLogicalFile (aggregation) is deleted
        # all files associated with that aggregation is not deleted but the associated metadata
        # is deleted

        self.create_composite_resource(file_to_upload=self.sqlite_file)
        res_file = self.composite_resource.files.first()

        # set the sqlite file to TimeSeriesLogicalFile (aggregation)
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test that we have one logical file of type TimeSeriesLogicalFile
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 1)
        self.assertEqual(TimeSeriesFileMetaData.objects.count(), 1)
        logical_file = TimeSeriesLogicalFile.objects.first()
        self.assertEqual(logical_file.files.all().count(), 1)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        self.assertEqual(set(self.composite_resource.files.all()),
                         set(logical_file.files.all()))

        # delete the aggregation (logical file) object using the remove_aggregation function
        logical_file.remove_aggregation()
        # test there is no TimeSeriesLogicalFile object
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 0)
        # test there is no TimeSeriesFileMetaData object
        self.assertEqual(TimeSeriesFileMetaData.objects.count(), 0)
        # check the files associated with the aggregation not deleted
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        # check the file folder is not deleted
        res_file = self.composite_resource.files.first()
        base_file_name, _ = os.path.splitext(res_file.file_name)
        file_folder = base_file_name
        for f in self.composite_resource.files.all():
            self.assertEqual(f.file_folder, file_folder)
        self.composite_resource.delete()

    def test_aggregation_folder_delete(self):
        # when  a file is set to TimeSeriesLogicalFile type
        # system automatically creates folder using the name of the file
        # that was used to set the file type
        # Here we need to test that when that folder gets deleted, all files
        # in that folder gets deleted, the logicalfile object gets deleted and
        # the associated metadata objects get deleted

        self.create_composite_resource(file_to_upload=self.sqlite_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # set the sqlite file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()
        base_file_name, _ = os.path.splitext(res_file.file_name)
        file_folder = base_file_name
        # test that we have one logical file of type TimeSeries
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 1)
        self.assertEqual(TimeSeriesFileMetaData.objects.count(), 1)
        # delete the folder for the logical file
        folder_path = "data/contents/{}".format(file_folder)
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

    def test_aggregation_metadata_on_file_delete(self):
        # test that when any file in TimeSeries logical file is deleted
        # all metadata associated with TimeSeriesLogicalFile is deleted
        # test for both .sqlite and .csv delete

        # test with deleting of 'sqlite' file
        self._test_file_metadata_on_file_delete(ext='.sqlite')

        # test with deleting of 'csv' file
        self._test_file_metadata_on_file_delete(ext='.csv')

    def test_aggregation_file_rename(self):
        # test that a file can't renamed for any resource file
        # that's part of the TimeSeries logical file

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.sqlite_file)
        res_file = self.composite_resource.files.first()

        # create aggregation from the sqlite file
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # test renaming of files that are associated with aggregation raises exception
        self.assertEqual(self.composite_resource.files.count(), 1)
        res_file = self.composite_resource.files.first()
        base_file_name, ext = os.path.splitext(res_file.file_name)
        expected_folder_name = base_file_name
        self.assertEqual(res_file.file_folder, expected_folder_name)
        src_path = 'data/contents/{0}/{1}.{2}'.format(expected_folder_name, base_file_name, ext)
        new_file_name = 'some_raster.{}'.format(ext)
        self.assertNotEqual(res_file.file_name, new_file_name)
        tgt_path = 'data/contents/{}/{}'.format(expected_folder_name, new_file_name)
        with self.assertRaises(DRF_ValidationError):
            move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                          tgt_path)

        self.composite_resource.delete()

    def test_aggregation_file_move(self):
        # test any resource file that's part of the TimeSeries logical file can't be moved

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.sqlite_file)
        res_file = self.composite_resource.files.first()

        # create the aggregation using the sqlite file
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # test renaming of files that are associated with timeseries aggregation - which
        # should raise exception
        self.assertEqual(self.composite_resource.files.count(), 1)
        res_file = self.composite_resource.files.first()
        base_file_name, ext = os.path.splitext(res_file.file_name)
        expected_folder_name = base_file_name
        self.assertEqual(res_file.file_folder, expected_folder_name)
        new_folder = 'timeseries_aggr'
        ResourceFile.create_folder(self.composite_resource, new_folder)

        # moving any of the resource files to this new folder should raise exception
        tgt_path = 'data/contents/{}'.format(new_folder)
        for res_file in self.composite_resource.files.all():
            with self.assertRaises(DRF_ValidationError):
                src_path = os.path.join('data', 'contents', res_file.short_path)
                move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                              tgt_path)

        self.composite_resource.delete()

    def test_aggregation_folder_rename(self):
        # test changes to aggregation name, aggregation metadata xml file path, and aggregation
        # resource map xml file path on folder name change

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.sqlite_file)
        res_file = self.composite_resource.files.first()
        base_file_name, ext = os.path.splitext(res_file.file_name)
        expected_folder_name = base_file_name

        # create aggregation from the sqlite file
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        self.assertEqual(self.composite_resource.files.count(), 1)
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.file_folder, expected_folder_name)

        # test aggregation name
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.aggregation_name, res_file.file_folder)

        # test aggregation xml file paths
        expected_meta_file_path = '{}/{}_meta.xml'.format(base_file_name, base_file_name)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_file_path)

        expected_map_file_path = '{}/{}_resmap.xml'.format(base_file_name, base_file_name)
        self.assertEqual(logical_file.map_short_file_path, expected_map_file_path)

        # test renaming folder
        src_path = 'data/contents/{}'.format(expected_folder_name)
        tgt_path = 'data/contents/{}_1'.format(expected_folder_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.file_folder, '{}_1'.format(expected_folder_name))

        # test aggregation name update
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.aggregation_name, res_file.file_folder)

        # test aggregation xml file paths
        expected_meta_file_path = '{}_1/{}_1_meta.xml'.format(expected_folder_name,
                                                              expected_folder_name)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_file_path)

        expected_map_file_path = '{}_1/{}_1_resmap.xml'.format(expected_folder_name,
                                                               expected_folder_name)
        self.assertEqual(logical_file.map_short_file_path, expected_map_file_path)

        self.composite_resource.delete()

    def test_aggregation_parent_folder_rename(self):
        # test changes to aggregation name, aggregation metadata xml file path, and aggregation
        # resource map xml file path on aggregation folder parent folder name change

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.sqlite_file)
        res_file = self.composite_resource.files.first()
        base_file_name, ext = os.path.splitext(res_file.file_name)
        aggregation_folder_name = base_file_name

        # create aggregation from the sqlite file
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # test renaming of files that are associated with aggregation raises exception
        self.assertEqual(self.composite_resource.files.count(), 1)

        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.file_folder, aggregation_folder_name)

        # test aggregation name
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.aggregation_name, res_file.file_folder)

        # test aggregation xml file paths
        # test aggregation xml file paths
        expected_meta_file_path = '{}/{}_meta.xml'.format(aggregation_folder_name,
                                                          aggregation_folder_name)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_file_path)

        expected_map_file_path = '{}/{}_resmap.xml'.format(aggregation_folder_name,
                                                           aggregation_folder_name)
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

        res_file = self.composite_resource.files.first()
        file_folder = '{}/{}'.format(parent_folder_rename, aggregation_folder_name)
        self.assertEqual(res_file.file_folder, file_folder)

        # test aggregation name after folder rename
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.aggregation_name, res_file.file_folder)

        # test aggregation xml file paths after folder rename
        expected_meta_file_path = '{0}/{1}/{2}_meta.xml'.format(parent_folder_rename,
                                                                aggregation_folder_name,
                                                                aggregation_folder_name)

        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_file_path)
        expected_map_file_path = '{0}/{1}/{2}_resmap.xml'.format(parent_folder_rename,
                                                                 aggregation_folder_name,
                                                                 aggregation_folder_name)

        self.assertEqual(logical_file.map_short_file_path, expected_map_file_path)

        self.composite_resource.delete()

    def test_aggregation_folder_move(self):
        # test changes to aggregation name, aggregation metadata xml file path, and aggregation
        # resource map xml file path on aggregation folder move

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.sqlite_file)
        res_file = self.composite_resource.files.first()
        base_file_name, ext = os.path.splitext(res_file.file_name)
        aggregation_folder_name = base_file_name

        # create aggregation from the sqlite file
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        self.assertEqual(self.composite_resource.files.count(), 1)
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.file_folder, aggregation_folder_name)

        # create a folder to move the aggregation folder there
        parent_folder = 'parent_folder'
        ResourceFile.create_folder(self.composite_resource, parent_folder)
        # move the aggregation folder to the parent folder
        src_path = 'data/contents/{}'.format(aggregation_folder_name)
        tgt_path = 'data/contents/{0}/{1}'.format(parent_folder, aggregation_folder_name)

        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        res_file = self.composite_resource.files.first()
        file_folder = '{0}/{1}'.format(parent_folder, aggregation_folder_name)
        self.assertEqual(res_file.file_folder, file_folder)

        # test aggregation name update
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.aggregation_name, res_file.file_folder)

        # test aggregation xml file paths
        expected_meta_file_path = '{0}/{1}/{2}_meta.xml'.format(parent_folder,
                                                                aggregation_folder_name,
                                                                aggregation_folder_name)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_file_path)

        expected_map_file_path = '{0}/{1}/{2}_resmap.xml'.format(parent_folder,
                                                                 aggregation_folder_name,
                                                                 aggregation_folder_name)

        self.assertEqual(logical_file.map_short_file_path, expected_map_file_path)

        self.composite_resource.delete()

    def test_aggregation_folder_move_not_allowed(self):
        # test a folder is not allowed to be moved into a folder that represents an aggregation

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.sqlite_file)
        res_file = self.composite_resource.files.first()
        base_file_name, ext = os.path.splitext(res_file.file_name)
        aggregation_folder_name = base_file_name

        # create aggregation from the sqlite file
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # create a folder to move the aggregation folder there
        new_folder = 'folder_to_move'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # move the new folder into the aggregation folder
        src_path = 'data/contents/{}'.format(new_folder)
        tgt_path = 'data/contents/{}'.format(aggregation_folder_name)
        with self.assertRaises(DRF_ValidationError):
            move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                          tgt_path)

        self.composite_resource.delete()

    def test_aggregation_folder_sub_folder_not_allowed(self):
        # test a folder can't be created inside a folder that represents an aggregation

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.sqlite_file)
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.file_folder, None)

        # create aggregation from the sqlite file
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()
        self.assertNotEqual(res_file.file_folder, None)
        # create a folder inside the aggregation folder
        new_folder = '{}/sub_folder'.format(res_file.file_folder)
        with self.assertRaises(DRF_ValidationError):
            ResourceFile.create_folder(self.composite_resource, new_folder)

        self.composite_resource.delete()

    def test_file_move_to_aggregation_not_allowed(self):
        # test no file can be moved into a folder that represents a timeseries aggregation

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.sqlite_file)
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.file_folder, None)

        # create aggregation from the sqlite file
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()
        self.assertNotEqual(res_file.file_folder, None)

        # add a file to the resource which will try to move into the aggregation folder
        res_file_to_move = self.add_file_to_resource(file_to_add=self.odm2_csv_file)
        src_path = os.path.join('data', 'contents', res_file_to_move.short_path)
        tgt_path = 'data/contents/{}'.format(res_file.file_folder)

        # move file to aggregation folder
        with self.assertRaises(DRF_ValidationError):
            move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                          tgt_path)
        self.composite_resource.delete()

    def test_upload_file_to_aggregation_not_allowed(self):
        # test no file can be uploaded into a folder that represents an aggregation

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.sqlite_file)
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.file_folder, None)

        # create aggregation from the sqlite file
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()
        self.assertNotEqual(res_file.file_folder, None)

        # add a file to the resource at the aggregation folder
        with self.assertRaises(ValidationError):
            self.add_file_to_resource(file_to_add=self.odm2_csv_file,
                                      upload_folder=res_file.file_folder)
        self.composite_resource.delete()

    def _test_aggregation_folder_creation(self, res_file, file_folder):
        # check that the resource file is not associated with any logical file at this point
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no TimeSeriesLogicalFile object
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 0)

        # set the sqlite file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # test logical file/aggregation
        # check that there is now one TimeSeriesLogicalFile object
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 1)
        self.assertEqual(len(self.composite_resource.logical_files), 1)
        logical_file = self.composite_resource.logical_files[0]
        self.assertEqual(logical_file.files.count(), 1)
        base_sqlite_file_name, _ = os.path.splitext(self.sqlite_file_name)
        expected_file_folder = '{0}/{1}'.format(file_folder, base_sqlite_file_name)
        res_file = logical_file.files.first()
        self.assertEqual(res_file.file_folder, expected_file_folder)
        self.assertTrue(isinstance(logical_file, TimeSeriesLogicalFile))
        self.assertTrue(logical_file.metadata, TimeSeriesFileMetaData)

        self.composite_resource.delete()

    def _test_CSV_aggregation(self, expected_aggr_folder):
        # test that the ODM2.sqlite blank file got added to the resource
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        csv_res_file = None
        sqlite_res_file = None
        for res_file in self.composite_resource.files.all():
            if res_file.extension == '.sqlite':
                sqlite_res_file = res_file
            elif res_file.extension == '.csv':
                csv_res_file = res_file

        self.assertNotEqual(csv_res_file, None)
        self.assertNotEqual(sqlite_res_file, None)

        self.assertEqual(csv_res_file.logical_file_type_name, "TimeSeriesLogicalFile")
        self.assertEqual(sqlite_res_file.logical_file_type_name, "TimeSeriesLogicalFile")
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 1)
        logical_file = csv_res_file.logical_file

        # test that both csv and sqlite files of the logical file are in a folder
        for res_file in logical_file.files.all():
            self.assertEqual(res_file.file_folder, expected_aggr_folder)

        # since the uploaded csv file has 2 data columns, the metadata should have 2 series names
        self.assertEqual(len(logical_file.metadata.series_names), 2)
        csv_data_column_names = set(['Temp_DegC_Mendon', 'Temp_DegC_Paradise'])
        self.assertEqual(set(logical_file.metadata.series_names), csv_data_column_names)

        # since the uploaded csv file has 2 data columns, the metadata should have
        # the attribute value_counts (dict) 2 elements
        self.assertEqual(len(logical_file.metadata.value_counts), 2)
        self.assertEqual(set(logical_file.metadata.value_counts.keys()), csv_data_column_names)

        # there should be 20 data values for each series
        self.assertEqual(logical_file.metadata.value_counts['Temp_DegC_Mendon'], '20')
        self.assertEqual(logical_file.metadata.value_counts['Temp_DegC_Paradise'], '20')

        # the dataset name (title) must be set the name of the folder in which the CSV file exist
        expected_dataset_name = os.path.basename(csv_res_file.file_folder)
        self.assertEqual(logical_file.dataset_name, expected_dataset_name)

        # there should not be any file level abstract
        self.assertEqual(logical_file.metadata.abstract, None)

        # there should not be any file level keywords
        self.assertEqual(logical_file.metadata.keywords, [])

        # there should be 1 coverage element of type period at the file level
        self.assertEqual(logical_file.metadata.coverages.all().count(), 1)
        self.assertEqual(logical_file.metadata.coverages.filter(type='period').count(), 1)
        self.assertEqual(logical_file.has_csv_file, True)

        # at file level there should not be any site element
        self.assertEqual(logical_file.metadata.sites.all().count(), 0)

        # at file level there should not be any method element
        self.assertEqual(logical_file.metadata.methods.all().count(), 0)

        # at file level there should not be any variable element
        self.assertEqual(logical_file.metadata.variables.all().count(), 0)

        # at file level there should not an any site processing level
        self.assertEqual(logical_file.metadata.processing_levels.all().count(), 0)

        # at file level there should not be any result element
        self.assertEqual(logical_file.metadata.time_series_results.all().count(), 0)

        # resource title does not get updated when csv is set to file type
        self.assertEqual(self.composite_resource.metadata.title.value, self.res_title)
        # self._test_no_change_in_metadata()
        # there should be  2 format elements - since the resource has a csv file and a sqlite file
        self.assertEqual(self.composite_resource.metadata.formats.all().count(), 2)

        # there should be 1 coverage element of type period
        self.assertEqual(self.composite_resource.metadata.coverages.all().count(), 1)
        self.assertEqual(self.composite_resource.metadata.coverages.filter(
            type='period').count(), 1)

    def _test_create_aggregation_from_folder_sqlite(self, sqlite_folder_path):
        self.res_title = 'Untitled resource'
        self.create_composite_resource()

        # create a folder to place the sqlite file in that folder before creating an
        # aggregation from the sqlite file
        ResourceFile.create_folder(self.composite_resource, sqlite_folder_path)
        self.add_file_to_resource(file_to_add=self.sqlite_file, upload_folder=sqlite_folder_path)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file at this point
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no TimeSeriesLogicalFile object
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 0)

        # set the sqlite file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user,
                                            folder_path=sqlite_folder_path)
        # test extracted metadata
        assert_time_series_file_type_metadata(self, expected_file_folder=sqlite_folder_path)

        self.composite_resource.delete()

    def _test_create_aggregation_from_folder_CSV(self, csv_folder_path):
        self.create_composite_resource()

        ResourceFile.create_folder(self.composite_resource, csv_folder_path)
        self.add_file_to_resource(file_to_add=self.odm2_csv_file, upload_folder=csv_folder_path)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no TimeSeriesLogicalFile object
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 0)

        # set the CSV file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user,
                                            folder_path=csv_folder_path)
        self._test_CSV_aggregation(expected_aggr_folder=csv_folder_path)

        self.composite_resource.delete()

    def _test_file_metadata_on_file_delete(self, ext):

        if ext == '.sqlite':
            self.create_composite_resource(file_to_upload=self.sqlite_file)
        else:
            # use csv file
            self.create_composite_resource(file_to_upload=self.odm2_csv_file)

        res_file = self.composite_resource.files.first()
        # set the sqlite file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

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

    def _test_invalid_file(self):
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # trying to set this invalid sqlite file to timeseries file type should raise
        # ValidationError
        with self.assertRaises(ValidationError):
            TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test that the invalid file did not get deleted
        self.assertEqual(self.composite_resource.files.all().count(), 1)

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

    def _test_invalid_csv_file(self, invalid_csv_file_name):
        invalid_csv_file = self._get_invalid_csv_file(invalid_csv_file_name)

        self.res_title = 'Untitled Resource'
        self.create_composite_resource(file_to_upload=invalid_csv_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no TimeSeriesLogicalFile object
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 0)

        # trying to set this invalid csv file to timeseries file type should raise
        # ValidationError
        with self.assertRaises(ValidationError):
            TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test that the invalid file did not get deleted
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # check that the resource file is still not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)
        self.composite_resource.delete()

    def _get_invalid_csv_file(self, invalid_csv_file_name):
        invalid_csv_file = 'hs_app_timeseries/tests/{}'.format(invalid_csv_file_name)
        return invalid_csv_file

    def test_main_file(self):
        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.sqlite_file)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        self.assertEqual(1, TimeSeriesLogicalFile.objects.count())
        self.assertEqual(".sqlite", TimeSeriesLogicalFile.objects.first().get_main_file_type())
        self.assertEqual(self.sqlite_file_name,
                         TimeSeriesLogicalFile.objects.first().get_main_file.file_name)
