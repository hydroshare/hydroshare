import json

from rest_framework import status

from hs_core.hydroshare import resource
from hs_access_control.models import PrivilegeCodes
from .base import HSRESTTestCase
from hs_core.hydroshare import users


class TestSetAccessRules(HSRESTTestCase):
    def setUp(self):
        super(TestSetAccessRules, self).setUp()
        self.secondUser = users.create_account(
            'test_user1@email.com',
            username='testuser1',
            first_name='some_first_name1',
            last_name='some_last_name1',
            groups=[],
            superuser=False)
        self.testGroup = self.user.uaccess.create_group(
            title="Test Group",
            description="Group for testing")

    def tearDown(self):
        super(TestSetAccessRules, self).tearDown()
        self.secondUser.delete()
        self.testGroup.delete()

    def test_get_access_rules_via_sysmeta(self):
        rtype = 'GenericResource'
        title = 'My Test resource'
        keywords = ('foo', 'bar')
        abstract = 'This is a resource used for testing /hsapi/resource/{id}/access/'
        new_res = resource.create_resource(rtype,
                                           self.user,
                                           title,
                                           keywords=keywords)
        new_res.metadata.create_element('description', abstract=abstract)
        res_id = new_res.short_id
        self.resources_to_delete.append(res_id)

        sysmeta_url = "/hsapi/resource/{res_id}/sysmeta/".format(res_id=res_id)
        response = self.client.get(sysmeta_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['resource_type'], rtype)
        self.assertEqual(content['resource_title'], title)
        self.assertFalse(content['public'])

    def test_get_resource_access(self):
        rtype = 'GenericResource'
        title = 'My Test resource'
        keywords = ('foo', 'bar')
        abstract = 'This is a resource used for testing /hsapi/resource/{id}/access/'
        new_res = resource.create_resource(rtype,
                                           self.user,
                                           title,
                                           keywords=keywords)
        new_res.metadata.create_element('description', abstract=abstract)
        res_id = new_res.short_id
        self.resources_to_delete.append(res_id)

        access_url = "/hsapi/resource/{res_id}/access/".format(res_id=res_id)
        response = self.client.get(access_url)
        self.assertEqual(1, len(response.data['users']))
        self.assertEqual(0, len(response.data['groups']))
        self.assertEqual("Owner", response.data['users'][0]['privilege'])
        self.assertEqual(self.user.id, response.data['users'][0]['user'])

    def test_set_and_delete_user_resource_access(self):
        rtype = 'GenericResource'
        title = 'My Test resource'
        keywords = ('foo', 'bar')
        abstract = 'This is a resource used for testing /hsapi/resource/{id}/access/'
        new_res = resource.create_resource(rtype,
                                           self.user,
                                           title,
                                           keywords=keywords)
        new_res.metadata.create_element('description', abstract=abstract)
        res_id = new_res.short_id
        self.resources_to_delete.append(res_id)

        access_url = "/hsapi/resource/{res_id}/access/".format(res_id=res_id)
        put_response = self.client.put(access_url, {
            "privilege": PrivilegeCodes.VIEW,
            "user_id": self.secondUser.id
        }, format='json')
        self.assertEqual("Resource access privileges added.", put_response.data['success'])

        get_response = self.client.get(access_url)
        self.assertEqual(2, len(get_response.data['users']))
        self.assertEqual(0, len(get_response.data['groups']))

        delete_response = self.client.delete(access_url + "?user_id=" + str(self.secondUser.id))
        self.assertEqual("Resource access privileges removed.", delete_response.data['success'])

        get_response = self.client.get(access_url)
        self.assertEqual(1, len(get_response.data['users']))

    def test_set_and_delete_group_resource_access(self):
        rtype = 'GenericResource'
        title = 'My Test resource'
        keywords = ('foo', 'bar')
        abstract = 'This is a resource used for testing /hsapi/resource/{id}/access/'
        new_res = resource.create_resource(rtype,
                                           self.user,
                                           title,
                                           keywords=keywords)
        new_res.metadata.create_element('description', abstract=abstract)
        res_id = new_res.short_id
        self.resources_to_delete.append(res_id)

        access_url = "/hsapi/resource/{res_id}/access/".format(res_id=res_id)
        put_response = self.client.put(access_url, {
            "privilege": PrivilegeCodes.VIEW,
            "group_id": self.testGroup.id
        }, format='json')
        self.assertEqual("Resource access privileges added.", put_response.data['success'])

        get_response = self.client.get(access_url)
        self.assertEqual(1, len(get_response.data['users']))
        self.assertEqual(1, len(get_response.data['groups']))

        delete_response = self.client.delete(access_url + "?group_id=" + str(self.testGroup.id))
        self.assertEqual("Resource access privileges removed.", delete_response.data['success'])

        get_response = self.client.get(access_url)
        self.assertEqual(0, len(get_response.data['groups']))

    def test_no_access(self):
        rtype = 'GenericResource'
        title = 'My Test resource'
        keywords = ('foo', 'bar')
        abstract = 'This is a resource used for testing /hsapi/resource/{id}/access/'
        new_res = resource.create_resource(rtype,
                                           self.secondUser,
                                           title,
                                           keywords=keywords)
        new_res.metadata.create_element('description', abstract=abstract)
        res_id = new_res.short_id
        self.resources_to_delete.append(res_id)

        access_url = "/hsapi/resource/{res_id}/access/".format(res_id=res_id)

        put_response = self.client.put(access_url, {
            "privilege": PrivilegeCodes.VIEW,
            "group_id": self.testGroup.id
        }, format='json')
        self.assertEqual("You do not have permission to perform this action.", put_response.data['detail'])

    def test_errors(self):
        rtype = 'GenericResource'
        title = 'My Test resource'
        keywords = ('foo', 'bar')
        abstract = 'This is a resource used for testing /hsapi/resource/{id}/access/'
        new_res = resource.create_resource(rtype,
                                           self.user,
                                           title,
                                           keywords=keywords)
        new_res.metadata.create_element('description', abstract=abstract)
        res_id = new_res.short_id
        self.resources_to_delete.append(res_id)

        access_url = "/hsapi/resource/{res_id}/access/".format(res_id=res_id)

        # Empty PUT
        put_response = self.client.put(access_url, {}, format='json')
        self.assertEqual(
            "Request must contain a 'resource' ID as well as a 'user_id' or " \
                  "'group_id', and 'privilege' must be one of 1, 2, or 3.",
            put_response.data['error'])

        # Incorrect PUT
        put_response = self.client.put(access_url, {
            "user_id": self.secondUser.id,
            "group_id": self.testGroup.id
        }, format='json')
        self.assertEqual(
            "Request cannot contain both a 'user_id' and a 'group_id' parameter.",
            put_response.data['error'])

        # Empty DELETE
        delete_response = self.client.delete(access_url)
        self.assertEqual(
            "Request must contain a 'resource' ID as well as a 'user_id' or 'group_id'",
            delete_response.data['error'])

        # Incorrect DELETE
        delete_response = self.client.put(access_url + "?user_id=2&group_id=3")
        self.assertEqual(
            "Request cannot contain both a 'user_id' and a 'group_id' parameter.",
            put_response.data['error'])



