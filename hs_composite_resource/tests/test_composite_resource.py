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
from hs_core.models import BaseResource
from hs_core.models import Coverage

from hs_file_types.utils import set_file_to_geo_raster_file_type
from hs_file_types.models import GeoRasterLogicalFile, GeoRasterFileMetaData

from hs_geo_raster_resource.models import OriginalCoverage, CellInformation, BandInformation

import mock


class CompositeResourceTest(MockIRODSTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(CompositeResourceTest, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        # self.composite_resource = hydroshare.create_resource(
        #     resource_type='CompositeResource',
        #     owner=self.user,
        #     title='Test Raster File Metadata'
        # )

        self.temp_dir = tempfile.mkdtemp()
        self.raster_file_name = 'small_logan.tif'
        self.raster_file = 'hs_composite_resource/tests/data/{}'.format(self.raster_file_name)

        target_temp_raster_file = os.path.join(self.temp_dir, self.raster_file_name)
        shutil.copy(self.raster_file, target_temp_raster_file)
        self.raster_file_obj = open(target_temp_raster_file, 'r')

    def tearDown(self):
        super(CompositeResourceTest, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_create_composite_resource(self):
        # there should not be any resource at this point
        self.assertEqual(BaseResource.objects.count(), 0)

        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Raster File Metadata'
        )

        # there should be one resource at this point

        self.assertEqual(BaseResource.objects.count(), 1)
        self.assertEqual(self.composite_resource.resource_type, "CompositeResource")

    def test_core_metadata(self):
        # TODO: implement this test
        pass

    def test_can_be_public_or_discoverable(self):
        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Raster File Metadata'
        )

        # TODO: implement the tests
