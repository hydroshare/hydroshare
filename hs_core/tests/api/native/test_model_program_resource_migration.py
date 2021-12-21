import os
from unittest import TestCase

from django.contrib.auth.models import Group
from django.core.files.uploadedfile import UploadedFile
from django.core.management import call_command

from hs_composite_resource.models import CompositeResource
from hs_core import hydroshare
from hs_core.hydroshare import add_file_to_resource
from hs_core.models import ResourceFile
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
        self.assertEqual(mp_res.files.count(), 0)
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains a folder based mp aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 0)
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        # there should be one aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.aggregation_name, self.MP_FOLDER_NAME)
        # check the aggregation meta xml files exist in iRODS
        self._test_aggr_meta_files(cmp_res, aggr_folder_path=self.MP_FOLDER_NAME)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # test no mp files types are created
        self.assertEqual(ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).count(), 0)

    def test_migrate_mp_resource_2(self):
        """
        Migrate a mp resource that has no files and but has mp specific metadata
        When converted to composite resource, it should have a mp aggregation (based on folder)
        and should have aggregation level metadata
        """

        # create a mp resource
        mp_res = self._create_mp_resource()
        self.assertEqual(mp_res.files.count(), 0)
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
        self.assertEqual(cmp_res.files.count(), 0)
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.aggregation_name, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        # check the aggregation meta xml files exist in iRODS
        self._test_aggr_meta_files(cmp_res, aggr_folder_path=self.MP_FOLDER_NAME)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # test no mp files types are created
        self.assertEqual(ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).count(), 0)

    def test_migrate_mp_resource_3(self):
        """
        Migrate a mp resource that has only one file
        When converted to composite resource, it should have a mp aggregation (based on the folder)
        and should have aggregation level metadata. The resource file will be moved to the new folder.
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
        self.assertEqual(cmp_res.files.count(), 1)
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check the res file moved to the mp aggregation folder
        res_file = cmp_res.files.first()
        self.assertEqual(res_file.file_folder, self.MP_FOLDER_NAME)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.aggregation_name, self.MP_FOLDER_NAME)
        # check the aggregation meta xml files exist in iRODS
        self._test_aggr_meta_files(cmp_res, aggr_folder_path=self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.files.count(), 1)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        # check that the resource level keywords copied over to the aggregation
        self.assertEqual(cmp_res.metadata.subjects.count(), 2)
        self.assertEqual(len(mp_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # test no mp files types are created
        self.assertEqual(ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).count(), 0)

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
        self.assertEqual(cmp_res.files.count(), 2)
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check both files are moved to the aggregation folder
        for res_file in cmp_res.files.all():
            self.assertEqual(res_file.file_folder, self.MP_FOLDER_NAME)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.aggregation_name, self.MP_FOLDER_NAME)
        # check the aggregation meta xml files exist in iRODS
        self._test_aggr_meta_files(cmp_res, aggr_folder_path=self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.files.count(), 2)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        # check that the resource level keywords copied over to the aggregation
        self.assertEqual(cmp_res.metadata.subjects.count(), 2)
        self.assertEqual(len(mp_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # test no mp files types are created
        self.assertEqual(ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).count(), 0)

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
        # check that the readme file was not moved to the aggregation folder
        res_file = cmp_res.files.first()
        self.assertEqual(res_file.file_folder, "")
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.aggregation_name, self.MP_FOLDER_NAME)
        # check the aggregation meta xml files exist in iRODS
        self._test_aggr_meta_files(cmp_res, aggr_folder_path=self.MP_FOLDER_NAME)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # test no mp files types are created
        self.assertEqual(ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).count(), 0)

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
        self.assertEqual(cmp_res.files.count(), 1)
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check that the readme file was not moved to the mp aggregation folder
        res_file = cmp_res.files.first()
        self.assertEqual(res_file.file_folder, "")
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.files.count(), 0)
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.aggregation_name, self.MP_FOLDER_NAME)
        # check the aggregation meta xml files exist in iRODS
        self._test_aggr_meta_files(cmp_res, aggr_folder_path=self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        # test no mp files types are created
        self.assertEqual(ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).count(), 0)

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
        self.assertEqual(cmp_res.files.count(), 2)
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check the folder of each of the files
        for res_file in cmp_res.files.all():
            if res_file.file_name != 'readme.txt':
                self.assertEqual(res_file.file_folder, self.MP_FOLDER_NAME)
            else:
                self.assertEqual(res_file.file_folder, "")
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.files.count(), 1)
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.aggregation_name, self.MP_FOLDER_NAME)
        # check the aggregation meta xml files exist in iRODS
        self._test_aggr_meta_files(cmp_res, aggr_folder_path=self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        # test no mp files types are created
        self.assertEqual(ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).count(), 0)

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
        self.assertEqual(cmp_res.files.count(), 3)
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check the folder for each of the files in composite resource
        for res_file in cmp_res.files.all():
            if res_file.file_name == 'readme.txt':
                self.assertEqual(res_file.file_folder, "")
            else:
                self.assertEqual(res_file.file_folder, self.MP_FOLDER_NAME)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.files.count(), 2)
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.aggregation_name, self.MP_FOLDER_NAME)
        # check the aggregation meta xml files exist in iRODS
        self._test_aggr_meta_files(cmp_res, aggr_folder_path=self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        # test no mp files types are created
        self.assertEqual(ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).count(), 0)

    def test_migrate_mp_resource_9(self):
        """
        Migrate a mp resource that has one file (file is specified as release notes) , and has all mp specific metadata
        When converted to composite resource, it should have a mp aggregation (based on folder)
        and should have aggregation level metadata and the file is set to release notes.
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
        self.assertEqual(cmp_res.files.count(), 1)
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # check file folder
        res_file = cmp_res.files.first()
        self.assertEqual(res_file.file_folder, self.MP_FOLDER_NAME)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.files.count(), 1)
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.aggregation_name, self.MP_FOLDER_NAME)
        # check the aggregation meta xml files exist in iRODS
        self._test_aggr_meta_files(cmp_res, aggr_folder_path=self.MP_FOLDER_NAME)
        # test aggregation level metadata
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        self.assertEqual(mp_aggr.metadata.programming_languages, ['Fortran', 'Python'])
        self.assertEqual(mp_aggr.metadata.operating_systems, ['Windows'])
        self.assertEqual(str(mp_aggr.metadata.release_date), release_date)
        self.assertEqual(mp_aggr.metadata.website, 'http://www.hydroshare.org')
        self.assertEqual(mp_aggr.metadata.code_repository, 'http://www.github.com')
        # test that the resource file is set to release notes
        mp_file_type = ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).first()
        self.assertEqual(mp_file_type.file_type, ModelProgramResourceFileType.RELEASE_NOTES)
        self.assertEqual(mp_file_type.res_file, mp_aggr.files.first())

    def test_migrate_mp_resource_10(self):
        """
        Migrate a published mp resource that has no files but has mp specific metadata
        When converted to composite resource, it should have a mp aggregation (based on folder)
        and should have aggregation level metadata
        """

        # create a mp resource
        mp_res = self._create_mp_resource()
        self.assertEqual(mp_res.files.count(), 0)
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
        self.assertEqual(cmp_res.files.count(), 0)
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertTrue(cmp_res.raccess.published)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.aggregation_name, self.MP_FOLDER_NAME)
        # check the aggregation meta xml files exist in iRODS
        self._test_aggr_meta_files(cmp_res, aggr_folder_path=self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        # test no mp files types are created
        self.assertEqual(ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).count(), 0)

    def test_migrate_mp_resource_with_folder_1(self):
        """
        Migrate a mp resource that has only one file in a folder
        When converted to composite resource, it should have a mp aggregation (based on the folder)
        and should have aggregation level metadata. The original folder will be moved into the new aggregation folder
        """

        # create a mp resource
        mp_res = self._create_mp_resource(add_keywords=True)
        self.assertEqual(mp_res.metadata.subjects.count(), 2)
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)

        # upload a file to mp resource
        file_path = 'hs_core/tests/data/test.txt'
        upload_folder = 'folder-1'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mp_res.files.count(), 1)
        # create Model program metadata
        mp_res.metadata.create_element('MpMetadata', modelVersion='5.1.011', modelDocumentation='test.txt')
        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mp aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 1)
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check the res file moved to the mp aggregation folder
        res_file = cmp_res.files.first()
        expected_file_folder = "{}/{}".format(self.MP_FOLDER_NAME, upload_folder)
        self.assertEqual(res_file.file_folder, expected_file_folder)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.aggregation_name, self.MP_FOLDER_NAME)
        # check the aggregation meta xml files exist in iRODS
        self._test_aggr_meta_files(cmp_res, aggr_folder_path=self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.files.count(), 1)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        # check that the resource level keywords copied over to the aggregation
        self.assertEqual(cmp_res.metadata.subjects.count(), 2)
        self.assertEqual(len(mp_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # test that the resource file is set to documentation
        mp_file_type = ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).first()
        self.assertEqual(mp_file_type.file_type, ModelProgramResourceFileType.DOCUMENTATION)
        self.assertEqual(mp_file_type.res_file, mp_aggr.files.first())

    def test_migrate_mp_resource_with_folder_2(self):
        """
        Migrate a mp resource that has 2 folders each containing a file
        When converted to composite resource, it should have a mp aggregation (based on the folder)
        and should have aggregation level metadata. The original 2 folders will be moved into the new aggregation folder
        """

        # create a mp resource
        mp_res = self._create_mp_resource(add_keywords=True)
        self.assertEqual(mp_res.metadata.subjects.count(), 2)
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)

        # upload a file to mp resource
        file_path = 'hs_core/tests/data/test.txt'
        upload_folder_1 = 'folder-1'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder_1)
        upload_folder_2 = 'folder-2'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder_2)

        self.assertEqual(mp_res.files.count(), 2)
        # create Model program metadata
        mp_res.metadata.create_element('MpMetadata', modelVersion='5.1.011', modelReleaseNotes='test.txt')

        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mp aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 2)
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check the res files moved to the mp aggregation folder
        expected_file_folders = ["{}/{}".format(self.MP_FOLDER_NAME, upload_folder_1),
                                 "{}/{}".format(self.MP_FOLDER_NAME, upload_folder_2)]
        for res_file in cmp_res.files.all():
            self.assertIn(res_file.file_folder, expected_file_folders)
        res_file_1 = cmp_res.files.all()[0]
        res_file_2 = cmp_res.files.all()[1]
        self.assertNotEqual(res_file_1.file_folder, res_file_2.file_folder)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.aggregation_name, self.MP_FOLDER_NAME)
        # check the aggregation meta xml files exist in iRODS
        self._test_aggr_meta_files(cmp_res, aggr_folder_path=self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.files.count(), 2)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        # check that the resource level keywords copied over to the aggregation
        self.assertEqual(cmp_res.metadata.subjects.count(), 2)
        self.assertEqual(len(mp_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # test that the resource file is set to release notes
        self.assertEqual(ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).count(), 1)
        mp_file_type = ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).first()
        self.assertEqual(mp_file_type.file_type, ModelProgramResourceFileType.RELEASE_NOTES)
        for aggr_res_file in mp_aggr.files.all():
            if mp_file_type.res_file.short_path == aggr_res_file.short_path:
                self.assertEqual(mp_file_type.res_file, aggr_res_file)
            else:
                self.assertNotEqual(mp_file_type.res_file, aggr_res_file)

    def test_migrate_mp_resource_with_folder_3(self):
        """
        Migrate a mp resource that has 2 folders - one folder contains a file the other one is empty
        When converted to composite resource, it should have a mp aggregation (based on the folder)
        and should have aggregation level metadata. The original folder that has a file will be moved into the
        new aggregation folder. The other empty folder will not be part of the mp aggregation.
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
        upload_folder_1 = 'folder-1'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder_1)
        upload_folder_2 = 'folder-2'
        ResourceFile.create_folder(mp_res, upload_folder_2)

        self.assertEqual(mp_res.files.count(), 1)
        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mp aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 1)
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check the res files moved to the mp aggregation folder
        res_file = cmp_res.files.first()
        expected_file_folder = "{}/{}".format(self.MP_FOLDER_NAME, upload_folder_1)
        self.assertEqual(res_file.file_folder, expected_file_folder)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.aggregation_name, self.MP_FOLDER_NAME)
        # check the aggregation meta xml files exist in iRODS
        self._test_aggr_meta_files(cmp_res, aggr_folder_path=self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.files.count(), 1)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        # check that the resource level keywords copied over to the aggregation
        self.assertEqual(cmp_res.metadata.subjects.count(), 2)
        self.assertEqual(len(mp_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # test no mp files types are created
        self.assertEqual(ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).count(), 0)

    def test_migrate_mp_resource_with_folder_4(self):
        """
        Migrate a mp resource that has a readme file and one folder that contains a file
        When converted to composite resource, it should have a mp aggregation (based on the folder)
        and should have aggregation level metadata. The original folder that has a file will be moved into the
        new aggregation folder. The readme file won't be part of the mp aggregation.
        """

        # create a mp resource
        mp_res = self._create_mp_resource(add_keywords=True)
        self.assertEqual(mp_res.metadata.subjects.count(), 2)
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model program metadata
        mp_res.metadata.create_element('MpMetadata', modelVersion='5.1.011')
        # upload a readme file to mp resource
        file_path = 'hs_core/tests/data/readme.txt'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))
        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder)
        # upload a file to mp resource folder
        file_path = 'hs_core/tests/data/test.txt'
        upload_folder_1 = 'folder-1'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder_1)

        self.assertEqual(mp_res.files.count(), 2)
        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mp aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 2)
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        # there should one mp aggregation that has one resource file
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check the res files moved to the mp aggregation folder
        # check the folder for each of the files in composite resource
        for res_file in cmp_res.files.all():
            if res_file.file_name == 'readme.txt':
                self.assertEqual(res_file.file_folder, "")
            else:
                expected_file_folder = "{}/{}".format(self.MP_FOLDER_NAME, upload_folder_1)
                self.assertEqual(res_file.file_folder, expected_file_folder)

        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.aggregation_name, self.MP_FOLDER_NAME)
        # check the aggregation meta xml files exist in iRODS
        self._test_aggr_meta_files(cmp_res, aggr_folder_path=self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.files.count(), 1)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        # check that the resource level keywords copied over to the aggregation
        self.assertEqual(cmp_res.metadata.subjects.count(), 2)
        self.assertEqual(len(mp_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # test no mp files types are created
        self.assertEqual(ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).count(), 0)

    def test_migrate_mp_resource_with_folder_5(self):
        """
        Migrate a mp resource that has 3 folders - one folder contains a file the other one is a nested folder (both
        parent and child each has a file)
        When converted to composite resource, it should have a mp aggregation (based on the folder)
        and should have aggregation level metadata. The original 3 folders will be moved into the
        new aggregation folder.
        """

        # create a mp resource
        mp_res = self._create_mp_resource(add_keywords=True)
        self.assertEqual(mp_res.metadata.subjects.count(), 2)
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model program metadata
        mp_res.metadata.create_element('MpMetadata', modelVersion='5.1.011')
        # upload a file to mp resource 'data' folder
        file_path = 'hs_core/tests/data/test.txt'
        upload_folder_1 = 'data'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder_1)
        # upload a file to mp resource 'contents' folder
        file_path = 'hs_core/tests/data/cea.tif'
        upload_folder_2 = 'contents'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))
        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder_2)

        # upload a file to mp resource 'contents/data' folder
        file_path = 'hs_core/tests/data/netcdf_valid.nc'
        upload_folder_3 = 'contents/data'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))
        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder_3)

        self.assertEqual(mp_res.files.count(), 3)
        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mp aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 3)
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)

        # check the res files moved to the mp aggregation folder
        # check the folder for each of the files in composite resource
        for res_file in cmp_res.files.all():
            if res_file.file_name == 'test.txt':
                expected_file_folder = "{}/{}".format(self.MP_FOLDER_NAME, upload_folder_1)
            elif res_file.file_name == 'cea.tif':
                expected_file_folder = "{}/{}".format(self.MP_FOLDER_NAME, upload_folder_2)
            else:
                expected_file_folder = "{}/{}".format(self.MP_FOLDER_NAME, upload_folder_3)

            self.assertEqual(res_file.file_folder, expected_file_folder)

        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.aggregation_name, self.MP_FOLDER_NAME)
        # check the aggregation meta xml files exist in iRODS
        self._test_aggr_meta_files(cmp_res, aggr_folder_path=self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.files.count(), 3)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        # check that the resource level keywords copied over to the aggregation
        self.assertEqual(cmp_res.metadata.subjects.count(), 2)
        self.assertEqual(len(mp_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # test no mp files types are created
        self.assertEqual(ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).count(), 0)

    def test_migrate_mp_resource_with_folder_6(self):
        """
        Migrate a mp resource that has only one file in a folder. The folder name is 'model-program'
        When converted to composite resource, it should have a mp aggregation (based on the folder)
        and should have aggregation level metadata. The original folder will be moved into the new aggregation folder.
        The newly created aggregation folder name should be 'model-program-1'
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
        upload_folder = 'folder-1'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mp_res.files.count(), 1)
        ResourceFile.create_folder(mp_res, folder='model-program')
        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mp aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 1)
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check the res file moved to the mp aggregation folder
        res_file = cmp_res.files.first()
        expected_file_folder = "{}-1/{}".format(self.MP_FOLDER_NAME, upload_folder)
        self.assertEqual(res_file.file_folder, expected_file_folder)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        expected_aggr_folder_name = "{}-1".format(self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.folder, expected_aggr_folder_name)
        self.assertEqual(mp_aggr.aggregation_name, expected_aggr_folder_name)
        # check the aggregation meta xml files exist in iRODS
        self._test_aggr_meta_files(cmp_res, aggr_folder_path=expected_aggr_folder_name)
        self.assertEqual(mp_aggr.files.count(), 1)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        # check that the resource level keywords copied over to the aggregation
        self.assertEqual(cmp_res.metadata.subjects.count(), 2)
        self.assertEqual(len(mp_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # test no mp files types are created
        self.assertEqual(ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).count(), 0)

    def test_migrate_mp_resource_missing_file_in_irods(self):
        """
        Migrate a mp resource that has 2 files in db but only one file in iRODS
        When converted to composite resource, it should have a mp aggregation (based on the folder)
        and should have aggregation level metadata. Only the resource file that is in iRODS will be part of the
        mp aggregation.
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
        text_res_file = mp_res.files.first()

        file_path = 'hs_core/tests/data/cea.tif'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder)

        self.assertEqual(mp_res.files.count(), 2)
        # delete the text file from iRODS
        istorage = mp_res.get_irods_storage()
        istorage.delete(text_res_file.public_path)

        # as pre the DB the MP resource still have 2 files
        self.assertEqual(mp_res.files.count(), 2)

        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mp aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 2)
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        # there should one mp aggregation containing only one resource file (tif file)
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check the res file moved to the mp aggregation folder
        for res_file in cmp_res.files.all():
            if res_file.file_name == 'cea.tif':
                self.assertEqual(res_file.file_folder, self.MP_FOLDER_NAME)

        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.aggregation_name, self.MP_FOLDER_NAME)
        # check the aggregation meta xml files exist in iRODS
        self._test_aggr_meta_files(cmp_res, aggr_folder_path=self.MP_FOLDER_NAME)
        # check that the file that exists in iRODS is part of the mp aggregation and the file that is
        # missing in iRODS is not part of the mp aggregation
        self.assertEqual(mp_aggr.files.count(), 1)
        aggr_res_file = mp_aggr.files.first()
        self.assertEqual(aggr_res_file.file_name, 'cea.tif')
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        # check that the resource level keywords copied over to the aggregation
        self.assertEqual(cmp_res.metadata.subjects.count(), 2)
        self.assertEqual(len(mp_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # test no mp files types are created
        self.assertEqual(ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).count(), 0)

    def test_migrate_mp_resource_with_mp_file_types_1(self):
        """
        Migrate a mp resource that has 1 folder containing a file  and another file at the root level.
        Both files are set to mp file types.
        When converted to composite resource, it should have a mp aggregation (based on the folder)
        and should have aggregation level metadata. The original folder will be moved into the new aggregation folder
        and each of the resource files will also be set to original mp file types
        """

        # create a mp resource
        mp_res = self._create_mp_resource(add_keywords=True)
        self.assertEqual(mp_res.metadata.subjects.count(), 2)
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)

        # upload a file to mp resource
        file_path = 'hs_core/tests/data/test.txt'
        upload_folder_1 = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder_1)
        file_path = 'hs_core/tests/data/cea.tif'
        upload_folder_2 = 'folder-1'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder_2)

        self.assertEqual(mp_res.files.count(), 2)
        # create Model program metadata
        mp_res.metadata.create_element('MpMetadata', modelVersion='5.1.011', modelReleaseNotes='test.txt',
                                       modelSoftware='cea.tif')

        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mp aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 2)
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check the res files moved to the mp aggregation folder
        expected_file_folders = [self.MP_FOLDER_NAME,
                                 "{}/{}".format(self.MP_FOLDER_NAME, upload_folder_2)]
        for res_file in cmp_res.files.all():
            self.assertIn(res_file.file_folder, expected_file_folders)
        res_file_1 = cmp_res.files.all()[0]
        res_file_2 = cmp_res.files.all()[1]
        self.assertNotEqual(res_file_1.file_folder, res_file_2.file_folder)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.aggregation_name, self.MP_FOLDER_NAME)
        # check the aggregation meta xml files exist in iRODS
        self._test_aggr_meta_files(cmp_res, aggr_folder_path=self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.files.count(), 2)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        # check that the resource level keywords copied over to the aggregation
        self.assertEqual(cmp_res.metadata.subjects.count(), 2)
        self.assertEqual(len(mp_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # test that the resource files are set to mp file types
        self.assertEqual(ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).count(), 2)
        for mp_file_type in ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).all():
            if mp_file_type.res_file.file_folder == "model-program":
                self.assertEqual(mp_file_type.file_type, ModelProgramResourceFileType.RELEASE_NOTES)
            else:
                self.assertEqual(mp_file_type.res_file.file_folder, "model-program/folder-1")
                self.assertEqual(mp_file_type.file_type, ModelProgramResourceFileType.SOFTWARE)

    def test_migrate_mp_resource_with_mp_file_types_2(self):
        """
        Migrate a mp resource that has 2 folders each containing a file (specified as mp file types)
        When converted to composite resource, it should have a mp aggregation (based on the folder)
        and should have aggregation level metadata. The original 2 folders will be moved into the new aggregation folder
        and each of the resource files will also be set to original mp file types
        """

        # create a mp resource
        mp_res = self._create_mp_resource(add_keywords=True)
        self.assertEqual(mp_res.metadata.subjects.count(), 2)
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)

        # upload a file to mp resource
        file_path = 'hs_core/tests/data/test.txt'
        upload_folder_1 = 'folder-1'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder_1)
        file_path = 'hs_core/tests/data/cea.tif'
        upload_folder_2 = 'folder-2'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder_2)

        self.assertEqual(mp_res.files.count(), 2)
        # create Model program metadata
        release_note_file_path = "{}/data/contents/test.txt".format(mp_res.short_id)
        mp_res.metadata.create_element('MpMetadata', modelVersion='5.1.011', modelReleaseNotes=release_note_file_path,
                                       modelSoftware='folder-2/cea.tif')

        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mp aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 2)
        self.assertEqual(mp_res.short_id, cmp_res.short_id)
        # there should one mp aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # check the res files moved to the mp aggregation folder
        expected_file_folders = ["{}/{}".format(self.MP_FOLDER_NAME, upload_folder_1),
                                 "{}/{}".format(self.MP_FOLDER_NAME, upload_folder_2)]
        for res_file in cmp_res.files.all():
            self.assertIn(res_file.file_folder, expected_file_folders)
        res_file_1 = cmp_res.files.all()[0]
        res_file_2 = cmp_res.files.all()[1]
        self.assertNotEqual(res_file_1.file_folder, res_file_2.file_folder)
        # check mp aggregation is folder based
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.aggregation_name, self.MP_FOLDER_NAME)
        # check the aggregation meta xml files exist in iRODS
        self._test_aggr_meta_files(cmp_res, aggr_folder_path=self.MP_FOLDER_NAME)
        self.assertEqual(mp_aggr.files.count(), 2)
        self.assertEqual(mp_aggr.metadata.version, '5.1.011')
        # check that the resource level keywords copied over to the aggregation
        self.assertEqual(cmp_res.metadata.subjects.count(), 2)
        self.assertEqual(len(mp_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # test that the resource files are set to mp file types
        self.assertEqual(ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).count(), 2)
        for mp_file_type in ModelProgramResourceFileType.objects.filter(mp_metadata=mp_aggr.metadata).all():
            if mp_file_type.res_file.file_folder == "model-program/folder-1":
                self.assertEqual(mp_file_type.file_type, ModelProgramResourceFileType.RELEASE_NOTES)
            else:
                self.assertEqual(mp_file_type.res_file.file_folder, "model-program/folder-2")
                self.assertEqual(mp_file_type.file_type, ModelProgramResourceFileType.SOFTWARE)

    def _test_aggr_meta_files(self, cmp_res, aggr_folder_path):
        # check the aggregation meta xml files exist in iRODS
        istorage = cmp_res.get_irods_storage()
        aggr_meta_file_path = os.path.join(cmp_res.file_path, aggr_folder_path,
                                           "{}_meta.xml".format(aggr_folder_path))
        self.assertTrue(istorage.exists(aggr_meta_file_path))
        aggr_map_file_path = os.path.join(cmp_res.file_path, aggr_folder_path,
                                          "{}_resmap.xml".format(aggr_folder_path))
        self.assertTrue(istorage.exists(aggr_map_file_path))

    def _create_mp_resource(self, add_keywords=False):
        mp_res = hydroshare.create_resource("ModelProgramResource", self.user,
                                            "Testing migrating to composite resource")
        if add_keywords:
            mp_res.metadata.create_element('subject', value='kw-1')
            mp_res.metadata.create_element('subject', value='kw-2')
        return mp_res
