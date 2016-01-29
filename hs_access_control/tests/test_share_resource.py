__author__ = 'Alva'

import unittest
from django.http import Http404
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User, Group
from pprint import pprint

from hs_access_control.models import UserAccess, GroupAccess, ResourceAccess, \
    UserResourcePrivilege, GroupResourcePrivilege, UserGroupPrivilege, PrivilegeCodes

from hs_core import hydroshare
from hs_core.models import GenericResource, BaseResource
from hs_core.testing import MockIRODSTestCaseMixin

from hs_access_control.tests.utilities import *


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
        self.holes = hydroshare.create_resource(resource_type='GenericResource',
                                                owner=self.cat,
                                                title='all about dog holes',
                                                metadata=[],)

        self.meowers = self.cat.uaccess.create_group('some random meowers')

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

        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.view_users))

        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.edit_users))
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.edit_groups))
        self.assertTrue(is_equal_to_as_set([], cat.uaccess.get_resource_unshare_users(holes)))
        self.assertTrue(is_equal_to_as_set([], cat.uaccess.get_resource_undo_users(holes)))
        self.assertTrue(is_equal_to_as_set([], cat.uaccess.get_resource_unshare_groups(holes)))
        self.assertTrue(is_equal_to_as_set([], cat.uaccess.get_resource_undo_groups(holes)))

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

        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

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
        self.assertTrue(is_equal_to_as_set([], cat.uaccess.get_resource_unshare_users(holes)))
        self.assertTrue(is_equal_to_as_set([], cat.uaccess.get_resource_undo_users(holes)))
        self.assertTrue(is_equal_to_as_set([], cat.uaccess.get_resource_unshare_groups(holes)))
        self.assertTrue(is_equal_to_as_set([], cat.uaccess.get_resource_undo_groups(holes)))

        self.assertEqual(holes.raccess.owners.count(), 1)
        self.assertEqual(holes.raccess.view_users.count(), 1)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # share holes with dog as owner
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.OWNER)

        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))

        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.edit_users))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.edit_groups))

        self.assertTrue(is_equal_to_as_set([cat, dog], cat.uaccess.get_resource_unshare_users(holes)))
        # the answer to the following should be dog, but cat is self-shared with the resource. Fixed.
        self.assertTrue(is_equal_to_as_set([dog], cat.uaccess.get_resource_undo_users(holes)))
        self.assertTrue(is_equal_to_as_set([], cat.uaccess.get_resource_unshare_groups(holes)))
        self.assertTrue(is_equal_to_as_set([], cat.uaccess.get_resource_undo_groups(holes)))

        self.assertEqual(holes.raccess.owners.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertTrue(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(dog.uaccess.can_change_resource_flags(holes))
        self.assertTrue(dog.uaccess.can_delete_resource(holes))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # test for idempotence
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.OWNER)

        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))

        self.assertEqual(holes.raccess.owners.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertTrue(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(dog.uaccess.can_change_resource_flags(holes))
        self.assertTrue(dog.uaccess.can_delete_resource(holes))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # recheck metadata state: should not have changed
        self.assertFalse(holes.raccess.public)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.immutable)
        self.assertTrue(holes.raccess.shareable)

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

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        self.assertFalse(cat.uaccess.can_undo_share_resource_with_user(holes, dog))
        self.assertFalse(cat.uaccess.can_unshare_resource_with_user(holes, dog))
        self.assertTrue(is_equal_to_as_set([], cat.uaccess.get_resource_undo_users(holes)))
        self.assertTrue(is_equal_to_as_set([], cat.uaccess.get_resource_unshare_users(holes)))

        # share with dog at rw privilege
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(cat.uaccess.can_undo_share_resource_with_user(holes, dog))
        self.assertTrue(cat.uaccess.can_unshare_resource_with_user(holes, dog))
        self.assertTrue(is_equal_to_as_set([dog], cat.uaccess.get_resource_undo_users(holes)))
        self.assertTrue(is_equal_to_as_set([dog], cat.uaccess.get_resource_unshare_users(holes)))

        # initial state
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))

        self.assertEqual(holes.raccess.owners.count(), 1)
        self.assertEqual(holes.raccess.view_users.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # test for idempotence of sharing
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.CHANGE)

        # check for unchanged configuration
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))

        self.assertEqual(holes.raccess.owners.count(), 1)
        self.assertEqual(holes.raccess.view_users.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # recheck metadata state
        self.assertFalse(holes.raccess.public)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.immutable)
        self.assertTrue(holes.raccess.shareable)

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

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # share with view privilege
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.VIEW)

        # shared state
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))

        self.assertEqual(holes.raccess.owners.count(), 1)
        self.assertEqual(holes.raccess.view_users.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # check for idempotence
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.VIEW)

        # same state
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))

        self.assertEqual(holes.raccess.owners.count(), 1)
        self.assertEqual(holes.raccess.view_users.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

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
        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # share as owner
        self.cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.OWNER)

        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))

        self.assertEqual(holes.raccess.owners.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertTrue(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))
        # composite django state
        self.assertTrue(dog.uaccess.can_change_resource_flags(holes))
        self.assertTrue(dog.uaccess.can_delete_resource(holes))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # metadata state
        self.assertFalse(holes.raccess.public)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.immutable)
        self.assertTrue(holes.raccess.shareable)

        # downgrade from OWNER to CHANGE
        self.cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.CHANGE)

        # check for correctness
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))

        self.assertEqual(holes.raccess.owners.count(), 1)
        self.assertEqual(holes.raccess.view_users.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # downgrade from CHANGE to VIEW
        self.cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.VIEW)
        # initial state
        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))
        self.assertTrue(is_equal_to_as_set([], holes.raccess.view_groups))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))

        self.assertEqual(holes.raccess.owners.count(), 1)
        self.assertEqual(holes.raccess.view_users.count(), 2)
        self.assertEqual(holes.raccess.view_users.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # downgrade to no privilege
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
        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # set edit privilege for mouse on holes
        self.cat.uaccess.share_resource_with_user(holes, mouse, PrivilegeCodes.CHANGE)
        self.assertEqual(self.holes.raccess.get_effective_privilege(self.mouse), PrivilegeCodes.CHANGE)

        # set edit privilege for dog on holes
        self.cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.CHANGE)
        self.assertEqual(self.holes.raccess.get_effective_privilege(self.dog), PrivilegeCodes.CHANGE)

        # non owner (mouse) should not be able to downgrade privilege of dog from edit/change
        # (originally granted by cat) to view
        with self.assertRaises(PermissionDenied): 
            self.mouse.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.VIEW)

        # non owner (mouse) should be able to downgrade privilege of a user (dog) originally granted by the same
        # non owner (mouse)
        self.cat.uaccess.unshare_resource_with_user(holes, dog)
        self.assertEqual(self.holes.raccess.get_effective_privilege(self.dog), PrivilegeCodes.NONE)
        self.mouse.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.CHANGE)
        self.assertEqual(self.holes.raccess.get_effective_privilege(self.dog), PrivilegeCodes.CHANGE)
        self.mouse.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.VIEW)
        self.assertEqual(self.holes.raccess.get_effective_privilege(self.dog), PrivilegeCodes.VIEW)

        # django admin should be able to downgrade privilege
        self.cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.OWNER)
        self.assertTrue(dog.uaccess.can_change_resource_flags(holes))
        self.assertTrue(dog.uaccess.owns_resource(holes))

        self.admin.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.CHANGE)
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.owns_resource(holes))

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

        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

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

        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # share meowers with dog as owner
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.OWNER)

        self.assertTrue(is_equal_to_as_set([cat, dog], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 2)
        self.assertEqual(meowers.gaccess.members.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertTrue(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state
        self.assertTrue(dog.uaccess.can_change_group_flags(meowers))
        self.assertTrue(dog.uaccess.can_delete_group(meowers))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # test for idempotence
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.OWNER)

        self.assertTrue(is_equal_to_as_set([cat, dog], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 2)
        self.assertEqual(meowers.gaccess.members.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertTrue(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state
        self.assertTrue(dog.uaccess.can_change_group_flags(meowers))
        self.assertTrue(dog.uaccess.can_delete_group(meowers))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # recheck metadata state: should not have changed
        self.assertTrue(meowers.gaccess.public)
        self.assertTrue(meowers.gaccess.discoverable)
        self.assertTrue(meowers.gaccess.shareable)

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
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # share with dog at rw privilege
        self.assertFalse(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertFalse(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        self.assertTrue(is_equal_to_as_set([], cat.uaccess.get_group_undo_users(meowers)))
        self.assertTrue(is_equal_to_as_set([], cat.uaccess.get_group_unshare_users(meowers)))

        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.CHANGE)

        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        self.assertTrue(is_equal_to_as_set([dog], cat.uaccess.get_group_undo_users(meowers)))
        self.assertTrue(is_equal_to_as_set([dog], cat.uaccess.get_group_unshare_users(meowers)))

        # check other state for this change
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 1)
        self.assertEqual(meowers.gaccess.members.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # test for idempotence of sharing
        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        # check for unchanged configuration
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 1)
        self.assertEqual(meowers.gaccess.members.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # recheck metadata state
        self.assertTrue(meowers.gaccess.public)
        self.assertTrue(meowers.gaccess.discoverable)
        self.assertTrue(meowers.gaccess.shareable)

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
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # share with view privilege
        self.assertFalse(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertFalse(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.VIEW)

        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        # shared state
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 1)
        self.assertEqual(meowers.gaccess.members.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # check for idempotence
        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.VIEW)
        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        # shared state
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 1)
        self.assertEqual(meowers.gaccess.members.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # recheck metadata state
        self.assertTrue(meowers.gaccess.public)
        self.assertTrue(meowers.gaccess.discoverable)
        self.assertTrue(meowers.gaccess.shareable)

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
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # share as owner
        self.assertFalse(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertFalse(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.OWNER)
        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        self.assertTrue(is_equal_to_as_set([cat, dog], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 2)
        self.assertEqual(meowers.gaccess.members.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertTrue(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertTrue(dog.uaccess.can_change_group_flags(meowers))
        self.assertTrue(dog.uaccess.can_delete_group(meowers))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # metadata state
        self.assertTrue(meowers.gaccess.public)
        self.assertTrue(meowers.gaccess.discoverable)
        self.assertTrue(meowers.gaccess.shareable)

        # downgrade from OWNER to CHANGE
        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        # check for correctness
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 1)
        self.assertEqual(meowers.gaccess.members.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # downgrade from CHANGE to VIEW
        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.VIEW)
        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        # initial state
        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], meowers.gaccess.members))
        self.assertTrue(is_equal_to_as_set([], meowers.gaccess.view_resources))

        self.assertEqual(meowers.gaccess.owners.count(), 1)
        self.assertEqual(meowers.gaccess.members.count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # downgrade to no privilege
        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        # TODO: test undo_share
        cat.uaccess.unshare_group_with_user(meowers, dog)
        self.assertFalse(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
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
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # admin too should be able to downgrade (e.g. from OWNER to CHANGE)
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.OWNER)
        self.assertTrue(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group_flags(meowers))

        self.admin.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.CHANGE)
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.owns_group(meowers))

    def test_11_resource_sharing_with_group(self):
        """Group cannot own a resource"""
        meowers = self.meowers
        holes = self.holes
        dog = self.dog
        cat = self.cat

        self.assertTrue(is_equal_to_as_set([cat], meowers.gaccess.owners))

        self.assertEqual(meowers.gaccess.owners.count(), 1)
        # make dog a co-owner
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.OWNER) # make dog a co-owner
        self.assertTrue(is_equal_to_as_set([cat, dog], meowers.gaccess.owners))
        self.assertEqual(meowers.gaccess.owners.count(), 2)
        # repeating the command should be idempotent
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.OWNER) # make dog a co-owner
        self.assertTrue(is_equal_to_as_set([cat, dog], meowers.gaccess.owners))
        self.assertEqual(meowers.gaccess.owners.count(), 2)

        self.assertTrue(is_equal_to_as_set([cat], holes.raccess.owners))

        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(cat.uaccess.can_unshare_resource_with_user(holes, dog))
        self.assertFalse(cat.uaccess.can_undo_share_resource_with_user(holes, dog))
        self.assertTrue(is_equal_to_as_set([], cat.uaccess.get_resource_undo_users(holes)))

        self.assertTrue(is_equal_to_as_set([], cat.uaccess.get_resource_unshare_users(holes)))

        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.OWNER)

        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))
        self.assertTrue(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.owns_group(meowers))

        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_unshare_resource_with_user(holes, dog))
        self.assertTrue(cat.uaccess.can_undo_share_resource_with_user(holes, dog))
        # dog is an owner; owner rule no longer applies!
        self.assertTrue(cat.uaccess.can_unshare_resource_with_user(holes, cat))
        self.assertFalse(cat.uaccess.can_undo_share_resource_with_user(holes, cat))
        self.assertTrue(dog.uaccess.can_unshare_resource_with_user(holes, dog))
        self.assertFalse(dog.uaccess.can_undo_share_resource_with_user(holes, dog))
        self.assertTrue(dog.uaccess.can_unshare_resource_with_user(holes, cat))
        self.assertFalse(dog.uaccess.can_undo_share_resource_with_user(holes, cat))

        # test list access functions for unshare targets
        self.assertTrue(is_equal_to_as_set([dog], cat.uaccess.get_resource_undo_users(holes)))
        self.assertTrue(is_equal_to_as_set([cat, dog], cat.uaccess.get_resource_unshare_users(holes)))

        # the following is correct only because  dog is an owner of holes
        self.assertTrue(is_equal_to_as_set([cat], dog.uaccess.get_resource_undo_users(holes)))
        self.assertTrue(is_equal_to_as_set([cat, dog], dog.uaccess.get_resource_unshare_users(holes)))

        # test idempotence of sharing
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.OWNER)
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_unshare_resource_with_user(holes, dog))
        self.assertTrue(cat.uaccess.can_undo_share_resource_with_user(holes, dog))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.owners))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))
        self.assertTrue(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.owns_group(meowers))

        # owner dog of meowers tries to make holes owned by group meowers
        with self.assertRaises(PermissionDenied) as cm:
            dog.uaccess.share_resource_with_group(holes, meowers, PrivilegeCodes.OWNER)
        self.assertEqual(cm.exception.message, 'Groups cannot own resources')

        # even django admin can't make a group as the owner of a resource
        with self.assertRaises(PermissionDenied) as cm:
            self.admin.uaccess.share_resource_with_group(holes, meowers, PrivilegeCodes.OWNER)
        self.assertEqual(cm.exception.message, 'Groups cannot own resources')

    def test_12_resource_sharing_rw_with_group(self):
        """Resource can be shared as CHANGE with a group"""
        dog = self.dog
        cat = self.cat
        holes = self.holes
        meowers = self.meowers

        # now share something with dog via group meowers
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set([cat, dog], meowers.gaccess.members.all()))

        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(cat.uaccess.can_unshare_resource_with_group(holes, meowers))
        self.assertFalse(cat.uaccess.can_undo_share_resource_with_group(holes, meowers))
        cat.uaccess.share_resource_with_group(holes, meowers, PrivilegeCodes.CHANGE)
        self.assertTrue(cat.uaccess.can_unshare_resource_with_group(holes, meowers))
        self.assertTrue(cat.uaccess.can_undo_share_resource_with_group(holes, meowers))
        self.assertTrue(is_equal_to_as_set([cat, dog], holes.raccess.view_users))

        # simple sharing state
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # turn off group sharing
        cat.uaccess.unshare_resource_with_group(holes, meowers)
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(cat.uaccess.can_unshare_resource_with_group(holes, meowers))
        self.assertFalse(cat.uaccess.can_undo_share_resource_with_group(holes, meowers))

        # simple sharing state
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))


