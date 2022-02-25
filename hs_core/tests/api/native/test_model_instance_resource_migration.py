import os
from unittest import TestCase

from django.contrib.auth.models import Group
from django.core.files.uploadedfile import UploadedFile
from django.core.management import call_command

from hs_composite_resource.models import CompositeResource
from hs_core import hydroshare
from hs_core.hydroshare import add_file_to_resource
from hs_core.testing import MockIRODSTestCaseMixin
from hs_file_types.models import ModelInstanceLogicalFile, ModelProgramLogicalFile
from hs_model_program.models import ModelProgramResource
from hs_modelinstance.models import ModelInstanceResource
from hs_swat_modelinstance.models import SWATModelInstanceResource
from hs_modflow_modelinstance.models import MODFLOWModelInstanceResource


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
        self.mi_migration_command = "migrate_model_instance_resources"
        self.mp_migration_command = "migrate_model_program_resources"
        self.prepare_mi_migration_command = "prepare_model_instance_resources_for_migration"
        self.MIGRATED_FROM_EXTRA_META_KEY = "MIGRATED_FROM"
        self.MIGRATING_RESOURCE_TYPE = "Model Instance Resource"
        self.EXECUTED_BY_EXTRA_META_KEY = "EXECUTED_BY_RES_ID"
        self.MI_FOLDER_NAME = "model-instance"
        # delete all resources in case a test isn't cleaning up after itself
        CompositeResource.objects.all().delete()
        ModelInstanceResource.objects.all().delete()

    def tearDown(self):
        super(TestModelInstanceResourceMigration, self).tearDown()
        self.user.delete()
        self.hs_group.delete()
        CompositeResource.objects.all().delete()
        ModelInstanceResource.objects.all().delete()
        ModelProgramResource.objects.all().delete()

    def test_prepare_generic_mi_for_migration_1(self):
        """Here we are testing that generic model instance resource that have a link to a model program resource
        the id of the mp resource gets saved in the mi resource extra_data field
        """

        # create a mi resource
        mi_res = self._create_mi_resource()
        self.assertEqual(ModelInstanceResource.objects.count(), 1)
        mp_res = self._create_mp_resource()
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        # link the mi res to mp resource
        mi_res.metadata.create_element('executedby', model_name=mp_res.short_id)
        self.assertNotEqual(mi_res.metadata.executed_by, None)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in mi_res.extra_data)
        # run  prepare migration command
        call_command(self.prepare_mi_migration_command)
        mi_res.refresh_from_db()
        self.assertTrue(self.EXECUTED_BY_EXTRA_META_KEY in mi_res.extra_data)
        self.assertEqual(mi_res.extra_data[self.EXECUTED_BY_EXTRA_META_KEY], mp_res.short_id)

    def test_prepare_generic_mi_for_migration_2(self):
        """Here we are testing that generic  model instance resource that does not have a link to a model program resource
        the id of the mp resource is NOT saved in the mi resource extra_data field
        """

        # create a mi resource
        mi_res = self._create_mi_resource()
        self.assertEqual(ModelInstanceResource.objects.count(), 1)
        self._create_mp_resource()
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        self.assertEqual(mi_res.metadata.executed_by, None)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in mi_res.extra_data)
        # run  prepare migration command
        call_command(self.prepare_mi_migration_command)
        mi_res.refresh_from_db()
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in mi_res.extra_data)

    def test_prepare_swat_mi_for_migration_1(self):
        """Here we are testing that SWAT model instance resource that have a link to a model program resource
        the id of the mp resource gets saved in the mi resource extra_data field
        """

        # create a SWAT mi resource
        mi_res = self._create_mi_resource(model_instance_type="SWATModelInstanceResource")
        self.assertEqual(SWATModelInstanceResource.objects.count(), 1)
        mp_res = self._create_mp_resource()
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        # link the mi res to mp resource
        mi_res.metadata.create_element('executedby', model_name=mp_res.short_id)
        self.assertNotEqual(mi_res.metadata.executed_by, None)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in mi_res.extra_data)
        # run  prepare migration command
        call_command(self.prepare_mi_migration_command)
        mi_res.refresh_from_db()
        self.assertTrue(self.EXECUTED_BY_EXTRA_META_KEY in mi_res.extra_data)
        self.assertEqual(mi_res.extra_data[self.EXECUTED_BY_EXTRA_META_KEY], mp_res.short_id)

    def test_prepare_swat_mi_for_migration_2(self):
        """Here we are testing that SWAT model instance resource that does not have a link to a model program resource
        the id of the mp resource is NOT saved in the mi resource extra_data field
        """

        # create a mi resource
        mi_res = self._create_mi_resource(model_instance_type="SWATModelInstanceResource")
        self.assertEqual(SWATModelInstanceResource.objects.count(), 1)
        self._create_mp_resource()
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        self.assertEqual(mi_res.metadata.executed_by, None)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in mi_res.extra_data)
        # run  prepare migration command
        call_command(self.prepare_mi_migration_command)
        mi_res.refresh_from_db()
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in mi_res.extra_data)

    def test_prepare_modflow_mi_for_migration_1(self):
        """Here we are testing that MODFLOW model instance resource that have a link to a model program resource
        the id of the mp resource gets saved in the mi resource extra_data field
        """

        # create a SWAT mi resource
        mi_res = self._create_mi_resource(model_instance_type="MODFLOWModelInstanceResource")
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 1)
        mp_res = self._create_mp_resource()
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        # link the mi res to mp resource
        mi_res.metadata.create_element('executedby', model_name=mp_res.short_id)
        self.assertNotEqual(mi_res.metadata.executed_by, None)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in mi_res.extra_data)
        # run  prepare migration command
        call_command(self.prepare_mi_migration_command)
        mi_res.refresh_from_db()
        self.assertTrue(self.EXECUTED_BY_EXTRA_META_KEY in mi_res.extra_data)
        self.assertEqual(mi_res.extra_data[self.EXECUTED_BY_EXTRA_META_KEY], mp_res.short_id)

    def test_prepare_modflow_mi_for_migration_2(self):
        """Here we are testing that MODFLOW model instance resource that does not have a link to a model program resource
        the id of the mp resource is NOT saved in the mi resource extra_data field
        """

        # create a mi resource
        mi_res = self._create_mi_resource(model_instance_type="MODFLOWModelInstanceResource")
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 1)
        self._create_mp_resource()
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        self.assertEqual(mi_res.metadata.executed_by, None)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in mi_res.extra_data)
        # run  prepare migration command
        call_command(self.prepare_mi_migration_command)
        mi_res.refresh_from_db()
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in mi_res.extra_data)

    def test_migrate_mi_resource_1(self):
        """
        Migrate a mi resource that has no files and no mi specific metadata
        A mi aggregation (folder based) will be created in the migrated composite resource
        """

        # create a mi resource
        mi_res = self._create_mi_resource()
        self.assertEqual(mi_res.files.count(), 0)
        self.assertEqual(ModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # run  migration command
        call_command(self.mi_migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 0)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # test that the converted resource contains one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_mi_resource_2(self):
        """
        Migrate a mi resource that has no files and but has mi specific metadata
        When converted to composite resource, it should have a mi aggregation (based on folder)
        and should have aggregation level metadata
        """

        # create a mi resource
        mi_res = self._create_mi_resource()
        self.assertEqual(mi_res.files.count(), 0)
        self.assertEqual(ModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model instance metadata
        mi_res.metadata.create_element('modeloutput', includes_output=True)

        # run  migration command
        call_command(self.mi_migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 0)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_mi_resource_3(self):
        """
        Migrate a mi resource that has only one file
        When converted to composite resource, it should have a mi aggregation (based on the folder)
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
        call_command(self.mi_migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 1)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertTrue(cmp_res.metadata.subjects)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        self.assertEqual(mi_aggr.files.count(), 1)
        res_file = cmp_res.files.first()
        self.assertEqual(res_file.file_folder, self.MI_FOLDER_NAME)
        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that the resource level keywords copied to the mi aggregation
        self.assertTrue(mi_aggr.metadata.keywords)
        self.assertEqual(len(mi_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_mi_resource_4(self):
        """
        Migrate a mi resource that has more than one file
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
        call_command(self.mi_migration_command)

        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertTrue(cmp_res.metadata.subjects)
        self.assertEqual(cmp_res.files.count(), 2)
        for res_file in cmp_res.files.all():
            self.assertEqual(res_file.file_folder, self.MI_FOLDER_NAME)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        self.assertEqual(mi_aggr.files.count(), 2)
        self.assertFalse(mi_aggr.metadata.has_model_output)
        # check that the resource level keywords copied to the mi aggregation
        self.assertTrue(mi_aggr.metadata.keywords)
        self.assertEqual(len(mi_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_mi_resource_5(self):
        """
        Migrate a mi resource that has a readme file only and no mi specific metadata
        A folder based mi aggregation is created in the migrated composite resource
        """

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
        call_command(self.mi_migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource does not contain any aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 1)
        # check the readme file was not moved to folder
        res_file = cmp_res.files.first()
        self.assertEqual(res_file.file_folder, "")
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # there should be one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_mi_resource_6(self):
        """
        Migrate a mi resource that has only a readme file and has mi specific metadata
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
        call_command(self.mi_migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 1)
        # check that the readme file is not moved to the aggregation folder
        res_file = cmp_res.files.first()
        self.assertEqual(res_file.file_folder, "")
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.files.count(), 0)
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_mi_resource_7(self):
        """
        Migrate a mi resource that has a readme file and another file, and has mi specific metadata
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
        self.assertEqual(mi_res.files.count(), 2)

        # run  migration command
        call_command(self.mi_migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 2)
        for res_file in cmp_res.files.all():
            if res_file.file_name == "cea.tif":
                self.assertEqual(res_file.file_folder, self.MI_FOLDER_NAME)
            else:
                self.assertEqual(res_file.file_folder, "")

        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check mi aggregation is not folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.files.count(), 1)
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_mi_resource_8(self):
        """
        Migrate a mi resource that has a readme file and 2 other files, and has mi specific metadata
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
        call_command(self.mi_migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 3)
        # check resource files folder
        for res_file in cmp_res.files.all():
            if res_file.file_name != "readme.txt":
                self.assertEqual(res_file.file_folder, self.MI_FOLDER_NAME)
            else:
                self.assertEqual(res_file.file_folder, "")

        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.files.count(), 2)
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_mi_resource_with_folder_1(self):
        """
        Migrate a mi resource that has only one file in one folder
        When converted to composite resource, it should have a mi aggregation (based on the folder)
        and should have aggregation level metadata. The original folder is moved into the aggregation folder.
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
        upload_folder = 'folder-1'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mi_res.files.count(), 1)
        # run  migration command
        call_command(self.mi_migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 1)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertTrue(cmp_res.metadata.subjects)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        self.assertEqual(mi_aggr.files.count(), 1)
        res_file = cmp_res.files.first()
        expected_file_folder = "{}/{}".format(self.MI_FOLDER_NAME, upload_folder)
        self.assertEqual(res_file.file_folder, expected_file_folder)

        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that the resource level keywords copied to the mi aggregation
        self.assertTrue(mi_aggr.metadata.keywords)
        self.assertEqual(len(mi_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_mi_resource_with_folder_2(self):
        """
        Migrate a mi resource that has 2 folders - each containing one file
        When converted to composite resource, it should have a mi aggregation (based on the folder)
        and should have aggregation level metadata. Both folders should be moved into the
        new aggregation folder.
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
        upload_folder_1 = 'folder-1'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder_1)
        upload_folder_2 = 'folder-2'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder_2)
        self.assertEqual(mi_res.files.count(), 2)
        # run  migration command
        call_command(self.mi_migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 2)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertTrue(cmp_res.metadata.subjects)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check the res files moved to the mi aggregation folder
        expected_file_folders = ["{}/{}".format(self.MI_FOLDER_NAME, upload_folder_1),
                                 "{}/{}".format(self.MI_FOLDER_NAME, upload_folder_2)]
        for res_file in cmp_res.files.all():
            self.assertIn(res_file.file_folder, expected_file_folders)

        res_file_1 = cmp_res.files.all()[0]
        res_file_2 = cmp_res.files.all()[1]
        self.assertNotEqual(res_file_1.file_folder, res_file_2.file_folder)
        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        self.assertEqual(mi_aggr.files.count(), 2)
        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that the resource level keywords copied to the mi aggregation
        self.assertTrue(mi_aggr.metadata.keywords)
        self.assertEqual(len(mi_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_mi_resource_with_folder_3(self):
        """
        Migrate a mi resource that has 2 folders - one folder is empty and the other one has a file
        When converted to composite resource, it should have a mi aggregation (based on the folder)
        and should have aggregation level metadata. Only ehe folder containing a file will be be moved into the
        new aggregation folder.
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
        upload_folder_1 = 'folder-1'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder_1)
        upload_folder_2 = 'folder-2'
        mi_res.create_folder(upload_folder_2)

        self.assertEqual(mi_res.files.count(), 1)
        # run  migration command
        call_command(self.mi_migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 1)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertTrue(cmp_res.metadata.subjects)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check the res files moved to the mi aggregation folder
        res_file = cmp_res.files.first()
        expected_file_folder = "{}/{}".format(self.MI_FOLDER_NAME, upload_folder_1)
        self.assertEqual(res_file.file_folder, expected_file_folder)

        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        self.assertEqual(mi_aggr.files.count(), 1)
        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that the resource level keywords copied to the mi aggregation
        self.assertTrue(mi_aggr.metadata.keywords)
        self.assertEqual(len(mi_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_mi_resource_with_folder_4(self):
        """
        Migrate a mi resource that has a readme file and one folder that contains a file
        When converted to composite resource, it should have a mi aggregation (based on the folder)
        and should have aggregation level metadata. The original folder that has a file will be moved into the
        new aggregation folder. The readme file won't be part of the mi aggregation.
        """

        # create a mi resource
        mi_res = self._create_mi_resource(add_keywords=True)
        self.assertTrue(mi_res.metadata.subjects)
        self.assertEqual(ModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model instance metadata
        mi_res.metadata.create_element('modeloutput', includes_output=True)
        # upload a readme file to mi resource
        file_path = 'hs_core/tests/data/readme.txt'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))
        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)

        # upload a file to mi resource
        file_path = 'hs_core/tests/data/test.txt'
        upload_folder_1 = 'folder-1'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder_1)
        self.assertEqual(mi_res.files.count(), 2)
        # run  migration command
        call_command(self.mi_migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 2)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertTrue(cmp_res.metadata.subjects)

        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check the res files moved to the mi aggregation folder
        # check the folder for each of the files in composite resource
        for res_file in cmp_res.files.all():
            if res_file.file_name == 'readme.txt':
                self.assertEqual(res_file.file_folder, "")
            else:
                expected_file_folder = "{}/{}".format(self.MI_FOLDER_NAME, upload_folder_1)
                self.assertEqual(res_file.file_folder, expected_file_folder)

        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        self.assertEqual(mi_aggr.files.count(), 1)
        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that the resource level keywords copied to the mi aggregation
        self.assertTrue(mi_aggr.metadata.keywords)
        self.assertEqual(len(mi_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_mi_resource_with_folder_5(self):
        """
        Migrate a mi resource that has 3 folders - one folder contains a file the other one is a nested folder (both
        parent and child each has a file)
        When converted to composite resource, it should have a mi aggregation (based on the folder)
        and should have aggregation level metadata. The original 3 folders will be moved into the
        new aggregation folder.
        """

        # create a mi resource
        mi_res = self._create_mi_resource(add_keywords=True)
        self.assertTrue(mi_res.metadata.subjects)
        self.assertEqual(ModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model instance metadata
        mi_res.metadata.create_element('modeloutput', includes_output=True)
        # upload a file to mi resource 'data' folder
        file_path = 'hs_core/tests/data/test.txt'
        upload_folder_1 = 'data'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder_1)
        # upload a file to mi resource 'contents' folder
        file_path = 'hs_core/tests/data/cea.tif'
        upload_folder_2 = 'contents'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))
        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder_2)

        # upload a file to mi resource 'contents/data' folder
        file_path = 'hs_core/tests/data/netcdf_valid.nc'
        upload_folder_3 = 'contents/data'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))
        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder_3)
        self.assertEqual(mi_res.files.count(), 3)
        # run  migration command
        call_command(self.mi_migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 3)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertTrue(cmp_res.metadata.subjects)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check the res files moved to the mi aggregation folder
        # check the folder for each of the files in composite resource
        for res_file in cmp_res.files.all():
            if res_file.file_name == 'test.txt':
                expected_file_folder = "{}/{}".format(self.MI_FOLDER_NAME, upload_folder_1)
            elif res_file.file_name == 'cea.tif':
                expected_file_folder = "{}/{}".format(self.MI_FOLDER_NAME, upload_folder_2)
            else:
                expected_file_folder = "{}/{}".format(self.MI_FOLDER_NAME, upload_folder_3)

            self.assertEqual(res_file.file_folder, expected_file_folder)

        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        self.assertEqual(mi_aggr.files.count(), 3)
        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that the resource level keywords copied to the mi aggregation
        self.assertTrue(mi_aggr.metadata.keywords)
        self.assertEqual(len(mi_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_mi_resource_with_folder_6(self):
        """
        Migrate a mi resource that has only one file in a folder. The folder name is 'model-instance'
        When converted to composite resource, it should have a mi aggregation (based on the folder)
        and should have aggregation level metadata. The original folder will be moved into the new aggregation folder.
        The newly created aggregation folder name should be 'model-instance-1'
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
        upload_folder = 'model-instance'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mi_res.files.count(), 1)
        # run  migration command
        call_command(self.mi_migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 1)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertTrue(cmp_res.metadata.subjects)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.files.count(), 1)
        expected_aggr_folder_name = "{}-1".format(self.MI_FOLDER_NAME)
        self.assertEqual(mi_aggr.folder, expected_aggr_folder_name)
        self.assertEqual(mi_aggr.aggregation_name, expected_aggr_folder_name)
        res_file = cmp_res.files.first()
        expected_file_folder = "{}-1/{}".format(self.MI_FOLDER_NAME, upload_folder)
        self.assertEqual(res_file.file_folder, expected_file_folder)

        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that the resource level keywords copied to the mi aggregation
        self.assertTrue(mi_aggr.metadata.keywords)
        self.assertEqual(len(mi_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_mi_resource_missing_file_in_irods(self):
        """
        Migrate a mi resource that has 2 files in db but only one file in iRODS
        When converted to composite resource, it should have a mi aggregation (based on the folder)
        and should have aggregation level metadata. Only the resource file that is in iRODS will be part of the
        mi aggregation.
        """

        # create a mi resource
        mi_res = self._create_mi_resource(add_keywords=True)
        self.assertTrue(mi_res.metadata.subjects)
        self.assertEqual(ModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model instance metadata
        mi_res.metadata.create_element('modeloutput', includes_output=True)
        # upload a readme file to mi resource
        file_path = 'hs_core/tests/data/readme.txt'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))
        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mi_res.files.count(), 1)
        text_res_file = mi_res.files.first()

        # upload a file to mi resource
        file_path = 'hs_core/tests/data/cea.tif'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))
        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mi_res.files.count(), 2)
        # delete the text file from iRODS
        istorage = mi_res.get_storage()
        istorage.delete(text_res_file.public_path)
        # as pre the DB the Mi resource still have 2 files
        self.assertEqual(mi_res.files.count(), 2)

        # run  migration command
        call_command(self.mi_migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 2)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        # check the res file moved to the mi aggregation folder
        for res_file in cmp_res.files.all():
            if res_file.file_name == 'cea.tif':
                self.assertEqual(res_file.file_folder, self.MI_FOLDER_NAME)
            else:
                self.assertEqual(res_file.file_folder, "")

        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertTrue(cmp_res.metadata.subjects)

        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)

        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        self.assertEqual(mi_aggr.files.count(), 1)
        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that the resource level keywords copied to the mi aggregation
        self.assertTrue(mi_aggr.metadata.keywords)
        self.assertEqual(len(mi_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_executed_by(self):
        """
        Migrate a mi resource that has a link (executed_by) to a composite resource
        If the linked resource has a mp aggregation, a link to the external mp aggregation is established
        """

        # create a mi resource
        mi_res = self._create_mi_resource()
        self.assertEqual(ModelInstanceResource.objects.count(), 1)
        mp_res = self._create_mp_resource()
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        upload_folder = ''
        file_path = 'hs_core/tests/data/cea.tif'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder)
        # check mp resource has 2 files
        self.assertEqual(mp_res.files.count(), 1)
        # no files in mi resource
        self.assertEqual(mi_res.files.count(), 0)

        # link the mi res to mp resource
        mi_res.metadata.create_element('executedby', model_name=mp_res.short_id)
        mi_res.metadata.create_element('modeloutput', includes_output=True)
        self.assertNotEqual(mi_res.metadata.executed_by, None)
        self.assertNotEqual(mi_res.metadata.model_output, None)

        # run  prepare migration command for preparing mi resource for migration
        call_command(self.prepare_mi_migration_command)
        # run migration command to migrate mp resource
        call_command(self.mp_migration_command)
        self.assertEqual(CompositeResource.objects.count(), 1)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, "model-program")

        # run  migration command to migrate mi resource
        call_command(self.mi_migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 2)
        cmp_res = CompositeResource.objects.get(short_id=mi_res.short_id)

        # test that the converted mi resource contains one mi aggregation
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertTrue(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertEqual(cmp_res.extra_data[self.EXECUTED_BY_EXTRA_META_KEY], mp_res.short_id)
        # no files in migrated mi resource
        self.assertEqual(cmp_res.files.count(), 0)
        # there should be only one mi aggregation in the migrated mi resource
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertTrue([lf for lf in cmp_res.logical_files if lf.is_model_instance])
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertTrue(mi_aggr.metadata.has_model_output)
        self.assertEqual(mi_aggr.metadata.executed_by, mp_aggr)
        # check that the linked mp aggregation is part of another resource
        self.assertNotEqual(mi_aggr.resource.short_id, mp_aggr.resource.short_id)
        self.assertEqual(mi_aggr.files.count(), 0)
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_delete_external_linked_mp_aggr(self):
        """
        Here we are testing that when the mp aggregation which is linked to a mi aggregation where the
        mi and mp aggregation are part of different resource, is deleted the mi aggregation metadata is set to dirty
        (metadata set to dirty will generate the mi xml file on bag download)
        """
        # create a mi resource
        mi_res = self._create_mi_resource()
        self.assertEqual(ModelInstanceResource.objects.count(), 1)
        mp_res = self._create_mp_resource()
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        upload_folder = ''
        file_path = 'hs_core/tests/data/cea.tif'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder)
        # check mp resource has 2 files
        self.assertEqual(mp_res.files.count(), 1)
        # no files in mi resource
        self.assertEqual(mi_res.files.count(), 0)

        # link the mi res to mp resource
        mi_res.metadata.create_element('executedby', model_name=mp_res.short_id)
        mi_res.metadata.create_element('modeloutput', includes_output=True)
        self.assertNotEqual(mi_res.metadata.executed_by, None)
        self.assertNotEqual(mi_res.metadata.model_output, None)

        # run  prepare migration command for preparing mi resource for migration
        call_command(self.prepare_mi_migration_command)
        # run migration command to migrate mp resource
        call_command(self.mp_migration_command)
        self.assertEqual(CompositeResource.objects.count(), 1)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, 'model-program')

        # run  migration command to migrate mi resource
        call_command(self.mi_migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 2)

        mi_aggr = ModelInstanceLogicalFile.objects.first()
        # when the new mi aggregation gets created, the aggregation metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)
        mi_aggr.metadata.is_dirty = False
        mi_aggr.metadata.save()
        # test deleting the linked mp aggregation sets the metadata for mi aggregation to dirty
        mp_aggr.delete()
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_delete_external_linked_mp_aggr_resource(self):
        """
        Here we are testing that when the resource having the mp aggregation which is linked to a mi aggregation
        where the mi and mp aggregation are part of different resource, is deleted the mi aggregation metadata
        is set to dirty (metadata set to dirty will generate the mi xml file on bag download)
        """
        # create a mi resource
        mi_res = self._create_mi_resource()
        self.assertEqual(ModelInstanceResource.objects.count(), 1)
        mp_res = self._create_mp_resource()
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        upload_folder = ''
        file_path = 'hs_core/tests/data/cea.tif'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder)
        # check mp resource has 2 files
        self.assertEqual(mp_res.files.count(), 1)
        # no files in mi resource
        self.assertEqual(mi_res.files.count(), 0)

        # link the mi res to mp resource
        mi_res.metadata.create_element('executedby', model_name=mp_res.short_id)
        mi_res.metadata.create_element('modeloutput', includes_output=True)
        self.assertNotEqual(mi_res.metadata.executed_by, None)
        self.assertNotEqual(mi_res.metadata.model_output, None)

        # run  prepare migration command for preparing mi resource for migration
        call_command(self.prepare_mi_migration_command)
        # run migration command to migrate mp resource
        call_command(self.mp_migration_command)
        self.assertEqual(CompositeResource.objects.count(), 1)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, "model-program")

        # run  migration command to migrate mi resource
        call_command(self.mi_migration_command)
        self.assertEqual(ModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 2)
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        # when the new mi aggregation gets created, the aggregation metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)
        mi_aggr.metadata.is_dirty = False
        mi_aggr.metadata.save()
        # test deleting the linked composite resource (containing the mp aggregation) sets the metadata
        # for mi aggregation to dirty
        mp_res.delete()
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def _create_mi_resource(self, model_instance_type="ModelInstanceResource", add_keywords=False):
        """Creates a model instance resource"""
        res = hydroshare.create_resource(model_instance_type, self.user,
                                         "Testing migrating to composite resource")
        if add_keywords:
            res.metadata.create_element('subject', value='kw-1')
            res.metadata.create_element('subject', value='kw-2')
        return res

    def _create_mp_resource(self, add_keywords=False):
        """Create a model program resource"""
        mp_res = hydroshare.create_resource("ModelProgramResource", self.user,
                                            "Testing migrating to composite resource")
        if add_keywords:
            mp_res.metadata.create_element('subject', value='kw-1')
            mp_res.metadata.create_element('subject', value='kw-2')
        return mp_res
