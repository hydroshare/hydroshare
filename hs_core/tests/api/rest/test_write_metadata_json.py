import json
from unittest import mock

from rest_framework import status
from django.conf import settings

from hs_core.hydroshare import resource
from hs_core.tests.api.rest.base import HSRESTTestCase

def get_response_content(response):
    """
    Helper function to get the content from a response, handling both JSON and HTML responses.
    """
    if hasattr(response, 'data'):
        # DRF response with data attribute
        return json.dumps(response.data)
    elif hasattr(response, 'content'):
        # Response with content attribute
        content = response.content.decode('utf-8')
        try:
            # Try to parse as JSON
            return json.dumps(json.loads(content))
        except json.JSONDecodeError:
            # Not JSON, return as is
            return content
    else:
        # Fallback
        return str(response)


class TestWriteMetadataJSON(HSRESTTestCase):
    def setUp(self):
        super(TestWriteMetadataJSON, self).setUp()

        self.rtype = 'CompositeResource'
        self.title = 'Test Resource'
        res = resource.create_resource(self.rtype,
                                       self.user,
                                       self.title)
        self.resource = res
        self.pid = res.short_id
        self.resources_to_delete.append(self.pid)

        # Store the original API_KEY setting
        self.original_api_key = getattr(settings, 'API_KEY', None)
        # Set a test API key for testing
        settings.API_KEY = 'test_api_key_for_testing'

    def tearDown(self):
        super(TestWriteMetadataJSON, self).tearDown()
        # Restore the original API_KEY setting
        if self.original_api_key:
            settings.API_KEY = self.original_api_key
        else:
            delattr(settings, 'API_KEY')

    @mock.patch('hs_core.views.resource_rest_api.save_resource_metadata_json')
    def test_write_metadata_json_success(self, mock_save_metadata_json):
        """Test that the WriteMetadataJSON endpoint works correctly with valid API key"""
        # Clear any existing authentication
        self.client.logout()
        self.client.force_authenticate(user=None)

        # Make the request with API key in header
        url = f"/hsapi/resource/{self.pid}/write-metadata/json/"
        response = self.client.put(url, HTTP_X_API_KEY=settings.API_KEY)

        # Check that the response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that save_resource_metadata_json was called with the correct resource
        mock_save_metadata_json.assert_called_once()
        called_resource = mock_save_metadata_json.call_args[0][0]
        self.assertEqual(called_resource.short_id, self.pid)

    def test_write_metadata_json_missing_api_key(self):
        """Test that requests without API key are rejected"""
        # Clear any existing authentication
        self.client.logout()
        self.client.force_authenticate(user=None)

        # Make the request without API key
        url = f"/hsapi/resource/{self.pid}/write-metadata/json/"
        response = self.client.put(url)

        # Without API key, the request should be rejected with 403 Forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response_content = get_response_content(response)
        self.assertIn('API key is required', response_content)

    def test_write_metadata_json_invalid_api_key(self):
        """Test that requests with invalid API key are rejected"""
        # Clear any existing authentication
        self.client.logout()
        self.client.force_authenticate(user=None)

        # Make the request with invalid API key
        url = f"/hsapi/resource/{self.pid}/write-metadata/json/"
        response = self.client.put(url, HTTP_X_API_KEY='invalid_api_key')

        # Check that the response is forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response_content = get_response_content(response)
        # The exact error message might vary, so we'll just check that it contains 'Invalid API key'
        self.assertIn('Invalid API key', response_content)

    def test_write_metadata_json_resource_not_found(self):
        """Test that the endpoint returns 404 for non-existent resources"""
        # Clear any existing authentication
        self.client.logout()
        self.client.force_authenticate(user=None)

        # Make the request with a non-existent resource ID
        url = "/hsapi/resource/nonexistent-id/write-metadata/json/"
        response = self.client.put(url, HTTP_X_API_KEY=settings.API_KEY)

        # Check that the response is not found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # For a non-existent resource, the server returns an HTML page with "Page not found"
        # instead of a JSON response
        response_content = get_response_content(response)
        self.assertIn('Page not found', response_content)

    @mock.patch('hs_core.views.resource_rest_api.save_resource_metadata_json')
    def test_write_metadata_json_error(self, mock_save_metadata_json):
        """Test that the endpoint handles errors from save_resource_metadata_json"""
        # Set up the mock to raise an exception
        mock_save_metadata_json.side_effect = Exception("Test error")

        # Clear any existing authentication
        self.client.logout()
        self.client.force_authenticate(user=None)

        # Make the request with API key
        url = f"/hsapi/resource/{self.pid}/write-metadata/json/"
        response = self.client.put(url, HTTP_X_API_KEY=settings.API_KEY)

        # Check that the response is an error
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        response_content = get_response_content(response)
        self.assertIn('Error saving metadata JSON files: Test error', response_content)
