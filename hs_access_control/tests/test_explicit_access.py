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


class T11ExplicitGet(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(T11ExplicitGet, self).setUp()
        global_reset()

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.A_user = hydroshare.create_account(
            'a_user@gmail.com',
            username='A',
            first_name='A First',
            last_name='A Last',
            superuser=False,
            groups=[]
        )

        self.B_user = hydroshare.create_account(
            'b_user@gmail.com',
            username='B',
            first_name='B First',
            last_name='B Last',
            superuser=False,
            groups=[]
        )

        self.C_user = hydroshare.create_account(
            'c_user@gmail.com',
            username='C',
            first_name='C First',
            last_name='C Last',
            superuser=False,
            groups=[]
        )

        self.r1_resource = hydroshare.create_resource(resource_type='GenericResource',
                                                      owner=self.A_user,
                                                      title='R1',
                                                      metadata=[],)

        self.r2_resource = hydroshare.create_resource(resource_type='GenericResource',
                                                      owner=self.A_user,
                                                      title='R2',
                                                      metadata=[],)

        self.r3_resource = hydroshare.create_resource(resource_type='GenericResource',
                                                      owner=self.A_user,
                                                      title='R3',
                                                      metadata=[],)

    def test_01_resource_unshared_state(self):
        "Resources cannot be accessed by users with no access"
        A_user = self.A_user
        B_user = self.B_user
        C_user = self.C_user
        r1_resource = self.r1_resource
        r2_resource = self.r2_resource
        r3_resource = self.r3_resource

        A_user.uaccess.share_resource_with_user(r1_resource, C_user, PrivilegeCodes.OWNER)
        A_user.uaccess.share_resource_with_user(r2_resource, C_user, PrivilegeCodes.OWNER)
        A_user.uaccess.share_resource_with_user(r3_resource, C_user, PrivilegeCodes.OWNER)

        foo = A_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)
        self.assertTrue(is_equal_to_as_set(foo, [r1_resource, r2_resource, r3_resource]))
        foo = A_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(foo, []))
        foo = A_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(foo, []))
        foo = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)
        self.assertTrue(is_equal_to_as_set(foo, [r1_resource, r2_resource, r3_resource]))
        foo = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(foo, []))
        foo = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(foo, []))

        A_user.uaccess.share_resource_with_user(r1_resource, B_user, PrivilegeCodes.OWNER)
        A_user.uaccess.share_resource_with_user(r2_resource, B_user, PrivilegeCodes.CHANGE)
        A_user.uaccess.share_resource_with_user(r3_resource, B_user, PrivilegeCodes.VIEW)

        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)
        self.assertTrue(is_equal_to_as_set(foo, [r1_resource]))
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(foo, [r2_resource]))
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(foo, [r3_resource]))

        # higher privileges are deleted when lower privileges are granted
        C_user.uaccess.share_resource_with_user(r1_resource, B_user, PrivilegeCodes.VIEW)
        C_user.uaccess.share_resource_with_user(r2_resource, B_user, PrivilegeCodes.VIEW)

        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)
        self.assertTrue(is_equal_to_as_set(foo, []))    # [r1_resource]
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(foo, []))    # [r2_resource]
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(foo, [r1_resource, r2_resource, r3_resource]))

        C_user.uaccess.share_resource_with_user(r1_resource, B_user, PrivilegeCodes.CHANGE)
        C_user.uaccess.share_resource_with_user(r2_resource, B_user, PrivilegeCodes.CHANGE)
        C_user.uaccess.share_resource_with_user(r3_resource, B_user, PrivilegeCodes.CHANGE)

        # higher privilege gets deleted when a lower privilege is granted
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)
        self.assertTrue(is_equal_to_as_set(foo, []))    # [r1_resource]
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(foo, [r1_resource, r2_resource, r3_resource]))
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(foo, []))

        # go from lower privilege to higher
        C_user.uaccess.share_resource_with_user(r1_resource, B_user, PrivilegeCodes.VIEW)
        C_user.uaccess.share_resource_with_user(r2_resource, B_user, PrivilegeCodes.VIEW)
        C_user.uaccess.share_resource_with_user(r3_resource, B_user, PrivilegeCodes.VIEW)

        A_user.uaccess.share_resource_with_user(r1_resource, B_user, PrivilegeCodes.CHANGE)
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(foo, [r1_resource]))
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(foo, [r2_resource, r3_resource]))

        A_user.uaccess.share_resource_with_user(r1_resource, B_user, PrivilegeCodes.OWNER)

        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)
        self.assertTrue(is_equal_to_as_set(foo, [r1_resource]))
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(foo, [r2_resource, r3_resource]))

        # go lower to higher
        C_user.uaccess.share_resource_with_user(r1_resource, B_user, PrivilegeCodes.VIEW)

        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)
        self.assertTrue(is_equal_to_as_set(foo, []))
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(foo, []))
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(foo, [r1_resource, r2_resource, r3_resource]))


