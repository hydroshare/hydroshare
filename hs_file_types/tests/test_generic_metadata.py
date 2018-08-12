# coding=utf-8
import os

from django.test import TransactionTestCase
from django.contrib.auth.models import Group

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.models import Coverage, ResourceFile
from hs_core.views.utils import move_or_rename_file_or_folder, create_folder
from utils import CompositeResourceTestMixin
from hs_file_types.models import GenericLogicalFile, GenericFileMetaData


class GenericFileTypeTest(MockIRODSTestCaseMixin, TransactionTestCase,
                          CompositeResourceTestMixin):
    def setUp(self):
        super(GenericFileTypeTest, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        self.res_title = "Test Generic File Type"
        self.logical_file_type_name = "GenericLogicalFile"

        self.generic_file_name = 'generic_file.txt'
        self.raster_zip_file_name = 'logan_vrt_small.zip'
        self.generic_file = 'hs_file_types/tests/{}'.format(self.generic_file_name)

    def test_create_aggregation_1(self):
        """Test that we can create a generic aggregation from a resource file that
        exists at the root of the folder hierarchy """

        self.create_composite_resource(self.generic_file)
        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # check that the resource file is not part of an aggregation
        self.assertEqual(res_file.has_logical_file, False)
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        # set file to generic logical file type (aggregation)
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()
        # file has no folder
        self.assertEqual(res_file.file_folder, None)
        self.assertEqual(res_file.logical_file_type_name, self.logical_file_type_name)
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

        self.composite_resource.delete()

    def test_create_aggregation_2(self):
        """Test that we can create a generic aggregation from a resource file that
        exists in a folder """

        self.create_composite_resource()
        new_folder = 'generic_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=new_folder)
        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # file has a folder
        self.assertEqual(res_file.file_folder, new_folder)
        # check that the resource file is not part of an aggregation
        self.assertEqual(res_file.has_logical_file, False)
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        # set file to generic logical file type (aggregation)
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()
        # file has the same folder
        self.assertEqual(res_file.file_folder, new_folder)
        self.assertEqual(res_file.logical_file_type_name, self.logical_file_type_name)
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

        self.composite_resource.delete()

    def test_aggregation_metadata(self):
        """Test that we can create the following metadata for a generic aggregation
           coverage (spatial and temporal)
           key/value metadata
           title (dataset_name)
           keywords
        """

        self.create_composite_resource(self.generic_file)

        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # set file to generic logical file type
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()
        base_file_name, _ = os.path.splitext(res_file.file_name)
        logical_file = res_file.logical_file
        # test that the generic logical file datataset_name attribute has the value of the
        # the content file name
        self.assertEqual(logical_file.dataset_name, base_file_name)
        dataset_name = "This is a generic dataset"
        logical_file.dataset_name = dataset_name
        logical_file.save()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.dataset_name, dataset_name)

        # check that the logical file has metadata object
        self.assertNotEqual(logical_file.metadata, None)

        # there should be no coverage element at this point
        self.assertEqual(logical_file.metadata.coverages.count(), 0)

        # there should not be any extra_metadata (key/value) at this point
        self.assertEqual(logical_file.metadata.extra_metadata, {})
        # create key/vale metadata
        logical_file.metadata.extra_metadata = {'key1': 'value 1', 'key2': 'value 2'}
        logical_file.metadata.save()
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.metadata.extra_metadata,
                         {'key1': 'value 1', 'key2': 'value 2'})

        # update key/value metadata
        logical_file.metadata.extra_metadata = {'key1': 'value 1', 'key2': 'value 2',
                                                'key 3': 'value3'}
        logical_file.metadata.save()
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.metadata.extra_metadata,
                         {'key1': 'value 1', 'key2': 'value 2', 'key 3': 'value3'})

        # delete key/value metadata
        logical_file.metadata.extra_metadata = {}
        logical_file.metadata.save()
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.metadata.extra_metadata, {})

        # test keywords
        self.assertEqual(logical_file.metadata.keywords, [])
        logical_file.metadata.keywords = ['kw-1', 'kw-2']
        logical_file.metadata.save()
        self.assertIn('kw-1', logical_file.metadata.keywords)
        self.assertIn('kw-2', logical_file.metadata.keywords)

        # test coverage element CRUD
        res_file = [f for f in self.composite_resource.files.all()
                    if f.logical_file_type_name == self.logical_file_type_name][0]

        gen_logical_file = res_file.logical_file
        value_dict = {'name': 'Name for period coverage', 'start': '1/1/2000', 'end': '12/12/2012'}
        temp_cov = gen_logical_file.metadata.create_element('coverage', type='period',
                                                            value=value_dict)
        self.assertEqual(temp_cov.value['name'], 'Name for period coverage')
        self.assertEqual(temp_cov.value['start'], '1/1/2000')
        self.assertEqual(temp_cov.value['end'], '12/12/2012')
        # update temporal coverage
        value_dict = {'start': '10/1/2010', 'end': '12/1/2016'}
        gen_logical_file.metadata.update_element('coverage', temp_cov.id, type='period',
                                                 value=value_dict)
        temp_cov = gen_logical_file.metadata.temporal_coverage
        self.assertEqual(temp_cov.value['name'], 'Name for period coverage')
        self.assertEqual(temp_cov.value['start'], '10/1/2010')
        self.assertEqual(temp_cov.value['end'], '12/1/2016')

        # add spatial coverage
        value_dict = {'east': '56.45678', 'north': '12.6789', 'units': 'Decimal degree'}
        spatial_cov = gen_logical_file.metadata.create_element('coverage', type='point',
                                                               value=value_dict)
        self.assertEqual(spatial_cov.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(spatial_cov.value['units'], 'Decimal degree')
        self.assertEqual(spatial_cov.value['north'], 12.6789)
        self.assertEqual(spatial_cov.value['east'], 56.45678)
        # update spatial coverage
        value_dict = {'east': '-156.45678', 'north': '45.6789', 'units': 'Decimal degree'}
        gen_logical_file.metadata.update_element('coverage', spatial_cov.id, type='point',
                                                 value=value_dict)
        spatial_cov = logical_file.metadata.spatial_coverage
        self.assertEqual(spatial_cov.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(spatial_cov.value['units'], 'Decimal degree')
        self.assertEqual(spatial_cov.value['north'], 45.6789)
        self.assertEqual(spatial_cov.value['east'], -156.45678)
        self.composite_resource.delete()
        # there should be no GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        # there should be no GenericFileMetaData object at this point
        self.assertEqual(GenericFileMetaData.objects.count(), 0)

    def test_aggregation_name(self):
        # test the aggregation_name property for the generic aggregation (logical file)

        self.create_composite_resource(self.generic_file)

        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        base_file_name, ext = os.path.splitext(res_file.file_name)
        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, False)
        # set file to generic logical file type
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.logical_file_type_name, self.logical_file_type_name)

        logical_file = res_file.logical_file
        self.assertEqual(logical_file.aggregation_name, res_file.file_name)

        # test the aggregation name after moving the file into a folder
        new_folder = 'generic_folder'
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

        self.create_composite_resource(self.generic_file)

        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        base_file_name, ext = os.path.splitext(res_file.file_name)
        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, False)
        # set file to generic logical file type
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
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

    def test_remove_aggregation(self):
        # test that when an instance GenericLogicalFile Type (aggregation) is deleted
        # all resource files associated with that aggregation is not deleted but the associated
        # metadata is deleted

        self.create_composite_resource(self.generic_file)
        res_file = self.composite_resource.files.first()

        # create generic aggregation
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test that we have one logical file of type GenericLogicalFile Type as a result
        # of setting file type (aggregation)
        self.assertEqual(GenericLogicalFile.objects.count(), 1)
        self.assertEqual(GenericFileMetaData.objects.count(), 1)
        logical_file = GenericLogicalFile.objects.first()
        self.assertEqual(logical_file.files.all().count(), 1)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        self.assertEqual(set(self.composite_resource.files.all()),
                         set(logical_file.files.all()))

        # delete the aggregation (logical file) object using the remove_aggregation function
        logical_file.remove_aggregation()
        # test there is no GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        # test there is no GenericFileMetaData object
        self.assertEqual(GenericFileMetaData.objects.count(), 0)
        # check the files previously associated with the generic aggregation not deleted
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        self.composite_resource.delete()

    def test_file_rename(self):
        # test that a resource file that is part of a GenericLogicalFile object
        # can be renamed

        self.create_composite_resource(self.generic_file)
        res_file = self.composite_resource.files.first()
        base_file_name, ext = os.path.splitext(res_file.file_name)
        self.assertEqual(res_file.file_name, 'generic_file.txt')
        # create generic aggregation
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
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

        self.create_composite_resource(self.generic_file)
        res_file = self.composite_resource.files.first()
        base_file_name, ext = os.path.splitext(res_file.file_name)
        self.assertEqual(res_file.file_name, 'generic_file.txt')
        # create generic aggregation
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
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

    def test_aggregation_metadata_on_file_delete(self):
        # test that when a file that's part of the GenericLogicalFile object
        # is deleted all metadata associated with the file type also get deleted

        self.create_composite_resource(self.generic_file)
        res_file = self.composite_resource.files.first()
        # set the file to generic logical file
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()
        gen_logical_file = res_file.logical_file
        self.assertEqual(GenericLogicalFile.objects.count(), 1)
        self.assertEqual(GenericFileMetaData.objects.count(), 1)
        # at this point there should not be any coverage elements associated with
        # logical file
        self.assertEqual(gen_logical_file.metadata.coverages.count(), 0)
        # at this point there should not be any key/value metadata associated with
        # logical file
        self.assertEqual(gen_logical_file.metadata.extra_metadata, {})
        # add temporal coverage
        value_dict = {'name': 'Name for period coverage', 'start': '1/1/2000', 'end': '12/12/2012'}
        gen_logical_file.metadata.create_element('coverage', type='period', value=value_dict)
        # add spatial coverage
        value_dict = {'east': '56.45678', 'north': '12.6789', 'units': 'Decimal degree'}
        gen_logical_file.metadata.create_element('coverage', type='point', value=value_dict)
        # at this point there should be 2 coverage elements associated with
        # logical file
        self.assertEqual(gen_logical_file.metadata.coverages.count(), 2)
        # at this point we should have 4 coverage elements (2 resource level
        # and 2 file type level
        self.assertEqual(Coverage.objects.count(), 4)
        # add key/value metadata
        gen_logical_file.metadata.extra_metadata = {'key1': 'value 1', 'key2': 'value 2'}
        gen_logical_file.metadata.save()
        hydroshare.delete_resource_file(self.composite_resource.short_id,
                                        res_file.id,
                                        self.user)
        # test that we don't have logical file of type GenericLogicalFile
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        self.assertEqual(GenericFileMetaData.objects.count(), 0)
        # test that resource level coverage element exist - not got deleted
        self.assertEqual(Coverage.objects.count(), 2)

    def test_main_file(self):
        self.create_composite_resource(self.generic_file)

        res_file = self.composite_resource.files.first()
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()

        self.assertEqual(1, GenericLogicalFile.objects.count())
        self.assertEqual(None, GenericLogicalFile.objects.first().get_main_file_type())
        self.assertEqual(None, GenericLogicalFile.objects.first().get_main_file)

    def test_has_modified_metadata_no_change(self):
        self.create_composite_resource(self.generic_file)

        res_file = self.composite_resource.files.first()
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        self.assertEqual(1, GenericLogicalFile.objects.count())
        gen_logical_file = GenericLogicalFile.objects.first()

        # check expected generated metadata state without modifications
        self.assertEqual(0, gen_logical_file.metadata.coverages.count())
        self.assertEqual({}, gen_logical_file.metadata.extra_metadata)
        self.assertEqual("generic_file", gen_logical_file.dataset_name)
        self.assertFalse(gen_logical_file.metadata.has_modified_metadata)

    def test_has_modified_metadata_empty_title(self):
        self.create_composite_resource(self.generic_file)

        res_file = self.composite_resource.files.first()
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        self.assertEqual(1, GenericLogicalFile.objects.count())
        gen_logical_file = GenericLogicalFile.objects.first()

        gen_logical_file.dataset_name = ""
        gen_logical_file.save()

        # check expected generated metadata state without modifications
        self.assertEqual(0, gen_logical_file.metadata.coverages.count())
        self.assertEqual({}, gen_logical_file.metadata.extra_metadata)
        self.assertFalse(gen_logical_file.dataset_name)
        self.assertFalse(gen_logical_file.metadata.has_modified_metadata)

    def test_has_modified_metadata_updated_title(self):
        self.create_composite_resource(self.generic_file)

        res_file = self.composite_resource.files.first()
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        self.assertEqual(1, GenericLogicalFile.objects.count())
        gen_logical_file = GenericLogicalFile.objects.first()

        gen_logical_file.dataset_name = "Updated"
        gen_logical_file.save()

        # check expected generated metadata state updated title only
        self.assertEqual(0, gen_logical_file.metadata.coverages.count())
        self.assertEqual({}, gen_logical_file.metadata.extra_metadata)
        self.assertEqual("Updated", gen_logical_file.dataset_name)
        self.assertTrue(gen_logical_file.metadata.has_modified_metadata)

    def test_has_modified_metadata_updated_coverages(self):
        self.create_composite_resource(self.generic_file)

        res_file = self.composite_resource.files.first()
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        self.assertEqual(1, GenericLogicalFile.objects.count())
        gen_logical_file = GenericLogicalFile.objects.first()

        value_dict = {'east': '56.45678', 'north': '12.6789', 'units': 'Decimal degree'}
        gen_logical_file.metadata.create_element('coverage', type='point', value=value_dict)

        # check expected generated metadata state updated coverages only
        self.assertEqual(1, gen_logical_file.metadata.coverages.count())
        self.assertEqual({}, gen_logical_file.metadata.extra_metadata)
        self.assertEqual("generic_file", gen_logical_file.dataset_name)
        self.assertTrue(gen_logical_file.metadata.has_modified_metadata)

    def test_has_modified_metadata_updated_extra_metadata(self):
        self.create_composite_resource(self.generic_file)

        res_file = self.composite_resource.files.first()
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        self.assertEqual(1, GenericLogicalFile.objects.count())
        gen_logical_file = GenericLogicalFile.objects.first()

        gen_logical_file.metadata.extra_metadata = {'key1': 'value 1', 'key2': 'value 2'}
        gen_logical_file.metadata.save()

        # check expected generated metadata state updated extra_metadata only
        self.assertEqual(0, gen_logical_file.metadata.coverages.count())
        self.assertEqual({'key1': 'value 1', 'key2': 'value 2'},
                         gen_logical_file.metadata.extra_metadata)
        self.assertEqual("generic_file", gen_logical_file.dataset_name)
        self.assertTrue(gen_logical_file.metadata.has_modified_metadata)
