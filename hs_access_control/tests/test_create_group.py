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

class T04CreateGroup(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(T04CreateGroup, self).setUp()
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

    def test_02_create(self):
        """Create a new group"""
        dog = self.dog
        cat = self.cat
        self.assertEqual(dog.uaccess.owned_groups.count(), 0)
        self.assertEqual(dog.uaccess.view_groups.count(), 0)

        # user 'dog' create a new group called 'arfers'
        arfers = dog.uaccess.create_group('arfers')

        self.assertEqual(dog.uaccess.owned_groups.count(), 1)
        self.assertEqual(dog.uaccess.view_groups.count(), 1)

        self.assertEqual(cat.uaccess.owned_groups.count(), 0)
        self.assertEqual(cat.uaccess.view_groups.count(), 0)

        self.assertTrue(is_equal_to_as_set([arfers], dog.uaccess.owned_groups))
        self.assertTrue(is_equal_to_as_set([arfers], dog.uaccess.view_groups))

        # check membership list
        self.assertEqual(arfers.gaccess.members.count(), 1)

        # metadata state
        self.assertTrue(arfers.gaccess.public)
        self.assertTrue(arfers.gaccess.discoverable)
        self.assertTrue(arfers.gaccess.shareable)

        # protection state for owner
        self.assertTrue(dog.uaccess.owns_group(arfers))
        self.assertTrue(dog.uaccess.can_change_group(arfers))
        self.assertTrue(dog.uaccess.can_view_group(arfers))

        # composite django state
        self.assertTrue(dog.uaccess.can_change_group_flags(arfers))
        self.assertTrue(dog.uaccess.can_delete_group(arfers))
        self.assertTrue(dog.uaccess.can_share_group(arfers, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_group(arfers, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(arfers, PrivilegeCodes.VIEW))

        # membership
        self.assertTrue(dog in arfers.gaccess.members)

        # protection state for other user
        self.assertFalse(cat.uaccess.owns_group(arfers))
        self.assertFalse(cat.uaccess.can_change_group(arfers))
        self.assertTrue(cat.uaccess.can_view_group(arfers))

        # composite django state for other user
        self.assertFalse(cat.uaccess.can_change_group_flags(arfers))
        self.assertFalse(cat.uaccess.can_delete_group(arfers))
        self.assertFalse(cat.uaccess.can_share_group(arfers, PrivilegeCodes.OWNER))
        self.assertFalse(cat.uaccess.can_share_group(arfers, PrivilegeCodes.CHANGE))
        self.assertFalse(cat.uaccess.can_share_group(arfers, PrivilegeCodes.VIEW))

        # membership for other user
        self.assertTrue(cat not in arfers.gaccess.members)

        # test django admin's group access permissions - admin has not been given any access over the group by anyone
        # even though admin does not own the group, admin can do anything to a group
        self.assertFalse(self.admin.uaccess.owns_group(arfers))
        self.assertTrue(self.admin.uaccess.can_change_group(arfers))
        self.assertTrue(self.admin.uaccess.can_change_group_flags(arfers))
        self.assertTrue(self.admin.uaccess.can_view_group(arfers))
        self.assertTrue(self.admin.uaccess.can_share_group(arfers, PrivilegeCodes.OWNER))
        self.assertTrue(self.admin.uaccess.can_share_group(arfers, PrivilegeCodes.CHANGE))
        self.assertTrue(self.admin.uaccess.can_share_group(arfers, PrivilegeCodes.VIEW))
        self.assertTrue(self.admin.uaccess.can_delete_group(arfers))
        self.admin.uaccess.delete_group(arfers)

    def test_04_retract_group(self):
        """Owner can retract a group"""
        dog = self.dog
        arfers = dog.uaccess.create_group('arfers')

        # check that it got created
        self.assertEqual(dog.uaccess.owned_groups.count(), 1)
        self.assertEqual(dog.uaccess.view_groups.count(), 1)

        # # THE FOLLOWING WORKS
        # # but is a synonym for UserGroupPrivilege.objects.filter(privilege=PrivilegeCodes.OWNER)
        # junk = GroupAccess.members.through.objects.filter(privilege=PrivilegeCodes.OWNER)
        # # returns UserGroupPrivilege objects.
        # pprint(junk)
        # print('Contents of junk:')
        # for g in junk:
        #     print(' ' + g.group.group.name)
        # # THIS DOESN'T WORK: "nested queries not permitted"
        # junk = GroupAccess.objects.filter(through__privilege=PrivilegeCodes.OWNER)

        dog.uaccess.delete_group(arfers)

        # check that it got destroyed according to statistics
        self.assertEqual(dog.uaccess.owned_groups.count(), 0)
        self.assertEqual(dog.uaccess.view_groups.count(), 0)


class T15CreateGroup(MockIRODSTestCaseMixin, TestCase):
    "Test creatng a group: flags and isolation"
    def setUp(self):
        super(T15CreateGroup, self).setUp()
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

        self.meowers = self.cat.uaccess.create_group('meowers')

    def test_01_default_group_ownership(self):
        "Defaults for group ownership are correct"
        cat = self.cat
        meowers = self.meowers
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))
        self.assertTrue(meowers.gaccess.public)
        self.assertTrue(meowers.gaccess.discoverable)
        self.assertTrue(meowers.gaccess.shareable)

    def test_02_default_group_isolation(self):
        "Users with no contact with the group have appropriate permissions"
        # start up as an unprivileged user with no access to the group
        dog = self.dog
        meowers = self.meowers
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        self.assertTrue(meowers.gaccess.public)
        self.assertTrue(meowers.gaccess.discoverable)
        self.assertTrue(meowers.gaccess.shareable)

    def test_03_change_group_not_public(self):
        "Can make a group not public"
        dog = self.dog
        meowers = self.meowers
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # now set it to non-public
        meowers.gaccess.public = False
        meowers.gaccess.save()

        # check flags
        self.assertFalse(meowers.gaccess.public)
        self.assertTrue(meowers.gaccess.discoverable)
        self.assertTrue(meowers.gaccess.shareable)

        # test that an unprivileged user cannot read the group now
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertFalse(dog.uaccess.can_view_group(meowers))

        # django admin can still have access to the private group
        self.assertFalse(self.admin.uaccess.owns_group(meowers))
        self.assertTrue(self.admin.uaccess.can_change_group(meowers))
        self.assertTrue(self.admin.uaccess.can_view_group(meowers))


    def test_03_change_group_not_discoverable(self):
        "Can make a group not discoverable"
        dog = self.dog
        meowers = self.meowers
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # now set it to non-discoverable
        meowers.gaccess.discoverable = False
        meowers.gaccess.save()

        # check flags
        self.assertTrue(meowers.gaccess.public)
        self.assertFalse(meowers.gaccess.discoverable)
        self.assertTrue(meowers.gaccess.shareable)

        # public -> discoverable; test that an unprivileged user can read the group now
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertFalse(dog.uaccess.owns_group(meowers))

        # django admin has access to not discoverable group
        self.assertTrue(self.admin.uaccess.can_view_group(meowers))
        self.assertTrue(self.admin.uaccess.can_change_group(meowers))
        self.assertFalse(self.admin.uaccess.owns_group(meowers))


