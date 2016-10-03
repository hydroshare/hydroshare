import os
import json
import tempfile
import shutil
from rest_framework import status

# from lxml import etree

from hs_core.hydroshare import resource
from .base import ResMapTestCase


class TestResourceMap(ResMapTestCase):

    def setUp(self):
        super(TestResourceMap, self).setUp()

        self.rtype = 'GenericResource'
        self.title = 'My Test resource'
        res = resource.create_resource(self.rtype,
                                       self.user,
                                       self.title)

        self.pid = res.short_id
        self.resources_to_delete.append(self.pid)
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)
        super(TestResourceMap, self).tearDown()

    def test_get_resmap(self):
        response = self.client.get("/hsapi/resmap/{pid}/".format(pid=self.pid),
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        response2 = self.client.get(response.url, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        content = json.loads(response2.content)

        # validate that this is an empty resource map.
        self.assertEqual(content['count'], 0)

        # now create a file in the resource map
        txt_file_name = 'text.txt'
        txt_file_path = os.path.join(self.tmp_dir, txt_file_name)
        txt = open(txt_file_path, 'w')
        txt.write("Hello World.\n")
        txt.close()

        # Upload the new resource file
        params = {'file': (txt_file_name,
                           open(txt_file_path),
                           'text/plain')}
        url = "/hsapi/resource/{pid}/files/".format(pid=self.pid)
        response = self.client.post(url, params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content = json.loads(response.content)
        self.assertEquals(content['resource_id'], self.pid)

        # Make sure the new file appears in the resource map
        response = self.client.get("/hsapi/resmap/{pid}/".format(pid=self.pid))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        response2 = self.client.get(response.url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        # TODO: parse XML response 
