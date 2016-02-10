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

        self.felines = self.dog.uaccess.create_group('felines')  # dog owns felines group
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


