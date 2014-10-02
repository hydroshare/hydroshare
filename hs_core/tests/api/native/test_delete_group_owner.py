__author__ = 'Pabitra'
from django.test import TestCase
from django.contrib.auth.models import User, Group
from hs_core.models import GroupOwnership
from hs_core import hydroshare

class TestDeleteGroupOwnerAPI(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        GroupOwnership.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()
        pass

    def test_delete_group_the_only_owner(self):
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

        # test we don't have any group ownership at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 0)

        hydroshare.set_group_owner(test_group, user_owner_1)

        # test we have only one group ownership at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 1)

        # this is the api call we are testing
        hydroshare.delete_group_owner(test_group, user_owner_1)

        # test we don't have any group ownership after we delete the group owner
        self.assertEqual(GroupOwnership.objects.all().count(), 0)

    def test_delete_group_the_same_owner_twice(self):
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

        # test we don't have any group ownership at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 0)

        hydroshare.set_group_owner(test_group, user_owner_1)

        # test we have only one group ownership at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 1)

        # this is the api call we are testing
        hydroshare.delete_group_owner(test_group, user_owner_1)

        # deleting the same owner again
        hydroshare.delete_group_owner(test_group, user_owner_1)

        # test we don't have any group ownership after we delete the group owner
        self.assertEqual(GroupOwnership.objects.all().count(), 0)

    def test_delete_group_one_of_the_owners(self):
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

        # test we don't have any group ownership at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 0)

        hydroshare.set_group_owner(test_group, user_owner_1)
        hydroshare.set_group_owner(test_group, user_owner_2)

        # test we have 2 group ownership at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 2)

        # this is the api call we are testing
        hydroshare.delete_group_owner(test_group, user_owner_1)

        # test we now have 1 group ownership after we delete one of the 2 group owners
        self.assertEqual(GroupOwnership.objects.all().count(), 1)

        # test we still have the 2nd group owner
        group_ownerships = GroupOwnership.objects.filter(group=test_group)
        self.assertIn(user_owner_2,
                      [grp_ownership.owner for grp_ownership in group_ownerships],
                      msg= '%s is not one of the group owner.' % user_owner_2
        )