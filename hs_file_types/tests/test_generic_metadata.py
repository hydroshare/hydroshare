# coding=utf-8
import os
import tempfile
import shutil

from django.core.files.uploadedfile import UploadedFile
from django.test import TransactionTestCase
from django.contrib.auth.models import Group

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.models import Coverage
from hs_core.hydroshare.utils import resource_post_create_actions
from hs_core.views.utils import move_or_rename_file_or_folder

from hs_file_types.models import GenericLogicalFile, GenericFileMetaData


class GenericFileTypeMetaDataTest(MockIRODSTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(GenericFileTypeMetaDataTest, self).setUp()
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
            title='Test Generic File Metadata'
        )

        self.temp_dir = tempfile.mkdtemp()
        self.generic_file_name = 'generic_file.txt'
        self.raster_zip_file_name = 'logan_vrt_small.zip'
        self.generic_file = 'hs_file_types/tests/{}'.format(self.generic_file_name)
        target_temp_generic_file = os.path.join(self.temp_dir, self.generic_file_name)
        shutil.copy(self.generic_file, target_temp_generic_file)
        self.generic_file_obj = open(target_temp_generic_file, 'r')

    def tearDown(self):
        super(GenericFileTypeMetaDataTest, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_generic_logical_file(self):
        # test that when any file is uploaded to Composite Resource
        # the file is assigned to GenericLogicalFile type
        # test that generic logical file type can have the following metadata (all optional:
        #   coverage (spatial and temporal)
        #   key/value metadata
        #   title (dataset_name)
        #   keywords
        self.generic_file_obj = open(self.generic_file, 'r')
        self._create_composite_resource()

        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")

        logical_file = res_file.logical_file
        # test that the generic logical file has no value for the datataset_name
        self.assertEqual(logical_file.dataset_name, None)
        logical_file.dataset_name = "This is a generic dataset"
        logical_file.save()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.dataset_name, "This is a generic dataset")

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
                    if f.logical_file_type_name == "GenericLogicalFile"][0]

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

    def test_file_rename_or_move(self):
        # test that resource file that belongs to GenericLogicalFile object
        # can be moved or renamed

        self.generic_file_obj = open(self.generic_file, 'r')
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()
        self.assertEqual(os.path.basename(res_file.resource_file.name), 'generic_file.txt')
        # test rename of file is allowed
        src_path = 'data/contents/generic_file.txt'
        tgt_path = "data/contents/generic_file_1.txt"
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)
        res_file = self.composite_resource.files.first()
        self.assertEqual(os.path.basename(res_file.resource_file.name), 'generic_file_1.txt')
        # test moving the file to a new folder is allowed
        src_path = 'data/contents/generic_file_1.txt'
        tgt_path = "data/contents/test_folder/generic_file_1.txt"
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)
        res_file = self.composite_resource.files.first()
        self.assertTrue(res_file.resource_file.name.endswith(tgt_path))

    def test_file_type_metadata_on_file_delete(self):
        # test that when a file that's part of the GenericLogicalFile object
        # is deleted all metadata associated with the file type also get deleted
        self.generic_file_obj = open(self.generic_file, 'r')
        self._create_composite_resource()
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
        # test that all metadata deleted
        self.assertEqual(Coverage.objects.count(), 0)

    def _create_composite_resource(self):
        uploaded_file = UploadedFile(file=self.generic_file_obj,
                                     name=os.path.basename(self.generic_file_obj.name))
        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Generic File Type Metadata',
            files=(uploaded_file,)
        )

        # set the logical file
        resource_post_create_actions(resource=self.composite_resource, user=self.user,
                                     metadata=self.composite_resource.metadata)
