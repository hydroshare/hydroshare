import base64
import uuid
from unittest import mock

from django.contrib.auth.models import AnonymousUser, User, Group
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.test import Client, RequestFactory, TestCase

from hs_access_control.models import PrivilegeCodes

from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.views.resource_rest_api import CustomTusUpload


class CustomTusUploadTests(TestCase):
    def fake_metadata(self):
        return {
            "filename": "test.txt",
            "hs_res_id": self.res.short_id,
            "username": self.user.username,
            "path": f"{self.res.short_id}/data/contents/test.txt"
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

    def test_post_returns_expected_metadata(self):
        view = CustomTusUpload()
        request = self.factory.post("/")
        request.user = self.user
        request.META["HTTP_TUS_RESUMABLE"] = "1.0.0"
        request.META["HTTP_UPLOAD_LENGTH"] = "123"
        self.create_request_metadata(request)
        view.request = request
        view.kwargs = {'resource_id': self.res.short_id}

        # Mock the get_metadata method to return fake metadata
        with mock.patch.object(view, "get_metadata", return_value=self.fake_metadata()):
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

        # Mock the get_metadata method to return fake metadata
        with mock.patch.object(view, "get_metadata", return_value=self.fake_metadata()), \
             mock.patch("hs_core.views.resource_rest_api.get_path", lambda meta: "some/path/"), \
             mock.patch("hs_core.views.resource_rest_api.CustomTusFile.check_existing_file", lambda path: False):
            resp = view.post(request)
            self.assertEqual(resp.status_code, 201)
            self.assertIn("Tus-Resumable", resp.headers)
            self.assertIn("Location", resp.headers)

    def test_patch_returns_204_on_success(self):
        view = CustomTusUpload()
        request = self.factory.patch("/")
        view.request = request
        view.kwargs = {'resource_id': 'fakeid'}
        tus_file = mock.Mock(
            is_valid=lambda: True,
            offset=0,
            file_size=10,
            is_complete=lambda: False
        )
        chunk = mock.Mock(offset=0)
        with mock.patch("hs_core.views.resource_rest_api.CustomTusFile", lambda rid: tus_file), \
             mock.patch("hs_core.views.resource_rest_api.TusChunk", lambda req: chunk):
            tus_file.upload_part.return_value = None
            resp = view.patch(request, "fakeid")
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

        # use mock to patch the get_metadata method to return fake metadata
        with mock.patch.object(view, "get_metadata", return_value=self.fake_metadata()):
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

        # use mock to patch the get_metadata method to return fake metadata
        view.kwargs = {'resource_id': self.res.short_id}
        with mock.patch.object(view, "get_metadata", return_value=self.fake_metadata()):
            resp = view.dispatch()
            self.assertIsInstance(resp, HttpResponseForbidden)

        # Do not mock authorize, just use a user with no permissions
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

        # Do not mock authorize, just use a user with no permissions
        resp = view.dispatch()
        self.assertIsInstance(resp, HttpResponseForbidden)

    def test_dispatch_returns_404_if_no_metadata_and_no_tusfile(self):
        view = CustomTusUpload()
        request = self.factory.get("/")
        view.request = request
        view.kwargs = {'resource_id': 'fakeid'}

        with mock.patch.object(view, "get_metadata", return_value=None), \
             mock.patch("hs_core.views.resource_rest_api.CustomTusFile", side_effect=Exception("fail")):
            resp = view.dispatch()
            self.assertIsInstance(resp, HttpResponseNotFound)
            self.assertIn("Error in getting metadata", resp.content.decode())

    def test_patch_returns_409_if_offset_mismatch(self):
        view = CustomTusUpload()
        request = self.factory.patch("/")
        view.request = request
        view.kwargs = {'resource_id': 'fakeid'}
        tus_file = mock.Mock(is_valid=lambda: True, offset=5, file_size=10)
        chunk = mock.Mock(offset=3)
        with mock.patch("hs_core.views.resource_rest_api.CustomTusFile", lambda rid: tus_file), \
             mock.patch("hs_core.views.resource_rest_api.TusChunk", lambda req: chunk):
            resp = view.patch(request, "fakeid")
            self.assertEqual(resp.status_code, 409)

    def test_patch_returns_409_if_offset_too_large(self):
        view = CustomTusUpload()
        request = self.factory.patch("/")
        view.request = request
        view.kwargs = {'resource_id': 'fakeid'}
        tus_file = mock.Mock(is_valid=lambda: True, offset=15, file_size=10)
        chunk = mock.Mock(offset=20)
        with mock.patch("hs_core.views.resource_rest_api.CustomTusFile", lambda rid: tus_file), \
             mock.patch("hs_core.views.resource_rest_api.TusChunk", lambda req: chunk):
            resp = view.patch(request, "fakeid")
            self.assertEqual(resp.status_code, 409)

    def test_post_returns_409_if_existing_file(self):
        view = CustomTusUpload()
        request = self.factory.post("/")
        request.META["HTTP_UPLOAD_LENGTH"] = "123"
        with mock.patch.object(view, "get_metadata", return_value=self.fake_metadata()), \
             mock.patch("hs_core.views.resource_rest_api.get_path", lambda meta: "some/path/"), \
             mock.patch("hs_core.views.resource_rest_api.CustomTusFile.check_existing_file", lambda path: True), \
             mock.patch("hs_core.views.resource_rest_api.settings", mock.Mock(TUS_EXISTING_FILE='error',
                                                                              TUS_FILE_NAME_FORMAT='keep')), \
             mock.patch.object(view, "validate_filename", lambda fn: fn["filename"]):
            resp = view.post(request)
            self.assertEqual(resp.status_code, 409)

    def test_patch_returns_410_if_invalid(self):
        view = CustomTusUpload()
        request = self.factory.patch("/")
        view.request = request
        view.kwargs = {'resource_id': 'fakeid'}
        with mock.patch("hs_core.views.resource_rest_api.CustomTusFile", lambda rid: mock.Mock(is_valid=lambda: False)):
            resp = view.patch(request, "fakeid")
            self.assertEqual(resp.status_code, 410)

    def test_patch_returns_413_if_offset_larger_than_file_size(self):
        view = CustomTusUpload()
        request = self.factory.patch("/")
        view.request = request
        view.kwargs = {'resource_id': self.res.short_id}
        tus_file = mock.Mock(is_valid=lambda: True, offset=15, file_size=10)
        chunk = mock.Mock(offset=15)
        with mock.patch("hs_core.views.resource_rest_api.CustomTusFile", lambda rid: tus_file), \
             mock.patch("hs_core.views.resource_rest_api.TusChunk", lambda req: chunk):
            resp = view.patch(request, "fakeid")
            self.assertEqual(resp.status_code, 413)

    def test_patch_returns_500_on_upload_part_error(self):
        view = CustomTusUpload()
        request = self.factory.patch("/")
        view.request = request
        view.kwargs = {'resource_id': 'fakeid'}
        tus_file = mock.Mock(is_valid=lambda: True, offset=0, file_size=10)
        chunk = mock.Mock(offset=0)
        with mock.patch("hs_core.views.resource_rest_api.CustomTusFile", lambda rid: tus_file), \
             mock.patch("hs_core.views.resource_rest_api.TusChunk", lambda req: chunk):
            tus_file.upload_part.side_effect = Exception("fail")
            resp = view.patch(request, "fakeid")
            self.assertEqual(resp.status_code, 500)

    def test_post_returns_500_on_create_initial_file_error(self):
        view = CustomTusUpload()
        request = self.factory.post("/")
        request.META["HTTP_UPLOAD_LENGTH"] = "123"
        with mock.patch.object(view, "get_metadata", return_value=self.fake_metadata()), \
             mock.patch("hs_core.views.resource_rest_api.get_path", lambda meta: "some/path/"), \
             mock.patch("hs_core.views.resource_rest_api.CustomTusFile.check_existing_file", lambda path: False), \
             mock.patch("hs_core.views.resource_rest_api.settings", mock.Mock(TUS_EXISTING_FILE='skip',
                                                                              TUS_FILE_NAME_FORMAT='keep')), \
             mock.patch.object(view, "validate_filename", lambda fn: fn["filename"]), \
             mock.patch("hs_core.views.resource_rest_api.CustomTusFile.create_initial_file",
                        mock.Mock(side_effect=Exception("fail"))):
            resp = view.post(request)
            self.assertEqual(resp.status_code, 500)
