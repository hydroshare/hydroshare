"""
Tests for UserResource table updates via signal handlers.

Tests the signal handlers in hs_core/receivers.py that update the UserResource table
when user permissions change through UserResourcePrivilege, GroupResourcePrivilege,
and UserGroupPrivilege modifications.
"""

from django.test import TestCase
from django.contrib.auth.models import Group

from hs_access_control.models import PrivilegeCodes
from hs_core import hydroshare
from hs_core.models import UserResource
from hs_core.testing import MockS3TestCaseMixin
from hs_access_control.tests.utilities import global_reset
from hs_labels.models import FlagCodes


class TestUserResourceTableUpdates(MockS3TestCaseMixin, TestCase):
    """Test signal handlers update UserResource table correctly"""

    def setUp(self):
        super().setUp()
        global_reset()

        # Create base group required by hydroshare
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        # Create test users
        self.owner = hydroshare.create_account(
            'owner@test.com',
            username='owner',
            first_name='Resource',
            last_name='Owner',
            superuser=False,
            groups=[]
        )

        self.user1 = hydroshare.create_account(
            'user1@test.com',
            username='user1',
            first_name='Test',
            last_name='User1',
            superuser=False,
            groups=[]
        )

        self.user2 = hydroshare.create_account(
            'user2@test.com',
            username='user2',
            first_name='Test',
            last_name='User2',
            superuser=False,
            groups=[]
        )

        self.user3 = hydroshare.create_account(
            'user3@test.com',
            username='user3',
            first_name='Test',
            last_name='User3',
            superuser=False,
            groups=[]
        )

        # Create test resource
        self.resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.owner,
            title='Test Resource for Signal Handlers',
            metadata=[]
        )

        # Create test groups
        self.test_group1 = self.owner.uaccess.create_group(
            title='Test Group 1',
            description='Group for testing signal handlers'
        )

        self.test_group2 = self.owner.uaccess.create_group(
            title='Test Group 2', 
            description='Second group for testing'
        )

    # def tearDown(self):
    #     super().tearDown()
    #     User.objects.all().delete()
    #     Group.objects.all().delete()

    def test_user_resource_privilege_create_updates_table(self):
        """Test that creating a UserResourcePrivilege updates UserResource table"""
        # Initially only owner should have UserResource entry
        initial_count = UserResource.objects.filter(resource=self.resource).count()
        self.assertEqual(initial_count, 1)  # Only owner

        # Grant user1 view permission
        self.owner.uaccess.share(
            resource=self.resource,
            user=self.user1,
            privilege=PrivilegeCodes.VIEW
        )

        # Check UserResource table was updated
        ur = UserResource.objects.get(user=self.user1, resource=self.resource)
        self.assertEqual(ur.permission, PrivilegeCodes.VIEW)
        self.assertFalse(ur.is_favorite)
        self.assertFalse(ur.is_discovered)

        # Total count should be 2 now
        total_count = UserResource.objects.filter(resource=self.resource).count()
        self.assertEqual(total_count, 2)

    def test_user_resource_privilege_update_changes_permission(self):
        """Test that updating a UserResourcePrivilege updates UserResource permission"""
        # Grant initial view permission
        self.owner.uaccess.share(
            resource=self.resource,
            user=self.user1,
            privilege=PrivilegeCodes.VIEW
        )

        # Verify initial state
        ur = UserResource.objects.get(user=self.user1, resource=self.resource)
        self.assertEqual(ur.permission, PrivilegeCodes.VIEW)

        # Upgrade to change permission
        self.owner.uaccess.share(
            resource=self.resource,
            user=self.user1,
            privilege=PrivilegeCodes.CHANGE
        )

        # Verify update
        ur.refresh_from_db()
        self.assertEqual(ur.permission, PrivilegeCodes.CHANGE)

    def test_user_resource_privilege_delete_removes_or_updates_entry(self):
        """Test that deleting UserResourcePrivilege removes or updates UserResource entry"""
        # Grant permission
        self.owner.uaccess.share(
            resource=self.resource,
            user=self.user1,
            privilege=PrivilegeCodes.VIEW
        )

        # Verify entry exists
        self.assertTrue(UserResource.objects.filter(user=self.user1, resource=self.resource).exists())

        # Remove permission
        self.owner.uaccess.unshare(
            resource=self.resource,
            user=self.user1
        )

        # Entry should be deleted since no flags are set
        self.assertFalse(UserResource.objects.filter(user=self.user1, resource=self.resource).exists())

    def test_user_resource_privilege_delete_preserves_flagged_entry(self):
        """Test that deleting UserResourcePrivilege preserves entry with flags but removes permission"""
        # Grant permission
        self.owner.uaccess.share(
            resource=self.resource,
            user=self.user1,
            privilege=PrivilegeCodes.VIEW
        )

        # Set a flag (simulate favoriting)
        ur = UserResource.objects.get(user=self.user1, resource=self.resource)
        ur.is_favorite = True
        ur.save()

        # Remove permission
        self.owner.uaccess.unshare(
            resource=self.resource,
            user=self.user1
        )

        # Entry should still exist but permission should be NONE
        ur.refresh_from_db()
        self.assertEqual(ur.permission, PrivilegeCodes.NONE)
        self.assertTrue(ur.is_favorite)

    def test_group_resource_privilege_create_updates_all_group_members(self):
        """Test that creating GroupResourcePrivilege updates UserResource for all group members"""
        # Add users to group
        self.owner.uaccess.share(
            group=self.test_group1,
            user=self.user1,
            privilege=PrivilegeCodes.VIEW
        )
        self.owner.uaccess.share(
            group=self.test_group1,
            user=self.user2,
            privilege=PrivilegeCodes.VIEW
        )

        # Grant group permission to resource
        self.owner.uaccess.share(
            resource=self.resource,
            group=self.test_group1,
            privilege=PrivilegeCodes.VIEW
        )

        # Both users should now have UserResource entries
        ur1 = UserResource.objects.get(user=self.user1, resource=self.resource)
        ur2 = UserResource.objects.get(user=self.user2, resource=self.resource)

        self.assertEqual(ur1.permission, PrivilegeCodes.VIEW)
        self.assertEqual(ur2.permission, PrivilegeCodes.VIEW)

    def test_group_resource_privilege_update_changes_all_group_members(self):
        """Test that updating GroupResourcePrivilege updates UserResource for all group members"""
        # Add users to group and grant initial permission
        self.owner.uaccess.share(group=self.test_group1, user=self.user1, privilege=PrivilegeCodes.VIEW)
        self.owner.uaccess.share(group=self.test_group1, user=self.user2, privilege=PrivilegeCodes.VIEW)
        self.owner.uaccess.share(resource=self.resource, group=self.test_group1, privilege=PrivilegeCodes.VIEW)

        # Verify initial state
        ur1 = UserResource.objects.get(user=self.user1, resource=self.resource)
        ur2 = UserResource.objects.get(user=self.user2, resource=self.resource)
        self.assertEqual(ur1.permission, PrivilegeCodes.VIEW)
        self.assertEqual(ur2.permission, PrivilegeCodes.VIEW)

        # Upgrade group permission
        self.owner.uaccess.share(
            resource=self.resource,
            group=self.test_group1,
            privilege=PrivilegeCodes.CHANGE
        )

        # Both users should have updated permissions
        ur1.refresh_from_db()
        ur2.refresh_from_db()
        self.assertEqual(ur1.permission, PrivilegeCodes.CHANGE)
        self.assertEqual(ur2.permission, PrivilegeCodes.CHANGE)

    def test_group_resource_privilege_delete_updates_all_group_members(self):
        """Test that deleting GroupResourcePrivilege updates UserResource for all group members"""
        # Setup group with members and permissions
        self.owner.uaccess.share(group=self.test_group1, user=self.user1, privilege=PrivilegeCodes.VIEW)
        self.owner.uaccess.share(group=self.test_group1, user=self.user2, privilege=PrivilegeCodes.VIEW)
        self.owner.uaccess.share(resource=self.resource, group=self.test_group1, privilege=PrivilegeCodes.VIEW)

        # Verify entries exist
        self.assertTrue(UserResource.objects.filter(user=self.user1, resource=self.resource).exists())
        self.assertTrue(UserResource.objects.filter(user=self.user2, resource=self.resource).exists())

        # Remove group permission
        self.owner.uaccess.unshare(
            resource=self.resource,
            group=self.test_group1
        )

        # Both users should have entries removed (no flags set)
        self.assertFalse(UserResource.objects.filter(user=self.user1, resource=self.resource).exists())
        self.assertFalse(UserResource.objects.filter(user=self.user2, resource=self.resource).exists())

    def test_user_group_privilege_create_grants_resource_access(self):
        """Test that adding user to group with resource access updates UserResource"""
        # Grant group permission to resource first
        self.owner.uaccess.share(
            resource=self.resource,
            group=self.test_group1,
            privilege=PrivilegeCodes.VIEW
        )

        # Add user to group
        self.owner.uaccess.share(
            group=self.test_group1,
            user=self.user1,
            privilege=PrivilegeCodes.VIEW
        )

        # User should now have access via group membership
        ur = UserResource.objects.get(user=self.user1, resource=self.resource)
        self.assertEqual(ur.permission, PrivilegeCodes.VIEW)

    def test_user_group_privilege_delete_removes_group_based_access(self):
        """Test that removing user from group removes group-based resource access"""
        # Setup group with resource access and user membership
        self.owner.uaccess.share(resource=self.resource, group=self.test_group1, privilege=PrivilegeCodes.VIEW)
        self.owner.uaccess.share(group=self.test_group1, user=self.user1, privilege=PrivilegeCodes.VIEW)

        # Verify user has access
        self.assertTrue(UserResource.objects.filter(user=self.user1, resource=self.resource).exists())

        # Remove user from group
        self.owner.uaccess.unshare(
            group=self.test_group1,
            user=self.user1
        )

        # User should lose access
        self.assertFalse(UserResource.objects.filter(user=self.user1, resource=self.resource).exists())

    def test_effective_privilege_calculation_user_and_group_permissions(self):
        """Test that effective privilege is calculated correctly with both user and group permissions"""

        # Add user to group with VIEW permission on the group
        self.owner.uaccess.share(group=self.test_group1, user=self.user1, privilege=PrivilegeCodes.VIEW)
        # Grant group VIEW permission on the resource
        self.owner.uaccess.share(resource=self.resource, group=self.test_group1, privilege=PrivilegeCodes.VIEW)

        # Verify user has VIEW permission via group
        ur = UserResource.objects.get(user=self.user1, resource=self.resource)
        self.assertEqual(ur.permission, PrivilegeCodes.VIEW)

        # Grant user direct CHANGE permission
        self.owner.uaccess.share(
            resource=self.resource,
            user=self.user1,
            privilege=PrivilegeCodes.CHANGE
        )

        # User should have CHANGE permission (higher of the two)
        ur.refresh_from_db()
        self.assertEqual(ur.permission, PrivilegeCodes.CHANGE)

        # Remove direct permission, should fall back to group permission
        self.owner.uaccess.unshare(
            resource=self.resource,
            user=self.user1
        )

        # Should still have VIEW from group membership
        ur.refresh_from_db()
        self.assertEqual(ur.permission, PrivilegeCodes.VIEW)

    def test_multiple_group_memberships_highest_permission(self):
        """Test that user gets highest permission from multiple group memberships"""
        # Add user to two groups with different permissions
        self.owner.uaccess.share(group=self.test_group1, user=self.user1, privilege=PrivilegeCodes.VIEW)
        self.owner.uaccess.share(group=self.test_group2, user=self.user1, privilege=PrivilegeCodes.VIEW)

        # Grant different permissions to groups
        self.owner.uaccess.share(resource=self.resource, group=self.test_group1, privilege=PrivilegeCodes.VIEW)
        self.owner.uaccess.share(resource=self.resource, group=self.test_group2, privilege=PrivilegeCodes.CHANGE)

        # User should have highest permission (CHANGE)
        ur = UserResource.objects.get(user=self.user1, resource=self.resource)
        self.assertEqual(ur.permission, PrivilegeCodes.CHANGE)

        # Remove higher permission group
        self.owner.uaccess.unshare(resource=self.resource, group=self.test_group2)

        # Should fall back to lower permission
        ur.refresh_from_db()
        self.assertEqual(ur.permission, PrivilegeCodes.VIEW)

    def test_mixed_permissions_direct_and_group(self):
        """Test complex scenario with both direct user permissions and group permissions"""
        # Start with group permission
        self.owner.uaccess.share(group=self.test_group1, user=self.user1, privilege=PrivilegeCodes.VIEW)
        self.owner.uaccess.share(resource=self.resource, group=self.test_group1, privilege=PrivilegeCodes.CHANGE)

        # User has CHANGE via group
        ur = UserResource.objects.get(user=self.user1, resource=self.resource)
        self.assertEqual(ur.permission, PrivilegeCodes.CHANGE)

        # Add direct VIEW permission (lower than group)
        self.owner.uaccess.share(resource=self.resource, user=self.user1, privilege=PrivilegeCodes.VIEW)

        # Should keep CHANGE (higher permission)
        ur.refresh_from_db()
        self.assertEqual(ur.permission, PrivilegeCodes.CHANGE)

        # Remove group permission
        self.owner.uaccess.unshare(resource=self.resource, group=self.test_group1)

        # Should fall back to direct VIEW permission
        ur.refresh_from_db()
        self.assertEqual(ur.permission, PrivilegeCodes.VIEW)

    def test_owner_permission_always_present(self):
        """Test that resource owner always has UserResource entry with owner permission"""
        # Owner should have UserResource entry
        ur = UserResource.objects.get(user=self.owner, resource=self.resource)
        self.assertEqual(ur.permission, PrivilegeCodes.OWNER)

    def test_cascading_group_membership_changes(self):
        """Test cascading changes when group memberships change"""
        # Create nested scenario: user in group, group has access to resource
        self.owner.uaccess.share(group=self.test_group1, user=self.user1, privilege=PrivilegeCodes.VIEW)
        self.owner.uaccess.share(resource=self.resource, group=self.test_group1, privilege=PrivilegeCodes.VIEW)

        # User2 joins group later
        self.owner.uaccess.share(group=self.test_group1, user=self.user2, privilege=PrivilegeCodes.VIEW)

        # Both users should have access
        ur1 = UserResource.objects.get(user=self.user1, resource=self.resource)
        ur2 = UserResource.objects.get(user=self.user2, resource=self.resource)
        self.assertEqual(ur1.permission, PrivilegeCodes.VIEW)
        self.assertEqual(ur2.permission, PrivilegeCodes.VIEW)

        # User1 leaves group
        self.owner.uaccess.unshare(group=self.test_group1, user=self.user1)

        # User1 loses access, User2 keeps it
        self.assertFalse(UserResource.objects.filter(user=self.user1, resource=self.resource).exists())
        self.assertTrue(UserResource.objects.filter(user=self.user2, resource=self.resource).exists())

    def test_no_permission_but_flags_preserved(self):
        """Test that UserResource entries with flags are preserved even without permissions"""
        # Grant permission and set flags
        self.owner.uaccess.share(resource=self.resource, user=self.user1, privilege=PrivilegeCodes.VIEW)

        ur = UserResource.objects.get(user=self.user1, resource=self.resource)
        ur.is_favorite = True
        ur.is_discovered = True
        ur.save()

        # Remove all permissions
        self.owner.uaccess.unshare(resource=self.resource, user=self.user1)

        # Entry should exist but with no permission
        ur.refresh_from_db()
        self.assertEqual(ur.permission, PrivilegeCodes.NONE)
        self.assertTrue(ur.is_favorite)
        self.assertTrue(ur.is_discovered)

    def test_signal_handlers_idempotent(self):
        """Test that signal handlers are idempotent - multiple calls don't create duplicates"""
        # Grant permission
        self.owner.uaccess.share(resource=self.resource, user=self.user1, privilege=PrivilegeCodes.VIEW)

        # Grant same permission again
        self.owner.uaccess.share(resource=self.resource, user=self.user1, privilege=PrivilegeCodes.VIEW)

        # Should still only have one UserResource entry
        count = UserResource.objects.filter(user=self.user1, resource=self.resource).count()
        self.assertEqual(count, 1)

    def test_bulk_operations_efficiency(self):
        """Test that signal handlers work efficiently with bulk operations"""
        users = [self.user1, self.user2, self.user3]

        # Add all users to group
        for user in users:
            self.owner.uaccess.share(group=self.test_group1, user=user, privilege=PrivilegeCodes.VIEW)

        # Grant group access to resource
        self.owner.uaccess.share(resource=self.resource, group=self.test_group1, privilege=PrivilegeCodes.VIEW)

        # All users should have UserResource entries
        for user in users:
            self.assertTrue(UserResource.objects.filter(user=user, resource=self.resource).exists())

        # Change group permission
        self.owner.uaccess.share(resource=self.resource, group=self.test_group1, privilege=PrivilegeCodes.CHANGE)

        # All users should have updated permissions
        for user in users:
            ur = UserResource.objects.get(user=user, resource=self.resource)
            self.assertEqual(ur.permission, PrivilegeCodes.CHANGE)

    def test_user_resource_flags_favorite_creates_entry(self):
        """Test that setting FAVORITE flag creates UserResource entry"""
        # Initially no UserResource entry for user1
        self.assertFalse(UserResource.objects.filter(user=self.user1, resource=self.resource).exists())

        # Set favorite flag
        self.user1.ulabels.flag_resource(self.resource, FlagCodes.FAVORITE)

        # UserResource entry should be created
        ur = UserResource.objects.get(user=self.user1, resource=self.resource)
        self.assertTrue(ur.is_favorite)
        self.assertFalse(ur.is_discovered)
        self.assertEqual(ur.permission, PrivilegeCodes.NONE)  # No permission granted

    def test_user_resource_flags_mine_creates_entry(self):
        """Test that setting MINE flag creates UserResource entry"""
        # Initially no UserResource entry for user1
        self.assertFalse(UserResource.objects.filter(user=self.user1, resource=self.resource).exists())

        # Set mine flag
        self.user1.ulabels.flag_resource(self.resource, FlagCodes.MINE)

        # UserResource entry should be created
        ur = UserResource.objects.get(user=self.user1, resource=self.resource)
        self.assertFalse(ur.is_favorite)
        self.assertTrue(ur.is_discovered)
        self.assertEqual(ur.permission, PrivilegeCodes.NONE)  # No permission granted

    def test_user_resource_flags_with_existing_permission(self):
        """Test that setting flags preserves existing permissions"""
        # Grant permission first
        self.owner.uaccess.share(resource=self.resource, user=self.user1, privilege=PrivilegeCodes.VIEW)

        ur = UserResource.objects.get(user=self.user1, resource=self.resource)
        self.assertEqual(ur.permission, PrivilegeCodes.VIEW)
        self.assertFalse(ur.is_favorite)

        # Set favorite flag
        self.user1.ulabels.flag_resource(self.resource, FlagCodes.FAVORITE)

        # Both permission and flag should be set
        ur.refresh_from_db()
        self.assertEqual(ur.permission, PrivilegeCodes.VIEW)
        self.assertTrue(ur.is_favorite)

    def test_user_resource_flags_remove_favorite_preserves_permission(self):
        """Test that removing FAVORITE flag preserves permission"""
        # Grant permission and set flag
        self.owner.uaccess.share(resource=self.resource, user=self.user1, privilege=PrivilegeCodes.VIEW)
        self.user1.ulabels.flag_resource(self.resource, FlagCodes.FAVORITE)

        # Verify both are set
        ur = UserResource.objects.get(user=self.user1, resource=self.resource)
        self.assertTrue(ur.is_favorite)
        self.assertEqual(ur.permission, PrivilegeCodes.VIEW)

        # Remove favorite flag
        self.user1.ulabels.unflag_resource(self.resource, FlagCodes.FAVORITE)

        # Permission should remain, flag should be cleared
        ur.refresh_from_db()
        self.assertFalse(ur.is_favorite)
        self.assertEqual(ur.permission, PrivilegeCodes.VIEW)

    def test_user_resource_flags_remove_favorite_no_permission_deletes_entry(self):
        """Test that removing FAVORITE flag with no permission deletes UserResource entry"""
        # Set favorite flag only (no permission)
        self.user1.ulabels.flag_resource(self.resource, FlagCodes.FAVORITE)

        # Verify entry exists
        self.assertTrue(UserResource.objects.filter(user=self.user1, resource=self.resource).exists())

        # Remove favorite flag
        self.user1.ulabels.unflag_resource(self.resource, FlagCodes.FAVORITE)

        # Entry should be deleted since no permission and no flags
        self.assertFalse(UserResource.objects.filter(user=self.user1, resource=self.resource).exists())

    def test_user_resource_flags_remove_mine_preserves_favorite(self):
        """Test that removing MINE flag preserves FAVORITE flag"""
        # Set both flags
        self.user1.ulabels.flag_resource(self.resource, FlagCodes.FAVORITE)
        self.user1.ulabels.flag_resource(self.resource, FlagCodes.MINE)

        # Verify both are set
        ur = UserResource.objects.get(user=self.user1, resource=self.resource)
        self.assertTrue(ur.is_favorite)
        self.assertTrue(ur.is_discovered)

        # Remove mine flag
        self.user1.ulabels.unflag_resource(self.resource, FlagCodes.MINE)

        # Favorite should remain, mine should be cleared
        ur.refresh_from_db()
        self.assertTrue(ur.is_favorite)
        self.assertFalse(ur.is_discovered)

    def test_user_resource_flags_both_flags_set(self):
        """Test that both FAVORITE and MINE flags can be set simultaneously"""
        # Set both flags
        self.user1.ulabels.flag_resource(self.resource, FlagCodes.FAVORITE)
        self.user1.ulabels.flag_resource(self.resource, FlagCodes.MINE)

        # Both should be set
        ur = UserResource.objects.get(user=self.user1, resource=self.resource)
        self.assertTrue(ur.is_favorite)
        self.assertTrue(ur.is_discovered)
        self.assertEqual(ur.permission, PrivilegeCodes.NONE)

    def test_user_resource_flags_permissions_and_flags_interaction(self):
        """Test complex interaction between permissions and flags"""
        # Start with favorite flag
        self.user1.ulabels.flag_resource(self.resource, FlagCodes.FAVORITE)
        ur = UserResource.objects.get(user=self.user1, resource=self.resource)
        self.assertTrue(ur.is_favorite)
        self.assertEqual(ur.permission, PrivilegeCodes.NONE)

        # Add permission
        self.owner.uaccess.share(resource=self.resource, user=self.user1, privilege=PrivilegeCodes.VIEW)
        ur.refresh_from_db()
        self.assertTrue(ur.is_favorite)
        self.assertEqual(ur.permission, PrivilegeCodes.VIEW)

        # Add mine flag
        self.user1.ulabels.flag_resource(self.resource, FlagCodes.MINE)
        ur.refresh_from_db()
        self.assertTrue(ur.is_favorite)
        self.assertTrue(ur.is_discovered)
        self.assertEqual(ur.permission, PrivilegeCodes.VIEW)

        # Remove permission
        self.owner.uaccess.unshare(resource=self.resource, user=self.user1)
        ur.refresh_from_db()
        self.assertTrue(ur.is_favorite)
        self.assertTrue(ur.is_discovered)
        self.assertEqual(ur.permission, PrivilegeCodes.NONE)

        # Remove favorite flag
        self.user1.ulabels.unflag_resource(self.resource, FlagCodes.FAVORITE)
        ur.refresh_from_db()
        self.assertFalse(ur.is_favorite)
        self.assertTrue(ur.is_discovered)
        self.assertEqual(ur.permission, PrivilegeCodes.NONE)

        # Remove mine flag (should delete entry)
        self.user1.ulabels.unflag_resource(self.resource, FlagCodes.MINE)
        self.assertFalse(UserResource.objects.filter(user=self.user1, resource=self.resource).exists())

    def test_user_resource_flags_signal_handlers_idempotent(self):
        """Test that flag signal handlers are idempotent"""
        # Set favorite flag twice
        self.user1.ulabels.flag_resource(self.resource, FlagCodes.FAVORITE)
        self.user1.ulabels.flag_resource(self.resource, FlagCodes.FAVORITE)  # Should be idempotent

        # Should still only have one UserResource entry
        count = UserResource.objects.filter(user=self.user1, resource=self.resource).count()
        self.assertEqual(count, 1)

        ur = UserResource.objects.get(user=self.user1, resource=self.resource)
        self.assertTrue(ur.is_favorite)
