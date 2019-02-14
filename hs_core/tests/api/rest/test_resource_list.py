import json
import os

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

        response = self.client.get('/hsapi/resource/', format='json')
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

        # pattern for end of all URLS
        res_tail = '/' + os.path.join('resource', '{res_id}') + '/'

        response = self.client.get('/hsapi/resource/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 3)

        self.assertEqual(content['results'][0]['resource_id'], gen_pid)
        self.assertTrue(content['results'][0]['resource_url'].startswith("http://"))
        self.assertTrue(content['results'][0]['resource_url']
                        .endswith(res_tail.format(res_id=gen_pid)))

        self.assertEqual(content['results'][1]['resource_id'], geo_pid)
        self.assertTrue(content['results'][1]['resource_url'].startswith("http://"))
        self.assertTrue(content['results'][1]['resource_url']
                        .endswith(res_tail.format(res_id=geo_pid)))

        self.assertEqual(content['results'][2]['resource_id'], app_pid)
        self.assertTrue(content['results'][2]['resource_url'].startswith("http://"))
        self.assertTrue(content['results'][2]['resource_url']
                        .endswith(res_tail.format(res_id=app_pid)))

        # Filter by type (single)
        response = self.client.get('/hsapi/resource/', {'type': 'RasterResource'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)

        self.assertEqual(content['count'], 1)
        self.assertEqual(content['results'][0]['resource_id'], geo_pid)
        self.assertTrue(content['results'][0]['resource_url'].startswith("http://"))
        self.assertTrue(content['results'][0]['resource_url']
                        .endswith(res_tail.format(res_id=geo_pid)))

        # Filter by type (multiple)
        response = self.client.get('/hsapi/resource/', {'type': ['RasterResource', 'ToolResource']},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 2)

        self.assertEqual(content['results'][0]['resource_id'], geo_pid)
        self.assertTrue(content['results'][0]['resource_url'].startswith("http://"))
        self.assertTrue(content['results'][0]['resource_url']
                        .endswith(res_tail.format(res_id=geo_pid)))

        self.assertEqual(content['results'][1]['resource_id'], app_pid)
        self.assertTrue(content['results'][1]['resource_url'].startswith("http://"))
        self.assertTrue(content['results'][1]['resource_url']
                        .endswith(res_tail.format(res_id=app_pid)))

    def test_resource_list_by_keyword(self):
        gen_res_one = resource.create_resource('GenericResource', self.user, 'Resource 1')
        gen_res_two = resource.create_resource('GenericResource', self.user, 'Resource 2')
        gen_res_three = resource.create_resource('GenericResource', self.user, 'Resource 3')
        gen_res_four = resource.create_resource('GenericResource', self.user, 'Resource 2')

        self.resources_to_delete.append(gen_res_one.short_id)
        self.resources_to_delete.append(gen_res_two.short_id)
        self.resources_to_delete.append(gen_res_three.short_id)
        self.resources_to_delete.append(gen_res_four.short_id)

        gen_res_one.metadata.create_element("subject", value="one")
        gen_res_two.metadata.create_element("subject", value="other")
        gen_res_three.metadata.create_element("subject", value="One")
        gen_res_four.metadata.create_element("subject", value="Other")

        response = self.client.get('/hsapi/resource/', {'subject': 'one'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 2)

        response = self.client.get('/hsapi/resource/', {'subject': 'other'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 2)

        response = self.client.get('/hsapi/resource/', {'subject': 'one,other'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 4)

        response = self.client.get('/hsapi/resource/', {'subject': 'oth'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 2)

    def test_resource_list_obsolete(self):
        gen_res_one = resource.create_resource('GenericResource', self.user, 'Resource 1')
        # make a new version of gen_res_one to make gen_res_one obsolete
        new_ver_gen_res_one = resource.create_empty_resource(gen_res_one.short_id, self.user)

        new_ver_gen_res_one = resource.create_new_version_resource(gen_res_one,
                                                                   new_ver_gen_res_one, self.user)

        self.resources_to_delete.append(new_ver_gen_res_one.short_id)
        self.resources_to_delete.append(gen_res_one.short_id)

        # the default for include_obsolete is False which should NOT return obsoleted resources
        response = self.client.get('/hsapi/resource/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 1)
        self.assertEqual(content['results'][0]['resource_id'], new_ver_gen_res_one.short_id)

        # set include_obsolete to True, which should return all resources including obsoleted ones
        response = self.client.get('/hsapi/resource/', {'include_obsolete': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 2)

        result_res_id_list = []
        result_res_id_list.append(content['results'][0]['resource_id'])
        result_res_id_list.append(content['results'][1]['resource_id'])

        self.assertIn(new_ver_gen_res_one.short_id, result_res_id_list,
                      msg='new versioned resource id is not included in returned resource list')
        self.assertIn(gen_res_one.short_id, result_res_id_list,
                      msg='obsoleted resource id is not included in returned resource list')

    def test_resource_list_by_bounding_box(self):
        metadata_dict_one = [{'coverage': {'type': 'box', 'value': {'northlimit': '80',
                                                                    'eastlimit': '40',
                                                                    'southlimit': '60',
                                                                    'westlimit': '20',
                                                                    'units': 'decimal deg'}}}]
        gen_res_one = resource.create_resource('GenericResource', self.user, 'Resource 1',
                                               metadata=metadata_dict_one)

        metadata_dict_two = [{'coverage': {'type': 'box', 'value': {'northlimit': '60',
                                                                    'eastlimit': '110',
                                                                    'southlimit': '50',
                                                                    'westlimit': '90',
                                                                    'units': 'decimal deg'}}}]
        gen_res_two = resource.create_resource('GenericResource', self.user, 'Resource 2',
                                               metadata=metadata_dict_two)

        metadata_dict_two = [{'coverage': {'type': 'point', 'value': {'north': '70',
                                                                      'east': '70',
                                                                      'units': 'decimal deg'}}}]
        gen_res_three = resource.create_resource('GenericResource', self.user, 'Resource 2',
                                                 metadata=metadata_dict_two)

        self.resources_to_delete.append(gen_res_one.short_id)
        self.resources_to_delete.append(gen_res_two.short_id)
        self.resources_to_delete.append(gen_res_three.short_id)

        response = self.client.get('/hsapi/resource/', {'coverage_type': 'box',
                                                        'north': '70',
                                                        'east': '50',
                                                        'south': '50',
                                                        'west': '30'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 1)

        response = self.client.get('/hsapi/resource/', {'coverage_type': 'box',
                                                        'north': '70',
                                                        'east': '120',
                                                        'south': '40',
                                                        'west': '100'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 1)

        response = self.client.get('/hsapi/resource/', {'coverage_type': 'box',
                                                        'north': '90',
                                                        'east': '140',
                                                        'south': '30',
                                                        'west': '0'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 3)

        # Bad coverage has no effect
        response = self.client.get('/hsapi/resource/', {'coverage_type': 'bad',
                                                        'nonsensical': '90',
                                                        'params': '140'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resource_list_by_group(self):
        group_one = self.user.uaccess.create_group(title='Group One',
                                                   description='This is a great group',
                                                   purpose='To have fun',
                                                   auto_approve=True)
        group_two = self.user.uaccess.create_group(title='Group Two',
                                                   description='This is another great group',
                                                   purpose='To have fun',
                                                   auto_approve=True)
        gen_res_one = resource.create_resource('GenericResource', self.user, 'Resource 1',
                                               edit_groups=[group_one, group_two], view_groups=None)
        gen_res_two = resource.create_resource('GenericResource', self.user, 'Resource 2',
                                               edit_groups=None, view_groups=[group_one, group_two])
        gen_res_three = resource.create_resource('GenericResource', self.user, 'Resource 3',
                                                 edit_groups=[group_one], view_groups=None)
        gen_res_four = resource.create_resource('GenericResource', self.user, 'Resource 4',
                                                edit_groups=None, view_groups=None)

        self.groups_to_delete.append(group_one)
        self.groups_to_delete.append(group_two)
        self.resources_to_delete.append(gen_res_one.short_id)
        self.resources_to_delete.append(gen_res_two.short_id)
        self.resources_to_delete.append(gen_res_three.short_id)
        self.resources_to_delete.append(gen_res_four.short_id)

        # resources by group id
        response = self.client.get('/hsapi/resource/', {'group': str(group_one.pk)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 3)

        response = self.client.get('/hsapi/resource/', {'group': str(group_two.pk)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 2)

        # resources by group name
        response = self.client.get('/hsapi/resource/', {'group': str(group_one.name)},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 3)

        response = self.client.get('/hsapi/resource/', {'group': str(group_two.name)},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 2)

    def test_resource_list_by_user(self):
        # HSRESTTestCase is forcing authentication of user, so we'll just test that user
        gen_res_one = resource.create_resource('GenericResource', self.user, 'Resource 1')
        gen_res_two = resource.create_resource('GenericResource', self.user, 'Resource 2')
        gen_res_three = resource.create_resource('GenericResource', self.user, 'Resource 3')

        self.resources_to_delete.append(gen_res_one.short_id)
        self.resources_to_delete.append(gen_res_two.short_id)
        self.resources_to_delete.append(gen_res_three.short_id)

        # resources by owner username
        response = self.client.get('/hsapi/resource/', {'owner': self.user.username}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 3)

        # resources by owner email
        response = self.client.get('/hsapi/resource/', {'owner': self.user.email}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 3)

        # resources by creator username
        response = self.client.get('/hsapi/resource/', {'creator': self.user.username},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 3)

        # resources by creator email
        response = self.client.get('/hsapi/resource/', {'creator': self.user.email}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 3)

        # resources by user username
        response = self.client.get('/hsapi/resource/', {'user': self.user.username},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 3)

        # resources by user email
        response = self.client.get('/hsapi/resource/', {'user': self.user.email}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 3)

        # resources by author email
        response = self.client.get('/hsapi/resource/', {'author': self.user.email}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 3)

        # resources by author email bad
        response = self.client.get('/hsapi/resource/',
                                   {'author': ','.join(self.user.email + "bad")}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 0)

        # resources by author bad
        response = self.client.get('/hsapi/resource/', {'author': "bad"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 0)
