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

class BasicFunction(MockIRODSTestCaseMixin, TestCase):
    """ test basic functions """

    def setUp(self):
        super(BasicFunction, self).setUp()
        global_reset()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        self.alva = hydroshare.create_account(
            'alva@gmail.com',
            username='alva',
            first_name='alva',
            last_name='couch',
            superuser=False,
            groups=[]
        )

        self.george = hydroshare.create_account(
            'george@gmail.com',
            username='george',
            first_name='george',
            last_name='miller',
            superuser=False,
            groups=[]
        )

        self.john = hydroshare.create_account(
            'john@gmail.com',
            username='john',
            first_name='john',
            last_name='miller',
            superuser=False,
            groups=[]
        )

        self.admin = hydroshare.create_account(
            'admin@gmail.com',
            username='admin',
            first_name='first_name_admin',
            last_name='last_name_admin',
            superuser=True,
            groups=[]
        )

        # george creates a resource 'bikes'
        self.bikes = hydroshare.create_resource(resource_type='GenericResource',
                                                owner=self.george,
                                                title='Bikes',
                                                metadata=[],)

        # george creates a group 'bikers'
        self.bikers = self.george.uaccess.create_group('Bikers')

        # george creates a group 'harpers'
        self.harpers = self.george.uaccess.create_group('Harpers')

    def test_matrix_testing(self):
        """ Test that matrix testing routines function as believed """
        george = self.george
        alva = self.alva
        john = self.john
        bikes = self.bikes
        bikers = self.bikers
        harpers = self.harpers

        assertResourceUserState(self, bikes, [george], [], [])
        assertUserResourceState(self, george, [bikes], [], [])
        assertUserResourceState(self, alva, [], [], [])
        assertUserResourceState(self, john, [], [], [])
        assertUserGroupState(self, george, [harpers, bikers], [], [])
        assertUserGroupState(self, alva, [], [], [])
        assertUserGroupState(self, john, [], [], [])

        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.CHANGE)

        assertResourceUserState(self, bikes, [george], [alva], [])
        assertUserResourceState(self, george, [bikes], [], [])
        assertUserResourceState(self, alva, [], [bikes], [])
        assertUserResourceState(self, john, [], [], [])

        george.uaccess.share_resource_with_user(bikes, john, PrivilegeCodes.VIEW)

        assertResourceUserState(self, bikes, [george], [alva], [john])
        assertUserResourceState(self, george, [bikes], [], [])
        assertUserResourceState(self, alva, [], [bikes], [])
        assertUserResourceState(self, john, [], [], [bikes])

        bikes.raccess.immutable = True
        bikes.raccess.save()

        assertResourceUserState(self, bikes, [george], [], [alva, john])  # immutable squashes CHANGE
        assertUserResourceState(self, george, [bikes], [], [])
        assertUserResourceState(self, alva, [], [], [bikes])  # immutable squashes CHANGE
        assertUserResourceState(self, john, [], [], [bikes])

        assertGroupUserState(self, bikers, [george], [], [])
        assertGroupUserState(self, harpers, [george], [], [])
        assertUserGroupState(self, george, [bikers, harpers], [], [])
        assertUserGroupState(self, alva, [], [], [])
        assertUserGroupState(self, john, [], [], [])

        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.CHANGE)

        assertGroupUserState(self, bikers, [george], [alva], [])
        assertGroupUserState(self, harpers, [george], [], [])
        assertUserGroupState(self, george, [bikers, harpers], [], [])
        assertUserGroupState(self, alva, [], [bikers], [])
        assertUserGroupState(self, john, [], [], [])

        george.uaccess.share_group_with_user(bikers, john, PrivilegeCodes.VIEW)

        assertGroupUserState(self, bikers, [george], [alva], [john])
        assertGroupUserState(self, harpers, [george], [], [])
        assertUserGroupState(self, george, [bikers, harpers], [], [])
        assertUserGroupState(self, alva, [], [bikers], [])
        assertUserGroupState(self, john, [], [], [bikers])

        assertResourceGroupState(self, bikes, [], [])
        assertGroupResourceState(self, bikers, [], [])

        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.CHANGE)

        assertResourceGroupState(self, bikes, [], [bikers])  # immutable squashes state
        assertGroupResourceState(self, bikers, [], [bikes])  # immutable squashes state

        bikes.raccess.immutable = False
        bikes.raccess.save()

        assertResourceGroupState(self, bikes, [bikers], [])  # without immutable, CHANGE returns
        assertGroupResourceState(self, bikers, [bikes], [])  # without immutable, CHANGE returns

    def test_share(self):
        bikes = self.bikes
        harpers = self.harpers 
        bikers = self.bikers 
        george = self.george
        alva = self.alva
        admin = self.admin
        john = self.john

        assertResourceUserState(self, bikes, [george], [], [])
        assertUserResourceState(self, george, [bikes], [], [])
        assertUserResourceState(self, alva, [], [], [])

        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.OWNER)

        assertResourceUserState(self, bikes, [george, alva], [], [])
        assertUserResourceState(self, george, [bikes], [], [])
        assertUserResourceState(self, alva, [bikes], [], [])

        # test a user can downgrade (e.g., from OWNER to CHANGE) his/her access privilege
        alva.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.CHANGE)

        assertResourceUserState(self, bikes, [george], [alva], [])
        assertUserResourceState(self, george, [bikes], [], [])
        assertUserResourceState(self, alva, [], [bikes], [])

        # unshare bikes
        george.uaccess.unshare_resource_with_user(bikes, alva)

        assertResourceUserState(self, bikes, [george], [], [])
        assertUserResourceState(self, george, [bikes], [], [])
        assertUserResourceState(self, alva, [], [], [])

        assertGroupResourceState(self, bikers, [], [])

        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.VIEW)

        assertGroupResourceState(self, bikers, [], [bikes])

        george.uaccess.share_resource_with_group(bikes, harpers, PrivilegeCodes.CHANGE)

        assertGroupResourceState(self, harpers, [bikes], [])

        george.uaccess.share_group_with_user(harpers, alva, PrivilegeCodes.CHANGE)

        assertUserGroupState(self, alva, [], [harpers], [])
        assertUserResourceState(self, alva, [], [], [])  # isolated from group privilege CHANGE
        assertGroupResourceState(self, harpers, [bikes], [])

        george.uaccess.unshare_group_with_user(harpers, alva)

        assertUserResourceState(self, alva, [], [], [])  # isolated from group privilege CHANGE

        george.uaccess.unshare_resource_with_group(bikes, harpers)

        assertGroupResourceState(self, harpers, [], [])

        ## test upgrade privilege by non owners
        # let george (owner) grant change privilege to alva (non owner)
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.CHANGE)

        assertUserResourceState(self, alva, [], [bikes], [])

        # let alva (non owner) grant view privilege to john (non owner)
        alva.uaccess.share_resource_with_user(bikes, self.john, PrivilegeCodes.VIEW)

        assertUserResourceState(self, john, [], [], [bikes])
        assertResourceUserState(self, bikes, [george], [alva], [john])

        # let alva (non owner) grant change privilege (upgrade) to john (non owner)
        alva.uaccess.share_resource_with_user(bikes, self.john, PrivilegeCodes.CHANGE)

        assertUserResourceState(self, john, [], [bikes], [])
        assertResourceUserState(self, bikes, [george], [alva, john], [])

        # test django admin has ownership permission over any resource even when not owning a resource
        self.assertFalse(admin.uaccess.owns_resource(bikes))
        self.assertEqual(bikes.raccess.get_effective_privilege(admin), PrivilegeCodes.OWNER)

        # test django admin can always view/change or delete any resource
        self.assertTrue(admin.uaccess.can_view_resource(bikes))
        self.assertTrue(admin.uaccess.can_change_resource(bikes))
        self.assertTrue(admin.uaccess.can_delete_resource(bikes))

        # test django admin can change resource flags
        self.assertTrue(admin.uaccess.can_change_resource_flags(bikes))

        # test django admin can share any resource with all possible permission types
        self.assertTrue(admin.uaccess.can_share_resource(bikes, PrivilegeCodes.OWNER))
        self.assertTrue(admin.uaccess.can_share_resource(bikes, PrivilegeCodes.CHANGE))
        self.assertTrue(admin.uaccess.can_share_resource(bikes, PrivilegeCodes.VIEW))

        # test django admin can share a resource with a specific user
        admin.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.OWNER)

        assertResourceUserState(self, bikes, [george, alva], [john], [])

        admin.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.CHANGE)

        assertResourceUserState(self, bikes, [george], [john, alva], [])

        admin.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.VIEW)

        assertResourceUserState(self, bikes, [george], [john], [alva])

        # test django admin can unshare a resource with a specific user
        admin.uaccess.unshare_resource_with_user(bikes, alva)

        assertResourceUserState(self, bikes, [george], [john], [])

        # test django admin can share a group with a user
        self.assertEqual(bikers.gaccess.members.count(), 1)
        self.assertFalse(admin.uaccess.owns_group(bikers))
        admin.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.OWNER)
        self.assertEqual(alva.uaccess.owned_groups.count(), 1)
        self.assertEqual(bikers.gaccess.members.count(), 2)

        # test django admin can share resource with a group
        self.assertFalse(admin.uaccess.can_share_resource_with_group(bikes, harpers, PrivilegeCodes.OWNER))
        self.assertTrue(admin.uaccess.can_share_resource_with_group(bikes, harpers, PrivilegeCodes.CHANGE))
        admin.uaccess.share_resource_with_group(bikes, harpers, PrivilegeCodes.CHANGE)
        self.assertTrue(bikes in harpers.gaccess.edit_resources)

        self.assertTrue(admin.uaccess.can_share_resource_with_group(bikes, harpers, PrivilegeCodes.VIEW))
        admin.uaccess.share_resource_with_group(bikes, harpers, PrivilegeCodes.VIEW)
        self.assertTrue(bikes in harpers.gaccess.view_resources)

        # test django admin can unshare a user with a group
        self.assertTrue(admin.uaccess.can_unshare_group_with_user(bikers, alva))
        admin.uaccess.unshare_group_with_user(bikers, alva)
        self.assertTrue(bikers.gaccess.members.count(), 1)
        self.assertEqual(alva.uaccess.owned_groups.count(), 0)

    def test_share_inactive_user(self):
        """
        Inactive grantor can't grant permission
        Inactive grantee can't be granted permission
        """
        george = self.george
        alva = self.alva
        john = self.john
        bikes = self.bikes

        self.assertEqual(bikes.raccess.get_effective_privilege(alva), PrivilegeCodes.NONE)

        # inactive users can't be granted access
        # set john to an inactive user
        john.is_active = False
        john.save()

        with self.assertRaises(PermissionDenied):
            george.uaccess.share_resource_with_user(bikes, john, PrivilegeCodes.CHANGE)

        john.is_active = True
        john.save()

        ## inactive grantor can't grant access
        # let's first grant John access privilege
        george.uaccess.share_resource_with_user(bikes, john, PrivilegeCodes.CHANGE)

        self.assertEqual(bikes.raccess.get_effective_privilege(john), PrivilegeCodes.CHANGE)

        john.is_active = False
        john.save()

        with self.assertRaises(PermissionDenied):
            john.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.VIEW)
