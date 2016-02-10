__author__ = 'Pabitra'

# TODO: These unit tests are for the update_group() api which needs to be updated based on access_control app. Until
# then these unit tests have to be skipped from test run

import unittest

from django.test import TestCase
from django.contrib.auth.models import User, Group
from hs_core.models import GroupOwnership
from hs_core import hydroshare

class TestUpdateGroupAPI(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        GroupOwnership.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()
        pass

    @unittest.skip
    def test_update_group_to_add_member(self):
        user_member_1 = hydroshare.create_account(
            'member_1@usu.edu',
            username='member_1',
            first_name='Member_1_FirstName',
            last_name='Member_1_LastName',
            superuser=False,
            groups=[]
        )

        group_name = 'Test Group'
        test_group = hydroshare.create_group(group_name)

        # this is the api call we are testing
        hydroshare.update_group(test_group, members=[user_member_1])

        # test at this point the group should have one member
        group_members = User.objects.filter(groups=test_group)
        self.assertEqual(len(group_members), 1)

        # test that it is the same member we used in updating the group
        self.assertEqual(group_members[0], user_member_1 )

    @unittest.skip
    def test_update_group_to_add_member_duplicate(self):
        user_member_1 = hydroshare.create_account(
            'member_1@usu.edu',
            username='member_1',
            first_name='Member_1_FirstName',
            last_name='Member_1_LastName',
            superuser=False,
            groups=[]
        )

        group_name = 'Test Group'
        test_group = hydroshare.create_group(group_name)

        # this is the api call we are testing
        hydroshare.update_group(test_group, members=[user_member_1])

        # update with duplicate data
        hydroshare.update_group(test_group, members=[user_member_1])

        # test at this point the group should have one member
        group_members = User.objects.filter(groups=test_group)
        self.assertEqual(len(group_members), 1)

        # test that it is the same member we used in updating the group
        self.assertEqual(group_members[0], user_member_1 )

    @unittest.skip
    def test_update_group_to_add_members(self):
        user_member_1 = hydroshare.create_account(
            'member_1@usu.edu',
            username='member_1',
            first_name='Member_1_FirstName',
            last_name='Member_1_LastName',
            superuser=False,
            groups=[]
        )

        user_member_2 = hydroshare.create_account(
            'member_2@usu.edu',
            username='member_2',
            first_name='Member_2_FirstName',
            last_name='Member_2_LastName',
            superuser=False,
            groups=[]
        )

        group_name = 'Test Group'
        test_group = hydroshare.create_group(group_name)

        # this is the api call we are testing
        hydroshare.update_group(test_group, members=[user_member_1, user_member_2])

        # test at this point the group should have 2 members
        group_members = User.objects.filter(groups=test_group)
        self.assertEqual(len(group_members), 2)

        # test that they are the same 2 members we used in updating the group
        self.assertIn(user_member_1,
                      group_members,
                      msg= '%s is not one of the group member.' % user_member_1
        )

        self.assertIn(user_member_2,
                      group_members,
                      msg= '%s is not one of the group member.' % user_member_2
        )

    @unittest.skip
    def test_update_group_to_add_owner(self):
        user_owner_1 = hydroshare.create_account(
            'owner_1@usu.edu',
            username='owner_1',
            first_name='Owner_1_FirstName',
            last_name='Owner_1_LastName',
            superuser=False,
            groups=[]
        )

        group_name = 'Test Group'
        test_group = hydroshare.create_group(group_name)

        # test we have only no group ownerships at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 0)

        # this is the api call we are testing
        hydroshare.update_group(test_group, owners=[user_owner_1])

        # test we have one group ownership at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 1)

        # test the group ownership has the correct group
        group_ownership = GroupOwnership.objects.filter(group=test_group)
        self.assertEqual(group_ownership[0].group, test_group)

        # test the group ownership has the correct owner
        self.assertEqual(group_ownership[0].owner, user_owner_1)

    @unittest.skip
    def test_update_group_to_add_owner_duplicate(self):
        user_owner_1 = hydroshare.create_account(
            'owner_1@usu.edu',
            username='owner_1',
            first_name='Owner_1_FirstName',
            last_name='Owner_1_LastName',
            superuser=False,
            groups=[]
        )

        group_name = 'Test Group'
        test_group = hydroshare.create_group(group_name)

        # test we have only no group ownerships at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 0)

        # this is the api call we are testing
        hydroshare.update_group(test_group, owners=[user_owner_1])

        # update with duplicate data
        hydroshare.update_group(test_group, owners=[user_owner_1])

        # test we have one group ownership at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 1)

        # test the group ownership has the correct group
        group_ownership = GroupOwnership.objects.filter(group=test_group)
        self.assertEqual(group_ownership[0].group, test_group)

        # test the group ownership has the correct owner
        self.assertEqual(group_ownership[0].owner, user_owner_1)

    @unittest.skip
    def test_update_group_to_add_owners(self):
        user_owner_1 = hydroshare.create_account(
            'owner_1@usu.edu',
            username='owner_1',
            first_name='Owner_1_FirstName',
            last_name='Owner_1_LastName',
            superuser=False,
            groups=[]
        )

        user_owner_2 = hydroshare.create_account(
            'owner_2@usu.edu',
            username='owner_2',
            first_name='Owner_2_FirstName',
            last_name='Owner_2_LastName',
            superuser=False,
            groups=[]
        )

        group_name = 'Test Group'
        test_group = hydroshare.create_group(group_name)

        # test we have only no group ownerships at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 0)

        # this is the api call we are testing
        hydroshare.update_group(test_group, owners=[user_owner_1, user_owner_2])

        # test we have two group ownership at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 2)

        # test the group ownership has the correct group
        group_ownerships = GroupOwnership.objects.filter(group=test_group)

        # test each of the 2 group ownership has the same group
        self.assertEqual(group_ownerships[0].group, test_group)
        self.assertEqual(group_ownerships[1].group, test_group)

        # test we have the 2 owners in the 2 group ownerships
        self.assertIn(user_owner_1,
                      [grp_ownership.owner for grp_ownership in group_ownerships],
                      msg= '%s is not one of the group owner.' % user_owner_1
        )

        self.assertIn(user_owner_2,
                      [grp_ownership.owner for grp_ownership in group_ownerships],
                      msg= '%s is not one of the group owner.' % user_owner_2
        )

