from django.conf import settings

from rest_framework import status
from .base import HSRESTTestCase
from hs_core.hydroshare import users


class TestInternalQuotaUpdateEndpoint(HSRESTTestCase):
    def setUp(self):
        super(TestInternalQuotaUpdateEndpoint, self).setUp()
        if settings.IRODS_SERVICE_ACCOUNT_USERNAME:
            # create the service account which needs to be authenticated in order to update quota
            self.irods_user = users.create_account(
                "irods@email.com",
                username=settings.IRODS_SERVICE_ACCOUNT_USERNAME,
                password="irods",
                first_name="irods",
                last_name="service",
                superuser=False,
            )

    def tearDown(self):
        super(TestInternalQuotaUpdateEndpoint, self).tearDown()
        if settings.IRODS_SERVICE_ACCOUNT_USERNAME:
            self.irods_user.delete()

    def test_quota_update_requests(self):
        if settings.IRODS_SERVICE_ACCOUNT_USERNAME:
            url = "/hsapi/_internal/update_quota_usage/{}/".format(self.user.username)
            response = self.client.post(url, {}, format="json")
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

            self.client.force_authenticate(user=self.irods_user)
            self.client.login(
                username=settings.IRODS_SERVICE_ACCOUNT_USERNAME, password="irods"
            )
            invalid_url = "/hsapi/_internal/update_quota_usage/invalid_user/"
            response = self.client.post(invalid_url, {}, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            response = self.client.post(url, {}, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
