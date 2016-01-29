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


class T12UserActive(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(T12UserActive, self).setUp()

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

        self.scratching = hydroshare.create_resource(resource_type='GenericResource',
                                                     owner=self.cat,
                                                     title='all about sofas as scrathing posts',
                                                     metadata=[],)

        self.felines = self.cat.uaccess.create_group('felines')  # dog owns felines group


    def test_00_exceptions(self):
        "All user routines raise PermissionDenied if user is inactive"
        scratching = self.scratching
        felines = self.felines
        dog = self.dog
        cat = self.cat

        # turn off active
        cat.is_active=False 
        cat.save()

        # all user routines should raise exceptions 
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.create_group('foo')
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.delete_group(felines)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.view_groups
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.owned_groups
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.owns_group(felines)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.can_change_group(felines)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.can_view_group(felines)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.can_view_group_metadata(felines)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.can_change_group_flags(felines)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.can_delete_group(felines)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.can_share_group(felines, PrivilegeCodes.VIEW)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.share_group_with_user(felines, dog, PrivilegeCodes.VIEW)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.unshare_group_with_user(felines, dog)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.can_unshare_group_with_user(felines, dog)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.undo_share_group_with_user(felines, dog)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.can_undo_share_group_with_user(felines, dog)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.get_group_undo_users(felines)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.get_group_unshare_users(felines)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.view_resources
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.owned_resources
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.edit_resources
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.owns_resource(scratching)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.can_change_resource(scratching)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.can_change_resource_flags(scratching)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.can_view_resource(scratching)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.can_delete_resource(scratching)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.can_share_resource(scratching, PrivilegeCodes.VIEW)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.can_share_resource_with_group(scratching, felines, PrivilegeCodes.VIEW)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.undo_share_resource_with_group(scratching, felines)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.can_undo_share_resource_with_group(scratching, felines)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.share_resource_with_user(scratching, dog, PrivilegeCodes.VIEW)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.unshare_resource_with_user(scratching, dog)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.can_unshare_resource_with_user(scratching, dog)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.undo_share_resource_with_user(scratching, dog)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.can_undo_share_resource_with_user(scratching, dog)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.share_resource_with_group(scratching, felines, PrivilegeCodes.VIEW)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.unshare_resource_with_group(scratching, felines)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.can_unshare_resource_with_group(scratching, felines)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.get_resource_undo_users(scratching)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.get_resource_unshare_users(scratching)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.get_resource_undo_groups(scratching)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.get_resource_unshare_groups(scratching)

    def test_01_reporting(self):
        "User records disappear when user is inactive"
        scratching = self.scratching
        felines = self.felines
        dog = self.dog
        cat = self.cat

        cat.uaccess.share_resource_with_user(scratching, dog, PrivilegeCodes.OWNER) 
        cat.uaccess.share_group_with_user(felines, dog, PrivilegeCodes.OWNER) 

        self.assertTrue(is_equal_to_as_set(cat.uaccess.get_group_unshare_users(felines), [cat, dog]))
        self.assertTrue(is_equal_to_as_set(cat.uaccess.get_group_undo_users(felines), [dog]))
        self.assertTrue(is_equal_to_as_set(cat.uaccess.get_resource_undo_users(scratching), [dog]))
        self.assertTrue(is_equal_to_as_set(cat.uaccess.get_resource_unshare_users(scratching), [cat, dog]))

        self.assertTrue(is_equal_to_as_set(felines.gaccess.members, [cat, dog]))
        self.assertTrue(is_equal_to_as_set(felines.gaccess.owners, [cat, dog]))

        self.assertTrue(is_equal_to_as_set(scratching.raccess.view_users, [cat, dog]))
        self.assertTrue(is_equal_to_as_set(scratching.raccess.edit_users, [cat, dog]))
        self.assertTrue(is_equal_to_as_set(scratching.raccess.owners, [cat, dog]))

        dog.is_active=False
        dog.save()

        self.assertTrue(is_equal_to_as_set(cat.uaccess.get_group_unshare_users(felines), []))
        self.assertTrue(is_equal_to_as_set(cat.uaccess.get_group_undo_users(felines), []))
        self.assertTrue(is_equal_to_as_set(cat.uaccess.get_resource_undo_users(scratching), []))
        self.assertTrue(is_equal_to_as_set(cat.uaccess.get_resource_unshare_users(scratching), []))

        self.assertTrue(is_equal_to_as_set(felines.gaccess.members, [cat]))
        self.assertTrue(is_equal_to_as_set(felines.gaccess.owners, [cat]))

        self.assertTrue(is_equal_to_as_set(scratching.raccess.view_users, [cat]))
        self.assertTrue(is_equal_to_as_set(scratching.raccess.edit_users, [cat]))
        self.assertTrue(is_equal_to_as_set(scratching.raccess.owners, [cat]))


