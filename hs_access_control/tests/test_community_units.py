from django.test import TestCase
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

from hs_access_control.models import \
    UserCommunityProvenance, UserCommunityPrivilege, \
    GroupCommunityProvenance, GroupCommunityPrivilege, \
    PrivilegeCodes

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin

from hs_access_control.tests.utilities import global_reset, is_equal_to_as_set

__author__ = 'Alva'


class UnitTests(MockIRODSTestCaseMixin, TestCase):
    """ test basic behavior of each routine """

    def setUp(self):
        super(UnitTests, self).setUp()
        global_reset()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        self.alva = hydroshare.create_account(
            'alva@gmail.com',
            username='alva',
            first_name='alva',
            last_name='couch',
            superuser=False,
            groups=[]
        )

        self.george = hydroshare.create_account(
            'george@gmail.com',
            username='george',
            first_name='george',
            last_name='miller',
            superuser=False,
            groups=[]
        )

        self.john = hydroshare.create_account(
            'john@gmail.com',
            username='john',
            first_name='john',
            last_name='miller',
            superuser=False,
            groups=[]
        )

        self.admin = hydroshare.create_account(
            'admin@gmail.com',
            username='admin',
            first_name='first_name_admin',
            last_name='last_name_admin',
            superuser=True,
            groups=[]
        )

        # george creates a entity 'bikes'
        self.bikes = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.george,
            title='Bikes',
            metadata=[],
        )

        # george creates a entity 'bikers'
        self.bikers = self.george.uaccess.create_group('Bikers', 'Of the human powered kind')

        # george creates a community 'rebels'
        self.rebels = self.george.uaccess.create_community('Rebels', 'Random rebels')

    def test_usercommunityprivilege_get_current_record(self):
        george = self.george
        rebels = self.rebels
        alva = self.alva
        UserCommunityProvenance.update(
            community=rebels,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        record = UserCommunityProvenance.get_current_record(
            community=rebels, user=alva)
        self.assertEqual(record.grantor, george)
        self.assertEqual(record.community, rebels)
        self.assertEqual(record.user, alva)

    def test_usercommunityprivilege_get_undo_users(self):
        george = self.george
        rebels = self.rebels
        alva = self.alva
        UserCommunityProvenance.update(
            community=rebels,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertTrue(
            is_equal_to_as_set(
                UserCommunityProvenance.get_undo_users(
                    community=rebels,
                    grantor=george),
                [alva, george]))

    def test_usercommunityprivilege_get_privilege(self):
        george = self.george
        rebels = self.rebels
        alva = self.alva
        self.assertEqual(
            UserCommunityProvenance.get_privilege(
                community=rebels,
                user=alva),
            PrivilegeCodes.NONE)
        UserCommunityProvenance.update(
            community=rebels,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserCommunityProvenance.get_privilege(
                community=rebels,
                user=alva),
            PrivilegeCodes.CHANGE)

    def test_usercommunityprivilege_update(self):
        george = self.george
        rebels = self.rebels
        alva = self.alva
        self.assertEqual(
            UserCommunityProvenance.get_privilege(
                community=rebels,
                user=alva),
            PrivilegeCodes.NONE)
        UserCommunityProvenance.update(
            community=rebels,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserCommunityProvenance.get_privilege(
                community=rebels,
                user=alva),
            PrivilegeCodes.CHANGE)

    def test_usercommunityprivilege_undo_share(self):
        george = self.george
        rebels = self.rebels
        alva = self.alva
        self.assertEqual(
            UserCommunityProvenance.get_privilege(
                community=rebels,
                user=alva),
            PrivilegeCodes.NONE)
        UserCommunityProvenance.update(
            community=rebels,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserCommunityProvenance.get_privilege(
                community=rebels,
                user=alva),
            PrivilegeCodes.CHANGE)
        UserCommunityProvenance.update(
            community=rebels,
            user=alva,
            privilege=PrivilegeCodes.NONE,
            grantor=george)
        self.assertEqual(
            UserCommunityProvenance.get_privilege(
                community=rebels,
                user=alva),
            PrivilegeCodes.NONE)
        UserCommunityProvenance.update(
            community=rebels,
            user=alva,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)
        self.assertEqual(
            UserCommunityProvenance.get_privilege(
                community=rebels,
                user=alva),
            PrivilegeCodes.VIEW)
        UserCommunityProvenance.undo_share(community=rebels, user=alva, grantor=george)
        self.assertEqual(
            UserCommunityProvenance.get_privilege(
                community=rebels,
                user=alva),
            PrivilegeCodes.NONE)

        # no further undo is possible.
        with self.assertRaises(PermissionDenied):
            UserCommunityProvenance.undo_share(community=rebels, user=alva, grantor=george)
        with self.assertRaises(PermissionDenied):
            UserCommunityProvenance.undo_share(community=rebels, user=alva, grantor=george)

        UserCommunityProvenance.update(
            community=rebels,
            user=alva,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)
        self.assertEqual(
            UserCommunityProvenance.get_privilege(
                community=rebels,
                user=alva),
            PrivilegeCodes.VIEW)
        UserCommunityProvenance.update(
            community=rebels,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserCommunityProvenance.get_privilege(
                community=rebels,
                user=alva),
            PrivilegeCodes.CHANGE)
        UserCommunityProvenance.undo_share(community=rebels, user=alva, grantor=george)
        self.assertEqual(
            UserCommunityProvenance.get_privilege(
                community=rebels,
                user=alva),
            PrivilegeCodes.VIEW)
        UserCommunityProvenance.update(
            community=rebels,
            user=alva,
            privilege=PrivilegeCodes.NONE,
            grantor=george)
        self.assertEqual(
            UserCommunityProvenance.get_privilege(
                community=rebels,
                user=alva),
            PrivilegeCodes.NONE)
        UserCommunityProvenance.update(
            community=rebels,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserCommunityProvenance.get_privilege(
                community=rebels,
                user=alva),
            PrivilegeCodes.CHANGE)

    def test_usercommunityresult_get_privilege(self):
        george = self.george
        rebels = self.rebels
        alva = self.alva
        self.assertEqual(
            UserCommunityPrivilege.get_privilege(
                community=rebels,
                user=alva),
            PrivilegeCodes.NONE)
        UserCommunityPrivilege.update(
            community=rebels,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserCommunityPrivilege.get_privilege(
                community=rebels,
                user=alva),
            PrivilegeCodes.CHANGE)

    def test_usercommunityresult_update(self):
        george = self.george
        rebels = self.rebels
        alva = self.alva
        self.assertEqual(
            UserCommunityPrivilege.get_privilege(
                community=rebels,
                user=alva),
            PrivilegeCodes.NONE)
        UserCommunityPrivilege.update(
            community=rebels,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserCommunityPrivilege.get_privilege(
                community=rebels,
                user=alva),
            PrivilegeCodes.CHANGE)

    def test_can_undo_share_community_with_user(self):
        george = self.george
        rebels = self.rebels
        alva = self.alva
        self.assertFalse(george.uaccess.can_undo_share_community_with_user(rebels, alva))
        self.assertFalse(george.uaccess.can_undo_share_community_with_user(rebels, george))
        self.assertFalse(alva.uaccess.can_undo_share_community_with_user(rebels, george))
        self.assertEqual(
            UserCommunityPrivilege.get_privilege(community=rebels, user=alva),
            PrivilegeCodes.NONE)
        george.uaccess.share_community_with_user(rebels, alva, PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserCommunityPrivilege.get_privilege(community=rebels, user=alva),
            PrivilegeCodes.CHANGE)
        self.assertTrue(george.uaccess.can_undo_share_community_with_user(rebels, alva))
        self.assertFalse(george.uaccess.can_undo_share_community_with_user(rebels, george))
        self.assertFalse(alva.uaccess.can_undo_share_community_with_user(rebels, george))
        george.uaccess.undo_share_community_with_user(rebels, alva)

        self.assertEqual(
            UserCommunityPrivilege.get_privilege(community=rebels, user=alva),
            PrivilegeCodes.NONE)
        self.assertFalse(george.uaccess.can_undo_share_community_with_user(rebels, alva))
        self.assertFalse(george.uaccess.can_undo_share_community_with_user(rebels, george))
        self.assertFalse(alva.uaccess.can_undo_share_community_with_user(rebels, george))
        george.uaccess.share_community_with_user(rebels, alva, PrivilegeCodes.VIEW)
        self.assertEqual(
            UserCommunityPrivilege.get_privilege(community=rebels, user=alva),
            PrivilegeCodes.VIEW)
        self.assertTrue(george.uaccess.can_undo_share_community_with_user(rebels, alva))
        self.assertFalse(george.uaccess.can_undo_share_community_with_user(rebels, george))
        self.assertFalse(alva.uaccess.can_undo_share_community_with_user(rebels, george))
        george.uaccess.undo_share_community_with_user(rebels, alva)
        self.assertEqual(
            UserCommunityPrivilege.get_privilege(community=rebels, user=alva),
            PrivilegeCodes.NONE)
        self.assertFalse(george.uaccess.can_undo_share_community_with_user(rebels, alva))
        self.assertFalse(george.uaccess.can_undo_share_community_with_user(rebels, george))
        self.assertFalse(alva.uaccess.can_undo_share_community_with_user(rebels, george))

    def test_undo_share_community_with_user(self):
        george = self.george
        rebels = self.rebels
        alva = self.alva
        self.assertEqual(
            UserCommunityPrivilege.get_privilege(community=rebels, user=alva),
            PrivilegeCodes.NONE)
        george.uaccess.share_community_with_user(rebels, alva, PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserCommunityPrivilege.get_privilege(community=rebels, user=alva),
            PrivilegeCodes.CHANGE)
        george.uaccess.undo_share_community_with_user(rebels, alva)
        self.assertEqual(
            UserCommunityPrivilege.get_privilege(community=rebels, user=alva),
            PrivilegeCodes.NONE)
        george.uaccess.share_community_with_user(rebels, alva, PrivilegeCodes.VIEW)
        self.assertEqual(
            UserCommunityPrivilege.get_privilege(community=rebels, user=alva),
            PrivilegeCodes.VIEW)
        george.uaccess.undo_share_community_with_user(rebels, alva)
        self.assertEqual(
            UserCommunityPrivilege.get_privilege(community=rebels, user=alva),
            PrivilegeCodes.NONE)

    def test_groupcommunityprivilege_get_current_record(self):
        george = self.george
        rebels = self.rebels
        bikers = self.bikers
        GroupCommunityProvenance.update(
            community=rebels,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        record = GroupCommunityProvenance.get_current_record(
            community=rebels, group=bikers)
        self.assertEqual(record.grantor, george)
        self.assertEqual(record.community, rebels)
        self.assertEqual(record.group, bikers)

    def test_groupcommunityprivilege_get_undo_groups(self):
        george = self.george
        rebels = self.rebels
        bikers = self.bikers
        GroupCommunityProvenance.update(
            community=rebels,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertTrue(
            is_equal_to_as_set(
                GroupCommunityProvenance.get_undo_groups(
                    community=rebels,
                    grantor=george),
                [bikers]))

    def test_groupcommunityprivilege_get_privilege(self):
        george = self.george
        rebels = self.rebels
        bikers = self.bikers
        self.assertEqual(
            GroupCommunityProvenance.get_privilege(
                community=rebels,
                group=bikers),
            PrivilegeCodes.NONE)
        GroupCommunityProvenance.update(
            community=rebels,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            GroupCommunityProvenance.get_privilege(
                community=rebels,
                group=bikers),
            PrivilegeCodes.CHANGE)

    def test_groupcommunityprivilege_update(self):
        george = self.george
        rebels = self.rebels
        bikers = self.bikers
        self.assertEqual(
            GroupCommunityProvenance.get_privilege(
                community=rebels,
                group=bikers),
            PrivilegeCodes.NONE)
        GroupCommunityProvenance.update(
            community=rebels,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            GroupCommunityProvenance.get_privilege(
                community=rebels,
                group=bikers),
            PrivilegeCodes.CHANGE)

    def test_groupcommunityprivilege_undo_share(self):
        george = self.george
        rebels = self.rebels
        bikers = self.bikers
        self.assertEqual(
            GroupCommunityProvenance.get_privilege(
                community=rebels,
                group=bikers),
            PrivilegeCodes.NONE)
        GroupCommunityProvenance.update(
            community=rebels,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            GroupCommunityProvenance.get_privilege(
                community=rebels,
                group=bikers),
            PrivilegeCodes.CHANGE)
        GroupCommunityProvenance.update(
            community=rebels,
            group=bikers,
            privilege=PrivilegeCodes.NONE,
            grantor=george)
        self.assertEqual(
            GroupCommunityProvenance.get_privilege(
                community=rebels,
                group=bikers),
            PrivilegeCodes.NONE)
        GroupCommunityProvenance.update(
            community=rebels,
            group=bikers,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)
        self.assertEqual(
            GroupCommunityProvenance.get_privilege(
                community=rebels,
                group=bikers),
            PrivilegeCodes.VIEW)
        GroupCommunityProvenance.undo_share(community=rebels, group=bikers, grantor=george)
        self.assertEqual(
            GroupCommunityProvenance.get_privilege(
                community=rebels,
                group=bikers),
            PrivilegeCodes.NONE)

        # no further undo is possible.
        with self.assertRaises(PermissionDenied):
            GroupCommunityProvenance.undo_share(community=rebels, group=bikers, grantor=george)
        with self.assertRaises(PermissionDenied):
            GroupCommunityProvenance.undo_share(community=rebels, group=bikers, grantor=george)

        GroupCommunityProvenance.update(
            community=rebels,
            group=bikers,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)
        self.assertEqual(
            GroupCommunityProvenance.get_privilege(
                community=rebels,
                group=bikers),
            PrivilegeCodes.VIEW)
        GroupCommunityProvenance.update(
            community=rebels,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            GroupCommunityProvenance.get_privilege(
                community=rebels,
                group=bikers),
            PrivilegeCodes.CHANGE)
        GroupCommunityProvenance.undo_share(community=rebels, group=bikers, grantor=george)
        self.assertEqual(
            GroupCommunityProvenance.get_privilege(
                community=rebels,
                group=bikers),
            PrivilegeCodes.VIEW)
        GroupCommunityProvenance.update(
            community=rebels,
            group=bikers,
            privilege=PrivilegeCodes.NONE,
            grantor=george)
        self.assertEqual(
            GroupCommunityProvenance.get_privilege(
                community=rebels,
                group=bikers),
            PrivilegeCodes.NONE)
        GroupCommunityProvenance.update(
            community=rebels,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            GroupCommunityProvenance.get_privilege(
                community=rebels,
                group=bikers),
            PrivilegeCodes.CHANGE)

    def test_groupcommunityresult_get_privilege(self):
        george = self.george
        rebels = self.rebels
        bikers = self.bikers
        self.assertEqual(
            GroupCommunityPrivilege.get_privilege(
                community=rebels,
                group=bikers),
            PrivilegeCodes.NONE)
        GroupCommunityPrivilege.update(
            community=rebels,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            GroupCommunityPrivilege.get_privilege(
                community=rebels,
                group=bikers),
            PrivilegeCodes.CHANGE)

    def test_groupcommunityresult_update(self):
        george = self.george
        rebels = self.rebels
        bikers = self.bikers
        self.assertEqual(
            GroupCommunityPrivilege.get_privilege(
                community=rebels,
                group=bikers),
            PrivilegeCodes.NONE)
        GroupCommunityPrivilege.update(
            community=rebels,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            GroupCommunityPrivilege.get_privilege(
                community=rebels,
                group=bikers),
            PrivilegeCodes.CHANGE)

    def test_can_undo_share_community_with_group(self):
        george = self.george
        rebels = self.rebels
        bikers = self.bikers
        self.assertFalse(george.uaccess.can_undo_share_community_with_group(rebels, bikers))
        self.assertEqual(
            GroupCommunityPrivilege.get_privilege(community=rebels, group=bikers),
            PrivilegeCodes.NONE)
        george.uaccess.share_community_with_group(rebels, bikers, PrivilegeCodes.CHANGE)
        self.assertEqual(
            GroupCommunityPrivilege.get_privilege(community=rebels, group=bikers),
            PrivilegeCodes.CHANGE)
        self.assertTrue(george.uaccess.can_undo_share_community_with_group(rebels, bikers))
        george.uaccess.undo_share_community_with_group(rebels, bikers)

        self.assertEqual(
            GroupCommunityPrivilege.get_privilege(community=rebels, group=bikers),
            PrivilegeCodes.NONE)
        self.assertFalse(george.uaccess.can_undo_share_community_with_group(rebels, bikers))
        george.uaccess.share_community_with_group(rebels, bikers, PrivilegeCodes.VIEW)
        self.assertEqual(
            GroupCommunityPrivilege.get_privilege(community=rebels, group=bikers),
            PrivilegeCodes.VIEW)
        self.assertTrue(george.uaccess.can_undo_share_community_with_group(rebels, bikers))
        george.uaccess.undo_share_community_with_group(rebels, bikers)
        self.assertEqual(
            GroupCommunityPrivilege.get_privilege(community=rebels, group=bikers),
            PrivilegeCodes.NONE)
        self.assertFalse(george.uaccess.can_undo_share_community_with_group(rebels, bikers))

    def test_undo_share_community_with_group(self):
        george = self.george
        rebels = self.rebels
        bikers = self.bikers
        self.assertEqual(
            GroupCommunityPrivilege.get_privilege(community=rebels, group=bikers),
            PrivilegeCodes.NONE)
        george.uaccess.share_community_with_group(rebels, bikers, PrivilegeCodes.CHANGE)
        self.assertEqual(
            GroupCommunityPrivilege.get_privilege(community=rebels, group=bikers),
            PrivilegeCodes.CHANGE)
        george.uaccess.undo_share_community_with_group(rebels, bikers)
        self.assertEqual(
            GroupCommunityPrivilege.get_privilege(community=rebels, group=bikers),
            PrivilegeCodes.NONE)
        george.uaccess.share_community_with_group(rebels, bikers, PrivilegeCodes.VIEW)
        self.assertEqual(
            GroupCommunityPrivilege.get_privilege(community=rebels, group=bikers),
            PrivilegeCodes.VIEW)
        george.uaccess.undo_share_community_with_group(rebels, bikers)
        self.assertEqual(
            GroupCommunityPrivilege.get_privilege(community=rebels, group=bikers),
            PrivilegeCodes.NONE)
