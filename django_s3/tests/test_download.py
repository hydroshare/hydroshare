from unittest import mock
from django.test import TestCase, RequestFactory
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django_s3.views import download
from django.contrib.auth.models import User
import json


class DownloadViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        self.res = mock.MagicMock()
        self.res.short_id = 'test_res_id'
        self.res.resource_type = 'CompositeResource'
        self.res.bag_path = 'bags/test_res_id.zip'
        self.res.bag_url = '/django_s3/rest_download/bags/test_res_id.zip'
        self.res.is_folder.return_value = False

        self.mock_istorage = mock.MagicMock()
        self.res.get_s3_storage.return_value = self.mock_istorage
        self.res.get_s3_path.side_effect = lambda path, prepend_short_id=False: path

        self.mock_istorage.exists.return_value = True
        self.mock_istorage.size.return_value = 100
        self.mock_istorage.signed_url.return_value = 'http://signed-url.com'

    @mock.patch('django_s3.views.authorize')
    @mock.patch('django_s3.views.check_resource_type')
    def test_basic_file_download(self, mock_check_resource_type, mock_authorize):
        """Test basic file download with valid permissions."""

        # Setup mocks
        mock_authorize.return_value = (self.res, True, self.user)
        mock_check_resource_type.return_value = mock.MagicMock()

        request = self.factory.get('/django_s3/download/test_res_id/data/contents/file.txt')
        request.user = self.user

        response = download(request, 'test_res_id/data/contents/file.txt')

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.url, 'http://signed-url.com')
        self.mock_istorage.signed_url.assert_called_once()
        self.res.update_download_count.assert_called_once()

    @mock.patch('django_s3.views.authorize')
    def test_unauthorized_download(self, mock_authorize):
        """Test download request without proper permissions."""

        mock_authorize.return_value = (None, False, None)

        request = self.factory.get('/django_s3/download/test_res_id/data/contents/file.txt')
        request.user = self.user

        response = download(request, 'test_res_id/data/contents/file.txt')

        self.assertEqual(response.status_code, 401)
        self.assertIn(b"You do not have permission", response.content)

    def test_invalid_path(self):
        """Test download request with an empty or invalid path."""

        request = self.factory.get('/django_s3/download/')
        request.user = self.user

        response = download(request, '')

        self.assertIsInstance(response, HttpResponseNotFound)

    @mock.patch('django_s3.views.authorize')
    @mock.patch('django_s3.views.check_resource_type')
    @mock.patch('django_s3.views.create_bag_by_s3')
    def test_bag_download_sync(self, mock_create_bag, mock_check_resource_type, mock_authorize):
        """Test synchronous bag download when bag is modified."""

        mock_authorize.return_value = (self.res, True, self.user)
        mock_check_resource_type.return_value = mock.MagicMock()
        mock_create_bag.return_value = True
        self.res.getAVU.return_value = True     # bag_modified = True

        request = self.factory.get('/django_s3/download/bags/test_res_id.zip')
        request.user = self.user

        response = download(request, 'bags/test_res_id.zip', use_async=False)

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.url, 'http://signed-url.com')
        mock_create_bag.assert_called_once_with('test_res_id')

    @mock.patch('django_s3.views.authorize')
    @mock.patch('django_s3.views.check_resource_type')
    @mock.patch('django_s3.views.create_bag_by_s3')
    @mock.patch('django_s3.views.get_resource_bag_task')
    @mock.patch('django_s3.views.get_task_user_id')
    @mock.patch('django_s3.views.get_or_create_task_notification')
    def test_bag_download_async(self, mock_get_notification, mock_get_user_id, mock_get_task,
                                mock_create_bag, mock_check_resource_type, mock_authorize):
        """Test asynchronous bag download when bag is modified."""

        mock_authorize.return_value = (self.res, True, self.user)
        mock_check_resource_type.return_value = mock.MagicMock()
        mock_get_task.return_value = None
        mock_get_user_id.return_value = self.user.id
        mock_get_notification.return_value = {'status': 'progress'}
        self.res.getAVU.return_value = True     # bag_modified = True

        # Mock celery task
        mock_task = mock.MagicMock()
        mock_task.task_id = 'task_id_123'
        mock_create_bag.apply_async.return_value = mock_task

        request = self.factory.get('/django_s3/download/bags/test_res_id.zip')
        request.user = self.user
        # Set CSRF_COOKIE to make api_request = False
        request.META['CSRF_COOKIE'] = 'some-cookie'
        mock_get_notification.return_value = {'status': 'progress'}

        response = download(request, 'bags/test_res_id.zip', use_async=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {'status': 'progress'})
        mock_create_bag.apply_async.assert_called_once()

    @mock.patch('django_s3.views.authorize')
    @mock.patch('django_s3.views.check_resource_type')
    @mock.patch('django_s3.views.create_temp_zip')
    def test_zip_download_sync(self, mock_create_zip, mock_check_resource_type, mock_authorize):
        """Test synchronous zipped file download."""
        mock_authorize.return_value = (self.res, True, self.user)
        mock_check_resource_type.return_value = mock.MagicMock()
        mock_create_zip.return_value = True

        # Request with ?zipped=true
        request = self.factory.get('/django_s3/download/test_res_id/data/contents/file.txt?zipped=true')
        request.user = self.user

        response = download(request, 'test_res_id/data/contents/file.txt', use_async=False)

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.url, 'http://signed-url.com')
        mock_create_zip.assert_called_once()

    @mock.patch('django_s3.views.authorize')
    @mock.patch('django_s3.views.check_resource_type')
    @mock.patch('django_s3.views.create_temp_zip')
    @mock.patch('django_s3.views.get_task_user_id')
    @mock.patch('django_s3.views.get_or_create_task_notification')
    def test_zip_download_async(self, mock_get_notification, mock_get_user_id, 
                                mock_create_zip, mock_check_resource_type, mock_authorize):
        """Test asynchronous zipped file download."""
        mock_authorize.return_value = (self.res, True, self.user)
        mock_check_resource_type.return_value = mock.MagicMock()
        mock_get_user_id.return_value = self.user.id
        mock_get_notification.return_value = {'status': 'progress'}

        # Mock celery task
        mock_task = mock.MagicMock()
        mock_task.task_id = 'task_id_456'
        mock_create_zip.apply_async.return_value = mock_task

        request = self.factory.get('/django_s3/download/test_res_id/data/contents/file.txt?zipped=true')
        request.user = self.user
        # Set CSRF_COOKIE to make api_request = False
        request.META['CSRF_COOKIE'] = 'some-cookie'
        mock_get_notification.return_value = {'status': 'progress'}

        response = download(request, 'test_res_id/data/contents/file.txt', use_async=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {'status': 'progress'})
        mock_create_zip.apply_async.assert_called_once()

    @mock.patch('django_s3.views.authorize')
    @mock.patch('django_s3.views.check_resource_type')
    @mock.patch('django_s3.views.create_temp_zip')
    def test_folder_download(self, mock_create_zip, mock_check_resource_type, mock_authorize):
        """Test folder download (always zipped)."""

        mock_authorize.return_value = (self.res, True, self.user)
        mock_check_resource_type.return_value = mock.MagicMock()
        mock_create_zip.return_value = True
        self.res.is_folder.return_value = True

        request = self.factory.get('/django_s3/download/test_res_id/data/contents/myfolder')
        request.user = self.user

        response = download(request, 'test_res_id/data/contents/myfolder', use_async=False)

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.url, 'http://signed-url.com')
        self.res.is_folder.assert_called_once_with('data/contents/myfolder')
        mock_create_zip.assert_called_once()

    @mock.patch('django_s3.views.authorize')
    @mock.patch('django_s3.views.check_resource_type')
    @mock.patch('django_s3.views.create_temp_zip')
    def test_aggregation_download(self, mock_create_zip, mock_check_resource_type, mock_authorize):
        """Test aggregation download (redirect or zipped)."""

        mock_authorize.return_value = (self.res, True, self.user)
        mock_check_resource_type.return_value = mock.MagicMock()
        mock_create_zip.return_value = True
        self.res.file_path = 'test_res_id/data/contents'

        mock_aggregation = mock.MagicMock()
        mock_aggregation.get_main_file.storage_path = 'test_res_id/data/contents/agg/main.nc'
        mock_aggregation.redirect_url = 'http://example.com'
        self.res.get_aggregation_by_aggregation_name.return_value = mock_aggregation

        # Test redirect case (default)
        request = self.factory.get('/django_s3/download/test_res_id/data/contents/agg?aggregation=true')
        request.user = self.user
        response = download(request, 'test_res_id/data/contents/agg', use_async=False)
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.url, 'http://example.com')

        # Test zip case
        request = self.factory.get('/django_s3/download/test_res_id/data/contents/agg?aggregation=true&zipped=true')
        request.user = self.user
        response = download(request, 'test_res_id/data/contents/agg', use_async=False)
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.url, 'http://signed-url.com')
        mock_create_zip.assert_called_once()

    @mock.patch('django_s3.views.authorize')
    @mock.patch('django_s3.views.check_resource_type')
    @mock.patch('django_s3.views.create_bag_by_s3')
    def test_resource_metadata_refresh(self, mock_create_bag, mock_check_resource_type, mock_authorize):
        """Test resource metadata refresh on download."""

        mock_authorize.return_value = (self.res, True, self.user)
        mock_check_resource_type.return_value = mock.MagicMock()
        self.res.getAVU.return_value = True     # bag_modified = True

        metadata_path = f'{self.res.short_id}/data/resourcemetadata.xml'
        request = self.factory.get(f'/django_s3/download/{metadata_path}')
        request.user = self.user

        response = download(request, metadata_path)

        self.assertIsInstance(response, HttpResponseRedirect)
        # Should trigger bag creation (metadata refresh)
        mock_create_bag.assert_called_once_with(self.res.short_id, create_zip=False)
        self.res.update_relation_meta.assert_called_once()

    @mock.patch('django_s3.views.authorize')
    @mock.patch('django_s3.views.check_resource_type')
    @mock.patch('django_s3.views.create_bag_by_s3')
    def test_resource_map_refresh(self, mock_create_bag, mock_check_resource_type, mock_authorize):
        """Test resource map refresh on download."""

        mock_authorize.return_value = (self.res, True, self.user)
        mock_check_resource_type.return_value = mock.MagicMock()
        self.res.getAVU.return_value = True     # bag_modified = True

        metadata_path = f'{self.res.short_id}/data/resourcemap.xml'
        request = self.factory.get(f'/django_s3/download/{metadata_path}')
        request.user = self.user

        response = download(request, metadata_path)

        self.assertIsInstance(response, HttpResponseRedirect)
        # Should trigger bag creation (metadata refresh)
        mock_create_bag.assert_called_once_with(self.res.short_id, create_zip=False)
        self.res.update_relation_meta.assert_called_once()

    @mock.patch('django_s3.views.authorize')
    @mock.patch('django_s3.views.check_resource_type')
    @mock.patch('django_s3.views.create_bag_by_s3')
    def test_bag_download_no_refresh(self, mock_create_bag, mock_check_resource_type, mock_authorize):
        """Test bag download when bag is already up-to-date."""

        mock_authorize.return_value = (self.res, True, self.user)
        mock_check_resource_type.return_value = mock.MagicMock()
        self.res.getAVU.return_value = False    # bag_modified = False
        self.mock_istorage.exists.return_value = True    # bag exists in S3

        request = self.factory.get('/django_s3/download/bags/test_res_id.zip')
        request.user = self.user

        response = download(request, 'bags/test_res_id.zip', use_async=False)

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.url, 'http://signed-url.com')
        # Should NOT trigger bag creation
        mock_create_bag.assert_not_called()

    @mock.patch('django_s3.views.authorize')
    @mock.patch('django_s3.views.check_resource_type')
    @mock.patch('django_s3.views.create_bag_by_s3')
    @mock.patch('django_s3.views.is_ajax')
    def test_bag_download_ajax_no_refresh(self, mock_is_ajax, mock_create_bag, mock_check_resource_type,
                                          mock_authorize):
        """Test AJAX bag download when bag is already up-to-date."""

        mock_authorize.return_value = (self.res, True, self.user)
        mock_check_resource_type.return_value = mock.MagicMock()
        self.res.getAVU.return_value = False    # bag_modified = False
        self.mock_istorage.exists.return_value = True    # bag exists in S3
        mock_is_ajax.return_value = True

        request = self.factory.get('/django_s3/download/bags/test_res_id.zip')
        request.user = self.user

        response = download(request, 'bags/test_res_id.zip', use_async=True)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'completed')
        self.assertEqual(data['payload'], self.res.bag_url)
        mock_create_bag.assert_not_called()

    @mock.patch('django_s3.views.authorize')
    @mock.patch('django_s3.views.check_resource_type')
    def test_aggregation_map_refresh(self, mock_check_resource_type, mock_authorize):
        """Test aggregation map refresh on download."""

        mock_authorize.return_value = (self.res, True, self.user)
        mock_check_resource_type.return_value = mock.MagicMock()

        agg_map_path = 'test_res_id/data/contents/agg_resmap.xml'
        mock_aggregation = mock.MagicMock()
        mock_aggregation.metadata.is_dirty = True
        self.res.get_aggregation_by_meta_file.return_value = mock_aggregation

        request = self.factory.get(f'/django_s3/download/{agg_map_path}')
        request.user = self.user

        response = download(request, agg_map_path)

        self.assertIsInstance(response, HttpResponseRedirect)
        self.res.get_aggregation_by_meta_file.assert_called_once_with(agg_map_path)
        mock_aggregation.create_aggregation_xml_documents.assert_called_once()

    @mock.patch('django_s3.views.authorize')
    @mock.patch('django_s3.views.check_resource_type')
    def test_aggregation_map_no_refresh(self, mock_check_resource_type, mock_authorize):
        """Test aggregation map download when no refresh is needed."""

        mock_authorize.return_value = (self.res, True, self.user)
        mock_check_resource_type.return_value = mock.MagicMock()

        agg_map_path = 'test_res_id/data/contents/agg_resmap.xml'
        mock_aggregation = mock.MagicMock()
        mock_aggregation.metadata.is_dirty = False
        self.res.get_aggregation_by_meta_file.return_value = mock_aggregation

        request = self.factory.get(f'/django_s3/download/{agg_map_path}')
        request.user = self.user

        response = download(request, agg_map_path)

        self.assertIsInstance(response, HttpResponseRedirect)
        self.res.get_aggregation_by_meta_file.assert_called_once_with(agg_map_path)
        mock_aggregation.create_aggregation_xml_documents.assert_not_called()

    @mock.patch('django_s3.views.authorize')
    @mock.patch('django_s3.views.check_resource_type')
    def test_aggregation_metadata_refresh(self, mock_check_resource_type, mock_authorize):
        """Test aggregation metadata refresh on download."""

        mock_authorize.return_value = (self.res, True, self.user)
        mock_check_resource_type.return_value = mock.MagicMock()
        self.res.getAVU.return_value = True     # bag_modified = True
        agg_meta_path = 'test_res_id/data/contents/agg_meta.xml'
        mock_aggregation = mock.MagicMock()
        mock_aggregation.metadata.is_dirty = True
        self.res.get_aggregation_by_meta_file.return_value = mock_aggregation

        request = self.factory.get(f'/django_s3/download/{agg_meta_path}')
        request.user = self.user

        response = download(request, agg_meta_path)

        self.assertIsInstance(response, HttpResponseRedirect)
        self.res.get_aggregation_by_meta_file.assert_called_once_with(agg_meta_path)
        mock_aggregation.create_aggregation_xml_documents.assert_called_once()

    @mock.patch('django_s3.views.authorize')
    @mock.patch('django_s3.views.check_resource_type')
    def test_aggregation_metadata_no_refresh(self, mock_check_resource_type, mock_authorize):
        """Test aggregation metadata download when no refresh is needed."""

        mock_authorize.return_value = (self.res, True, self.user)
        mock_check_resource_type.return_value = mock.MagicMock()
        self.res.getAVU.return_value = True     # bag_modified = True
        agg_meta_path = 'test_res_id/data/contents/agg_meta.xml'
        mock_aggregation = mock.MagicMock()
        mock_aggregation.metadata.is_dirty = False
        self.res.get_aggregation_by_meta_file.return_value = mock_aggregation

        request = self.factory.get(f'/django_s3/download/{agg_meta_path}')
        request.user = self.user

        response = download(request, agg_meta_path)

        self.assertIsInstance(response, HttpResponseRedirect)
        self.res.get_aggregation_by_meta_file.assert_called_once_with(agg_meta_path)
        mock_aggregation.create_aggregation_xml_documents.assert_not_called()
