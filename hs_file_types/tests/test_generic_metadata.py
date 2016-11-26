# coding=utf-8
import os
import tempfile
import shutil

from django.test import TransactionTestCase
from django.db import IntegrityError
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.models import Coverage
from hs_core.hydroshare.utils import resource_post_create_actions, \
    get_resource_file_name_and_extension
from hs_core.views.utils import remove_folder

from hs_file_types.utils import set_file_to_geo_raster_file_type
from hs_file_types.models import GeoRasterLogicalFile, GeoRasterFileMetaData, GenericLogicalFile

from hs_geo_raster_resource.models import OriginalCoverage, CellInformation, BandInformation


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

        # test coverage element CRUD
        # TODO: need to implement

    def test_file_rename_or_move(self):
        # test that resource file that belongs to GenericLogicalFile object
        # can be moved or renamed
        # TODO: Implement this test
        pass

    def _create_composite_resource(self):
        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Generic File Type Metadata',
            files=(self.generic_file_obj,)
        )

        # set the logical file
        resource_post_create_actions(resource=self.composite_resource, user=self.user,
                                     metadata=self.composite_resource.metadata)