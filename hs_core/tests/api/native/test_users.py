
import unittest

from django.contrib.auth.models import User, Group
from django.db import IntegrityError
from django.test import TestCase
from hs_core import hydroshare
from hs_core.models import GroupOwnership, GenericResource

# TODO: These unit tests can't be part of the test run until the api(s) being tested here are fixed based on access
# control api. May be since similar api for listing members of a group is already there and being tested, we don't
# need this test in hs_core. Suggestion - delete this file.


class TestUsersAPI(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @unittest.skip
    def test_create_group(self):
        user1 = hydroshare.create_account(
            'jeff@renci.org',
            username='jeff',
            first_name='Jefferson',
            last_name='Heard',
            superuser=False,
            groups=[]
        )
        user2 = hydroshare.create_account(
            'jeff.2@renci.org',
            username='jeff2',
            first_name='Jefferson',
            last_name='Heard',
            superuser=False,
            groups=[]
        )

        a_group = hydroshare.create_group(
            'A Group',
            members=[user1, user2],
            owners=[user1])

        # test that the group is the same in the database
        self.assertEqual(
            a_group,
            Group.objects.get(name='A Group')
        )

        self.assertIn(
            user1,
            [a for a in hydroshare.list_group_members(a_group)],
            msg='user1 not listed in the group membership list'
        )

        self.assertIn(
            user2,
            [a for a in hydroshare.list_group_members(a_group)],
            msg='user2 not listed in the group membership list'
        )

        self.assertIn(
            user1,
            [a.owner for a in GroupOwnership.objects.filter(group=a_group)],
            msg='user1 not listed in the group ownership list'
        )

        self.assertNotIn(
            user2,
            [a.owner for a in GroupOwnership.objects.filter(group=a_group)],
            msg='user2 listed in the group ownership list'
        )

        user1.delete()
        user2.delete()
        a_group.delete()

    @unittest.skip
    def test_create_account(self):
        a_group = hydroshare.create_group('A Group')

        # create a user with everything put in
        fully_specified_user = hydroshare.create_account(
            'jeff@renci.org',
            username='jeff',
            first_name='Jefferson',
            last_name='Heard',
            superuser=False,
            groups=[a_group]
        )

        user_without_username = hydroshare.create_account(
            'jefferson.r.heard@gmail.com',
            first_name='Jefferson',
            last_name='Heard',
            superuser=False,
            groups=[a_group]
        )

        self.assertEqual(
            fully_specified_user.username,
            'jeff',
            msg='Username got overwritten'
        )

        self.assertEqual(
            User.objects.get(username='jeff'),
            fully_specified_user
        )

        self.assertEqual(
            User.objects.get(username='jefferson.r.heard@gmail.com'),
            user_without_username
        )

        self.assertIn(
            fully_specified_user,
            [a for a in hydroshare.list_group_members(a_group)],
            msg='user not listed in the group membership list'
        )

        user_without_username.delete()
        fully_specified_user.delete()
        a_group.delete()


