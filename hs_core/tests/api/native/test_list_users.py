__author__ = 'shaunjl'
"""
Tastypie API tests for list_users

comments-

"""
from tastypie.test import ResourceTestCase, TestApiClient
from tastypie.serializers import Serializer
from django.contrib.auth.models import User
from hs_core import hydroshare

class ListUsersTest(ResourceTestCase):
    serializer = Serializer()
    def setUp(self):
        u0 = hydroshare.create_account(
            'shaun@gmail.com',
            username='user0',
            first_name='User0_FirstName',
            last_name='User0_LastName',
        )
        u1 = hydroshare.create_account(
            'shaun@gmail.com',
            username='user1',
            first_name='User1_FirstName',
            last_name='User1_LastName',
        )
        u2 = hydroshare.create_account(
            'shaun@gmail.com',
            username='user2',
            first_name='User2_FirstName',
            last_name='User2_LastName',
        )

        self.u_ids=[u0.id,u1.id,u2.id]

        self.query = {'email':'shaun@gmail.com'}

    def tearDown(self):
        User.objects.all().delete()

    def test_using_json(self):
        q = self.serialize(self.query)
        l = hydroshare.list_users(query=q)
        self.assertEqual(len(l),3)
        new_ids = []
        for u in l:
            new_ids.append(u.id)

        self.assertEqual(self.u_ids,sorted(new_ids))

    def test_using_dict(self):
        q = self.query
        l = hydroshare.list_users(query=q)

        self.assertEqual(len(l),3)
        new_ids = []
        for u in l:
            new_ids.append(u.id)

        self.assertEqual(self.u_ids,sorted(new_ids))

    def test_differentiate(self):
        new_user = hydroshare.create_account(
            'joe@gmail.com',
            username='user3',
            first_name='User3_FirstName',
            last_name='User3_LastName',
        )

        q = self.query
        l = hydroshare.list_users(query=q)

        self.assertEqual(len(l),3)
        new_ids = []
        for u in l:
            new_ids.append(u.id)

        self.assertEqual(self.u_ids,sorted(new_ids))
        self.assertNotIn(new_user.id,l)
