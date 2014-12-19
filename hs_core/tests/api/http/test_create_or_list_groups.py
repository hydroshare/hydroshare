import json

__author__ = 'shaunjl'
"""
Tastypie REST API tests for CreateOrListGroups.as_view() modeled after: https://github.com/hydroshare/hs_core/blob/master/tests/api/http/test_resource.py

comments- post returns TypeError, put returns HttpResponseForbidden (403)


"""
from tastypie.test import ResourceTestCase, TestApiClient
from tastypie.serializers import Serializer
from django.contrib.auth.models import Group, User
from hs_core import hydroshare


class CreateOrListGroupsTest(ResourceTestCase):
    serializer = Serializer()
    def setUp(self):

        self.api_client = TestApiClient()

        self.user = hydroshare.create_account(   
            'shaun@gmail.com',
            username='user0',
            first_name='User0_FirstName',
            last_name='User0_LastName',
            superuser=True,
            password='foobar'
        )

        g0=hydroshare.create_group(name="group0")
        g1=hydroshare.create_group(name="group1")
        g2=hydroshare.create_group(name="group2")
        self.user.groups.add(g0,g1,g2)
        self.g_ids=[g0.id,g1.id,g2.id]
            
        self.groups_url_base = '/hsapi/groups/'
        self.api_client.client.login(username=self.user.username, password=self.user.password)

    def tearDown(self):
        Group.objects.all().delete()
        User.objects.all().delete()

    def test_create_group(self):
        post_data = {'name': 'newgroup'}

        resp = self.api_client.post(self.groups_url_base, data=post_data)

        self.assertHttpCreated(resp)
        
        grouplist = Group.objects.all() 
        num_of_groups=len(grouplist)
        
        self.assertTrue(any(Group.objects.filter(name='newgroup')))
        self.assertEqual(num_of_groups, 4)

    def test_list_groups(self):

        query = self.serialize({'user': self.user.id})  

        get_data = {'query': query}

        resp = self.api_client.get(self.groups_url_base, data=get_data)
        print resp
        self.assertEqual(resp.status_code, 200)

        groups = self.deserialize(resp)
        
        new_ids = []
        for num in range(len(groups)):
            new_ids.append(groups[num]['id'])
            self.assertTrue(Group.objects.filter(user='user{0}'.format(num)).exists())
            self.assertEqual(str(groups[num]['name']), 'group{0}'.format(num))c

        self.assertEqual(sorted(self.g_ids), sorted(new_ids))



'''
from test_list_groups:
print resp
Vary: Accept-Language, Cookie
Content-Type: application/json
Content-Language: en

[{"id": 4, "name": "group0", "resource_uri": "/api/v1/group/4/"}, {"id": 5, "name": "group1",
"resource_uri": "/api/v1/group/5/"}, {"id": 6, "name": "group2", "resource_uri": "/api/v1/group/6/"}]
'''
