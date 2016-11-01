# coding=utf-8
import os
import tempfile
import shutil

from django.test import TransactionTestCase
from django.contrib.auth.models import Group

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.signals import post_add_files_to_resource
from hs_core.hydroshare.utils import resource_file_add_process, resource_post_create_actions

from hs_file_types.models import GenericLogicalFile


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
        # test that we can create a composite resource

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

    def test_create_composite_resource_with_file_upload(self):
        # test that when we create composite resource with an uploaded file, then the uploaded file
        # is automatically set to genericlogicalfile type
        self.assertEqual(BaseResource.objects.count(), 0)
        self.raster_file_obj = open(self.raster_file, 'r')

        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Raster File Metadata',
            files=(self.raster_file_obj,)
        )

        # there should not be aby GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

        # set the logical file
        resource_post_create_actions(resource=self.composite_resource, user=self.user,
                                     metadata=self.composite_resource.metadata)

        # there should be one resource at this point
        self.assertEqual(BaseResource.objects.count(), 1)
        self.assertEqual(self.composite_resource.resource_type, "CompositeResource")
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
        # there should be 1 GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

    def test_file_add_to_composite_resource(self):
        # test that when we add file to an existing composite resource, the added file
        # automatically set to genericlogicalfile type
        self.assertEqual(BaseResource.objects.count(), 0)
        self.raster_file_obj = open(self.raster_file, 'r')

        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Raster File Metadata'
        )

        # there should not be aby GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

        # add a file to the resource
        resource_file_add_process(resource=self.composite_resource,
                                  files=(self.raster_file_obj,), user=self.user)

        # there should be one resource at this point
        self.assertEqual(BaseResource.objects.count(), 1)
        self.assertEqual(self.composite_resource.resource_type, "CompositeResource")
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
        # there should be 1 GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

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
