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


class T11PreserveOwnership(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(T11PreserveOwnership, self).setUp()
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
        self.dog.uaccess.share_group_with_user(self.felines, self.cat, PrivilegeCodes.VIEW)  # poetic justice

    def test_01_remove_last_owner_of_group(self):
        """Cannot remove last owner of a group"""
        felines = self.felines
        dog = self.dog
        self.assertTrue(dog.uaccess.owns_group(felines))
        self.assertEqual(felines.gaccess.owners.count(), 1)

        # try to downgrade your own privilege
        with self.assertRaises(PermissionDenied) as cm:
            dog.uaccess.share_group_with_user(felines, dog, PrivilegeCodes.VIEW)
        self.assertEqual(cm.exception.message, 'Cannot remove sole owner of group')

    def test_01_remove_last_owner_of_resource(self):
        """Cannot remove last owner of a resource"""
        scratching = self.scratching
        dog = self.dog
        self.assertTrue(dog.uaccess.owns_resource(scratching))
        self.assertEqual(scratching.raccess.owners.count(), 1)

        # try to downgrade your own privilege
        with self.assertRaises(PermissionDenied) as cm:
            dog.uaccess.share_resource_with_user(scratching, dog, PrivilegeCodes.VIEW)
        self.assertEqual(cm.exception.message, 'Cannot remove sole owner of resource')


