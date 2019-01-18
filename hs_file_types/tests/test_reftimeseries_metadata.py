import os

from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.models import ResourceFile
from hs_core.views.utils import move_or_rename_file_or_folder, create_folder
from utils import assert_ref_time_series_file_type_metadata, CompositeResourceTestMixin

from hs_file_types.models import RefTimeseriesLogicalFile, RefTimeseriesFileMetaData


class RefTimeseriesFileTypeTest(MockIRODSTestCaseMixin, TransactionTestCase,
                                CompositeResourceTestMixin):
    def setUp(self):
        super(RefTimeseriesFileTypeTest, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        self.logical_file_type_name = "RefTimeseriesLogicalFile"
        self.res_title = "Test Ref Timeseries File Type"
        self.refts_file_name = 'multi_sites_formatted_version1.0.refts.json'
        self.refts_file = 'hs_file_types/tests/{}'.format(self.refts_file_name)

    def test_create_aggregation_1(self):
        # here we are using a valid time series json file for setting it
        # to RefTimeSeries file type which includes metadata extraction
        # this resource file is at the root of folder hierarchy

        self.res_title = "Untitled resource"
        self.create_composite_resource(self.refts_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # test resource file is not in a folder
        self.assertEqual(res_file.file_folder, None)
        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no RefTimeseriesLogicalFile object
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 0)

        # set the json file to RefTimeseries file type
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # check that there is one RefTimeseriesLogicalFile object
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 1)
        res_file = self.composite_resource.files.first()
        # test resource file is not in a folder
        self.assertEqual(res_file.file_folder, None)
        self.assertEqual(res_file.logical_file_type_name, self.logical_file_type_name)
        # test extracted ref time series file type metadata
        assert_ref_time_series_file_type_metadata(self)

        # test that the content of the json file is same is what we have
        # saved in json_file_content field of the file metadata object
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.metadata.json_file_content, res_file.resource_file.read())

        # test resource file is not in a folder
        self.assertEqual(res_file.file_folder, None)

        self.composite_resource.delete()

    def test_create_aggregation_2(self):
        # here we are using a valid time series json file for setting it
        # to RefTimeSeries file type which includes metadata extraction
        # this resource file is in a folder

        self.res_title = "Untitled resource"
        self.create_composite_resource()
        new_folder = 'refts_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the json file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.refts_file, upload_folder=new_folder)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # test resource file is in a folder
        self.assertEqual(res_file.file_folder, new_folder)
        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no RefTimeseriesLogicalFile object
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 0)

        # set the json file to RefTimeseries file type
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()
        # check that there is one RefTimeseriesLogicalFile object
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 1)
        # test resource file is in the same folder
        self.assertEqual(res_file.file_folder, new_folder)
        self.assertEqual(res_file.logical_file_type_name, self.logical_file_type_name)
        # test extracted ref time series file type metadata
        assert_ref_time_series_file_type_metadata(self)

        # test that the content of the json file is same is what we have
        # saved in json_file_content field of the file metadata object
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.metadata.json_file_content, res_file.resource_file.read())

        # test resource file is in a folder
        self.assertEqual(res_file.file_folder, new_folder)

        self.composite_resource.delete()

    def test_res_metadata_on_create_aggregation(self):
        # here we are using a valid time series json file for setting it
        # to RefTimeSeries file type which includes metadata extraction.
        # resource level metadata (excluding coverage) should not be updated
        # as part setting the json file to RefTimeseries file type

        self.res_title = "Test Composite Resource"
        self.create_composite_resource(self.refts_file)
        # set resource abstract
        self.composite_resource.metadata.create_element('description', abstract="Some abstract")

        # add resource level keywords
        self.composite_resource.metadata.create_element('subject', value="key-word-1")
        self.composite_resource.metadata.create_element('subject', value="CUAHSI")

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # check that there is no RefTimeseriesLogicalFile object
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 0)

        # set the json file to RefTimeseries file type
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # check that there is one RefTimeseriesLogicalFile object
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 1)

        # test that the resource title has not changed
        self.assertEqual(self.composite_resource.metadata.title.value, self.res_title)
        # test that the abstract has not changed
        self.assertEqual(self.composite_resource.metadata.description.abstract, "Some abstract")
        # resource keywords should have been updated (with one keyword added from the json file)
        keywords = [kw.value for kw in self.composite_resource.metadata.subjects.all()]
        for kw in keywords:
            self.assertIn(kw, ["key-word-1", "CUAHSI", "Time Series"])

        self.composite_resource.delete()

    def test_aggregation_name(self):
        # test the aggregation_name property for the refts aggregation (logical file)

        self.create_composite_resource(self.refts_file)

        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        base_file_name, ext = os.path.splitext(res_file.file_name)
        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, False)
        # set file to refts logical file type
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.logical_file_type_name, self.logical_file_type_name)

        logical_file = res_file.logical_file
        self.assertEqual(logical_file.aggregation_name, res_file.file_name)

        # test the aggregation name after moving the file into a folder
        new_folder = 'refts_folder'
        create_folder(self.composite_resource.short_id, 'data/contents/{}'.format(new_folder))
        src_path = 'data/contents/{}'.format(res_file.file_name)
        tgt_path = 'data/contents/{0}/{1}'.format(new_folder, res_file.file_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)

        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        expected_aggregation_name = '{0}/{1}'.format(new_folder, res_file.file_name)
        self.assertEqual(logical_file.aggregation_name, expected_aggregation_name)

        # test the aggregation name after renaming the file
        src_path = 'data/contents/{0}/{1}'.format(new_folder, res_file.file_name)
        tgt_path = 'data/contents/{0}/{1}_1{2}'.format(new_folder, base_file_name, ext)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        expected_aggregation_name = '{0}/{1}_1{2}'.format(new_folder, base_file_name, ext)
        self.assertEqual(logical_file.aggregation_name, expected_aggregation_name)

        # test the aggregation name after renaming the folder
        folder_rename = '{}_1'.format(new_folder)
        src_path = 'data/contents/{}'.format(new_folder)
        tgt_path = 'data/contents/{}'.format(folder_rename)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)
        logical_file = res_file.logical_file
        expected_aggregation_name = '{0}/{1}'.format(folder_rename, res_file.file_name)
        self.assertEqual(logical_file.aggregation_name, expected_aggregation_name)
        self.composite_resource.delete()

    def test_aggregation_xml_file_paths(self):
        # test the aggregation meta and map xml file paths with file name and folder name
        # changes

        self.create_composite_resource(self.refts_file)

        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        base_file_name, ext = os.path.splitext(res_file.file_name)
        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, False)
        # set file to generic logical file type
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.logical_file_type_name, self.logical_file_type_name)

        logical_file = res_file.logical_file
        expected_meta_path = '{}_meta.xml'.format(res_file.file_name)
        expected_map_path = '{}_resmap.xml'.format(res_file.file_name)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_path)
        self.assertEqual(logical_file.map_short_file_path, expected_map_path)

        # test xml file paths after moving the file into a folder
        new_folder = 'test_folder'
        create_folder(self.composite_resource.short_id, 'data/contents/{}'.format(new_folder))
        src_path = 'data/contents/{}'.format(res_file.file_name)
        tgt_path = 'data/contents/{0}/{1}'.format(new_folder, res_file.file_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)

        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        expected_meta_path = '{0}/{1}_meta.xml'.format(new_folder, res_file.file_name)
        expected_map_path = '{0}/{1}_resmap.xml'.format(new_folder, res_file.file_name)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_path)
        self.assertEqual(logical_file.map_short_file_path, expected_map_path)

        # test xml file paths after renaming the file
        src_path = 'data/contents/{0}/{1}'.format(new_folder, res_file.file_name)
        tgt_path = 'data/contents/{0}/{1}_1{2}'.format(new_folder, base_file_name, ext)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        expected_meta_path = '{0}/{1}_meta.xml'.format(new_folder, res_file.file_name)
        expected_map_path = '{0}/{1}_resmap.xml'.format(new_folder, res_file.file_name)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_path)
        self.assertEqual(logical_file.map_short_file_path, expected_map_path)

        # test the xml file path after renaming the folder
        folder_rename = '{}_1'.format(new_folder)
        src_path = 'data/contents/{}'.format(new_folder)
        tgt_path = 'data/contents/{}'.format(folder_rename)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        expected_meta_path = '{0}/{1}_meta.xml'.format(folder_rename, res_file.file_name)
        expected_map_path = '{0}/{1}_resmap.xml'.format(folder_rename, res_file.file_name)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_path)
        self.assertEqual(logical_file.map_short_file_path, expected_map_path)
        self.composite_resource.delete()

    def test_file_rename(self):
        # test that a resource file that is part of a RefTimeseriesLogicalFile object
        # can be renamed

        self.create_composite_resource(self.refts_file)
        res_file = self.composite_resource.files.first()
        base_file_name, ext = os.path.splitext(res_file.file_name)
        self.assertEqual(res_file.file_name, self.refts_file_name)
        # create refts aggregation
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # file should not be in a folder
        self.assertEqual(res_file.file_folder, None)
        # test rename of file is allowed
        src_path = 'data/contents/{}'.format(res_file.file_name)
        tgt_path = "data/contents/{0}_1{1}".format(base_file_name, ext)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.file_name, '{0}_1{1}'.format(base_file_name, ext))

        self.composite_resource.delete()

    def test_file_move(self):
        # test that a resource file that is part of a GenericLogicalFile object
        # can be moved

        self.create_composite_resource(self.refts_file)
        res_file = self.composite_resource.files.first()
        base_file_name, ext = os.path.splitext(res_file.file_name)
        self.assertEqual(res_file.file_name, self.refts_file_name)
        # create generic aggregation
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # file should not be in a folder
        self.assertEqual(res_file.file_folder, None)

        # test moving the file to a new folder is allowed
        new_folder = 'test_folder'
        create_folder(self.composite_resource.short_id, 'data/contents/{}'.format(new_folder))
        src_path = 'data/contents/{}'.format(res_file.file_name)
        tgt_path = "data/contents/{0}/{1}".format(new_folder, res_file.file_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)
        res_file = self.composite_resource.files.first()
        # file should in a folder
        self.assertEqual(res_file.file_folder, new_folder)
        self.assertTrue(res_file.resource_file.name.endswith(tgt_path))
        self.composite_resource.delete()

    def test_create_aggregation_with_invalid_urls(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail as the 'url' specified in this files
        # doesn't exist

        self._test_invalid_json_file('refts_invalid_urls.refts.json')

    def test_create_aggregation_with_invalid_method_link(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail as it as has an invalid method link - the
        # url specified doesn't exist

        self._test_invalid_json_file('refts_invalid_method_link.refts.json')

    def test_create_aggregation_with_unknown_method_link(self):
        # here we are using a valid time series json file with methodLink set to 'unknown'
        # for setting it to RefTimeseries file type which should pass json validation
        # and a RefTimeseries aggregation should be created

        self._test_valid_json_file('refts_method_link_unknown_lc.refts.json')

    def test_create_aggregation_with_UNKNOWN_method_link(self):
        # here we are using a valid time series json file with methodLink set to 'UNKNOWN'
        # for setting it to RefTimeseries file type which should pass json validation
        # and a RefTimeseries aggregation should be created

        self._test_valid_json_file('refts_method_link_unknown_uc.refts.json')

    def test_create_aggregation_with_invalid_date_value(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        # beginDate has an invalid date value

        self._test_invalid_json_file('refts_invalid_dates_1.refts.json')

    def test_create_aggregation_with_invalid_date_order(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        # beginDate > endDate

        self._test_invalid_json_file('refts_invalid_dates_2.refts.json')

    def test_create_aggregation_with_missing_key(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        # key 'site' is missing

        self._test_invalid_json_file('refts_missing_key.refts.json')

    def test_create_aggregation_fail_with_empty_title(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        # as this file has title attribute with a value of empty string

        self._test_invalid_json_file('refts_invalid_title_empty_string.refts.json')

    def test_create_aggregation_fail_with_empty_abstract(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        # as this file has abstract attribute with a value of empty string

        self._test_invalid_json_file('refts_invalid_abstract_empty_string.refts.json')

    def test_create_aggregation_fail_with_negative_valuecount(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        # as this file has valueCount attribute with a -ve value

        self._test_invalid_json_file('refts_invalid_abstract_empty_string.refts.json')

    def test_create_aggregation_with_null_title(self):
        # here we are using a valid time series json file with 'title' set to null
        # for setting it to RefTimeseries file type which should pass json validation
        # and a RefTimeseries aggregation should be created

        self._test_valid_json_file('refts_valid_title_null.refts.json')

    def test_create_aggregation_with_null_abstract(self):
        # here we are using a valid time series json file with 'abstract' set to null
        # for setting it to RefTimeseries file type which should pass json validation
        # and a RefTimeseries aggregation should be created

        self._test_valid_json_file('refts_valid_abstract_null.refts.json')

    def test_create_aggregation_with_null_keywords(self):
        # here we are using a valid time series json file with 'abstract' set to null
        # for setting it to RefTimeseries file type which should pass json validation
        # and a RefTimeseries aggregation should be created

        self._test_valid_json_file('refts_valid_keywords_missing.refts.json')

    def test_create_aggregation_with_null_fileversion(self):
        # here we are using a valid time series json file with 'fileVersion' set to null
        # for setting it to RefTimeseries file type which should pass json validation
        # and a RefTimeseries aggregation should be created

        self._test_valid_json_file('refts_valid_fileversion_null.refts.json')

    def test_create_aggregation_with_null_symbol(self):
        # here we are using a valid time series json file with 'symbol' set to null
        # for setting it to RefTimeseries file type which should pass json validation
        # and a RefTimeseries aggregation should be created

        self._test_valid_json_file('refts_valid_symbol_null.refts.json')

    def test_create_aggregation_with_null_variablename(self):
        # here we are using a valid time series json file with 'variableName' set to null
        # for setting it to RefTimeseries file type which should pass json validation
        # and a RefTimeseries aggregation should be created

        self._test_valid_json_file('refts_valid_variable_name_null.refts.json')

    def test_create_aggregation_with_null_methodlink(self):
        # here we are using a valid time series json file with 'methodLink' set to null
        # for setting it to RefTimeseries file type which should pass json validation
        # and a RefTimeseries aggregation should be created

        self._test_valid_json_file('refts_valid_method_link_null.refts.json')

    def test_create_aggregation_with_null_methoddescription(self):
        # here we are using a valid time series json file with 'methodDescription' set to null
        # for setting it to RefTimeseries file type which should pass json validation
        # and a RefTimeseries aggregation should be created

        self._test_valid_json_file('refts_valid_method_description_null.refts.json')

    def test_create_aggregation_with_null_sitename(self):
        # here we are using a valid time series json file with 'siteName' set to null
        # for setting it to RefTimeseries file type which should pass json validation
        # and a RefTimeseries aggregation should be created

        self._test_valid_json_file('refts_valid_site_name_null.refts.json')

    def test_create_aggregation_with_null_samplemedium(self):
        # here we are using a valid time series json file with 'sampleMedium' set to null
        # for setting it to RefTimeseries file type which should pass json validation
        # and a RefTimeseries aggregation should be created

        self._test_valid_json_file('refts_valid_sample_medium_null.refts.json')

    def test_create_aggregation_with_null_valuecount(self):
        # here we are using a valid time series json file with 'valueCount' set to null
        # for setting it to RefTimeseries file type which should pass json validation
        # and a RefTimeseries aggregation should be created

        self._test_valid_json_file('refts_valid_value_count_null.refts.json')

    def test_create_aggregation_fail_with_duplicate_keywords(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        # as this file has duplicate keywords
        # Note we don't need to test for missing of any other required keys as we
        # don't want to unit test the jsonschema module

        self._test_invalid_json_file('invalid_duplicate_keywords.refts.json')

    def test_create_aggregation_fail_with_invalid_service_type(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        # as this file has invalid service type
        # Note we don't need to test for missing of any other required keys as we
        # don't want to unit test the jsonschema module

        self._test_invalid_json_file('invalid_service_type.refts.json')

    def test_create_aggregation_fail_with_invalid_return_type(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        # as this file has invalid return type
        # Note we don't need to test for missing of any other required keys as we
        # don't want to unit test the jsonschema module

        self._test_invalid_json_file('invalid_return_type.refts.json')

    def test_create_aggregation_fail_with_invalid_ref_type(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        # as this file has invalid ref type
        # Note we don't need to test for missing of any other required keys as we
        # don't want to unit test the jsonschema module

        self._test_invalid_json_file('invalid_ref_type.refts.json')

    def test_create_aggregation_fail_with_empty_method_link(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        # as this file has a value of empty string for methodLink

        self._test_invalid_json_file('refts_invalid_method_link_empty_string.refts.json')

    def test_create_aggregation_fail_with_empty_method_description(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        # as this file has a value of empty string for methodDescription

        self._test_invalid_json_file('refts_invalid_method_description_empty_string.refts.json')

    def test_create_aggregation_fail_with_empty_sample_medium(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        # as this file has a value of empty string for sampleMedium

        self._test_invalid_json_file('refts_invalid_sample_medium_empty_string.refts.json')

    def test_create_aggregation_fail_with_empty_file_version(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        # as this file has a value of empty string for fileVesrion

        self._test_invalid_json_file('refts_invalid_fileversion_empty_string.refts.json')

    def test_create_aggregation_fail_with_empty_symbol(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        # as this file has a value of empty string for symbol

        self._test_invalid_json_file('refts_invalid_symbol_empty_string.refts.json')

    def test_create_aggregation_fail_with_empty_variable_name(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        # as this file has a value of empty string for variableName

        self._test_invalid_json_file('refts_invalid_variable_name_empty_string.refts.json')

    def test_create_aggregation_fail_with_empty_site_name(self):
        # here we are using an invalid time series json file for setting it
        # to RefTimeseries file type which should fail
        # as this file has a value of empty string for siteName

        self._test_invalid_json_file('refts_invalid_site_name_empty_string.refts.json')

    def test_remove_aggregation(self):
        # test that when an instance RefTimeseriesLogicalFile (aggregation) is deleted
        # all files associated with that aggregation is not deleted but the associated metadata
        # is deleted
        self.create_composite_resource(self.refts_file)
        res_file = self.composite_resource.files.first()

        # set the json file to RefTimeSeriesLogicalFile (aggregation) type
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test that we have one logical file of type RefTimeseriesLogicalFile as a result
        # of setting aggregation
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 1)
        self.assertEqual(RefTimeseriesFileMetaData.objects.count(), 1)
        logical_file = RefTimeseriesLogicalFile.objects.first()
        self.assertEqual(logical_file.files.all().count(), 1)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        self.assertEqual(set(self.composite_resource.files.all()),
                         set(logical_file.files.all()))

        # delete the aggregation (logical file) object using the remove_aggregation function
        logical_file.remove_aggregation()
        # test there is no RefTimeseriesLogicalFile object
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 0)
        # test there is no RefTimeseriesFileMetaData object
        self.assertEqual(RefTimeseriesFileMetaData.objects.count(), 0)
        # check the files associated with the aggregation not deleted
        self.assertEqual(self.composite_resource.files.all().count(), 1)

        self.composite_resource.delete()

    def test_main_file(self):
        self.create_composite_resource(self.refts_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        self.assertEqual(1, RefTimeseriesLogicalFile.objects.count())
        self.assertEqual(".json", RefTimeseriesLogicalFile.objects.first().get_main_file_type())
        self.assertEqual(self.refts_file_name,
                         RefTimeseriesLogicalFile.objects.first().get_main_file.file_name)

    def _test_valid_json_file(self, json_file_name):
        refts_file = 'hs_file_types/tests/{}'.format(json_file_name)

        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 0)
        self.create_composite_resource(refts_file)
        json_res_file = self.composite_resource.files.first()
        # set the json file to RefTimeseries file type
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, self.user, json_res_file.id)
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 1)
        json_res_file = self.composite_resource.files.first()
        self.assertTrue(json_res_file.has_logical_file)
        logical_file = json_res_file.logical_file
        self.assertTrue(isinstance(logical_file, RefTimeseriesLogicalFile))
        self.assertEqual(logical_file.metadata.json_file_content,
                         json_res_file.resource_file.read())
        self.composite_resource.delete()

    def _test_invalid_json_file(self, invalid_json_file_name):
        invalid_json_file = 'hs_file_types/tests/{}'.format(invalid_json_file_name)

        self.create_composite_resource(invalid_json_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # trying to set this invalid tif file to RefTimeseries file type should raise
        # ValidationError
        with self.assertRaises(ValidationError):
            RefTimeseriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test that the invalid file did not get deleted
        self.assertEqual(self.composite_resource.files.all().count(), 1)

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)
        self.composite_resource.delete()
