__author__ = 'Tian Gan'

## unit test for list_group_member() from users.py
from django.test import TestCase
from django.contrib.auth.models import User, Group
from hs_core import hydroshare


class TestListGroupMembers(TestCase):
    def setUp(self):
        # create 2 users
        self.user1 = hydroshare.create_account(
            'user1@gmail.com',
            username='user1',
            first_name='user1_first',
            last_name='user1_last',
            superuser=False,
            groups=[]
        )

        self.user2 = hydroshare.create_account(
            'user2@gmail.com',
            username='user2',
            first_name='user2_first',
            last_name='user2_last',
            superuser=False,
            groups=[]
        )
        # create 1 group
        self.group = hydroshare.create_group(
            'Test group',
            members=[self.user2],
            owners=[self.user1]
        )

    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()

    def test_list_group_members(self):
        # assign group instance to get the member list
        print list(hydroshare.list_group_members(self.group))
        self.assertListEqual(
            list(hydroshare.list_group_members(self.group)),
            [self.user2],
            msg='pass group instance can not return group member list'
        )

        # assign group name to get the member list
        self.assertListEqual(
            list(hydroshare.list_group_members(self.group.name)),
            [self.user2],
            msg='pass group name can not return group member list'
        )

        # assign group pk to get the member list
        self.assertListEqual(
            list(hydroshare.list_group_members(self.group.pk)),
            [self.user2],
            msg='pass group pk can not return group member list'
        )