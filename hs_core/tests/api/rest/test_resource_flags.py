from rest_framework import status

from hs_core.hydroshare import resource

from .base import HSRESTTestCase


class TestPublicResourceFlagsEndpoint(HSRESTTestCase):
    def setUp(self):
        super(TestPublicResourceFlagsEndpoint, self).setUp()

        self.rtype = 'GenericResource'
        self.title = 'My Test resource'
        res = resource.create_resource(self.rtype,
                                       self.user,
                                       self.title)

        self.pid = res.short_id
        self.resources_to_delete.append(self.pid)

    def test_set_resource_flag_make_public(self):
        flag_url = "/hsapi/resource/%s/flag/" % self.pid
        response = self.client.post(flag_url, {
            "t": "make_public"
        }, format='json')
        self.assertEqual(response.context, None)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_set_resource_flag_make_private(self):
        flag_url = "/hsapi/resource/%s/flag/" % self.pid
        response = self.client.post(flag_url, {
            "t": "make_private"
        }, format='json')
        self.assertEqual(response.context, None)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_set_resource_flag_make_discoverable(self):
        flag_url = "/hsapi/resource/%s/flag/" % self.pid
        response = self.client.post(flag_url, {
            "t": "make_discoverable"
        }, format='json')
        self.assertEqual(response.context, None)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_set_resource_flag_make_not_discoverable(self):
        flag_url = "/hsapi/resource/%s/flag/" % self.pid
        response = self.client.post(flag_url, {
            "t": "make_not_discoverable"
        }, format='json')
        self.assertEqual(response.context, None)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_set_resource_flag_make_not_shareable(self):
        flag_url = "/hsapi/resource/%s/flag/" % self.pid
        response = self.client.post(flag_url, {
            "t": "make_not_shareable"
        }, format='json')
        self.assertEqual(response.context, None)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_set_resource_flag_make_shareable(self):
        flag_url = "/hsapi/resource/%s/flag/" % self.pid
        response = self.client.post(flag_url, {
            "t": "make_shareable"
        }, format='json')
        self.assertEqual(response.context, None)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
