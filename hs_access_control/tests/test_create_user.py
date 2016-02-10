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


class T01CreateUser(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(T01CreateUser, self).setUp()
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

        self.dpg = hydroshare.create_account(
            'dog@gmail.com',
            username='dog',
            first_name='a little',
            last_name='arfer',
            superuser=False,
            groups=[]
        )

    def test_01_create_state(self):
        """User state is correct after creation"""
        # check that privileged user was created correctly
        self.assertEqual(self.admin.uaccess.user.username, 'admin')
        self.assertEqual(self.admin.uaccess.user.first_name, 'administrator')
        self.assertTrue(self.admin.is_active)

        # start as privileged user
        assertUserResourceState(self, self.admin, [], [], [])

        # check that unprivileged user was created correctly
        self.assertEqual(self.cat.uaccess.user.username, 'cat')
        self.assertEqual(self.cat.uaccess.user.first_name, 'not a dog')
        self.assertTrue(self.cat.is_active)

        # check that user cat owns and holds nothing
        assertUserResourceState(self, self.cat, [], [], [])
        assertUserGroupState(self, self.cat, [], [], [])
