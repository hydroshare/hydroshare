
# TODO: the api being tested  here (hydroshare.set_group_owner()) is not based on new access_control app. Since
# similar api is available in the access_control app, do we need a wrapper api in hs_core? If not then we should delete
# this test since access_control app has this test

import unittest

from django.test import TestCase
from django.contrib.auth.models import User, Group
from hs_core.models import GroupOwnership
from hs_core import hydroshare

class TestSetGroupOwnerAPI(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        GroupOwnership.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()
        pass

    @unittest.skip
    def test_set_group_owner(self):
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

        # test the group ownership has the correct group
        group_ownership = GroupOwnership.objects.filter(group=test_group)
        self.assertEqual(group_ownership[0].group, test_group)

        # test the group ownership has the correct owner
        self.assertEqual(group_ownership[0].owner, user_owner_1)

    @unittest.skip
    def test_set_group_owner_duplicate(self):
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

        # this is the api call we are testing
        hydroshare.set_group_owner(test_group, user_owner_1)

        # set the same user again as the group owner
        hydroshare.set_group_owner(test_group, user_owner_1)

        # test we have only one group ownership at this point
        self.assertEqual(GroupOwnership.objects.all().count(), 1)

        # test the group ownership has the correct group
        group_ownership = GroupOwnership.objects.filter(group=test_group)
        self.assertEqual(group_ownership[0].group, test_group)

        # test the group ownership has the correct owner
        self.assertEqual(group_ownership[0].owner, user_owner_1)