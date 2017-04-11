import os
import tempfile
import shutil
from dateutil import parser

from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.hydroshare.utils import resource_post_create_actions

from hs_file_types.models import RefTimeseriesLogicalFile, GenericLogicalFile


class RefTimeseriesFileTypeMetaDataTest(MockIRODSTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(RefTimeseriesFileTypeMetaDataTest, self).setUp()
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
            title='Test Ref Time Series File Type Metadata'
        )

        self.temp_dir = tempfile.mkdtemp()
        self.refts_file_name = 'multi_sites_formatted.json.refts'
        self.refts_file = 'hs_file_types/tests/{}'.format(self.refts_file_name)

        target_temp_refts_file = os.path.join(self.temp_dir, self.refts_file_name)
        shutil.copy(self.refts_file, target_temp_refts_file)
        self.refts_file_obj = open(target_temp_refts_file, 'r')

        self.refts_duplicate_series_file_name = 'refts_duplicate_series.json.refts'
        self.refts_duplicate_series_file = 'hs_file_types/tests/{}'.format(
            self.refts_duplicate_series_file_name)

        tgt_temp_refts_duplicate_series_file = os.path.join(self.temp_dir,
                                                            self.refts_duplicate_series_file_name)
        shutil.copy(self.refts_duplicate_series_file, tgt_temp_refts_duplicate_series_file)

        self.refts_invalid_url_file_name = 'refts_invalid_urls.json.refts'
        self.refts_invalid_url_file = 'hs_file_types/tests/{}'.format(
            self.refts_invalid_url_file_name)

        tgt_temp_refts_invalid_urls_file = os.path.join(self.temp_dir,
                                                        self.refts_invalid_url_file_name)
        shutil.copy(self.refts_invalid_url_file, tgt_temp_refts_invalid_urls_file)

        self.refts_invalid_dates_1_file_name = 'refts_invalid_dates_1.json.refts'
        self.refts_invalid_dates_1_file = 'hs_file_types/tests/{}'.format(
            self.refts_invalid_dates_1_file_name)

        tgt_temp_refts_invalid_dates_1_file = os.path.join(self.temp_dir,
                                                           self.refts_invalid_dates_1_file_name)
        shutil.copy(self.refts_invalid_dates_1_file, tgt_temp_refts_invalid_dates_1_file)

        self.refts_invalid_dates_2_file_name = 'refts_invalid_dates_2.json.refts'
        self.refts_invalid_dates_2_file = 'hs_file_types/tests/{}'.format(
            self.refts_invalid_dates_2_file_name)

        tgt_temp_refts_invalid_dates_2_file = os.path.join(self.temp_dir,
                                                           self.refts_invalid_dates_2_file_name)
        shutil.copy(self.refts_invalid_dates_2_file, tgt_temp_refts_invalid_dates_2_file)

        self.refts_missing_key_file_name = 'refts_missing_key.json.refts'
        self.refts_missing_key_file = 'hs_file_types/tests/{}'.format(
            self.refts_missing_key_file_name)

        tgt_temp_refts_missing_key_file = os.path.join(self.temp_dir,
                                                       self.refts_missing_key_file_name)
        shutil.copy(self.refts_missing_key_file, tgt_temp_refts_missing_key_file)

    def tearDown(self):
        super(RefTimeseriesFileTypeMetaDataTest, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_set_file_type_to_refts(self):
        # here we are using a valid time series json file for setting it
        # to RefTimeSeries file type which includes metadata extraction
        self.refts_file_obj = open(self.refts_file, 'r')
        self._create_composite_resource(title="Untitled resource")

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
        # check that there is one GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

        # check that there is no RefTimeseriesLogicalFile object
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 0)

        # set the json file to RefTimeseries file type
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        # check that there is one RefTimeseriesLogicalFile object
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 1)

        # test extracted metadata that updates resource level metadata

        # resource title should have been updated from the title value in json file
        res_title = "Sites, Variable"
        self.assertEqual(self.composite_resource.metadata.title.value, res_title)
        # resource abstract should have been updated from the abstract value in json file
        abstract = "Discharge, cubic feet per second,Blue-green algae (cyanobacteria), " \
                   "phycocyanin data collected from 2016-04-06 to 2017-02-09 created on " \
                   "Thu Apr 06 2017 09:15:56 GMT-0600 (Mountain Daylight Time) from the " \
                   "following site(s): HOBBLE CREEK AT 1650 WEST AT SPRINGVILLE, UTAH, and " \
                   "Provo River at Charleston Advanced Aquatic. Data created by " \
                   "CUAHSI HydroClient: http://data.cuahsi.org/#."

        self.assertEqual(self.composite_resource.metadata.description.abstract, abstract)

        # test keywords - resource level keywords should have been updated with data from the json
        # file
        keywords = [kw.value for kw in self.composite_resource.metadata.subjects.all()]
        for kw in keywords:
            self.assertIn(kw, ["Time Series", "CUAHSI"])

        # test coverage metadata
        box_coverage = self.composite_resource.metadata.coverages.all().filter(type='box').first()
        self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(box_coverage.value['northlimit'], 40.48498)
        self.assertEqual(box_coverage.value['eastlimit'], -111.46245)
        self.assertEqual(box_coverage.value['southlimit'], 40.1788719)
        self.assertEqual(box_coverage.value['westlimit'], -111.639338)

        temporal_coverage = self.composite_resource.metadata.coverages.all().filter(
            type='period').first()
        self.assertEqual(parser.parse(temporal_coverage.value['start']).date(),
                         parser.parse('04/06/2016').date())
        self.assertEqual(parser.parse(temporal_coverage.value['end']).date(),
                         parser.parse('02/09/2017').date())

        # test file level metadata
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.dataset_name, res_title)
        for kw in logical_file.metadata.keywords:
            self.assertIn(kw, ["Time Series", "CUAHSI"])
        box_coverage = logical_file.metadata.coverages.all().filter(type='box').first()
        self.assertEqual(box_coverage.value['projection'], 'Unknown')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(box_coverage.value['northlimit'], 40.48498)
        self.assertEqual(box_coverage.value['eastlimit'], -111.46245)
        self.assertEqual(box_coverage.value['southlimit'], 40.1788719)
        self.assertEqual(box_coverage.value['westlimit'], -111.639338)
        temporal_coverage = logical_file.metadata.coverages.all().filter(
            type='period').first()
        self.assertEqual(parser.parse(temporal_coverage.value['start']).date(),
                         parser.parse('04/06/2016').date())
        self.assertEqual(parser.parse(temporal_coverage.value['end']).date(),
                         parser.parse('02/09/2017').date())

        # file level abstract
        self.assertEqual(logical_file.metadata.abstract, abstract)
        # there should be 2 time series
        self.assertEqual(len(logical_file.metadata.time_serieses), 2)

        # test site related metadata

        self.assertEqual(len(logical_file.metadata.sites), 2)
        site_names = [site.name for site in logical_file.metadata.sites]
        self.assertIn("HOBBLE CREEK AT 1650 WEST AT SPRINGVILLE, UTAH", site_names)
        self.assertIn("Provo River at Charleston Advanced Aquatic", site_names)
        site_codes = [site.code for site in logical_file.metadata.sites]
        self.assertIn("NWISDV:10153100", site_codes)
        self.assertIn("Provo River GAMUT:PR_CH_AA", site_codes)
        site_lats = [site.latitude for site in logical_file.metadata.sites]
        self.assertIn(40.178871899999997, site_lats)
        self.assertIn(40.48498, site_lats)
        site_lons = [site.longitude for site in logical_file.metadata.sites]
        self.assertIn(-111.639338, site_lons)
        self.assertIn(-111.46245, site_lons)

        # there should be 2 variables
        self.assertEqual(len(logical_file.metadata.variables), 2)
        var_names = [var.name for var in logical_file.metadata.variables]
        self.assertIn("Discharge, cubic feet per second", var_names)
        self.assertIn("Blue-green algae (cyanobacteria), phycocyanin", var_names)
        var_codes = [var.code for var in logical_file.metadata.variables]
        self.assertIn("NWISDV:00060/DataType=MEAN", var_codes)
        self.assertIn("iutah:BGA", var_codes)
        # there should be 2 web services
        self.assertEqual(len(logical_file.metadata.web_services), 2)
        web_urls = [web.url for web in logical_file.metadata.web_services]
        self.assertIn("http://hydroportal.cuahsi.org/nwisdv/cuahsi_1_1.asmx?WSDL", web_urls)
        self.assertIn("http://data.iutahepscor.org/ProvoRiverWOF/cuahsi_1_1.asmx?WSDL", web_urls)
        web_service_types = [web.service_type for web in logical_file.metadata.web_services]
        self.assertIn("SOAP", web_service_types)
        self.assertEqual(len(set(web_service_types)), 1)
        web_reference_types = [web.reference_type for web in logical_file.metadata.web_services]
        self.assertIn("WOF", web_reference_types)
        web_return_types = [web.return_type for web in logical_file.metadata.web_services]
        self.assertIn("WaterML 1.1", web_return_types)

        self.composite_resource.delete()

    def test_set_file_type_to_refts_res_metadata(self):
        # here we are using a valid time series json file for setting it
        # to RefTimeSeries file type which includes metadata extraction.
        # resource level metadata (excluding coverage) should not be updated
        # as part setting the json file to RefTimeseries file type
        self.refts_file_obj = open(self.refts_file, 'r')
        res_title = "Test Composite Resource"
        self._create_composite_resource(title=res_title)
        # set resource abstract
        self.composite_resource.metadata.create_element('description', abstract="Some abstract")

        # add resource level keywords
        self.composite_resource.metadata.create_element('subject', value="key-word-1")
        self.composite_resource.metadata.create_element('subject', value="CUAHSI")

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
        # check that there is one GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

        # check that there is no RefTimeseriesLogicalFile object
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 0)

        # set the json file to RefTimeseries file type
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        # check that there is one RefTimeseriesLogicalFile object
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 1)

        # test that the resource title has not changed
        self.assertEqual(self.composite_resource.metadata.title.value, res_title)
        # test that the abstract has not changed
        self.assertEqual(self.composite_resource.metadata.description.abstract, "Some abstract")
        # resource keywords should have been updated (with one keyword added from the json file)
        keywords = [kw.value for kw in self.composite_resource.metadata.subjects.all()]
        for kw in keywords:
            self.assertIn(kw, ["key-word-1", "CUAHSI", "Time Series"])

        self.composite_resource.delete()

    def test_set_file_type_to_file_with_duplicate_series(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        self.refts_file_obj = open(self.refts_duplicate_series_file, 'r')
        self._create_composite_resource()
        self._test_invalid_file()
        self.composite_resource.delete()

    def test_set_file_type_to_file_with_invalid_urls(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        self.refts_file_obj = open(self.refts_invalid_url_file, 'r')
        self._create_composite_resource()
        self._test_invalid_file()
        self.composite_resource.delete()

    def test_set_file_type_to_file_with_invalid_date_value(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        # beginDate has an invalid date value
        self.refts_file_obj = open(self.refts_invalid_dates_1_file, 'r')
        self._create_composite_resource()
        self._test_invalid_file()
        self.composite_resource.delete()

    def test_set_file_type_to_file_with_invalid_date_order(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        # beginDate > endDate
        self.refts_file_obj = open(self.refts_invalid_dates_2_file, 'r')
        self._create_composite_resource()
        self._test_invalid_file()
        self.composite_resource.delete()

    def test_set_file_type_to_file_with_missing_key(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        # key 'site' is missing
        # Note we don't need to test for missing of any other required keys as we
        # don't want to unit test the jsonschema module
        self.refts_file_obj = open(self.refts_missing_key_file, 'r')
        self._create_composite_resource()
        self._test_invalid_file()
        self.composite_resource.delete()

    def _test_invalid_file(self):
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is associated with the generic logical file
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")

        # trying to set this invalid tif file to RefTimeseries file type should raise
        # ValidationError
        with self.assertRaises(ValidationError):
            RefTimeseriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)

        # test that the invalid file did not get deleted
        self.assertEqual(self.composite_resource.files.all().count(), 1)

        # check that the resource file is not associated with generic logical file
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")

    def _create_composite_resource(self, title='Test Ref Time Series File Type Metadata'):
        uploaded_file = UploadedFile(file=self.refts_file_obj,
                                     name=os.path.basename(self.refts_file_obj.name))
        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title=title,
            files=(uploaded_file,)
        )

        # set the generic logical file as part of resource post create signal
        resource_post_create_actions(resource=self.composite_resource, user=self.user,
                                     metadata=self.composite_resource.metadata)
