__author__ = 'Pabitra'
from django.test import TestCase
from django.contrib.auth.models import User, Group
from hs_core.models import GroupOwnership
from hs_core import hydroshare

class TestCreateGroupAPI(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        GroupOwnership.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()
        pass

    def test_create_group_no_member_no_owner(self):
        group_name = 'Test Group'
        test_group = hydroshare.create_group(group_name)

        # test the group has the matching name
        self.assertEqual(test_group.name, group_name)

        # test that there are no members in this group yet this point
        group_members = User.objects.filter(groups=test_group)
        self.assertEqual(len(group_members), 0)

        # test we don't have any group ownership at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 0)

    def test_create_group_one_member_no_owner(self):
        # create a user to be used for creating the resource
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

        # test we don't have any group ownership at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 0)

        # test creating a group with one member
        group_name = 'Test Group with one member'
        test_group = hydroshare.create_group(group_name, members=[user_member_1])

        # test the group has the matching name
        self.assertEqual(test_group.name, group_name)

        # test at this point the group has only one member
        group_members = User.objects.filter(groups=test_group)
        self.assertEqual(len(group_members), 1)

        # test that it is the same member we used in creating the group
        self.assertEqual(group_members[0], user_member_1 )

        # test that user_member_2 is not part of the group
        self.assertNotEqual(group_members[0], user_member_2 )

        # test we don't have any group ownership at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 0)

    def test_create_group_two_members_no_owner(self):
        # create a user to be used for creating the resource
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

        # test we don't have any group ownership at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 0)

        # test creating a group with 2 members
        group_name = 'Test Group with 2 members'
        test_group = hydroshare.create_group(group_name, members=[user_member_1, user_member_2])

        # test the group has the matching name
        self.assertEqual(test_group.name, group_name)

        # test at this point the group has only 2 members
        group_members = User.objects.filter(groups=test_group)
        self.assertEqual(len(group_members), 2)

        # test that they are the same 2 members we used in creating the group
        self.assertIn(user_member_1,
                      group_members,
                      msg= '%s is not one of the group member.' % user_member_1
        )

        self.assertIn(user_member_2,
                      group_members,
                      msg= '%s is not one of the group member.' % user_member_2
        )

        # test we don't have any group ownership at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 0)

    def test_create_group_no_member_one_owner(self):
        user_owner_1 = hydroshare.create_account(
            'owner_1@usu.edu',
            username='owner_1',
            first_name='Owner_1_FirstName',
            last_name='Owner_1_LastName',
            superuser=False,
            groups=[]
        )

        # test we have only no group ownerships at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 0)

        # test creating a group with one owner
        group_name = 'Test Group with one owner'
        test_group = hydroshare.create_group(group_name, owners=[user_owner_1])

        # test the group has the matching name
        self.assertEqual(test_group.name, group_name)

        # test we have only one group ownership at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 1)

        # test the group ownership has the correct group
        group_ownership = GroupOwnership.objects.filter(group=test_group)
        self.assertEqual(group_ownership[0].group, test_group)

        # test the group ownership has the correct owner
        self.assertEqual(group_ownership[0].owner, user_owner_1)

    def test_create_group_no_member_two_owners(self):

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

        # test we have only no group ownerships at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 0)

        # test creating a group with 2 owners
        group_name = 'Test Group with 2 owners'
        test_group = hydroshare.create_group(group_name, owners=[user_owner_1, user_owner_2])

        # test the group has the matching name
        self.assertEqual(test_group.name, group_name)

        # test we have only 2 group ownerships at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 2)

        # test we have only 2 group ownerships for the group we created
        group_ownerships = GroupOwnership.objects.filter(group=test_group)
        self.assertEqual(len(group_ownerships), 2)

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

    def test_create_group_two_members_two_owners(self):
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

        # test we have only no group ownerships at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 0)

        # test creating a group with 2 members and 2 owners
        group_name = 'Test Group with 2 members and 2 owners'
        test_group = hydroshare.create_group(group_name, members=[user_member_1, user_member_2], owners=[user_owner_1, user_owner_2])

        # test the group has the matching name
        self.assertEqual(test_group.name, group_name)

        # test at this point the group has only 2 members
        group_members = User.objects.filter(groups=test_group)
        self.assertEqual(len(group_members), 2)

        # test that they are the same 2 members we used in creating the group
        self.assertIn(user_member_1,
                      group_members,
                      msg= '%s is not one of the group member.' % user_member_1
        )

        self.assertIn(user_member_2,
                      group_members,
                      msg= '%s is not one of the group member.' % user_member_2
        )

        # test we have only 2 group ownerships at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 2)

        # test we have only 2 group ownerships for the group we created
        group_ownerships = GroupOwnership.objects.filter(group=test_group)
        self.assertEqual(len(group_ownerships), 2)

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