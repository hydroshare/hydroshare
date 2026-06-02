from django.urls import reverse
from django.utils.dateparse import parse_datetime

from hs_core.tests.api.rest.base import HSRESTTestCase
from unittest import skip


class TestServiceAccountMinIO(HSRESTTestCase):

    def test_create_service_account_expiry_defaults_and_override(self):
        service_account_url = reverse('minio_service_accounts')

        # default expiry should be 180 days
        response = self.client.post(service_account_url, data={}, format='json')
        self.assertEqual(response.status_code, 201)
        response_json = response.json()
        created = parse_datetime(response_json['created'])
        expiry = parse_datetime(response_json['expiry'])
        self.assertIsNotNone(created)
        self.assertIsNotNone(expiry)
        self.assertEqual((expiry - created).days, 180)

        # custom expiry should honor the request value (days)
        response = self.client.post(service_account_url, data={'expiry': 1}, format='json')
        self.assertEqual(response.status_code, 201)
        response_json = response.json()
        created = parse_datetime(response_json['created'])
        expiry = parse_datetime(response_json['expiry'])
        self.assertIsNotNone(created)
        self.assertIsNotNone(expiry)
        self.assertEqual((expiry - created).days, 1)

    def test_create_service_account_invalid_expiry(self):
        service_account_url = reverse('minio_service_accounts')

        response = self.client.post(service_account_url, data={'expiry': 0}, format='json')
        self.assertEqual(response.status_code, 400)

        response = self.client.post(service_account_url, data={'expiry': 'abc'}, format='json')
        self.assertEqual(response.status_code, 400)

    @skip("Skipping, hs-s3-auth needs to be configured to use the test database")
    def test_add_list_remove_service_account(self):
        # create
        service_account_url = reverse('minio_service_accounts')
        response = self.client.post(service_account_url)
        self.assertEqual(response.status_code, 201)
        response_json = response.json()
        self.assertIn('access_key', response_json)
        self.assertIn('secret_key', response_json)
        access_key = response_json['access_key']
        service_account_key = access_key.split(':', 1)[1]

        # list
        response = self.client.get(service_account_url)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertIn('service_accounts', response_json)
        service_account = response_json['service_accounts'][0]
        self.assertTrue(service_account['access_key'].endswith(f":{service_account_key}"))

        # delete
        service_account_delete_url = reverse('minio_service_accounts_delete',
                                             kwargs={'access_key': access_key})
        response = self.client.delete(service_account_delete_url)
        self.assertEqual(response.status_code, 204)
