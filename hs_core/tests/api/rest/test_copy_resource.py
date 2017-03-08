import os
import tempfile
import zipfile

from rest_framework import status

from hs_core.hydroshare import resource
from hs_core.tests.api.utils import MyTemporaryUploadedFile

from .base import HSRESTTestCase


class TestPublicCopyResourceEndpoint(HSRESTTestCase):
    def setUp(self):
        super(TestPublicCopyResourceEndpoint, self).setUp()

        self.rtype = 'GenericResource'
        self.title = 'My Test resource'
        res = resource.create_resource(self.rtype,
                                       self.user,
                                       self.title)

        self.pid = res.short_id
        self.resources_to_delete.append(self.pid)

    def test_copy(self):
        copy_url = "/hsapi/resource/%s/copy/" % self.pid
        response = self.client.post(copy_url, {}, format='json')
        new_pid = response.url.split('/')[4]
        self.resources_to_delete.append(new_pid)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_copy_bad_resource(self):
        copy_url = "/hsapi/resource/%s/copy/" % "lalalal"
        response = self.client.post(copy_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)