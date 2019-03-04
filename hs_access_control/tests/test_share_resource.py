from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group

from hs_access_control.models import UserResourcePrivilege, GroupResourcePrivilege, PrivilegeCodes

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin

from hs_access_control.tests.utilities import global_reset, is_equal_to_as_set, \
    assertUserResourceUnshareCoherence, assertUserGroupUnshareCoherence


class T05ShareResource(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(T05ShareResource, self).setUp()
        global_reset()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.admin = hydroshare.create_account(
            'admin@gmail.com',
            username='admin',
            first_name='administrator',
            last_name='couch',
            superuser=True,
            groups=[]
        )

        self.cat = hydroshare.create_account(
            'cat@gmail.com',
            username='cat',
            first_name='not a dog',
            last_name='last_name_cat',
            superuser=False,
            groups=[]
        )

        self.dog = hydroshare.create_account(
            'dog@gmail.com',
            username='dog',
            first_name='a little arfer',
            last_name='last_name_dog',
            superuser=False,
            groups=[]
        )

        # use this as non owner
        self.mouse = hydroshare.create_account(
            'mouse@gmail.com',
            username='mouse',
            first_name='first_name_mouse',
            last_name='last_name_mouse',
            superuser=False,
            groups=[]
        )
        self.holes = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.cat,
            title='all about dog holes',
            metadata=[],
        )

        self.meowers = self.cat.uaccess.create_group(
            title='some random meowers', description="some random group")

    def test_01_resource_unshared_state(self):
        """Resources cannot be accessed by users with no access"""
        # dog should not have sharing privileges
        holes = self.holes
        cat = self.cat
        dog = self.dog

        # privilege of owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))
        self.assertEqual(
            1, UserResourcePrivilege.objects.filter(
                user=cat, resource=holes).count())

        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.view_users))

        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.edit_users))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.edit_groups))
        self.assertTrue(
            is_equal_to_as_set(
                [], cat.uaccess.get_resource_unshare_users(holes)))
        self.assertTrue(
            is_equal_to_as_set(
                [], cat.uaccess.get_resource_unshare_groups(holes)))

        # metadata state
        self.assertFalse(holes.raccess.public)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.immutable)
        self.assertTrue(holes.raccess.shareable)

        # privilege of other user
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))
        self.assertEqual(
            0, UserResourcePrivilege.objects.filter(
                user=dog, resource=holes).count())

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # unshare method coherence
        assertUserResourceUnshareCoherence(self)

    def test_02_share_resource_ownership(self):
        """Resources can be shared as OWNER by owner"""
        holes = self.holes
        dog = self.dog
        cat = self.cat

        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.edit_users))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.edit_groups))
        self.assertTrue(
            is_equal_to_as_set(
                [], cat.uaccess.get_resource_unshare_users(holes)))
        self.assertTrue(
            is_equal_to_as_set(
                [], cat.uaccess.get_resource_unshare_groups(holes)))

        self.assertEqual(holes.raccess.owners.count(), 1)
        self.assertEqual(holes.raccess.view_users.count(), 1)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))
        self.assertEqual(
            1, UserResourcePrivilege.objects.filter(
                user=cat, resource=holes).count())

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))
        self.assertEqual(
            0, UserResourcePrivilege.objects.filter(
                user=dog, resource=holes).count())

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # unshare method coherence
        assertUserResourceUnshareCoherence(self)

        # share holes with dog as owner
        self.assertTrue(
            cat.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.OWNER))
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.OWNER)

        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))

        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.edit_users))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.edit_groups))

        # cat is the quota holder, so cannot be unshared
        self.assertTrue(is_equal_to_as_set([dog], cat.uaccess.get_resource_unshare_users(holes)))
        self.assertTrue(
            is_equal_to_as_set(
                [], cat.uaccess.get_resource_unshare_groups(holes)))

        self.assertEqual(holes.raccess.owners.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))
        self.assertEqual(
            1, UserResourcePrivilege.objects.filter(
                user=cat, resource=holes).count())

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertTrue(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))
        self.assertEqual(
            1, UserResourcePrivilege.objects.filter(
                user=dog, resource=holes).count())
        self.assertEqual(
            cat, UserResourcePrivilege.objects.get(
                user=dog, resource=holes).grantor)

        # composite django state for dog
        self.assertTrue(dog.uaccess.can_change_resource_flags(holes))
        self.assertTrue(dog.uaccess.can_delete_resource(holes))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # unshare method coherence
        assertUserResourceUnshareCoherence(self)

        # test for idempotence of owner shares
        self.assertTrue(
            cat.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.OWNER))
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.OWNER)

        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))

        self.assertEqual(holes.raccess.owners.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertTrue(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))
        self.assertEqual(
            1, UserResourcePrivilege.objects.filter(
                user=dog, resource=holes).count())
        self.assertEqual(
            cat, UserResourcePrivilege.objects.get(
                user=dog, resource=holes).grantor)

        # composite django state for dog
        self.assertTrue(dog.uaccess.can_change_resource_flags(holes))
        self.assertTrue(dog.uaccess.can_delete_resource(holes))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # recheck metadata state: should not have changed
        self.assertFalse(holes.raccess.public)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.immutable)
        self.assertTrue(holes.raccess.shareable)

        # unshare method coherence
        assertUserResourceUnshareCoherence(self)

    def test_03_share_resource_rw(self):
        """Resources can be shared as CHANGE by owner"""
        holes = self.holes
        dog = self.dog
        cat = self.cat

        # initial state
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.view_users))

        self.assertEqual(holes.raccess.owners.count(), 1)
        self.assertEqual(holes.raccess.view_users.count(), 1)
        self.assertEqual(holes.raccess.view_users.count(), 1)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))
        self.assertEqual(
            0, UserResourcePrivilege.objects.filter(
                user=dog, resource=holes).count())

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        self.assertFalse(
            cat.uaccess.can_unshare_resource_with_user(
                holes, dog))
        self.assertTrue(
            is_equal_to_as_set(
                [], cat.uaccess.get_resource_unshare_users(holes)))

        # unshare method coherence
        assertUserResourceUnshareCoherence(self)

        # share with dog at rw privilege
        self.assertTrue(
            cat.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.CHANGE))
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.CHANGE)

        self.assertTrue(cat.uaccess.can_unshare_resource_with_user(holes, dog))
        self.assertTrue(
            is_equal_to_as_set(
                [dog],
                cat.uaccess.get_resource_unshare_users(holes)))

        # initial state
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))

        self.assertEqual(holes.raccess.owners.count(), 1)
        self.assertEqual(holes.raccess.view_users.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # unshare method coherence
        assertUserResourceUnshareCoherence(self)

        # test for idempotence of sharing
        self.assertTrue(
            cat.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.CHANGE))
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.CHANGE)

        # check for unchanged configuration
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))

        self.assertEqual(holes.raccess.owners.count(), 1)
        self.assertEqual(holes.raccess.view_users.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # recheck metadata state
        self.assertFalse(holes.raccess.public)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.immutable)
        self.assertTrue(holes.raccess.shareable)

        # unshare method coherence
        assertUserResourceUnshareCoherence(self)

    def test_04_share_resource_ro(self):
        """Resources can be shared as VIEW by owner"""
        holes = self.holes
        dog = self.dog
        cat = self.cat

        # initial state
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.view_users))

        self.assertEqual(holes.raccess.owners.count(), 1)
        self.assertEqual(holes.raccess.view_users.count(), 1)
        self.assertEqual(holes.raccess.view_users.count(), 1)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # unshare method coherence
        assertUserResourceUnshareCoherence(self)

        # share with view privilege
        self.assertTrue(
            cat.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.VIEW))
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.VIEW)

        # shared state
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))

        self.assertEqual(holes.raccess.owners.count(), 1)
        self.assertEqual(holes.raccess.view_users.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # unshare method coherence
        assertUserResourceUnshareCoherence(self)

        # check for idempotence
        self.assertTrue(
            cat.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.VIEW))
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.VIEW)

        # same state
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))

        self.assertEqual(holes.raccess.owners.count(), 1)
        self.assertEqual(holes.raccess.view_users.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # recheck metadata state
        self.assertFalse(holes.raccess.public)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.immutable)
        self.assertTrue(holes.raccess.shareable)

        # ensure that nothing changed
        self.assertFalse(holes.raccess.public)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.immutable)
        self.assertTrue(holes.raccess.shareable)

        # unshare method coherence
        assertUserResourceUnshareCoherence(self)

    def test_05_share_resource_downgrade_privilege(self):
        """Resource sharing privileges can be downgraded by owner"""
        holes = self.holes
        dog = self.dog
        cat = self.cat
        mouse = self.mouse
        # initial state
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.view_users))

        self.assertEqual(holes.raccess.owners.count(), 1)
        self.assertEqual(holes.raccess.view_users.count(), 1)
        self.assertEqual(holes.raccess.view_users.count(), 1)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # unshare method coherence
        assertUserResourceUnshareCoherence(self)

        # share as owner
        self.assertTrue(
            self.cat.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.OWNER))
        self.cat.uaccess.share_resource_with_user(
            holes, dog, PrivilegeCodes.OWNER)

        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))

        self.assertEqual(holes.raccess.owners.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertTrue(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))

        # composite django state for dog
        self.assertTrue(dog.uaccess.can_change_resource_flags(holes))
        self.assertTrue(dog.uaccess.can_delete_resource(holes))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # metadata state
        self.assertFalse(holes.raccess.public)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.immutable)
        self.assertTrue(holes.raccess.shareable)

        # unshare method coherence
        assertUserResourceUnshareCoherence(self)

        # downgrade from OWNER to CHANGE
        self.assertTrue(
            self.cat.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.CHANGE))
        self.cat.uaccess.share_resource_with_user(
            holes, dog, PrivilegeCodes.CHANGE)

        # check for correctness
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))

        self.assertEqual(holes.raccess.owners.count(), 1)
        self.assertEqual(holes.raccess.view_users.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # unshare method coherence
        assertUserResourceUnshareCoherence(self)

        # downgrade from CHANGE to VIEW
        self.assertTrue(
            self.cat.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.VIEW))
        self.cat.uaccess.share_resource_with_user(
            holes, dog, PrivilegeCodes.VIEW)

        # initial state
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))

        self.assertEqual(holes.raccess.owners.count(), 1)
        self.assertEqual(holes.raccess.view_users.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # unshare method coherence
        assertUserResourceUnshareCoherence(self)

        # downgrade to no privilege
        self.assertTrue(
            self.cat.uaccess.can_unshare_resource_with_user(
                holes, dog))
        self.cat.uaccess.unshare_resource_with_user(holes, dog)

        # initial state
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.edit_users))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.edit_groups))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state for car
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # unshare method coherence
        assertUserResourceUnshareCoherence(self)

        # set edit privilege for mouse on holes
        self.assertTrue(
            self.cat.uaccess.can_share_resource_with_user(
                holes, mouse, PrivilegeCodes.CHANGE))
        self.cat.uaccess.share_resource_with_user(
            holes, mouse, PrivilegeCodes.CHANGE)

        self.assertEqual(
            self.holes.raccess.get_effective_privilege(
                self.mouse), PrivilegeCodes.CHANGE)

        # set edit privilege for dog on holes
        self.assertTrue(
            self.cat.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.CHANGE))
        self.cat.uaccess.share_resource_with_user(
            holes, dog, PrivilegeCodes.CHANGE)
        self.assertEqual(
            self.holes.raccess.get_effective_privilege(
                self.dog), PrivilegeCodes.CHANGE)

        # non owner (mouse) should not be able to downgrade privilege of dog from edit/change
        # (originally granted by cat) to view
        self.assertFalse(
            self.mouse.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.VIEW))
        with self.assertRaises(PermissionDenied):
            self.mouse.uaccess.share_resource_with_user(
                holes, dog, PrivilegeCodes.VIEW)
        self.assertTrue(
            self.cat.uaccess.can_unshare_resource_with_user(
                holes, dog))
        self.cat.uaccess.unshare_resource_with_user(holes, dog)
        self.assertEqual(
            self.holes.raccess.get_effective_privilege(
                self.dog), PrivilegeCodes.NONE)

        # non owner (mouse) should NOT be able to downgrade privilege of a user (dog) originally
        # granted by the same non owner (mouse). This is the new semantics.
        self.assertTrue(
            self.mouse.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.CHANGE))
        self.mouse.uaccess.share_resource_with_user(
            holes, dog, PrivilegeCodes.CHANGE)
        self.assertEqual(
            self.holes.raccess.get_effective_privilege(
                self.dog), PrivilegeCodes.CHANGE)
        self.assertFalse(
            self.mouse.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.VIEW))
        with self.assertRaises(PermissionDenied):
            self.mouse.uaccess.share_resource_with_user(
                holes, dog, PrivilegeCodes.VIEW)
        self.assertEqual(
            self.holes.raccess.get_effective_privilege(
                self.dog), PrivilegeCodes.CHANGE)

        # django admin should be able to downgrade privilege
        self.assertTrue(
            self.cat.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.OWNER))
        self.cat.uaccess.share_resource_with_user(
            holes, dog, PrivilegeCodes.OWNER)
        self.assertTrue(dog.uaccess.can_change_resource_flags(holes))
        self.assertTrue(dog.uaccess.owns_resource(holes))

        self.assertTrue(
            self.admin.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.CHANGE))
        self.admin.uaccess.share_resource_with_user(
            holes, dog, PrivilegeCodes.CHANGE)
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.owns_resource(holes))

        # unshare method coherence
        assertUserResourceUnshareCoherence(self)

    def test_06_group_unshared_state(self):
        """Groups cannot be accessed by users with no access"""
        # dog should not have sharing privileges
        meowers = self.meowers
        cat = self.cat
        dog = self.dog

        # privilege of owner
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertTrue(meowers.gaccess.public)
        self.assertTrue(meowers.gaccess.discoverable)
        self.assertTrue(meowers.gaccess.shareable)

        # privilege of other user
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # test for coherence of group sharing functions
        assertUserGroupUnshareCoherence(self)

    def test_07_share_group_ownership(self):
        """Groups can be shared as OWNER by owner"""
        meowers = self.meowers
        dog = self.dog
        cat = self.cat

        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 1)
        self.assertEqual(meowers.gaccess.members.count(), 1)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # test for coherence of group sharing functions
        assertUserGroupUnshareCoherence(self)

        # share meowers with dog as owner
        self.assertTrue(
            cat.uaccess.can_share_group_with_user(
                meowers, dog, PrivilegeCodes.OWNER))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.OWNER)

        self.assertTrue(is_equal_to_as_set([cat, dog], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 2)
        self.assertEqual(meowers.gaccess.members.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertTrue(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state for dog
        self.assertTrue(dog.uaccess.can_change_group_flags(meowers))
        self.assertTrue(dog.uaccess.can_delete_group(meowers))
        self.assertTrue(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertTrue(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # test for coherence of group sharing functions
        assertUserGroupUnshareCoherence(self)

        # test for idempotence of owner request
        self.assertTrue(
            cat.uaccess.can_share_group_with_user(
                meowers, dog, PrivilegeCodes.OWNER))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.OWNER)

        self.assertTrue(is_equal_to_as_set([cat, dog], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 2)
        self.assertEqual(meowers.gaccess.members.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertTrue(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state for dog
        self.assertTrue(dog.uaccess.can_change_group_flags(meowers))
        self.assertTrue(dog.uaccess.can_delete_group(meowers))
        self.assertTrue(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertTrue(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # recheck metadata state: should not have changed
        self.assertTrue(meowers.gaccess.public)
        self.assertTrue(meowers.gaccess.discoverable)
        self.assertTrue(meowers.gaccess.shareable)

        # test for coherence of group unsharing functions
        assertUserGroupUnshareCoherence(self)

    def test_08_share_group_rw(self):
        """Groups can be shared as CHANGE by owner"""
        meowers = self.meowers
        dog = self.dog
        cat = self.cat

        # initial state
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 1)
        self.assertEqual(meowers.gaccess.members.count(), 1)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # share with dog at rw privilege
        self.assertFalse(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        self.assertTrue(
            is_equal_to_as_set(
                [], cat.uaccess.get_group_unshare_users(meowers)))

        # coherence of unsharing
        assertUserGroupUnshareCoherence(self)

        self.assertTrue(
            cat.uaccess.can_share_group_with_user(
                meowers, dog, PrivilegeCodes.CHANGE))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.CHANGE)

        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        self.assertTrue(
            is_equal_to_as_set(
                [dog],
                cat.uaccess.get_group_unshare_users(meowers)))

        # check other state for this change
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 1)
        self.assertEqual(meowers.gaccess.members.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertTrue(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # test for coherence of group unsharing functions
        assertUserGroupUnshareCoherence(self)

        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        # test for idempotence of owner sharing
        self.assertTrue(
            cat.uaccess.can_share_group_with_user(
                meowers, dog, PrivilegeCodes.CHANGE))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        # check for unchanged configuration
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 1)
        self.assertEqual(meowers.gaccess.members.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertTrue(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # recheck metadata state
        self.assertTrue(meowers.gaccess.public)
        self.assertTrue(meowers.gaccess.discoverable)
        self.assertTrue(meowers.gaccess.shareable)

        # test for coherence of group unsharing functions
        assertUserGroupUnshareCoherence(self)

    def test_09_share_group_ro(self):
        """Groups can be shared as VIEW by owner"""
        meowers = self.meowers
        dog = self.dog
        cat = self.cat

        # initial state
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 1)
        self.assertEqual(meowers.gaccess.members.count(), 1)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # test for coherence of group unsharing functions
        assertUserGroupUnshareCoherence(self)

        # share with view privilege
        self.assertFalse(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        self.assertTrue(
            cat.uaccess.can_share_group_with_user(
                meowers, dog, PrivilegeCodes.VIEW))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.VIEW)
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        # shared state
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 1)
        self.assertEqual(meowers.gaccess.members.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # test for coherence of group unsharing functions
        assertUserGroupUnshareCoherence(self)

        # check for idempotence
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        self.assertTrue(
            cat.uaccess.can_share_group_with_user(
                meowers, dog, PrivilegeCodes.VIEW))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.VIEW)
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        # shared state
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 1)
        self.assertEqual(meowers.gaccess.members.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # recheck metadata state
        self.assertTrue(meowers.gaccess.public)
        self.assertTrue(meowers.gaccess.discoverable)
        self.assertTrue(meowers.gaccess.shareable)

        # test for coherence of group unsharing functions
        assertUserGroupUnshareCoherence(self)

    def test_10_share_group_downgrade_privilege(self):
        """Group sharing privileges can be downgraded by owner"""
        meowers = self.meowers
        dog = self.dog
        cat = self.cat

        # initial state
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 1)
        self.assertEqual(meowers.gaccess.members.count(), 1)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # test for coherence of group unsharing functions
        assertUserGroupUnshareCoherence(self)

        # share as owner
        self.assertFalse(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        self.assertTrue(
            cat.uaccess.can_share_group_with_user(
                meowers, dog, PrivilegeCodes.OWNER))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.OWNER)
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        self.assertTrue(is_equal_to_as_set([cat, dog], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 2)
        self.assertEqual(meowers.gaccess.members.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertTrue(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state for dog
        self.assertTrue(dog.uaccess.can_change_group_flags(meowers))
        self.assertTrue(dog.uaccess.can_delete_group(meowers))
        self.assertTrue(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertTrue(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # metadata state
        self.assertTrue(meowers.gaccess.public)
        self.assertTrue(meowers.gaccess.discoverable)
        self.assertTrue(meowers.gaccess.shareable)

        # test for coherence of group unsharing functions
        assertUserGroupUnshareCoherence(self)

        # downgrade from OWNER to CHANGE
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        self.assertTrue(
            cat.uaccess.can_share_group_with_user(
                meowers, dog, PrivilegeCodes.CHANGE))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        # check for correctness
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 1)
        self.assertEqual(meowers.gaccess.members.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertTrue(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # test for coherence of group unsharing functions
        assertUserGroupUnshareCoherence(self)

        # downgrade from CHANGE to VIEW
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        self.assertTrue(
            cat.uaccess.can_share_group_with_user(
                meowers, dog, PrivilegeCodes.VIEW))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.VIEW)
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        # initial state
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 1)
        self.assertEqual(meowers.gaccess.members.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # test for coherence of group unsharing functions
        assertUserGroupUnshareCoherence(self)

        # downgrade to no privilege
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        cat.uaccess.unshare_group_with_user(meowers, dog)
        self.assertFalse(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        # back to initial state
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 1)
        self.assertEqual(meowers.gaccess.members.count(), 1)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        # composite django state for cat
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.CHANGE))
        self.assertFalse(
            dog.uaccess.can_share_group(
                meowers, PrivilegeCodes.VIEW))

        # admin too should be able to downgrade (e.g. from OWNER to CHANGE)
        self.assertTrue(
            cat.uaccess.can_share_group_with_user(
                meowers, dog, PrivilegeCodes.OWNER))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.OWNER)
        self.assertTrue(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group_flags(meowers))

        self.assertTrue(
            self.admin.uaccess.can_share_group_with_user(
                meowers, dog, PrivilegeCodes.CHANGE))
        self.admin.uaccess.share_group_with_user(
            meowers, dog, PrivilegeCodes.CHANGE)
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.owns_group(meowers))

        # test for coherence of group unsharing functions
        assertUserGroupUnshareCoherence(self)

    def test_11_resource_sharing_with_group(self):
        """Group cannot own a resource"""
        meowers = self.meowers
        holes = self.holes
        dog = self.dog
        cat = self.cat

        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.owners))

        self.assertEqual(meowers.gaccess.owners.count(), 1)
        # make dog a co-owner
        self.assertTrue(
            cat.uaccess.can_share_group_with_user(
                meowers, dog, PrivilegeCodes.OWNER))
        cat.uaccess.share_group_with_user(
            meowers, dog, PrivilegeCodes.OWNER)  # make dog a co-owner
        self.assertTrue(is_equal_to_as_set([cat, dog], meowers.gaccess.owners))
        self.assertEqual(meowers.gaccess.owners.count(), 2)
        # repeating the command should be idempotent
        self.assertTrue(
            cat.uaccess.can_share_group_with_user(
                meowers, dog, PrivilegeCodes.OWNER))
        cat.uaccess.share_group_with_user(
            meowers, dog, PrivilegeCodes.OWNER)  # make dog a co-owner
        self.assertTrue(is_equal_to_as_set([cat, dog], meowers.gaccess.owners))
        self.assertEqual(meowers.gaccess.owners.count(), 2)

        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))

        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertFalse(
            cat.uaccess.can_unshare_resource_with_user(
                holes, dog))

        self.assertTrue(
            is_equal_to_as_set(
                [], cat.uaccess.get_resource_unshare_users(holes)))

        self.assertTrue(
            cat.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.OWNER))
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.OWNER)

        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))
        self.assertTrue(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.owns_group(meowers))

        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_unshare_resource_with_user(holes, dog))
        # assert cat is the quota holder and quota holder cannot be removed from ownership
        self.assertTrue(holes.get_quota_holder(), cat)
        self.assertFalse(cat.uaccess.can_unshare_resource_with_user(holes, cat))
        self.assertTrue(dog.uaccess.can_unshare_resource_with_user(holes, dog))
        self.assertFalse(dog.uaccess.can_unshare_resource_with_user(holes, cat))

        # test list access functions for unshare targets
        self.assertTrue(is_equal_to_as_set(
            [dog], cat.uaccess.get_resource_unshare_users(holes)))

        self.assertTrue(is_equal_to_as_set(
            [dog], dog.uaccess.get_resource_unshare_users(holes)))

        # test idempotence of sharing
        self.assertTrue(
            cat.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.OWNER))
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.OWNER)
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_unshare_resource_with_user(holes, dog))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))
        self.assertTrue(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.owns_group(meowers))

        # owner dog of meowers tries to make holes owned by group meowers
        self.assertFalse(
            dog.uaccess.can_share_resource_with_group(
                holes, meowers, PrivilegeCodes.OWNER))
        with self.assertRaises(PermissionDenied) as cm:
            dog.uaccess.share_resource_with_group(
                holes, meowers, PrivilegeCodes.OWNER)
        self.assertEqual(cm.exception.message, 'Groups cannot own resources')

        # even django admin can't make a group as the owner of a resource
        self.assertFalse(
            self.admin.uaccess.can_share_resource_with_group(
                holes, meowers, PrivilegeCodes.OWNER))
        with self.assertRaises(PermissionDenied) as cm:
            self.admin.uaccess.share_resource_with_group(
                holes, meowers, PrivilegeCodes.OWNER)
        self.assertEqual(cm.exception.message, 'Groups cannot own resources')

    def test_12_resource_sharing_rw_with_group(self):
        """Resource can be shared as CHANGE with a group"""
        dog = self.dog
        cat = self.cat
        holes = self.holes
        meowers = self.meowers

        # now share something with dog via group meowers
        self.assertTrue(
            cat.uaccess.can_share_group_with_user(
                meowers, dog, PrivilegeCodes.CHANGE))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], meowers.gaccess.members.all()))

        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertFalse(
            cat.uaccess.can_unshare_resource_with_group(
                holes, meowers))

        self.assertTrue(
            cat.uaccess.can_share_resource_with_group(
                holes, meowers, PrivilegeCodes.CHANGE))
        cat.uaccess.share_resource_with_group(
            holes, meowers, PrivilegeCodes.CHANGE)
        self.assertTrue(
            cat.uaccess.can_unshare_resource_with_group(
                holes, meowers))
        self.assertTrue(is_equal_to_as_set(
            [cat, dog], holes.raccess.view_users))

        # simple sharing state
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # turn off group sharing
        cat.uaccess.unshare_resource_with_group(holes, meowers)
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertFalse(
            cat.uaccess.can_unshare_resource_with_group(
                holes, meowers))
        # simple sharing state
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

    def test_13_self_reduction_of_privilege(self):
        """ Test that a non-owner can self-degrade CHANGE to VIEW and from VIEW to NONE """
        holes = self.holes
        cat = self.cat
        dog = self.dog
        self.assertTrue(
            cat.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.CHANGE))
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.CHANGE)

        self.assertTrue(
            dog.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.VIEW))
        dog.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.VIEW)

        # simple sharing state
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # self-unshare
        self.assertTrue(dog.uaccess.can_unshare_resource_with_user(holes, dog))
        dog.uaccess.unshare_resource_with_user(holes, dog)
        assertUserResourceUnshareCoherence(self)

        # simple sharing state
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))

        # composite django state for dog
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

    def test_14_non_idempotence_of_unprivileged_share(self):
        """ test that unprivileged shares are not repeatable """
        cat = self.cat
        dog = self.dog
        mouse = self.mouse
        holes = self.holes
        meowers = self.meowers

        # for resources:
        self.assertTrue(
            cat.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.VIEW))
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.VIEW)
        self.assertTrue(
            dog.uaccess.can_share_resource_with_user(
                holes, mouse, PrivilegeCodes.VIEW))
        dog.uaccess.share_resource_with_user(holes, mouse, PrivilegeCodes.VIEW)
        self.assertFalse(
            dog.uaccess.can_share_resource_with_user(
                holes, mouse, PrivilegeCodes.VIEW))
        with self.assertRaises(PermissionDenied):  # not idempotent
            dog.uaccess.share_resource_with_user(
                holes, mouse, PrivilegeCodes.VIEW)
        # but can increase privilege
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(
            dog.uaccess.can_share_resource_with_user(
                holes, mouse, PrivilegeCodes.CHANGE))
        dog.uaccess.share_resource_with_user(
            holes, mouse, PrivilegeCodes.CHANGE)
        self.assertFalse(
            dog.uaccess.can_share_resource_with_user(
                holes, mouse, PrivilegeCodes.CHANGE))
        with self.assertRaises(PermissionDenied):  # not idempotent
            dog.uaccess.share_resource_with_user(
                holes, mouse, PrivilegeCodes.CHANGE)
        self.assertFalse(
            dog.uaccess.can_share_resource_with_user(
                holes, mouse, PrivilegeCodes.VIEW))
        # unpriviliged user cannot downgrade
        with self.assertRaises(PermissionDenied):
            dog.uaccess.share_resource_with_user(
                holes, mouse, PrivilegeCodes.VIEW)

        # for groups:
        self.assertTrue(
            cat.uaccess.can_share_group_with_user(
                meowers, dog, PrivilegeCodes.CHANGE))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(
            dog.uaccess.can_share_group_with_user(
                meowers, mouse, PrivilegeCodes.VIEW))
        dog.uaccess.share_group_with_user(meowers, mouse, PrivilegeCodes.VIEW)
        self.assertFalse(
            dog.uaccess.can_share_group_with_user(
                meowers, mouse, PrivilegeCodes.VIEW))
        with self.assertRaises(PermissionDenied):  # non-idempotent
            dog.uaccess.share_group_with_user(
                meowers, mouse, PrivilegeCodes.VIEW)
        # but can raise privilege
        self.assertTrue(
            cat.uaccess.can_share_group_with_user(
                meowers, dog, PrivilegeCodes.CHANGE))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(
            dog.uaccess.can_share_group_with_user(
                meowers, mouse, PrivilegeCodes.CHANGE))
        dog.uaccess.share_group_with_user(
            meowers, mouse, PrivilegeCodes.CHANGE)
        # and raised privilege is not idempotent
        self.assertFalse(
            dog.uaccess.can_share_group_with_user(
                meowers, mouse, PrivilegeCodes.CHANGE))
        with self.assertRaises(PermissionDenied):
            dog.uaccess.share_group_with_user(
                meowers, mouse, PrivilegeCodes.CHANGE)

        # for resources over groups
        self.assertTrue(
            dog.uaccess.can_share_resource_with_group(
                holes, meowers, PrivilegeCodes.VIEW))
        dog.uaccess.share_resource_with_group(
            holes, meowers, PrivilegeCodes.VIEW)
        self.assertFalse(
            dog.uaccess.can_share_resource_with_group(
                holes, meowers, PrivilegeCodes.VIEW))
        with self.assertRaises(PermissionDenied):
            dog.uaccess.share_resource_with_group(
                holes, meowers, PrivilegeCodes.VIEW)
        self.assertTrue(
            cat.uaccess.can_share_resource_with_user(
                holes, dog, PrivilegeCodes.CHANGE))
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(
            dog.uaccess.can_share_resource_with_group(
                holes, meowers, PrivilegeCodes.CHANGE))
        dog.uaccess.share_resource_with_group(
            holes, meowers, PrivilegeCodes.CHANGE)
        self.assertFalse(
            dog.uaccess.can_share_resource_with_group(
                holes, meowers, PrivilegeCodes.CHANGE))
        with self.assertRaises(PermissionDenied):
            dog.uaccess.share_resource_with_group(
                holes, meowers, PrivilegeCodes.CHANGE)

    def test_15_share_record_printing(self):
        """ test stringification of sharing records for debugging """
        cat = self.cat
        holes = self.holes
        meowers = self.meowers
        cat.uaccess.share_resource_with_group(
            holes, meowers, PrivilegeCodes.VIEW)

        # format sharing record for user
        foo = str(UserResourcePrivilege.objects.get(user=cat, resource=holes))
        self.assertTrue(foo.find(holes.short_id.encode('ascii')) >= 0)

        # format sharing record for group
        foo = str(
            GroupResourcePrivilege.objects.get(
                group=meowers,
                resource=holes))
        self.assertTrue(foo.find(holes.short_id.encode('ascii')) >= 0)

    def test_privilege_to_string(self):
        self.assertEquals(PrivilegeCodes.VIEW, PrivilegeCodes.from_string("view"))
        self.assertEquals(PrivilegeCodes.CHANGE, PrivilegeCodes.from_string("edit"))
        self.assertEquals(PrivilegeCodes.OWNER, PrivilegeCodes.from_string("owner"))
        self.assertEquals(PrivilegeCodes.NONE, PrivilegeCodes.from_string("none"))
        self.assertEquals(None, PrivilegeCodes.from_string("bads"))
