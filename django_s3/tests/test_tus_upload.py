import base64
import uuid
from unittest import mock

from django.contrib.auth.models import AnonymousUser, User, Group
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.test import Client, RequestFactory, TestCase

from hs_access_control.models import PrivilegeCodes

from hs_core import hydroshare
from hs_core.models import BaseResource
from django_s3.views import CustomTusUpload
import os


class CustomTusUploadTests(TestCase):
    def fake_metadata(self):
        return {
            "filename": "test.txt",
            "hs_res_id": self.res.short_id,
            "username": self.user.username,
            "path": f"{self.res.short_id}/data/contents/test.txt",
            "file_size": str(self.file_size),
        }

    def create_request_metadata(self, request):
        # https://github.com/alican/django-tus/blob/2aac2e7c0e6bac79a1cb07721947a48d9cc40ec8/django_tus/views.py#L38

        # build the HTTP_UPLOAD_METADATA string as comma and space separated key-value pairs
        metadata = self.fake_metadata()
        encoded_metadata = ",".join(
            f"{key} {base64.b64encode(value.encode()).decode('utf-8')}" if isinstance(value, str) else f"{key} {value}"
            for key, value in metadata.items()
        )
        request.META["HTTP_UPLOAD_METADATA"] = encoded_metadata
        request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        request.META["HTTP_CONTENT_LENGTH"] = str(self.file_size)

    def initial_post(self):
        post_request = self.factory.post("/")
        post_request.user = self.user
        self.create_request_metadata(post_request)
        post_view = CustomTusUpload()
        post_view.request = post_request
        return post_view.post(post_request)

    def setUp(self):
        self.factory = RequestFactory()
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
        # create file
        self.n1 = "test.txt"

        test_file = open(self.n1, 'w')
        test_file.write("Test text file in test.txt")
        self.file_size = os.path.getsize(self.n1)
        test_file.close()

        # open files for read and upload
        self.myfile1 = open(self.n1, "rb")

        self.res = hydroshare.create_resource(resource_type='CompositeResource',
                                              owner=self.user,
                                              title='My Test Resource ' * 10,
                                              keywords=('a', 'b', 'c'))
        self.res.metadata.create_element("description", abstract="new abstract for the resource " * 10)
        self.res.save()
        self.client = Client()

    def tearDown(self):
        super(CustomTusUploadTests, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        BaseResource.objects.all().delete()
        Group.objects.all().delete()
        self.myfile1.close()
        os.remove(self.myfile1.name)

    def test_patch_marks_resource_modified_on_completion(self):
        """Test that PATCH marks resource as modified when upload completes"""
        post_response = self.initial_post()
        self.assertEqual(post_response.status_code, 201)

        # get the resource_id from the response
        resource_id = post_response.headers.get("Location").split("/")[-1]

        # Store original modified date
        original_modified_date = self.res.metadata.dates.filter(type='modified').first()
        _ = self.res.last_updated

        # Now PATCH to upload the complete file
        self.myfile1.seek(0)
        file_content = self.myfile1.read()
        patch_request = self.factory.patch("/", data=file_content, content_type="application/offset+octet-stream")
        patch_request.user = self.user
        patch_request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        patch_request.META["HTTP_UPLOAD_OFFSET"] = "0"
        patch_request.META["HTTP_CONTENT_LENGTH"] = str(len(file_content))
        self.create_request_metadata(patch_request)
        patch_view = CustomTusUpload()
        patch_view.request = patch_request
        patch_view.kwargs = {'resource_id': resource_id}

        # Mock the async task to avoid celery dependency in tests
        with mock.patch("django_s3.views.set_resource_files_system_metadata.apply_async") as mock_async:
            resp = patch_view.patch(patch_request, resource_id)
            self.assertEqual(resp.status_code, 204)

            # Refresh resource from database
            self.res.refresh_from_db()

            # Verify resource was modified
            new_modified_date = self.res.metadata.dates.filter(type='modified').first()
            self.assertIsNotNone(new_modified_date)

            # The modified date should be updated (can't compare exact times due to test speed)
            self.assertNotEqual(original_modified_date.start_date, new_modified_date.start_date)

            # Verify last_changed_by is set correctly
            self.assertEqual(self.res.last_changed_by, self.user)

            # Verify last_updated matches the modified date
            self.assertEqual(self.res.last_updated, new_modified_date.start_date)

            # Verify async task was called
            mock_async.assert_called_once_with((self.res.short_id,))

    def test_patch_calls_resource_modified_function(self):
        """Test that resource_modified function is called on upload completion"""
        post_response = self.initial_post()
        self.assertEqual(post_response.status_code, 201)

        # get the resource_id from the response
        resource_id = post_response.headers.get("Location").split("/")[-1]

        # Now PATCH to upload the complete file
        self.myfile1.seek(0)
        file_content = self.myfile1.read()
        patch_request = self.factory.patch("/", data=file_content, content_type="application/offset+octet-stream")
        patch_request.user = self.user
        patch_request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        patch_request.META["HTTP_UPLOAD_OFFSET"] = "0"
        patch_request.META["HTTP_CONTENT_LENGTH"] = str(len(file_content))
        self.create_request_metadata(patch_request)
        patch_view = CustomTusUpload()
        patch_view.request = patch_request
        patch_view.kwargs = {'resource_id': resource_id}

        # Mock both the resource_modified function and async task
        with mock.patch("django_s3.views.resource_modified") as mock_resource_modified, \
             mock.patch("django_s3.views.set_resource_files_system_metadata.apply_async") as mock_async:

            resp = patch_view.patch(patch_request, resource_id)
            self.assertEqual(resp.status_code, 204)

            # Verify resource_modified was called with correct parameters
            mock_resource_modified.assert_called_once_with(
                self.res, 
                self.user, 
                overwrite_bag=False
            )

            # Verify async task was called
            mock_async.assert_called_once_with((self.res.short_id,))

    def test_partial_patch_does_not_mark_resource_modified(self):
        """Test that partial PATCH (incomplete upload) doesn't mark resource as modified"""
        post_response = self.initial_post()
        self.assertEqual(post_response.status_code, 201)

        # get the resource_id from the response
        resource_id = post_response.headers.get("Location").split("/")[-1]

        # Store original modified date
        _ = self.res.metadata.dates.filter(type='modified').first()

        # PATCH with only part of the file (incomplete upload)
        self.myfile1.seek(0)
        partial_content = self.myfile1.read(10)  # Only read first 10 bytes
        patch_request = self.factory.patch("/", data=partial_content, content_type="application/offset+octet-stream")
        patch_request.user = self.user
        patch_request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        patch_request.META["HTTP_UPLOAD_OFFSET"] = "0"
        patch_request.META["HTTP_CONTENT_LENGTH"] = str(len(partial_content))
        self.create_request_metadata(patch_request)
        patch_view = CustomTusUpload()
        patch_view.request = patch_request
        patch_view.kwargs = {'resource_id': resource_id}

        # Mock the functions to ensure they're not called
        with mock.patch("django_s3.views.resource_modified") as mock_resource_modified, \
             mock.patch("django_s3.views.set_resource_files_system_metadata.apply_async") as mock_async:

            resp = patch_view.patch(patch_request, resource_id)
            # Should be 204 even for partial upload
            self.assertEqual(resp.status_code, 204)

            # Verify resource_modified was NOT called (upload not complete)
            mock_resource_modified.assert_not_called()

            # Verify async task was NOT called
            mock_async.assert_not_called()

    def test_resource_modified_called_with_correct_user(self):
        """Test that resource_modified is called with the correct user"""
        post_response = self.initial_post()
        self.assertEqual(post_response.status_code, 201)

        # get the resource_id from the response
        resource_id = post_response.headers.get("Location").split("/")[-1]

        # Create a different user who has edit permissions
        other_user = hydroshare.create_account(
            'otheruser@email.com',
            username='otheruser',
            first_name='Other',
            last_name='User',
            superuser=False,
            groups=[]
        )
        self.user.uaccess.share_resource_with_user(self.res, other_user, PrivilegeCodes.CHANGE)

        # Now PATCH to upload the complete file as the other user
        self.myfile1.seek(0)
        file_content = self.myfile1.read()
        patch_request = self.factory.patch("/", data=file_content, content_type="application/offset+octet-stream")
        patch_request.user = other_user  # Different user making the upload
        patch_request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        patch_request.META["HTTP_UPLOAD_OFFSET"] = "0"
        patch_request.META["HTTP_CONTENT_LENGTH"] = str(len(file_content))
        self.create_request_metadata(patch_request)
        patch_view = CustomTusUpload()
        patch_view.request = patch_request
        patch_view.kwargs = {'resource_id': resource_id}

        # Mock to verify correct user is passed
        with mock.patch("django_s3.views.resource_modified") as mock_resource_modified, \
             mock.patch("django_s3.views.set_resource_files_system_metadata.apply_async"):

            resp = patch_view.patch(patch_request, resource_id)
            self.assertEqual(resp.status_code, 204)

            # Verify resource_modified was called with the correct user (the one making the request)
            mock_resource_modified.assert_called_once_with(
                self.res, 
                other_user,  # Should be the user who made the upload request
                overwrite_bag=False
            )

    def test_post_returns_expected_metadata(self):
        view = CustomTusUpload()
        request = self.factory.post("/")
        request.user = self.user
        request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        request.META["HTTP_UPLOAD_LENGTH"] = "123"
        self.create_request_metadata(request)
        view.request = request
        view.kwargs = {'resource_id': self.res.short_id}

        resp = view.dispatch(request)
        self.assertEqual(resp.status_code, 201)
        self.assertIn("Tus-Resumable", resp.headers)

    def test_post_returns_201_on_success(self):
        view = CustomTusUpload()
        request = self.factory.post("/")
        request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        request.META["HTTP_UPLOAD_LENGTH"] = "123"
        self.create_request_metadata(request)
        view.request = request
        view.kwargs = {'resource_id': self.res.short_id}

        resp = view.post(request)
        self.assertEqual(resp.status_code, 201)
        self.assertIn("Tus-Resumable", resp.headers)
        self.assertIn("Location", resp.headers)

    def test_patch_returns_204_on_success(self):
        post_response = self.initial_post()
        self.assertEqual(post_response.status_code, 201)

        # get the resource_id from the response
        resource_id = post_response.headers.get("Location").split("/")[-1]

        # Now PATCH to upload the chunk
        self.myfile1.seek(0)
        file_content = self.myfile1.read()
        patch_request = self.factory.patch("/", data=file_content, content_type="application/offset+octet-stream")
        patch_request.user = self.user
        patch_request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        patch_request.META["HTTP_UPLOAD_OFFSET"] = "0"
        self.create_request_metadata(patch_request)
        patch_view = CustomTusUpload()
        patch_view.request = patch_request
        patch_view.kwargs = {'resource_id': resource_id}

        resp = patch_view.patch(patch_request, resource_id)
        self.assertEqual(resp.status_code, 204)

    def test_that_user_with_edit_permission_on_resource_can_post(self):
        view = CustomTusUpload()
        request = self.factory.post("/")

        # create a new user to make the request
        self.user2 = hydroshare.create_account(
            'testuser2@email.com',
            username='testuser2',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[]
        )
        self.user.uaccess.share_resource_with_user(self.res, self.user2, PrivilegeCodes.CHANGE)

        request.user = self.user2
        request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        request.META["HTTP_UPLOAD_LENGTH"] = "123"
        self.create_request_metadata(request)
        view.request = request
        view.kwargs = {'resource_id': self.res.short_id}

        resp = view.dispatch(request)
        self.assertEqual(resp.status_code, 201)

    def test_dispatch_returns_403_for_non_editor(self):
        view = CustomTusUpload()
        request = self.factory.get("/")
        # create a new user to make the request
        self.user2 = hydroshare.create_account(
            'testuser2@email.com',
            username='testuser2',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[]
        )

        request.user = self.user2
        request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        request.META["HTTP_UPLOAD_LENGTH"] = "123"
        self.create_request_metadata(request)
        view.request = request
        view.kwargs = {'resource_id': self.res.short_id}

        view.kwargs = {'resource_id': self.res.short_id}
        resp = view.dispatch()
        self.assertIsInstance(resp, HttpResponseForbidden)

        resp = view.dispatch()
        self.assertIsInstance(resp, HttpResponseForbidden)

    def test_dispatch_returns_403_if_anonymous_user_with_no_permissions(self):
        view = CustomTusUpload()
        factory = RequestFactory()
        request = factory.post("/")
        request.META["HTTP_UPLOAD_LENGTH"] = "123"
        self.create_request_metadata(request)

        request.user = AnonymousUser()
        view.request = request
        view.kwargs = {'resource_id': self.res.short_id}

        resp = view.dispatch()
        self.assertIsInstance(resp, HttpResponseForbidden)

    def test_dispatch_returns_404_if_no_metadata_and_no_tusfile(self):
        view = CustomTusUpload()
        request = self.factory.get("/")
        view.request = request
        view.kwargs = {'resource_id': self.res.short_id}
        resp = view.dispatch()
        self.assertIsInstance(resp, HttpResponseNotFound)
        self.assertIn("Error in getting metadata", resp.content.decode())

    def test_patch_returns_404_if_invalid_resource_id(self):
        post_response = self.initial_post()
        self.assertEqual(post_response.status_code, 201)

        # read the file content
        file_content = self.myfile1.read()
        self.myfile1.seek(0)

        # Now PATCH with a resource_id that does not exist (simulate invalid file)
        patch_request = self.factory.patch("/", data=file_content, content_type="application/offset+octet-stream")
        patch_request.user = self.user
        patch_request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        patch_request.META["HTTP_UPLOAD_OFFSET"] = "0"
        patch_request.META["HTTP_CONTENT_LENGTH"] = str(len(file_content))
        self.create_request_metadata(patch_request)
        patch_view = CustomTusUpload()
        patch_view.request = patch_request
        patch_view.kwargs = {'resource_id': "invalid"}  # intentionally invalid resource_id

        resp = patch_view.patch(patch_request, "invalid")
        self.assertEqual(resp.status_code, 404)

    def test_patch_returns_409_if_offset_mismatch(self):
        post_response = self.initial_post()
        self.assertEqual(post_response.status_code, 201)

        # get the resource_id from the response
        resource_id = post_response.headers.get("Location").split("/")[-1]
        self.assertEqual(post_response.status_code, 201)

        # read the file content
        file_content = self.myfile1.read()
        self.myfile1.seek(0)

        # Now PATCH with an offset mismatch (offset != file offset)
        patch_request = self.factory.patch("/", data=file_content[:3], content_type="application/offset+octet-stream")
        patch_request.user = self.user
        patch_request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        patch_request.META["HTTP_UPLOAD_OFFSET"] = "5"  # mismatch: should be 0
        patch_request.META["HTTP_CONTENT_LENGTH"] = str(len(file_content[:3]))
        self.create_request_metadata(patch_request)
        patch_view = CustomTusUpload()
        patch_view.request = patch_request
        patch_view.kwargs = {'resource_id': resource_id}

        resp = patch_view.patch(patch_request, resource_id)
        self.assertEqual(resp.status_code, 409)

    def test_patch_returns_409_if_offset_too_large(self):
        post_response = self.initial_post()
        self.assertEqual(post_response.status_code, 201)

        # get the resource_id from the response
        resource_id = post_response.headers.get("Location").split("/")[-1]

        # read the file content
        file_content = self.myfile1.read()
        self.myfile1.seek(0)

        # Now PATCH with an offset that is too large (offset > file_size)
        patch_request = self.factory.patch("/", data=file_content, content_type="application/offset+octet-stream")
        patch_request.user = self.user
        patch_request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        patch_request.META["HTTP_UPLOAD_OFFSET"] = str(len(file_content) + 10)  # offset too large
        patch_request.META["HTTP_CONTENT_LENGTH"] = str(len(file_content))
        self.create_request_metadata(patch_request)
        patch_view = CustomTusUpload()
        patch_view.request = patch_request
        patch_view.kwargs = {'resource_id': resource_id}

        resp = patch_view.patch(patch_request, resource_id)
        self.assertEqual(resp.status_code, 409)

    def test_post_returns_500_if_existing_file_keep(self):
        post_response = self.initial_post()
        self.assertEqual(post_response.status_code, 201)

        # get the resource_id from the response
        resource_id = post_response.headers.get("Location").split("/")[-1]

        # Now PATCH to upload the chunk
        self.myfile1.seek(0)
        file_content = self.myfile1.read()
        patch_request = self.factory.patch("/", data=file_content, content_type="application/offset+octet-stream")
        patch_request.user = self.user
        patch_request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        patch_request.META["HTTP_UPLOAD_OFFSET"] = "0"
        self.create_request_metadata(patch_request)
        patch_view = CustomTusUpload()
        patch_view.request = patch_request
        patch_view.kwargs = {'resource_id': resource_id}

        resp = patch_view.patch(patch_request, resource_id)
        self.assertEqual(resp.status_code, 204)

        # Now try to POST the same file again
        with mock.patch("django_s3.views.settings", mock.Mock(TUS_EXISTING_FILE='error',
                                                              TUS_FILE_NAME_FORMAT='keep')):
            post_response2 = self.initial_post()
            self.assertEqual(post_response2.status_code, 500)

    def test_post_returns_500_if_existing_file_increment(self):
        post_response = self.initial_post()
        self.assertEqual(post_response.status_code, 201)

        # get the resource_id from the response
        resource_id = post_response.headers.get("Location").split("/")[-1]

        # Now PATCH to upload the chunk
        self.myfile1.seek(0)
        file_content = self.myfile1.read()
        patch_request = self.factory.patch("/", data=file_content, content_type="application/offset+octet-stream")
        patch_request.user = self.user
        patch_request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        patch_request.META["HTTP_UPLOAD_OFFSET"] = "0"
        self.create_request_metadata(patch_request)
        patch_view = CustomTusUpload()
        patch_view.request = patch_request
        patch_view.kwargs = {'resource_id': resource_id}

        resp = patch_view.patch(patch_request, resource_id)
        self.assertEqual(resp.status_code, 204)

        # Now try to POST the same file again
        with mock.patch("django_s3.views.settings", mock.Mock(TUS_EXISTING_FILE='increment',
                                                              TUS_FILE_NAME_FORMAT='keep')):
            post_response2 = self.initial_post()
            print(post_response2)
            self.assertEqual(post_response2.status_code, 500)

    def test_patch_returns_409_if_offset_larger_than_file_size(self):
        post_response = self.initial_post()
        self.assertEqual(post_response.status_code, 201)

        # get the resource_id from the response
        resource_id = post_response.headers.get("Location").split("/")[-1]

        # read the file content
        file_content = self.myfile1.read()
        self.myfile1.seek(0)

        # Now PATCH with an offset larger than file size
        patch_request = self.factory.patch("/", data=file_content, content_type="application/offset+octet-stream")
        patch_request.user = self.user
        patch_request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        patch_request.META["HTTP_UPLOAD_OFFSET"] = str(len(file_content) + 5)  # offset larger than file size
        patch_request.META["HTTP_CONTENT_LENGTH"] = str(len(file_content))
        self.create_request_metadata(patch_request)
        patch_view = CustomTusUpload()
        patch_view.request = patch_request
        patch_view.kwargs = {'resource_id': resource_id}

        resp = patch_view.patch(patch_request, resource_id)
        self.assertEqual(resp.status_code, 409)

    def test_patch_returns_500_on_upload_part_error(self):
        view = CustomTusUpload()
        request = self.factory.patch("/")
        view.request = request
        view.kwargs = {'resource_id': 'fakeid'}
        tus_file = mock.Mock(is_valid=lambda: True, offset=0, file_size=10)
        chunk = mock.Mock(offset=0)
        with mock.patch("django_s3.views.CustomTusFile", lambda rid: tus_file), \
             mock.patch("django_s3.views.TusChunk", lambda req: chunk):
            tus_file.upload_part.side_effect = Exception("fail")
            resp = view.patch(request, "fakeid")
        self.assertEqual(resp.status_code, 500)

    def test_post_returns_500_on_create_initial_file_error(self):
        view = CustomTusUpload()
        request = self.factory.post("/")
        request.META["HTTP_UPLOAD_LENGTH"] = "123"
        with mock.patch.object(view, "get_metadata", return_value=self.fake_metadata()), \
             mock.patch("django_s3.views.get_path", lambda meta: "some/path/"), \
             mock.patch("django_s3.views.CustomTusFile.check_existing_file", lambda path: False), \
             mock.patch("django_s3.views.settings", mock.Mock(TUS_EXISTING_FILE='skip',
                                                              TUS_FILE_NAME_FORMAT='keep')), \
             mock.patch.object(view, "validate_filename", lambda fn: fn["filename"]), \
             mock.patch("django_s3.views.CustomTusFile.create_initial_file",
                        mock.Mock(side_effect=Exception("fail"))):
            resp = view.post(request)
            self.assertEqual(resp.status_code, 500)

    def test_post_returns_403_when_resource_published(self):
        """Test that POST returns 403 when resource is published"""
        view = CustomTusUpload()
        request = self.factory.post("/")
        request.user = self.user

        # Set resource to published
        self.res.raccess.published = True
        self.res.raccess.save()

        self.create_request_metadata(request)
        view.request = request
        view.kwargs = {'resource_id': self.res.short_id}

        resp = view.post(request)
        # Should return 403 if resource is published
        self.assertEqual(resp.status_code, 403)

    def test_post_returns_413_when_user_exceeds_quota(self):
        """Test that POST returns 413 when user exceeds quota"""
        view = CustomTusUpload()
        request = self.factory.post("/")
        request.user = self.user

        # Set HTTP_UPLOAD_LENGTH to a large value to exceed quota
        self.file_size = 1000000000000

        self.create_request_metadata(request)
        view.request = request
        view.kwargs = {'resource_id': self.res.short_id}

        resp = view.post(request)
        # Should return 413 if quota is exceeded
        self.assertEqual(resp.status_code, 413)

    def test_post_uses_metadata_file_size_when_no_upload_length(self):
        """Test that POST uses file_size from metadata when HTTP_UPLOAD_LENGTH is missing"""
        view = CustomTusUpload()
        request = self.factory.post("/")
        request.user = self.user
        request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        # Don't set HTTP_UPLOAD_LENGTH - should use metadata file_size
        self.create_request_metadata(request)
        view.request = request
        view.kwargs = {'resource_id': self.res.short_id}

        resp = view.post(request)
        # Should succeed and use file_size from metadata
        self.assertEqual(resp.status_code, 201)

    def test_post_prioritizes_upload_length_over_metadata_file_size(self):
        """Test that HTTP_UPLOAD_LENGTH takes precedence over metadata file_size"""
        view = CustomTusUpload()
        request = self.factory.post("/")
        request.user = self.user
        request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        request.META["HTTP_UPLOAD_LENGTH"] = "500"  # Different from metadata file_size
        self.create_request_metadata(request)  # Contains file_size = self.file_size
        view.request = request
        view.kwargs = {'resource_id': self.res.short_id}

        resp = view.post(request)
        # Should succeed using HTTP_UPLOAD_LENGTH (500) instead of metadata file_size
        self.assertEqual(resp.status_code, 201)

    def test_post_handles_missing_metadata_file_size(self):
        """Test that POST handles missing metadata file_size"""
        view = CustomTusUpload()
        request = self.factory.post("/")
        request.user = self.user
        request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        request.META["HTTP_UPLOAD_LENGTH"] = "300"

        # Modify the metadata to have missing file_size
        metadata = {
            "filename": "test.txt",
            "hs_res_id": self.res.short_id,
            "username": self.user.username,
            "path": f"{self.res.short_id}/data/contents/test.txt",
        }
        encoded_metadata = ",".join(
            f"{key} {base64.b64encode(value.encode()).decode('utf-8')}" if isinstance(value, str) else f"{key} {value}"
            for key, value in metadata.items()
        )
        request.META["HTTP_UPLOAD_METADATA"] = encoded_metadata

        view.request = request
        view.kwargs = {'resource_id': self.res.short_id}

        resp = view.post(request)
        # Should succeed using HTTP_UPLOAD_LENGTH (300) since metadata file_size is 'null'
        self.assertEqual(resp.status_code, 201)

    def test_post_uses_metadata_file_size_when_upload_length_zero(self):
        """Test that POST uses metadata file_size when HTTP_UPLOAD_LENGTH is 0"""
        view = CustomTusUpload()
        request = self.factory.post("/")
        request.user = self.user
        request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        request.META["HTTP_UPLOAD_LENGTH"] = "0"  # Zero upload length
        self.create_request_metadata(request)
        view.request = request
        view.kwargs = {'resource_id': self.res.short_id}

        resp = view.post(request)
        # Should succeed using metadata file_size since HTTP_UPLOAD_LENGTH is 0
        self.assertEqual(resp.status_code, 201)

    def test_post_quota_check_for_different_resource_owners(self):
        """Test that quota is checked against the resource owner, not the uploading user"""
        # Create a different user who owns the resource
        resource_owner = hydroshare.create_account(
            'owner@email.com',
            username='resourceowner',
            first_name='Owner',
            last_name='User',
            superuser=False,
            groups=[self.group]
        )

        # Create a resource owned by resource_owner but editable by test user
        owned_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=resource_owner,
            title='Owned Resource',
            keywords=('test',)
        )

        # Share edit permission with test user
        resource_owner.uaccess.share_resource_with_user(
            owned_resource, self.user, PrivilegeCodes.CHANGE
        )

        view = CustomTusUpload()
        request = self.factory.post("/")
        request.user = self.user  # User with edit permission but not owner

        # Create metadata for the owned resource
        metadata = self.fake_metadata()
        metadata['hs_res_id'] = owned_resource.short_id
        encoded_metadata = ",".join(
            f"{key} {base64.b64encode(value.encode()).decode('utf-8')}" if isinstance(value, str) else f"{key} {value}"
            for key, value in metadata.items()
        )
        request.META["HTTP_UPLOAD_METADATA"] = encoded_metadata
        request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        request.META["HTTP_UPLOAD_LENGTH"] = "1000"

        view.request = request
        view.kwargs = {'resource_id': owned_resource.short_id}

        resp = view.post(request)
        # Should succeed - quota is checked against resource owner
        self.assertEqual(resp.status_code, 201)

    def test_post_with_reasonable_file_size_succeeds(self):
        """Test that POST succeeds with a reasonable file size that doesn't exceed quota"""
        view = CustomTusUpload()
        request = self.factory.post("/")
        request.user = self.user
        request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        # Use a small file size that should be within quota
        request.META["HTTP_UPLOAD_LENGTH"] = "1000"  # 1KB file
        self.create_request_metadata(request)
        view.request = request
        view.kwargs = {'resource_id': self.res.short_id}

        resp = view.post(request)
        # Should succeed with 201 status
        self.assertEqual(resp.status_code, 201)
        self.assertIn("Location", resp.headers)

    def test_post_without_file_size_in_metadata_or_header_succeeds(self):
        """Test that POST succeeds when no file size is provided in metadata or header"""
        view = CustomTusUpload()
        request = self.factory.post("/")
        request.user = self.user
        request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"

        # Don't set HTTP_UPLOAD_LENGTH and remove file_size from metadata
        metadata = self.fake_metadata()
        del metadata['file_size']  # Remove file_size from metadata
        encoded_metadata = ",".join(
            f"{key} {base64.b64encode(value.encode()).decode('utf-8')}" if isinstance(value, str) else f"{key} {value}"
            for key, value in metadata.items()
        )
        request.META["HTTP_UPLOAD_METADATA"] = encoded_metadata

        view.request = request
        view.kwargs = {'resource_id': self.res.short_id}
        resp = view.post(request)
        self.assertEqual(resp.status_code, 201)
