import json

from rest_framework import status

from hs_core.hydroshare import resource
from .base import HSRESTTestCase


class TestSetAccessRules(HSRESTTestCase):

    def test_set_access_rules(self):
        rtype = 'GenericResource'
        title = 'My Test resource'
        keywords = ('foo', 'bar')
        abstract = 'This is a resource used for testing /hsapi/accessRules'
        new_res = resource.create_resource(rtype,
                                           self.user,
                                           title,
                                           keywords=keywords)
        new_res.metadata.create_element('description', abstract=abstract)
        res_id = new_res.short_id
        self.resources_to_delete.append(res_id)

        sysmeta_url = "/hsapi/sysmeta/{res_id}/".format(res_id=res_id)
        response = self.client.get(sysmeta_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['resource_type'], rtype)
        self.assertEqual(content['resource_title'], title)
        self.assertFalse(content['public'])

        access_url = "/hsapi/resource/accessRules/{res_id}/".format(res_id=res_id)
        response = self.client.put(access_url, {'public': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(sysmeta_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertTrue(content['public'])