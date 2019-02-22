import os
import json
import tempfile
import shutil

from lxml import etree

from rest_framework import status

from hs_core.hydroshare import resource
from .base import HSRESTTestCase


class TestResourceMetadata(HSRESTTestCase):

    def setUp(self):
        super(TestResourceMetadata, self).setUp()

        self.rtype = 'GenericResource'
        self.title = 'My Test resource'
        res = resource.create_resource(self.rtype,
                                       self.user,
                                       self.title)
        self.pid = res.short_id
        self.resources_to_delete.append(self.pid)

    def test_get_sysmeta(self):
        # Get the resource system metadata
        sysmeta_url = "/hsapi/resource/{res_id}/sysmeta/".format(res_id=self.pid)
        response = self.client.get(sysmeta_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['resource_type'], self.rtype)
        self.assertEqual(content['resource_title'], self.title)
        res_tail = '/' + os.path.join('resource', self.pid) + '/'
        self.assertTrue(content['resource_url'].startswith('http://'))
        self.assertTrue(content['resource_url'].endswith(res_tail))
