from rest_framework import status

from hs_core.hydroshare import resource

from .base import HSRESTTestCase


class TestCreateResourceVersion(HSRESTTestCase):
    def setUp(self):
        super(TestCreateResourceVersion, self).setUp()

        self.rtype = 'GenericResource'
        self.title = 'My Test resource'
        res = resource.create_resource(self.rtype,
                                       self.user,
                                       self.title,
                                       unpack_file=False)

        self.pid = res.short_id

    def test_create_resource(self):
        version_url = "/hsapi/resource/%s/version/" % self.pid
        response = self.client.post(version_url, {}, format='json')
        new_pid = response.url.split('/')[4]
        self.resources_to_delete.append(new_pid)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_create_bad_resource(self):
        version_url = "/hsapi/resource/%s/version/" % "fafafa"
        response = self.client.post(version_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
