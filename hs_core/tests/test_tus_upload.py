import uuid
from unittest import mock
from django.http import HttpResponseForbidden, HttpResponseNotFound
from hs_core.views.resource_rest_api import CustomTusUpload
from django.test import RequestFactory, TestCase, Client
from django.contrib.auth.models import AnonymousUser, User, Group
from hs_core import hydroshare
from hs_core.models import BaseResource
import base64


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

    def test_dispatch_returns_403_if_user_not_authenticated_and_no_session(self):
        view = CustomTusUpload()
        request = self.factory.get("/")
        request.user = AnonymousUser()
        view.request = request
        view.kwargs = {'resource_id': 'fakeid'}

        with mock.patch.object(view, "get_metadata", return_value=self.fake_metadata()), \
             mock.patch("hs_core.views.resource_rest_api.Session"):
            resp = view.dispatch()
            self.assertIsInstance(resp, HttpResponseForbidden)

    def test_dispatch_returns_403_if_permission_denied(self):
        view = CustomTusUpload()
        request = self.factory.get("/")
        request.user = AnonymousUser()
        view.request = request
        self.create_request_metadata(request)

        # use mock to patch the get_metadata method to return fake metadata
        view.kwargs = {'resource_id': self.res.short_id}
        with mock.patch.object(view, "get_metadata", return_value=self.fake_metadata()):
            resp = view.dispatch()
            self.assertIsInstance(resp, HttpResponseForbidden)

        # Do not mock authorize, just use a user with no permissions
        resp = view.dispatch()
        self.assertIsInstance(resp, HttpResponseForbidden)

    def test_patch_returns_410_if_invalid(self):
        view = CustomTusUpload()
        request = self.factory.patch("/")
        view.request = request
        view.kwargs = {'resource_id': 'fakeid'}
        with mock.patch("hs_core.views.resource_rest_api.CustomTusFile", lambda rid: mock.Mock(is_valid=lambda: False)):
            resp = view.patch(request, "fakeid")
            self.assertEqual(resp.status_code, 410)

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


def test_dispatch_returns_404_if_no_metadata_and_no_tusfile(monkeypatch, rf):
    view = CustomTusUpload()
    request = rf.get("/")
    view.request = request
    view.kwargs = {'resource_id': 'fakeid'}

    monkeypatch.setattr(view, "get_metadata", lambda req: None)
    monkeypatch.setattr("hs_core.views.resource_rest_api.CustomTusFile", mock.Mock(side_effect=Exception("fail")))
    resp = view.dispatch()
    assert isinstance(resp, HttpResponseNotFound)
    assert "Error in getting metadata" in resp.content.decode()


def test_dispatch_returns_403_if_user_not_authenticated_and_no_session(monkeypatch, rf, fake_metadata):
    view = CustomTusUpload()
    request = rf.get("/")
    request.user = AnonymousUser()
    view.request = request
    view.kwargs = {'resource_id': 'fakeid'}

    monkeypatch.setattr(view, "get_metadata", lambda req: fake_metadata)
    monkeypatch.setattr("hs_core.views.resource_rest_api.Session", mock.Mock())
    resp = view.dispatch()
    assert isinstance(resp, HttpResponseForbidden)


def test_dispatch_returns_403_if_anonymous_user_with_no_permissions(self):
    view = CustomTusUpload()
    factory = RequestFactory()
    request = factory.get("/")

    request.user = AnonymousUser()
    view.request = request
    view.kwargs = {'resource_id': 'fakeid'}

    # Do not mock authorize, just use a user with no permissions
    resp = view.dispatch()
    assert isinstance(resp, HttpResponseForbidden)


def test_dispatch_calls_super_on_success(monkeypatch, rf, fake_metadata, fake_user):
    view = CustomTusUpload()
    request = rf.get("/")
    request.user = fake_user
    view.request = request
    view.kwargs = {'resource_id': 'fakeid'}

    monkeypatch.setattr(view, "get_metadata", lambda req: fake_metadata)
    monkeypatch.setattr("hs_core.views.resource_rest_api.view_utils.authorize",
                        mock.Mock(return_value=(None, None, fake_user)))
    monkeypatch.setattr("django.utils.decorators.method_decorator", lambda x: x)
    monkeypatch.setattr(CustomTusUpload, "dispatch", lambda self, *a, **kw: "called-super")
    # Call the original method, not the monkeypatched one
    result = CustomTusUpload.__bases__[0].dispatch(view, request)
    assert result == "called-super"


def test_patch_returns_410_if_invalid(monkeypatch, rf, fake_user):
    view = CustomTusUpload()
    request = rf.patch("/")
    view.request = request
    view.kwargs = {'resource_id': 'fakeid'}
    monkeypatch.setattr("hs_core.views.resource_rest_api.CustomTusFile", lambda rid: mock.Mock(is_valid=lambda: False))
    resp = view.patch(request, "fakeid")
    assert resp.status_code == 410


def test_patch_returns_409_if_offset_mismatch(monkeypatch, rf, fake_user):
    view = CustomTusUpload()
    request = rf.patch("/")
    view.request = request
    view.kwargs = {'resource_id': 'fakeid'}
    tus_file = mock.Mock(is_valid=lambda: True, offset=5, file_size=10)
    chunk = mock.Mock(offset=3)
    monkeypatch.setattr("hs_core.views.resource_rest_api.CustomTusFile", lambda rid: tus_file)
    monkeypatch.setattr("hs_core.views.resource_rest_api.TusChunk", lambda req: chunk)
    resp = view.patch(request, "fakeid")
    assert resp.status_code == 409


