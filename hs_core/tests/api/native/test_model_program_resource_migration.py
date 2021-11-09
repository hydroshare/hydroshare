import os
from unittest import TestCase

from django.contrib.auth.models import Group
from django.core.files.uploadedfile import UploadedFile
from django.core.management import call_command

from hs_composite_resource.models import CompositeResource
from hs_core import hydroshare
from hs_core.hydroshare import add_file_to_resource
from hs_core.testing import MockIRODSTestCaseMixin
from hs_file_types.models import ModelProgramLogicalFile, ModelProgramResourceFileType
from hs_model_program.models import ModelProgramResource


class TestModelProgramResourceMigration(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(TestModelProgramResourceMigration, self).setUp()

        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = hydroshare.create_account(
            'mp_resource_migration@email.com',
            username='mp_resource_migration',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[self.hs_group],
        )
        self.migration_command = "migrate_model_program_resources"
        self.MIGRATED_FROM_EXTRA_META_KEY = "MIGRATED_FROM"
        self.MIGRATING_RESOURCE_TYPE = "Model Program Resource"
        self.MP_FOLDER_NAME = "model-program"

        # delete all resources in case a test isn't cleaning up after itself
        CompositeResource.objects.all().delete()
        ModelProgramResource.objects.all().delete()

    def tearDown(self):
        super(TestModelProgramResourceMigration, self).tearDown()
        self.user.delete()
        self.hs_group.delete()
        CompositeResource.objects.all().delete()
        ModelProgramResource.objects.all().delete()

    def test_migrate_mp_resource_1(self):
        """
        Migrate a mp resource that has no files and no mp specific metadata
        A folder based mp aggregation will be created in the migrated resource.
        """

        # create a mp resource
        mp_res = self._create_mp_resource()
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains a folder based mp aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        # there should be one aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)

    def test_migrate_mp_resource_2(self):
        """
        Migrate a mp resource that has no files and but has mp specific metadata
        When converted to composite resource, it should have a mp aggregation (based on folder)
        and should have aggregation level metadata
        """

        # create a mp resource
        mp_res = self._create_mp_resource()
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model program metadata
        mp_res.metadata.create_element('MpMetadata', modelVersion='5.1.011')

        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mp aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)

    def test_migrate_mp_resource_3(self):
        """
        Migrate a mp resource that has only one file
        When converted to composite resource, it should have a mp aggregation (based on the folder)
        and should have aggregation level metadata
        """

        # create a mp resource
        mp_res = self._create_mp_resource(add_keywords=True)
        self.assertEqual(mp_res.metadata.subjects.count(), 2)
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model program metadata
        mp_res.metadata.create_element('MpMetadata', modelVersion='5.1.011')
        # upload a file to mp resource
        file_path = 'hs_core/tests/data/test.txt'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mp_res.files.count(), 1)
        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mp aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.files.count(), 1)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        # check that the resource level keywords copied over to the aggregation
        self.assertEqual(cmp_res.metadata.subjects.count(), 2)
        self.assertEqual(len(mp_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)

    def test_migrate_mp_resource_4(self):
        """
        Migrate a mp resource that has more than one file
        When converted to composite resource, it should have a mp aggregation (based on the folder)
        and should have aggregation level metadata
        """

        # create a mp resource
        mp_res = self._create_mp_resource(add_keywords=True)
        self.assertEqual(mp_res.metadata.subjects.count(), 2)
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model program metadata
        mp_res.metadata.create_element('MpMetadata', modelVersion='5.1.011')
        # upload a file to mp resource
        file_path = 'hs_core/tests/data/test.txt'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder)

        # upload a 2nd file to mp resource
        file_path = 'hs_core/tests/data/cea.tif'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder)

        self.assertEqual(mp_res.files.count(), 2)
        # run  migration command
        call_command(self.migration_command)

        self.assertEqual(ModelProgramResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mp aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.files.count(), 2)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        # check that the resource level keywords copied over to the aggregation
        self.assertEqual(cmp_res.metadata.subjects.count(), 2)
        self.assertEqual(len(mp_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)

    def test_migrate_mp_resource_5(self):
        """
        Migrate a mp resource that has a readme file only and no mp specific metadata
        A folder based mp aggregation is created in the migrated resource
        """

        # create a mp resource
        mp_res = self._create_mp_resource()
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # upload a file to mp resource
        file_path = 'hs_core/tests/data/readme.txt'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mp_res.files.count(), 1)
        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource does not contain any aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 1)
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        # there should ne one aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)

    def test_migrate_mp_resource_6(self):
        """
        Migrate a mp resource that has only a readme file and has mp specific metadata
        When converted to composite resource, it should have a mp aggregation (based on folder)
        and should have aggregation level metadata
        """

        # create a mp resource
        mp_res = self._create_mp_resource()
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model program metadata
        mp_res.metadata.create_element('MpMetadata', modelVersion='5.1.011')
        # upload a file to mp resource
        file_path = 'hs_core/tests/data/readme.txt'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mp_res.files.count(), 1)

        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mp aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.files.count(), 0)
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')

    def test_migrate_mp_resource_7(self):
        """
        Migrate a mp resource that has a readme file and another file, and has mp specific metadata
        When converted to composite resource, it should have a mp aggregation (based on folder)
        and should have aggregation level metadata
        """

        # create a mp resource
        mp_res = self._create_mp_resource()
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model program metadata
        mp_res.metadata.create_element('MpMetadata', modelVersion='5.1.011')
        # upload a file to mp resource
        file_path = 'hs_core/tests/data/readme.txt'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder)
        # upload a 2nd file to mp resource
        file_path = 'hs_core/tests/data/cea.tif'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mp_res.files.count(), 2)

        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mp aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.files.count(), 1)
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')

    def test_migrate_mp_resource_8(self):
        """
        Migrate a mp resource that has a readme file and 2 other files, and has mp specific metadata
        When converted to composite resource, it should have a mp aggregation (based on folder)
        and should have aggregation level metadata
        """

        # create a mp resource
        mp_res = self._create_mp_resource()
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model program metadata
        mp_res.metadata.create_element('MpMetadata', modelVersion='5.1.011')
        # upload a file to mp resource
        file_path = 'hs_core/tests/data/readme.txt'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder)

        # upload a 2nd file to mp resource
        file_path = 'hs_core/tests/data/cea.tif'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder)

        # upload a 3rd file to mp resource
        file_path = 'hs_core/tests/data/netcdf_valid.nc'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mp_res.files.count(), 3)

        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mp aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.files.count(), 2)
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')

    def test_migrate_mp_resource_9(self):
        """
        Migrate a mp resource that has one file , and has all mp specific metadata
        When converted to composite resource, it should have a mp aggregation (based on folder)
        and should have aggregation level metadata
        """

        # create a mp resource
        mp_res = self._create_mp_resource()
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)

        # upload a file to mp resource
        file_path = 'hs_core/tests/data/cea.tif'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))
        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mp_res.files.count(), 1)

        # create Model program metadata
        release_date = '2016-10-24'
        mp_res.metadata.create_element('MpMetadata',
                                       modelVersion='5.1.011',
                                       modelProgramLanguage='Fortran, Python',
                                       modelOperatingSystem='Windows',
                                       modelReleaseDate=release_date,
                                       modelWebsite='http://www.hydroshare.org',
                                       modelCodeRepository='http://www.github.com',
                                       modelReleaseNotes='cea.tif',
                                       )

        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mp aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.files.count(), 1)
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        # test aggregation level metadata
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        self.assertEqual(mp_aggr.metadata.programming_languages, ['Fortran', 'Python'])
        self.assertEqual(mp_aggr.metadata.operating_systems, ['Windows'])
        self.assertEqual(str(mp_aggr.metadata.release_date), release_date)
        self.assertEqual(mp_aggr.metadata.website, 'http://www.hydroshare.org')
        self.assertEqual(mp_aggr.metadata.code_repository, 'http://www.github.com')
        mp_file_type = ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).first()
        self.assertEqual(mp_file_type.file_type, ModelProgramResourceFileType.RELEASE_NOTES)

    def test_migrate_mp_resource_10(self):
        """
        Migrate a published mp resource that has no files but has mp specific metadata
        When converted to composite resource, it should have a mp aggregation (based on folder)
        and should have aggregation level metadata
        """

        # create a mp resource
        mp_res = self._create_mp_resource()
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model program metadata
        mp_res.metadata.create_element('MpMetadata', modelVersion='5.1.011')
        # set the resource to published
        mp_res.raccess.published = True
        mp_res.raccess.save()
        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mp aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertTrue(cmp_res.raccess.published)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')

    def _create_mp_resource(self, add_keywords=False):
        mp_res = hydroshare.create_resource("ModelProgramResource", self.user,
                                            "Testing migrating to composite resource")
        if add_keywords:
            mp_res.metadata.create_element('subject', value='kw-1')
            mp_res.metadata.create_element('subject', value='kw-2')
        return mp_res
