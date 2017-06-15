import os
import tempfile
import shutil

from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.hydroshare.utils import resource_post_create_actions
from utils import assert_ref_time_series_file_type_metadata

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
        self.refts_file_name = 'multi_sites_formatted_version1.0.json.refts'
        self.refts_file = 'hs_file_types/tests/{}'.format(self.refts_file_name)

        target_temp_refts_file = os.path.join(self.temp_dir, self.refts_file_name)
        shutil.copy(self.refts_file, target_temp_refts_file)
        self.refts_file_obj = open(target_temp_refts_file, 'r')

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
        # test extracted ref time series file type metadata
        assert_ref_time_series_file_type_metadata(self)

        # test that the content of the json file is same is what we have
        # saved in json_file_content field of the file metadata object
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.metadata.json_file_content, res_file.resource_file.read())

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
