from rest_framework import status

from hs_core.hydroshare import resource
from theme.models import QuotaMessage

from .base import HSRESTTestCase


class TestCreateResourceVersion(HSRESTTestCase):
    def setUp(self):
        super(TestCreateResourceVersion, self).setUp()
        # create files
        self.n1 = "test1.txt"
        test_file = open(self.n1, 'w')
        test_file.write("Test text file in test1.txt")
        test_file.close()
        # open files for read and upload
        self.myfile1 = open(self.n1, "rb")
        self.rtype = 'CompositeResource'
        self.title = 'My Test resource'
        res = resource.create_resource(self.rtype,
                                       self.user,
                                       self.title,
                                       files=[self.myfile1],)
        self.pid = res.short_id

    def test_create_resource_version(self):
        version_url = "/hsapi/resource/%s/version/" % self.pid
        response = self.client.post(version_url, {}, format='json')
        self.resources_to_delete.append(response.content.decode())
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_create_resource_version_over_quota(self):
        """
        Test case to verify the behavior of creating a resource version when the user is over their quota.
        """
        uquota = self.user.quotas.first()
        from hs_core.tests.utils.test_utils import set_quota_usage_over_hard_limit, wait_for_quota_update
        set_quota_usage_over_hard_limit(uquota)

        version_url = "/hsapi/resource/%s/version/" % self.pid
        response = self.client.post(version_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # increase quota to allow version creation
        uquota.save_allocated_value(20, "GB")
        wait_for_quota_update(uquota)
        response = self.client.post(version_url, {}, format='json')
        self.resources_to_delete.append(response.content.decode())
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_create_version_bad_resource(self):
        version_url = "/hsapi/resource/%s/version/" % "fafafa"
        response = self.client.post(version_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
