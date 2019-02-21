from django.test import TestCase
from django.contrib.auth.models import Group

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_access_control.models import PrivilegeCodes


class TestExplicitResourceAccess(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(TestExplicitResourceAccess, self).setUp()
        self.hs_group, _ = Group.objects.get_or_create(
            name='Hydroshare Author')

        self.user_A = hydroshare.create_account(
            'user_A@gmail.com',
            username='usera',
            first_name='First Name A',
            last_name='Last Name A',
            superuser=False,
            groups=[]
        )
        self.user_B = hydroshare.create_account(
            'user_B@gmail.com',
            username='userb',
            first_name='First Name B',
            last_name='Last Name B',
            superuser=False,
            groups=[]
        )

        self.user_C = hydroshare.create_account(
            'user_C@gmail.com',
            username='userc',
            first_name='First Name C',
            last_name='Last Name C',
            superuser=False,
            groups=[]
        )

        # user_A owns resource
        self.resource = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.user_A,
            title='Test Resource',
            metadata=[],
        )

        # user_A owns group_test group
        self.group_test = self.user_A.uaccess\
            .create_group(title='Test Group',
                          description="This group is all about testing")

    def test_explicit_resource_access(self):
        # test users with explict resource access
        # here we are testing the get_users_with_explicit_access() function of
        # ResourceAccess class

        # at this point there should be only one user (user_A) with ownership
        # access to the resource
        users = self.resource.raccess\
            .get_users_with_explicit_access(PrivilegeCodes.OWNER,
                                            include_user_granted_access=True,
                                            include_group_granted_access=False)
        self.assertEqual(len(users), 1)
        self.assertIn(self.user_A, users)

        users = self.resource.raccess\
            .get_users_with_explicit_access(PrivilegeCodes.OWNER,
                                            include_user_granted_access=True,
                                            include_group_granted_access=True)
        self.assertEqual(len(users), 1)
        self.assertIn(self.user_A, users)

        # at this point there should be no user with explicit view access to
        # the resource
        users = self.resource.raccess\
            .get_users_with_explicit_access(PrivilegeCodes.VIEW,
                                            include_user_granted_access=True,
                                            include_group_granted_access=False)
        self.assertEqual(len(users), 0)

        users = self.resource.raccess\
            .get_users_with_explicit_access(PrivilegeCodes.VIEW,
                                            include_user_granted_access=True,
                                            include_group_granted_access=True)
        self.assertEqual(len(users), 0)

        # grant User_B view permission on resource
        self.user_A.uaccess.share_resource_with_user(
            self.resource, self.user_B, PrivilegeCodes.VIEW)
        # at this point there should be only one user (user_B)
        # with explicit view access to the resource
        users = self.resource.raccess\
            .get_users_with_explicit_access(PrivilegeCodes.VIEW,
                                            include_user_granted_access=True,
                                            include_group_granted_access=False)
        self.assertEqual(len(users), 1)
        self.assertIn(self.user_B, users)

        users = self.resource.raccess\
            .get_users_with_explicit_access(PrivilegeCodes.VIEW,
                                            include_user_granted_access=True,
                                            include_group_granted_access=True)
        self.assertEqual(len(users), 1)
        self.assertIn(self.user_B, users)

        # make user C a member of the test_group with view permission
        self.user_A.uaccess.share_group_with_user(self.group_test, self.user_C,
                                                  PrivilegeCodes.VIEW)
        # grant group view permission over resource
        self.user_A.uaccess.share_resource_with_group(
            self.resource, self.group_test, PrivilegeCodes.VIEW)
        # at this point there should be 1 user (user_B)
        # with explicit view access to the resource (user granted access)
        users = self.resource.raccess\
            .get_users_with_explicit_access(PrivilegeCodes.VIEW,
                                            include_user_granted_access=True,
                                            include_group_granted_access=False)
        self.assertEqual(len(users), 1)
        self.assertIn(self.user_B, users)

        # at this point there should be 2 users (user_A and user_C) (since the group has 2 members)
        # with explicit view access to the resource (group granted access)
        users = self.resource.raccess\
            .get_users_with_explicit_access(PrivilegeCodes.VIEW,
                                            include_user_granted_access=False,
                                            include_group_granted_access=True)
        self.assertEqual(len(users), 2)
        self.assertIn(self.user_A, users)
        self.assertIn(self.user_C, users)

        # at this point there should be 2 users with explicit view access to the resource:
        # user_B through user granted access and the user_C via group granted access
        # user_A is excluded as it is an owner.
        users = self.resource.raccess\
            .get_users_with_explicit_access(PrivilegeCodes.VIEW,
                                            include_user_granted_access=True,
                                            include_group_granted_access=True)

        self.assertEqual(len(users), 2)
        self.assertIn(self.user_B, users)
        self.assertIn(self.user_C, users)

        # there should be no users (empty list) if both parameters are set to
        # False
        users = self.resource.raccess\
            .get_users_with_explicit_access(PrivilegeCodes.VIEW,
                                            include_user_granted_access=False,
                                            include_group_granted_access=False)

        self.assertEqual(len(users), 0)

        # remove user C from group membership
        self.user_A.uaccess.unshare_group_with_user(
            self.group_test, self.user_C)

        # at this point there should be one user (user_A) (since the group has 1 member)
        # with explicit view access to the resource (group granted access)
        users = self.resource.raccess\
            .get_users_with_explicit_access(PrivilegeCodes.VIEW,
                                            include_user_granted_access=False,
                                            include_group_granted_access=True)
        self.assertEqual(len(users), 1)
        self.assertIn(self.user_A, users)

        # make user C a member of the test_group with edit permission
        self.user_A.uaccess.share_group_with_user(self.group_test, self.user_C,
                                                  PrivilegeCodes.CHANGE)
        # grant group edit permission over resource
        self.user_A.uaccess.share_resource_with_group(
            self.resource, self.group_test, PrivilegeCodes.CHANGE)
        # at this point there should be 1 user with explicit view (user_B) access to the resource
        # (user granted access)
        users = self.resource.raccess\
            .get_users_with_explicit_access(PrivilegeCodes.VIEW,
                                            include_user_granted_access=True,
                                            include_group_granted_access=False)
        self.assertEqual(len(users), 1)
        self.assertIn(self.user_B, users)

        # at this point there should be 2 users (user_A and user_C) (since the group has 2 members)
        # with explicit edit access to the resource (group granted access)
        users = self.resource.raccess\
            .get_users_with_explicit_access(PrivilegeCodes.CHANGE,
                                            include_user_granted_access=False,
                                            include_group_granted_access=True)
        self.assertEqual(len(users), 2)
        self.assertIn(self.user_A, users)
        self.assertIn(self.user_C, users)

        # at this point there should be 2 users with explicit edit access (via
        # group granted access) and one excluded by being an owner
        users = self.resource.raccess\
            .get_users_with_explicit_access(PrivilegeCodes.CHANGE,
                                            include_user_granted_access=True,
                                            include_group_granted_access=True)
        self.assertEqual(len(users), 1)
        self.assertIn(self.user_C, users)

        # remove user C from group membership
        self.user_A.uaccess.unshare_group_with_user(
            self.group_test, self.user_C)

        # at this point there should be one user (user_A) (since the group has 1 member)
        # with explicit edit access to the resource (group granted access)
        users = self.resource.raccess\
            .get_users_with_explicit_access(PrivilegeCodes.CHANGE,
                                            include_user_granted_access=False,
                                            include_group_granted_access=True)
        self.assertEqual(len(users), 1)
        self.assertIn(self.user_A, users)
