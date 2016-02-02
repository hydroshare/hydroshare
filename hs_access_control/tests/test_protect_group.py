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


class T06ProtectGroup(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(T06ProtectGroup, self).setUp()
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

    def test_01_create(self):
        "Initial group state is correct"

        cat = self.cat
        polyamory = cat.uaccess.create_group('polyamory')

        # flag state
        self.assertTrue(polyamory.gaccess.public)
        self.assertTrue(polyamory.gaccess.shareable)
        self.assertTrue(polyamory.gaccess.discoverable)

        # privilege
        self.assertTrue(cat.uaccess.owns_group(polyamory))
        self.assertTrue(cat.uaccess.can_change_group(polyamory))
        self.assertTrue(cat.uaccess.can_view_group(polyamory))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(polyamory))
        self.assertTrue(cat.uaccess.can_delete_group(polyamory))
        self.assertTrue(cat.uaccess.can_share_group(polyamory, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(polyamory, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(polyamory, PrivilegeCodes.VIEW))

        # membership
        self.assertTrue(cat in polyamory.gaccess.members)

        # ensure that this group was created and current user is a member
        self.assertTrue(is_equal_to_as_set([polyamory], cat.uaccess.view_groups))

    def test_02_isolate(self):
        "Groups cannot be changed by non-members"
        cat = self.cat
        dog = self.dog
        polyamory = cat.uaccess.create_group('polyamory')

        # dog should not have access to the group privilege
        self.assertFalse(dog.uaccess.owns_group(polyamory))
        self.assertFalse(dog.uaccess.can_change_group(polyamory))
        self.assertTrue(dog.uaccess.can_view_group(polyamory))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(polyamory))
        self.assertFalse(dog.uaccess.can_delete_group(polyamory))
        self.assertFalse(dog.uaccess.can_share_group(polyamory, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_group(polyamory, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_group(polyamory, PrivilegeCodes.VIEW))

        # dog's groups should be unchanged
        self.assertTrue(is_equal_to_as_set([], dog.uaccess.view_groups))

        # dog should not be able to modify group members
        with self.assertRaises(PermissionDenied) as cm:
            dog.uaccess.share_group_with_user(polyamory, dog, PrivilegeCodes.CHANGE)
        self.assertEqual(cm.exception.message, 'User has insufficient privilege over group')

    def test_03_share_rw(self):
        "Sharing with PrivilegeCodes.CHANGE privilege allows group changes "
        cat = self.cat
        dog = self.dog
        bat = self.bat
        polyamory = cat.uaccess.create_group('polyamory')
        self.assertTrue(cat.uaccess.can_share_group(polyamory, PrivilegeCodes.CHANGE))
        cat.uaccess.share_group_with_user(polyamory, dog, PrivilegeCodes.CHANGE)

        # now check the state of 'dog'
        # dog should not have access to the group privilege
        self.assertFalse(dog.uaccess.owns_group(polyamory))
        self.assertTrue(dog.uaccess.can_change_group(polyamory))
        self.assertTrue(dog.uaccess.can_view_group(polyamory))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(polyamory))
        self.assertFalse(dog.uaccess.can_delete_group(polyamory))
        self.assertFalse(dog.uaccess.can_share_group(polyamory, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_group(polyamory, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(polyamory, PrivilegeCodes.VIEW))

        # try to add someone to group
        self.assertTrue(dog.uaccess.can_share_group(polyamory, PrivilegeCodes.CHANGE))
        dog.uaccess.share_group_with_user(polyamory, bat, PrivilegeCodes.CHANGE)

        # bat should not have access to dog's privileges
        self.assertFalse(bat.uaccess.owns_group(polyamory))
        self.assertTrue(bat.uaccess.can_change_group(polyamory))
        self.assertTrue(bat.uaccess.can_view_group(polyamory))

        # composite django state
        self.assertFalse(bat.uaccess.can_change_group_flags(polyamory))
        self.assertFalse(bat.uaccess.can_delete_group(polyamory))
        self.assertFalse(bat.uaccess.can_share_group(polyamory, PrivilegeCodes.OWNER))
        self.assertTrue(bat.uaccess.can_share_group(polyamory, PrivilegeCodes.CHANGE))
        self.assertTrue(bat.uaccess.can_share_group(polyamory, PrivilegeCodes.VIEW))

    def test_04_share_ro(self):
        "Sharing with PrivilegeCodes.VIEW privilege disallows group changes "
        cat = self.cat
        dog = self.dog
        bat = self.bat
        polyamory = cat.uaccess.create_group('polyamory')
        cat.uaccess.share_group_with_user(polyamory, dog, PrivilegeCodes.VIEW)

        # now check the state of 'dog'
        self.assertFalse(dog.uaccess.owns_group(polyamory))
        self.assertFalse(dog.uaccess.can_change_group(polyamory))
        self.assertTrue(dog.uaccess.can_view_group(polyamory))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(polyamory))
        self.assertFalse(dog.uaccess.can_delete_group(polyamory))
        self.assertFalse(dog.uaccess.can_share_group(polyamory, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_group(polyamory, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(polyamory, PrivilegeCodes.VIEW))

        # try to add someone to group
        dog.uaccess.share_group_with_user(polyamory, bat, PrivilegeCodes.VIEW)

        # now check the state of 'bat': should have dog's privileges
        self.assertFalse(bat.uaccess.owns_group(polyamory))
        self.assertFalse(bat.uaccess.can_change_group(polyamory))
        self.assertTrue(bat.uaccess.can_view_group(polyamory))

        # composite django state
        self.assertFalse(bat.uaccess.can_change_group_flags(polyamory))
        self.assertFalse(bat.uaccess.can_delete_group(polyamory))
        self.assertFalse(bat.uaccess.can_share_group(polyamory, PrivilegeCodes.OWNER))
        self.assertFalse(bat.uaccess.can_share_group(polyamory, PrivilegeCodes.CHANGE))
        self.assertTrue(bat.uaccess.can_share_group(polyamory, PrivilegeCodes.VIEW))


