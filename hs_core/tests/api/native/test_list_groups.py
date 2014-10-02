__author__ = 'shaunjl'
"""
Tastypie API tests for list_groups 

comments-

"""
from tastypie.test import ResourceTestCase, TestApiClient
from tastypie.serializers import Serializer
from django.contrib.auth.models import Group, User
from hs_core import hydroshare

class ListGroupsTest(ResourceTestCase):
    serializer = Serializer()
    def setUp(self):
        self.user = hydroshare.create_account(   
            'shaun@gmail.com',
            username='user0',
            first_name='User0_FirstName',
            last_name='User0_LastName',
        )

        g0 = hydroshare.create_group(name="group0")
        g1 = hydroshare.create_group(name="group1")
        g2 = hydroshare.create_group(name="group2")
        self.user.groups.add(g0,g1,g2)
        self.g_ids = sorted([g0.id,g1.id,g2.id])

        self.query = {'user': self.user.id}

    def tearDown(self):
        Group.objects.all().delete()
        User.objects.all().delete()
        
    def test_using_json(self):
        q = self.serialize(self.query)
        l = hydroshare.list_groups(query=q)

        self.assertEqual(len(l),3)
        new_ids = []
        for g in l:
            new_ids.append(g.id) 

        self.assertEqual(self.g_ids,sorted(new_ids))

    def test_using_dict(self):   
        q = self.query
        l = hydroshare.list_groups(query=q)

        self.assertEqual(len(l),3)
        new_ids = []
        for g in l:
            new_ids.append(g.id) 

        self.assertEqual(self.g_ids,sorted(new_ids))

    def test_differentiate(self):
        user1 = hydroshare.create_account(   
            'joe@gmail.com',
            username='user1',
            first_name='User1_FirstName',
            last_name='User1_LastName',
        )
        g3 = hydroshare.create_group(name="group3")
        user1.groups.add(g3)

        q = self.query
        l = hydroshare.list_groups(query=q)

        self.assertEqual(len(l),3)
        new_ids = []
        for g in l:
            new_ids.append(g.id)
            
        self.assertEqual(self.g_ids,sorted(new_ids))
        self.assertNotIn(g3.id,l)

        

        
        


        
