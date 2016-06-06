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


class T10GroupFlags(MockIRODSTestCaseMixin, TestCase):
    "Test for effects of group flags" 

    def setUp(self):
        super(T10GroupFlags, self).setUp()
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

        self.bat = hydroshare.create_account(
            'bat@gmail.com',
            username='bat',
            first_name='not a man',
            last_name='last_name_bat',
            superuser=False,
            groups=[]
        )

        self.nobody = hydroshare.create_account(
            'nobody@gmail.com',
            username='nobody',
            first_name='no one in particular',
            last_name='last_name_nobody',
            superuser=False,
            groups=[]
        )

        self.scratching = hydroshare.create_resource(resource_type='GenericResource',
                                                     owner=self.dog,
                                                     title='all about sofas as scrathing posts',
                                                     metadata=[],)

        # dog owns felines group
        self.felines = self.dog.uaccess.create_group(title='felines', description="Wre are the felines")
        self.dog.uaccess.share_group_with_user(self.felines, self.cat, PrivilegeCodes.VIEW)
        # poetic justice: cat can VIEW what dogs think about scratching sofas

    def test_00_defaults(self):
        """Defaults for created groups are correct"""
        felines = self.felines
        cat = self.cat
        self.assertFalse(cat.uaccess.owns_group(felines))
        self.assertFalse(cat.uaccess.can_change_group(felines))
        self.assertTrue(cat.uaccess.can_view_group(felines))

    def test_05_get_discoverable(self):
        """Getting discoverable groups works properly"""
        felines = self.felines

        self.assertTrue(felines in hydroshare.get_discoverable_groups())

    def test_06_make_not_discoverable(self):
        """Can make a group undiscoverable"""
        felines = self.felines
        dog = self.dog

        felines.gaccess.discoverable = False
        felines.gaccess.save()

        self.assertTrue(dog.uaccess.owns_group(felines))
        self.assertTrue(dog.uaccess.can_change_group(felines))
        self.assertTrue(dog.uaccess.can_view_group(felines))
        self.assertTrue(felines.gaccess.public)
        self.assertFalse(felines.gaccess.discoverable)
        self.assertTrue(felines.gaccess.shareable)

        self.assertTrue(felines in hydroshare.get_discoverable_groups())
        self.assertTrue(felines in hydroshare.get_public_groups())  # still public!

        # undo prior change
        felines.gaccess.discoverable = True
        felines.gaccess.save()

        self.assertTrue(dog.uaccess.owns_group(felines))
        self.assertTrue(dog.uaccess.can_change_group(felines))
        self.assertTrue(dog.uaccess.can_view_group(felines))
        self.assertTrue(felines.gaccess.public)
        self.assertTrue(felines.gaccess.discoverable)
        self.assertTrue(felines.gaccess.shareable)

        self.assertTrue(felines in hydroshare.get_discoverable_groups())  # still discoverable
        self.assertTrue(felines in hydroshare.get_public_groups())  # still public!

    def test_07_make_not_public(self):
        """Can make a group not public"""
        felines = self.felines
        dog = self.dog

        felines.gaccess.public = False
        felines.gaccess.save()

        self.assertTrue(dog.uaccess.owns_group(felines))
        self.assertTrue(dog.uaccess.can_change_group(felines))
        self.assertTrue(dog.uaccess.can_view_group(felines))
        self.assertFalse(felines.gaccess.public)
        self.assertTrue(felines.gaccess.discoverable)
        self.assertTrue(felines.gaccess.shareable)

        self.assertTrue(felines in hydroshare.get_discoverable_groups())  # still discoverable
        self.assertTrue(felines not in hydroshare.get_public_groups())  # not still public!

        felines.gaccess.public = True
        felines.gaccess.save()

        self.assertTrue(dog.uaccess.owns_group(felines))
        self.assertTrue(dog.uaccess.can_change_group(felines))
        self.assertTrue(dog.uaccess.can_view_group(felines))
        self.assertTrue(felines.gaccess.public)
        self.assertTrue(felines.gaccess.discoverable)
        self.assertTrue(felines.gaccess.shareable)

        self.assertTrue(felines in hydroshare.get_discoverable_groups())  # still public!
        self.assertTrue(felines in hydroshare.get_public_groups())  # still public!

    def test_07_make_private(self):
        """Making a group not public and not discoverable hides it"""
        felines = self.felines
        dog = self.dog

        felines.gaccess.public = False
        felines.gaccess.discoverable = False
        felines.gaccess.save()

        self.assertTrue(dog.uaccess.owns_group(felines))
        self.assertTrue(dog.uaccess.can_change_group(felines))
        self.assertTrue(dog.uaccess.can_view_group(felines))
        self.assertFalse(felines.gaccess.public)
        self.assertFalse(felines.gaccess.discoverable)
        self.assertTrue(felines.gaccess.shareable)

        self.assertTrue(felines not in hydroshare.get_discoverable_groups())
        self.assertTrue(felines not in hydroshare.get_public_groups())

        # django admin has access to private and not discoverable group
        self.assertFalse(self.admin.uaccess.owns_group(felines))
        self.assertTrue(self.admin.uaccess.can_change_group(felines))
        self.assertTrue(self.admin.uaccess.can_view_group(felines))

        # can an unrelated user do anything with the group?
        nobody = self.nobody
        self.assertEqual(hydroshare.get_discoverable_groups().count(), 0)
        self.assertEqual(hydroshare.get_public_groups().count(), 0)

        self.assertFalse(nobody.uaccess.owns_group(felines))
        self.assertFalse(nobody.uaccess.can_change_group(felines))
        self.assertFalse(nobody.uaccess.can_view_group(felines))
        self.assertFalse(felines.gaccess.public)
        self.assertFalse(felines.gaccess.discoverable)
        self.assertTrue(felines.gaccess.shareable)

        felines.gaccess.public = True
        felines.gaccess.discoverable = True
        felines.gaccess.save()

        self.assertTrue(dog.uaccess.owns_group(felines))
        self.assertTrue(dog.uaccess.can_change_group(felines))
        self.assertTrue(dog.uaccess.can_view_group(felines))
        self.assertTrue(felines.gaccess.public)
        self.assertTrue(felines.gaccess.discoverable)
        self.assertTrue(felines.gaccess.shareable)

        self.assertTrue(felines in hydroshare.get_discoverable_groups())
        self.assertTrue(felines in hydroshare.get_public_groups())

    def test_08_make_not_shareable(self):
        """Can remove sharing privilege from a group"""
        felines = self.felines
        dog = self.dog

        # check shareable flag
        felines.gaccess.shareable = False
        felines.gaccess.save()

        self.assertTrue(dog.uaccess.owns_group(felines))
        self.assertTrue(dog.uaccess.can_change_group(felines))
        self.assertTrue(dog.uaccess.can_view_group(felines))
        self.assertTrue(felines.gaccess.public)
        self.assertTrue(felines.gaccess.discoverable)
        self.assertFalse(felines.gaccess.shareable)

        # django admin still has full access to the unshared group
        self.assertFalse(self.admin.uaccess.owns_group(felines))
        self.assertTrue(self.admin.uaccess.can_change_group(felines))
        self.assertTrue(self.admin.uaccess.can_view_group(felines))

        felines.gaccess.shareable = True
        felines.gaccess.save()

        self.assertTrue(dog.uaccess.owns_group(felines))
        self.assertTrue(dog.uaccess.can_change_group(felines))
        self.assertTrue(dog.uaccess.can_view_group(felines))
        self.assertTrue(felines.gaccess.public)
        self.assertTrue(felines.gaccess.discoverable)
        self.assertTrue(felines.gaccess.shareable)

    def test_09_make_not_active(self):
        felines = self.felines

        # dog is group owner
        dog = self.dog
        # cat is a group member
        cat = self.cat

        # make group inactive
        self.assertTrue(felines.gaccess.active)
        felines.gaccess.active = False
        felines.gaccess.save()
        self.assertFalse(felines.gaccess.active)

        self.assertTrue(dog.uaccess.owns_group(felines))

        # even the group owner (dog) can't edit inactive group
        with self.assertRaises(PermissionDenied):
            dog.uaccess.can_change_group(felines)

        # group owner should be able to view inactive group
        self.assertTrue(dog.uaccess.can_view_group(felines))

        # group owner shouldn't be able to view metadata for an inactive group
        with self.assertRaises(PermissionDenied):
            dog.uaccess.can_view_group_metadata(felines)

        # group member (cat) should not be able to view inactive group
        with self.assertRaises(PermissionDenied):
            cat.uaccess.can_view_group(felines)

        # group owner (dog) should be able to change  group flags for inactive group
        self.assertTrue(dog.uaccess.can_change_group_flags(felines))

        # group owner (dog) should be able to delete inactive group
        self.assertTrue(dog.uaccess.can_delete_group(felines))

        # even the group owner (dog) can't share/unshare inactive group
        with self.assertRaises(PermissionDenied):
            dog.uaccess.can_share_group(felines, PrivilegeCodes.VIEW)

        with self.assertRaises(PermissionDenied):
            dog.uaccess.share_group_with_user(felines, self.bat, PrivilegeCodes.VIEW)

        with self.assertRaises(PermissionDenied):
            dog.uaccess.can_share_resource_with_group(self.scratching, felines, PrivilegeCodes.VIEW)

        with self.assertRaises(PermissionDenied):
            dog.uaccess.share_resource_with_group(self.scratching, felines, PrivilegeCodes.VIEW)

        with self.assertRaises(PermissionDenied):
            dog.uaccess.can_unshare_group_with_user(felines, self.cat)

        with self.assertRaises(PermissionDenied):
            dog.uaccess.unshare_group_with_user(felines, self.cat)

        with self.assertRaises(PermissionDenied):
            dog.uaccess.can_unshare_resource_with_group(self.scratching, felines)

        with self.assertRaises(PermissionDenied):
            dog.uaccess.unshare_resource_with_group(self.scratching, felines)

        # group owner (dog) can invite a user to join a group
        with self.assertRaises(PermissionDenied):
            dog.uaccess.create_group_membership_request(felines, self.bat)

        # user can't make a request to join a group
        with self.assertRaises(PermissionDenied):
            self.bat.uaccess.create_group_membership_request(felines)

        # group owner should have 1 owned group
        self.assertEqual(len(dog.uaccess.owned_groups), 1)

        # group owner should not have any edit groups
        self.assertEqual(len(dog.uaccess.edit_groups), 0)

        # group owner should not have any view groups
        self.assertEqual(len(dog.uaccess.view_groups), 0)

        # make the group active for testing resource related groups
        felines.gaccess.active = True
        felines.gaccess.save()
        self.assertTrue(felines.gaccess.active)

        # share the resource with the group
        dog.uaccess.share_resource_with_group(self.scratching, felines, PrivilegeCodes.VIEW)
        # for the active group the resource should have 1 group with view permission
        self.assertEqual(len(self.scratching.raccess.view_groups), 1)
        # for the active group the resource should not have any group with edit permission
        self.assertEqual(len(self.scratching.raccess.edit_groups), 0)

        self.assertEqual(len(felines.gaccess.members), 2)
        # for the active group the resource should have 2 user with view permission
        self.assertEqual(len(self.scratching.raccess.view_users), 2)
        # for the active group the resource should have one user with edit permission
        self.assertEqual(len(self.scratching.raccess.edit_users), 1)

        dog.uaccess.share_resource_with_group(self.scratching, felines, PrivilegeCodes.CHANGE)
        # for the active group the resource should have 1 group with view permission
        self.assertEqual(len(self.scratching.raccess.view_groups), 1)
        # for the active group the resource should have 1 group with edit permission
        self.assertEqual(len(self.scratching.raccess.edit_groups), 1)

        # for the active group the resource should have 2 user with view permission
        self.assertEqual(len(self.scratching.raccess.view_users), 2)
        # for the active group the resource should have one user with edit permission
        self.assertEqual(len(self.scratching.raccess.edit_users), 2)

        # make the group inactive
        felines.gaccess.active = False
        felines.gaccess.save()
        self.assertFalse(felines.gaccess.active)
        # for the inactive group the resource should have no group with view permission
        self.assertEqual(len(self.scratching.raccess.view_groups), 0)
        # for the inactive group the resource should have no group with edit permission
        self.assertEqual(len(self.scratching.raccess.edit_groups), 0)

        # for the inactive group the resource should have no user with view permission
        self.assertEqual(len(self.scratching.raccess.view_users), 0)
        # for the inactive group the resource should have no user with edit permission
        self.assertEqual(len(self.scratching.raccess.edit_users), 0)

        # TODO: Test get_effective_privilege() for inactive group status









