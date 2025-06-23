from django.urls import reverse

from hs_core.tests.api.rest.base import HSRESTTestCase


class TestServiceAccountMinIO(HSRESTTestCase):
    
    def setUp(self):
        super(TestServiceAccountMinIO, self).setUp()

    def test_add_list_remove_service_account(self):
        # create
        service_account_url = reverse('minio_service_accounts')
        response = self.client.post(service_account_url)
        self.assertEqual(response.status_code, 201)
        response_json = response.json()
        self.assertIn('access_key', response_json)
        self.assertIn('secret_key', response_json)
        access_key = response_json['access_key']

        # list
        response = self.client.get(service_account_url)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertIn('service_accounts', response_json)
        service_account = response_json['service_accounts'][0]
        self.assertEqual(service_account['access_key'], access_key)

        # delete
        service_account_delete_url = reverse('minio_service_accounts_delete',
                                             kwargs={'service_account_key': access_key})
        response = self.client.delete(service_account_delete_url)
        self.assertEqual(response.status_code, 204)