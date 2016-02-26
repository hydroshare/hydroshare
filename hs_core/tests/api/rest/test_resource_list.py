import json

from rest_framework import status

from hs_core.hydroshare import resource
from .base import HSRESTTestCase


class TestResourceList(HSRESTTestCase):

    def test_resource_list(self):

        new_res = resource.create_resource('GenericResource',
                                           self.user,
                                           'My Test Resource')
        pid = new_res.short_id
        self.resources_to_delete.append(pid)

        response = self.client.get('/hsapi/resourceList/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 1)
        self.assertEqual(content['results'][0]['resource_id'], pid)

    def test_resource_list_by_type(self):

        gen_res = resource.create_resource('GenericResource',
                                           self.user,
                                           'My Test Resource')
        gen_pid = gen_res.short_id
        self.resources_to_delete.append(gen_pid)

        raster = open('hs_core/tests/data/cea.tif')
        geo_res = resource.create_resource('RasterResource',
                                           self.user,
                                           'My raster resource',
                                           files=(raster,))
        geo_pid = geo_res.short_id
        self.resources_to_delete.append(geo_pid)

        app_res = resource.create_resource('ToolResource',
                                           self.user,
                                           'My Test App Resource')
        app_pid = app_res.short_id
        self.resources_to_delete.append(app_pid)

        response = self.client.get('/hsapi/resourceList/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 3)
        self.assertEqual(content['results'][0]['resource_id'], gen_pid)
        self.assertEqual(content['results'][0]['resource_url'], self.resource_url.format(res_id=gen_pid))
        self.assertEqual(content['results'][1]['resource_id'], geo_pid)
        self.assertEqual(content['results'][1]['resource_url'], self.resource_url.format(res_id=geo_pid))
        self.assertEqual(content['results'][2]['resource_id'], app_pid)
        self.assertEqual(content['results'][2]['resource_url'], self.resource_url.format(res_id=app_pid))

        # Filter by type (single)
        response = self.client.get('/hsapi/resourceList/', {'type': 'RasterResource'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 1)
        self.assertEqual(content['results'][0]['resource_id'], geo_pid)
        self.assertEqual(content['results'][0]['resource_url'], self.resource_url.format(res_id=geo_pid))

        # Filter by type (multiple)
        response = self.client.get('/hsapi/resourceList/', {'type': ['RasterResource', 'ToolResource']},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 2)
        self.assertEqual(content['results'][0]['resource_id'], geo_pid)
        self.assertEqual(content['results'][0]['resource_url'], self.resource_url.format(res_id=geo_pid))
        self.assertEqual(content['results'][1]['resource_id'], app_pid)
        self.assertEqual(content['results'][1]['resource_url'], self.resource_url.format(res_id=app_pid))
