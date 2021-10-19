import os
from unittest import TestCase

from django.contrib.auth.models import Group
from django.core.files.uploadedfile import UploadedFile
from django.core.management import call_command

from hs_composite_resource.models import CompositeResource
from hs_core import hydroshare
from hs_core.hydroshare import add_file_to_resource
from hs_core.testing import MockIRODSTestCaseMixin
from hs_file_types.models import ModelInstanceLogicalFile
from hs_modelinstance.models import ModelInstanceResource


class TestModelInstanceResourceMigration(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(TestModelInstanceResourceMigration, self).setUp()

        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = hydroshare.create_account(
            'mi_resource_migration@email.com',
            username='mi_resource_migration',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[self.hs_group],
        )
        self.migration_command = "migrate_model_instance_resources"
        # delete all resources in case a test isn't cleaning up after itself
        CompositeResource.objects.all().delete()
        ModelInstanceResource.objects.all().delete()

    def tearDown(self):
        super(TestModelInstanceResourceMigration, self).tearDown()
        self.user.delete()
        self.hs_group.delete()
        CompositeResource.objects.all().delete()
        ModelInstanceResource.objects.all().delete()

    def test_migrate_mi_resource_1(self):
        """Migrate a mi resource that has no files and no mi specific metadata"""

        # create a mi resource
        mi_res = self._create_mi_resource()
        self.assertEqual(ModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource does not contain any aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        # there should be no mi aggregations
        self.assertEqual(len(list(cmp_res.logical_files)), 0)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 0)

    def test_migrate_mi_resource_2(self):
        """Migrate a mi resource that has no files and but has mi specific metadata
        When converted to composite resource, it should have a mi aggregation (based on folder)
        and should have aggregation level metadata
        """

        # create a mi resource
        mi_res = self._create_mi_resource()
        self.assertEqual(ModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model instance metadata
        mi_res.metadata.create_element('modeloutput', includes_output=True)

        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, 'mi')
        self.assertTrue(mi_aggr.metadata.has_model_output)

    def test_migrate_mi_resource_3(self):
        """Migrate a mi resource that has only one file
        When converted to composite resource, it should have a mi aggregation (based on the file)
        and should have aggregation level metadata
        """

        # create a mi resource
        mi_res = self._create_mi_resource(add_keywords=True)
        self.assertTrue(mi_res.metadata.subjects)
        self.assertEqual(ModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model instance metadata
        mi_res.metadata.create_element('modeloutput', includes_output=True)
        # upload a file to mi resource
        file_path = 'hs_core/tests/data/test.txt'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mi_res.files.count(), 1)
        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertTrue(cmp_res.metadata.subjects)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check mi aggregation is not folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, None)
        self.assertEqual(mi_aggr.files.count(), 1)
        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that the resource level keywords copied to the mi aggregation
        self.assertTrue(mi_aggr.metadata.keywords)
        self.assertEqual(len(mi_aggr.metadata.keywords), cmp_res.metadata.subjects.count())

    def test_migrate_mi_resource_4(self):
        """Migrate a mi resource that has more than one file
        When converted to composite resource, it should have a mi aggregation (based on the folder)
        and should have aggregation level metadata
        """

        # create a mi resource
        mi_res = self._create_mi_resource(add_keywords=True)
        self.assertTrue(mi_res.metadata.subjects)
        self.assertEqual(ModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model program metadata
        mi_res.metadata.create_element('modeloutput', includes_output=False)
        # upload a file to mi resource
        file_path = 'hs_core/tests/data/test.txt'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)

        # upload a 2nd file to mi resource
        file_path = 'hs_core/tests/data/cea.tif'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)

        self.assertEqual(mi_res.files.count(), 2)
        # run  migration command
        call_command(self.migration_command)

        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertTrue(cmp_res.metadata.subjects)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, 'mi')
        self.assertEqual(mi_aggr.files.count(), 2)
        self.assertFalse(mi_aggr.metadata.has_model_output)
        # check that the resource level keywords copied to the mi aggregation
        self.assertTrue(mi_aggr.metadata.keywords)
        self.assertEqual(len(mi_aggr.metadata.keywords), cmp_res.metadata.subjects.count())

    def test_migrate_mi_resource_5(self):
        """Migrate a mi resource that has a readme file only and no mi specific metadata"""

        # create a mi resource
        mi_res = self._create_mi_resource()
        self.assertEqual(ModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # upload a file to mi resource
        file_path = 'hs_core/tests/data/readme.txt'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mi_res.files.count(), 1)
        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource does not contain any aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 1)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        # there should not be any mi aggregation
        self.assertFalse(list(cmp_res.logical_files))
        self.assertEqual(ModelInstanceResource.objects.count(), 0)

    def test_migrate_mi_resource_6(self):
        """Migrate a mi resource that has only a readme file and has mi specific metadata
        When converted to composite resource, it should have a mi aggregation (based on folder)
        and should have aggregation level metadata
        """

        # create a mi resource
        mi_res = self._create_mi_resource()
        self.assertEqual(ModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model instance metadata
        mi_res.metadata.create_element('modeloutput', includes_output=True)
        # upload a file to mi resource
        file_path = 'hs_core/tests/data/readme.txt'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mi_res.files.count(), 1)

        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.files.count(), 0)
        self.assertEqual(mi_aggr.folder, 'mi')
        self.assertTrue(mi_aggr.metadata.has_model_output)

    def test_migrate_mi_resource_7(self):
        """Migrate a mi resource that has a readme file and another file, and has mi specific metadata
        When converted to composite resource, it should have a mi aggregation (based on file)
        and should have aggregation level metadata
        """

        # create a mi resource
        mi_res = self._create_mi_resource()
        self.assertEqual(ModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model instance metadata
        mi_res.metadata.create_element('modeloutput', includes_output=True)
        # upload a file to mi resource
        file_path = 'hs_core/tests/data/readme.txt'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)
        # upload a 2nd file to mi resource
        file_path = 'hs_core/tests/data/cea.tif'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mi_res.files.count(), 2)

        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check mi aggregation is not folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.files.count(), 1)
        self.assertEqual(mi_aggr.folder, None)
        self.assertTrue(mi_aggr.metadata.has_model_output)

    def test_migrate_mi_resource_8(self):
        """Migrate a mi resource that has a readme file and 2 other files, and has mi specific metadata
        When converted to composite resource, it should have a mi aggregation (based on folder)
        and should have aggregation level metadata
        """

        # create a mi resource
        mi_res = self._create_mi_resource()
        self.assertEqual(ModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model instance metadata
        mi_res.metadata.create_element('modeloutput', includes_output=True)
        # upload a file to mi resource
        file_path = 'hs_core/tests/data/readme.txt'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)

        # upload a 2nd file to mi resource
        file_path = 'hs_core/tests/data/cea.tif'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)

        # upload a 3rd file to mi resource
        file_path = 'hs_core/tests/data/netcdf_valid.nc'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mi_res.files.count(), 3)

        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.files.count(), 2)
        self.assertEqual(mi_aggr.folder, 'mi')
        self.assertTrue(mi_aggr.metadata.has_model_output)

    def _create_mi_resource(self, add_keywords=False):

        res = hydroshare.create_resource("ModelInstanceResource", self.user,
                                         "Testing migrating to composite resource")
        if add_keywords:
            res.metadata.create_element('subject', value='kw-1')
            res.metadata.create_element('subject', value='kw-2')
        return res