def test_patch_returns_413_if_offset_too_large(monkeypatch, rf, fake_user):
    view = CustomTusUpload()
    request = rf.patch("/")
    view.request = request
    view.kwargs = {'resource_id': 'fakeid'}
    tus_file = mock.Mock(is_valid=lambda: True, offset=15, file_size=10)
    chunk = mock.Mock(offset=20)
    monkeypatch.setattr("hs_core.views.resource_rest_api.CustomTusFile", lambda rid: tus_file)
    monkeypatch.setattr("hs_core.views.resource_rest_api.TusChunk", lambda req: chunk)
    resp = view.patch(request, "fakeid")
    assert resp.status_code == 413


def test_patch_returns_500_on_upload_part_error(monkeypatch, rf, fake_user):
    view = CustomTusUpload()
    request = rf.patch("/")
    view.request = request
    view.kwargs = {'resource_id': 'fakeid'}
    tus_file = mock.Mock(is_valid=lambda: True, offset=0, file_size=10)
    chunk = mock.Mock(offset=0)
    monkeypatch.setattr("hs_core.views.resource_rest_api.CustomTusFile", lambda rid: tus_file)
    monkeypatch.setattr("hs_core.views.resource_rest_api.TusChunk", lambda req: chunk)
    tus_file.upload_part.side_effect = Exception("fail")
    resp = view.patch(request, "fakeid")
    assert resp.status_code == 500
    assert "Unable to write chunk" in resp.reason


def test_patch_returns_204_on_success(monkeypatch, rf, fake_user):
    view = CustomTusUpload()
    request = rf.patch("/")
    view.request = request
    view.kwargs = {'resource_id': 'fakeid'}
    tus_file = mock.Mock(
        is_valid=lambda: True,
        offset=0,
        file_size=10,
        is_complete=lambda: False
    )
    chunk = mock.Mock(offset=0)
    monkeypatch.setattr("hs_core.views.resource_rest_api.CustomTusFile", lambda rid: tus_file)
    monkeypatch.setattr("hs_core.views.resource_rest_api.TusChunk", lambda req: chunk)
    tus_file.upload_part.return_value = None
    resp = view.patch(request, "fakeid")
    assert resp.status_code == 204


def test_post_returns_409_if_existing_file(monkeypatch, rf, fake_metadata):
    view = CustomTusUpload()
    request = rf.post("/")
    request.META["HTTP_UPLOAD_LENGTH"] = "123"
    monkeypatch.setattr(view, "get_metadata", lambda req: fake_metadata)
    monkeypatch.setattr("hs_core.views.resource_rest_api.get_path", lambda meta: "some/path/")
    monkeypatch.setattr("hs_core.views.resource_rest_api.CustomTusFile.check_existing_file", lambda path: True)
    monkeypatch.setattr("hs_core.views.resource_rest_api.settings", mock.Mock(TUS_EXISTING_FILE='error',
                                                                              TUS_FILE_NAME_FORMAT='keep'))
    monkeypatch.setattr(view, "validate_filename", lambda fn: fn["filename"])
    resp = view.post(request)
    assert resp.status_code == 409


def test_post_returns_500_on_create_initial_file_error(monkeypatch, rf, fake_metadata):
    view = CustomTusUpload()
    request = rf.post("/")
    request.META["HTTP_UPLOAD_LENGTH"] = "123"
    monkeypatch.setattr(view, "get_metadata", lambda req: fake_metadata)
    monkeypatch.setattr("hs_core.views.resource_rest_api.get_path", lambda meta: "some/path/")
    monkeypatch.setattr("hs_core.views.resource_rest_api.CustomTusFile.check_existing_file", lambda path: False)
    monkeypatch.setattr("hs_core.views.resource_rest_api.settings", mock.Mock(TUS_EXISTING_FILE='skip',
                                                                              TUS_FILE_NAME_FORMAT='keep'))
    monkeypatch.setattr(view, "validate_filename", lambda fn: fn["filename"])
    monkeypatch.setattr("hs_core.views.resource_rest_api.CustomTusFile.create_initial_file",
                        mock.Mock(side_effect=Exception("fail")))
    resp = view.post(request)
    assert resp.status_code == 500
    assert "Unable to create file" in resp.reason


def test_post_returns_201_on_success(monkeypatch, rf, fake_metadata):
    view = CustomTusUpload()
    request = rf.post("/")
    request.build_absolute_uri = lambda: "http://test/"
    request.META["HTTP_UPLOAD_LENGTH"] = "123"
    monkeypatch.setattr(view, "get_metadata", lambda req: fake_metadata)
    monkeypatch.setattr("hs_core.views.resource_rest_api.get_path", lambda meta: "some/path/")
    monkeypatch.setattr("hs_core.views.resource_rest_api.CustomTusFile.check_existing_file", lambda path: False)
    monkeypatch.setattr("hs_core.views.resource_rest_api.settings",
                        mock.Mock(TUS_EXISTING_FILE='skip', TUS_FILE_NAME_FORMAT='keep'))
    monkeypatch.setattr(view, "validate_filename", lambda fn: fn["filename"])
    tus_file = mock.Mock(resource_id="abc123")
    monkeypatch.setattr("hs_core.views.resource_rest_api.CustomTusFile.create_initial_file",
                        mock.Mock(return_value=tus_file))
    resp = view.post(request)
    assert resp.status_code == 201
    assert resp["Location"].endswith("abc123")
