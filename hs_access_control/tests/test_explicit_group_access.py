from django.test import TestCase
from django.contrib.auth.models import Group

from hs_core.testing import MockS3TestCaseMixin
from hs_core import hydroshare
from hs_access_control.models import PrivilegeCodes


class TestExplicitGroupAccess(MockS3TestCaseMixin, TestCase):

    def setUp(self):
        super(TestExplicitGroupAccess, self).setUp()
        self.hs_group, _ = Group.objects.get_or_create(
            name='Hydroshare Author')
        self.grp_creator_user = hydroshare.create_account(
            'grp_creator@gmail.com',
            username='grpcreator',
            first_name='Group',
            last_name='Creator',
            superuser=False,
            groups=[]
        )
        self.user_A = hydroshare.create_account(
            'user_A@gmail.com',
            username='usera',
            first_name='UserA',
            last_name='Last Name A',
            superuser=False,
            groups=[]
        )
        self.user_B = hydroshare.create_account(
            'user_B@gmail.com',
            username='userb',
            first_name='UserB',
            last_name='Last Name B',
            superuser=False,
            groups=[]
        )

        # grp_creator_user owns group_test group
        self.group_test = self.grp_creator_user.uaccess\
            .create_group(title='Test Group',
                          description="This group is all about testing")

    def test_explicit_access(self):
        # test explict group ownership access - there should be only one owner
        # at this point
        self.assertEqual(
            self.group_test.gaccess .get_users_with_explicit_access(
                PrivilegeCodes.OWNER).count(), 1)
        self.assertTrue(self.grp_creator_user in self.group_test.gaccess
                        .get_users_with_explicit_access(PrivilegeCodes.OWNER))

        # There should not be any user with explict Edit permission on
        # group_test
        self.assertEqual(
            self.group_test.gaccess .get_users_with_explicit_access(
                PrivilegeCodes.CHANGE).count(), 0)
        # add user_A to the group with Edit permission
        self.grp_creator_user.uaccess.share_group_with_user(
            self.group_test, self.user_A, PrivilegeCodes.CHANGE)
        # There should be 1 user with explict Edit permission on group_test
        self.assertEqual(
            self.group_test.gaccess .get_users_with_explicit_access(
                PrivilegeCodes.CHANGE).count(), 1)
        self.assertTrue(self.user_A in self.group_test.gaccess
                        .get_users_with_explicit_access(PrivilegeCodes.CHANGE))

        # There should not be any user with explict View permission on
        # group_test
        self.assertEqual(
            self.group_test.gaccess .get_users_with_explicit_access(
                PrivilegeCodes.VIEW).count(), 0)
        # add user_B to the group with View permission
        self.grp_creator_user.uaccess.share_group_with_user(
            self.group_test, self.user_B, PrivilegeCodes.VIEW)
        # There should be 1 user with explict View permission on group_test
        self.assertEqual(
            self.group_test.gaccess .get_users_with_explicit_access(
                PrivilegeCodes.VIEW).count(), 1)
        self.assertTrue(
            self.user_B in self.group_test.gaccess.get_users_with_explicit_access(
                PrivilegeCodes.VIEW))

        # There should be 3 members in the group (one owner, one editor and one
        # viewer)
        self.assertEqual(self.group_test.gaccess.members.count(), 3)
