from rest_framework import status

from hs_core.hydroshare import resource

from .base import HSRESTTestCase


class TestCustomScimetaEndpoint(HSRESTTestCase):
    V2_API_ROOT = "/api/v2/resource"

    def setUp(self):
        super(TestCustomScimetaEndpoint, self).setUp()

        self.rtype = 'GenericResource'
        self.title = 'My Test resource'
        res = resource.create_resource(self.rtype,
                                       self.user,
                                       self.title)

        self.pid = res.short_id
        self.resources_to_delete.append(self.pid)

    def test_DEPRECATED_set_custom_metadata_multiple(self, root="/hsapi/resource"):
        set_metadata = root + "/%s/scimeta/custom/" % self.pid

        response = self.client.post(set_metadata, {
            "foo": "bar",
            "foo2": "bar2"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_set_custom_metadata_multiple(self):
        self.test_DEPRECATED_set_custom_metadata_multiple(root=self.V2_API_ROOT)

    def test_DEPRECATED_set_custom_metadata_single(self, root="/hsapi/resource"):
        set_metadata = root + "/%s/scimeta/custom/" % self.pid
        response = self.client.post(set_metadata, {
            "foo": "bar"
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_set_custom_metadata_single(self):
        self.test_DEPRECATED_set_custom_metadata_single(root=self.V2_API_ROOT)
