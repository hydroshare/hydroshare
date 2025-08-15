import uuid
from unittest import mock
from django.test import TestCase
from django_s3.utils import bucket_and_name
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from hs_core import hydroshare
from hs_core.models import BaseResource
from django_s3.views import CustomTusFile


class TestCustomTusFile(TestCase):

    def setUp(self):
        self.username = 'testuser'
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            f'{self.username}@email.com',
            username=self.username + uuid.uuid4().hex,  # to ensure unique bucket in minio
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[self.group]
        )

        self.res = hydroshare.create_resource(resource_type='CompositeResource',
                                              owner=self.user,
                                              title='My Test Resource ' * 10,
                                              keywords=('a', 'b', 'c'))
        self.res.metadata.create_element("description", abstract="new abstract for the resource " * 10)
        bucket, _ = bucket_and_name(self.res.short_id)

        self.metadata = {
            "filename": "test1.txt",
            "path": "test1.txt",
            "hs_res_id": self.res.short_id,
            "bucket": bucket,
        }
        self.file_size = 1024  # 1 KB for testing

    def tearDown(self):
        super(TestCustomTusFile, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        BaseResource.objects.all().delete()
        Group.objects.all().delete()

    def test_create_initial_file_sets_cache(self):
        tus_file = CustomTusFile.create_initial_file(self.metadata, self.file_size)
        self.assertEqual(tus_file.filename, self.metadata["filename"])
        self.assertEqual(tus_file.file_size, self.file_size)
        self.assertEqual(tus_file.path, self.metadata["path"])

        filename = cache.get("tus-uploads/{}/filename".format(tus_file.resource_id))
        self.assertEqual(filename, self.metadata["filename"])
        path = cache.get("tus-uploads/{}/path".format(tus_file.resource_id))
        self.assertEqual(path, self.metadata["path"])

    def test_check_existing_file_true(self):
        with mock.patch("django_s3.views.S3Storage.exists", return_value=True):
            self.assertTrue(CustomTusFile.check_existing_file("some/path"))

    def test_check_existing_file_false(self):
        with mock.patch("django_s3.views.S3Storage.exists", return_value=False):
            self.assertFalse(CustomTusFile.check_existing_file("some/path"))

    @mock.patch.object(CustomTusFile, "initiate_multipart_upload")
    def test_is_valid_true(self, _):
        tus_file = CustomTusFile.create_initial_file(self.metadata, self.file_size)
        self.assertTrue(tus_file.is_valid())

    def test_is_valid_false(self):
        tus_file = CustomTusFile.__new__(CustomTusFile)
        tus_file.filename = None
        self.assertFalse(tus_file.is_valid())

    def test_upload_part(self):
        tus_file = CustomTusFile.create_initial_file(self.metadata, 13)

        chunk = mock.Mock()
        chunk.content = b'data'
        chunk.chunk_size = 4
        chunk.content_length = 4

        tus_file.upload_part(chunk)

        # Check that part was appended
        self.assertEqual(tus_file.parts[0].get('PartNumber'), 1)
        self.assertEqual(tus_file.part_number, 2)
        self.assertEqual(tus_file.offset, 4)

        # upload another chunk
        chunk.content = b'more data'
        chunk.chunk_size = 9
        chunk.content_length = 9
        tus_file.upload_part(chunk)
        # Check that part was appended
        self.assertEqual(tus_file.parts[1].get('PartNumber'), 2)
        self.assertEqual(tus_file.part_number, 3)
        self.assertEqual(tus_file.offset, 13)
        # Check that the file size is correct
        self.assertEqual(tus_file.file_size, 13)
