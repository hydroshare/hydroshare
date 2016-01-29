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


class UnitTests(MockIRODSTestCaseMixin, TestCase):
    """ test basic behavior of each routine """

    def setUp(self):
        super(UnitTests, self).setUp()
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

    def test_user_create_group(self):
        george = self.george
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(george.uaccess.view_groups, [bikers]))
        foo = george.uaccess.create_group('Foozball')
        self.assertTrue(is_equal_to_as_set(george.uaccess.view_groups, [foo, bikers]))

    def test_user_delete_group(self):
        george = self.george
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(george.uaccess.view_groups, [bikers]))
        george.uaccess.delete_group(bikers)
        self.assertTrue(is_equal_to_as_set(george.uaccess.view_groups, []))

    def test_user_owned_groups(self):
        george = self.george
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(george.uaccess.owned_groups, [bikers]))

    def test_user_owns_group(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertTrue(george.uaccess.owns_group(bikers))
        self.assertFalse(alva.uaccess.owns_group(bikers))

    def test_user_can_change_group(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertTrue(george.uaccess.can_change_group(bikers))
        self.assertFalse(alva.uaccess.can_change_group(bikers))

    def test_user_can_view_group(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertTrue(george.uaccess.can_view_group(bikers))
        bikers.gaccess.public=False
        bikers.save()
        self.assertFalse(alva.uaccess.can_view_group(bikers))

    def test_user_can_view_group_metadata(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertTrue(george.uaccess.can_view_group_metadata(bikers))
        bikers.gaccess.public=False
        bikers.gaccess.discoverable=False
        bikers.save()
        self.assertFalse(alva.uaccess.can_view_group_metadata(bikers))

    def test_user_can_change_group_flags(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertTrue(george.uaccess.can_change_group_flags(bikers))
        self.assertFalse(alva.uaccess.can_change_group_flags(bikers))

    def test_user_can_delete_group(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertTrue(george.uaccess.can_delete_group(bikers))
        self.assertFalse(alva.uaccess.can_delete_group(bikers))

    def test_user_can_share_group(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertTrue(george.uaccess.can_share_group(bikers, PrivilegeCodes.VIEW))
        self.assertFalse(alva.uaccess.can_share_group(bikers, PrivilegeCodes.VIEW))

    def test_user_share_group_with_user(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.members, [george]))
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.members, [george, alva]))

    def test_user_unshare_group_with_user(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.members, [george]))
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.members, [george, alva]))
        george.uaccess.unshare_group_with_user(bikers, alva)
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.members, [george]))

    def test_user_can_unshare_group_with_user(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertFalse(george.uaccess.can_unshare_group_with_user(bikers, alva))
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.VIEW)
        self.assertTrue(george.uaccess.can_unshare_group_with_user(bikers, alva))

    def test_user_undo_share_group_with_user(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.members, [george]))
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.members, [george, alva]))
        george.uaccess.undo_share_group_with_user(bikers, alva)
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.members, [george]))

    def test_user_can_undo_share_group_with_user(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertFalse(george.uaccess.can_undo_share_group_with_user(bikers, alva))
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.VIEW)
        self.assertTrue(george.uaccess.can_undo_share_group_with_user(bikers, alva))

    def test_user_get_group_undo_users(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_group_undo_users(bikers), []))
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_group_undo_users(bikers), [alva]))

    def test_user_get_group_unshare_users(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_group_unshare_users(bikers), []))
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_group_unshare_users(bikers), [alva]))

    def test_user_view_resources(self):
        george = self.george
        bikes = self.bikes
        self.assertTrue(is_equal_to_as_set(george.uaccess.view_resources, [bikes]))
        trikes = hydroshare.create_resource(resource_type='GenericResource',
                                            owner=self.george,
                                            title='Trikes',
                                            metadata=[],)
        self.assertTrue(is_equal_to_as_set(george.uaccess.view_resources, [bikes, trikes]))

    def test_user_owned_resources(self):
        george = self.george
        bikes = self.bikes
        self.assertTrue(is_equal_to_as_set(george.uaccess.owned_resources, [bikes]))
        trikes = hydroshare.create_resource(resource_type='GenericResource',
                                            owner=self.george,
                                            title='Trikes',
                                            metadata=[],)
        self.assertTrue(is_equal_to_as_set(george.uaccess.owned_resources, [bikes, trikes]))

    def test_user_edit_resources(self):
        george = self.george
        bikes = self.bikes
        self.assertTrue(is_equal_to_as_set(george.uaccess.edit_resources, [bikes]))
        trikes = hydroshare.create_resource(resource_type='GenericResource',
                                            owner=self.george,
                                            title='Trikes',
                                            metadata=[],)
        self.assertTrue(is_equal_to_as_set(george.uaccess.edit_resources, [bikes, trikes]))

    def test_user_get_resources_with_explicit_access(self):
        george = self.george
        bikes = self.bikes
        self.assertTrue(is_equal_to_as_set(
            george.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER), [bikes]))
        self.assertTrue(is_equal_to_as_set(
            george.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE), []))
        self.assertTrue(is_equal_to_as_set(
            george.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW), []
        ))

    def test_user_get_groups_with_explicit_access(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(
            george.uaccess.get_groups_with_explicit_access(PrivilegeCodes.OWNER), [bikers]
        ))
        self.assertTrue(is_equal_to_as_set(
            alva.uaccess.get_groups_with_explicit_access(PrivilegeCodes.CHANGE), []
        ))
        self.assertTrue(is_equal_to_as_set(
            alva.uaccess.get_groups_with_explicit_access(PrivilegeCodes.VIEW), []
        ))

    def test_user_owns_resource(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(george.uaccess.owns_resource(bikes))
        self.assertFalse(alva.uaccess.owns_resource(bikes))

    def test_user_can_change_resource(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(george.uaccess.can_change_resource(bikes))
        self.assertFalse(alva.uaccess.can_change_resource(bikes))

    def test_user_can_change_resource_flags(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(george.uaccess.can_change_resource_flags(bikes))
        self.assertFalse(alva.uaccess.can_change_resource_flags(bikes))

    def test_user_can_view_resource(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(george.uaccess.can_view_resource(bikes))
        self.assertFalse(alva.uaccess.can_view_resource(bikes))

    def test_user_can_delete_resource(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(george.uaccess.can_delete_resource(bikes))
        self.assertFalse(alva.uaccess.can_delete_resource(bikes))

    def test_user_can_share_resource(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(george.uaccess.can_share_resource(bikes, PrivilegeCodes.VIEW))
        self.assertFalse(alva.uaccess.can_share_resource(bikes, PrivilegeCodes.VIEW))

    def test_user_can_share_resource_with_group(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        bikers = self.bikers
        self.assertTrue(george.uaccess.can_share_resource_with_group(bikes, bikers, PrivilegeCodes.VIEW))
        self.assertFalse(alva.uaccess.can_share_resource_with_group(bikes, bikers, PrivilegeCodes.VIEW))

    def test_user_undo_share_resource_with_group(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.view_resources, []))
        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.view_resources, [bikes]))
        george.uaccess.undo_share_resource_with_group(bikes, bikers)
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.view_resources, []))

    def test_user_can_undo_share_resource_with_group(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers
        self.assertFalse(george.uaccess.can_undo_share_resource_with_group(bikes, bikers))
        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.VIEW)
        self.assertTrue(george.uaccess.can_undo_share_resource_with_group(bikes, bikers))

    def test_user_share_resource_with_user(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(is_equal_to_as_set(alva.uaccess.view_resources, []))
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(alva.uaccess.view_resources, [bikes]))

    def test_user_unshare_resource_with_user(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(is_equal_to_as_set(alva.uaccess.view_resources, []))
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(alva.uaccess.view_resources, [bikes]))
        george.uaccess.unshare_resource_with_user(bikes, alva)
        self.assertTrue(is_equal_to_as_set(alva.uaccess.view_resources, []))

    def test_user_can_unshare_resource_with_user(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertFalse(george.uaccess.can_unshare_resource_with_user(bikes, alva))
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.VIEW)
        self.assertTrue(george.uaccess.can_unshare_resource_with_user(bikes, alva))

    def test_user_undo_share_resource_with_user(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(is_equal_to_as_set(alva.uaccess.view_resources, []))
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(alva.uaccess.view_resources, [bikes]))
        george.uaccess.undo_share_resource_with_user(bikes, alva)
        self.assertTrue(is_equal_to_as_set(alva.uaccess.view_resources, []))

    def test_user_can_undo_share_resource_with_user(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertFalse(george.uaccess.can_undo_share_resource_with_user(bikes, alva))
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.VIEW)
        self.assertTrue(george.uaccess.can_undo_share_resource_with_user(bikes, alva))

    def test_user_share_resource_with_group(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.view_resources, []))
        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.view_resources, [bikes]))

    def test_user_unshare_resource_with_group(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.view_resources, []))
        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.view_resources, [bikes]))
        george.uaccess.unshare_resource_with_group(bikes, bikers)
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.view_resources, []))

    def test_user_can_unshare_resource_with_group(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers
        self.assertFalse(george.uaccess.can_unshare_resource_with_group(bikes, bikers))
        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.VIEW)
        self.assertTrue(george.uaccess.can_unshare_resource_with_group(bikes, bikers))

    def test_user_get_resource_undo_users(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_resource_undo_users(bikes), []))
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_resource_undo_users(bikes), [alva]))

    def test_user_get_resource_unshare_users(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_resource_unshare_users(bikes), []))
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_resource_unshare_users(bikes), [alva]))

    def test_user_get_resource_undo_groups(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_resource_undo_groups(bikes), []))
        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_resource_undo_groups(bikes), [bikers]))

    def test_user_get_resource_unshare_groups(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_resource_unshare_groups(bikes), []))
        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_resource_unshare_groups(bikes), [bikers]))

    def test_group_members(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.members, [george]))
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.members, [george, alva]))

    def test_group_view_resources(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.view_resources, []))
        george.uaccess.share_resource_with_group(bikes, bikers,  PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.view_resources, [bikes]))

    def test_group_edit_resources(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.edit_resources, []))
        george.uaccess.share_resource_with_group(bikes, bikers,  PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.edit_resources, [bikes]))

    def test_group_get_resources_with_explicit_access(self):
        george = self.george
        bikers = self.bikers
        bikes = self.bikes
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW), []))
        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE), [bikes]))

    def test_group_owners(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.owners, [george]))
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.OWNER)
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.owners, [george, alva]))

    def test_group_view_users(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.members, [george]))
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.OWNER)
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.members, [george, alva]))

    def test_group_edit_users(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.edit_users, [george]))
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.OWNER)
        self.assertTrue(is_equal_to_as_set(bikers.gaccess.edit_users, [george, alva]))

    def test_group_get_effective_privilege(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertEqual(bikers.gaccess.get_effective_privilege(george), PrivilegeCodes.OWNER)
        self.assertEqual(bikers.gaccess.get_effective_privilege(alva), PrivilegeCodes.NONE)

    def test_resource_view_users(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(is_equal_to_as_set(bikes.raccess.view_users, [george]))
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.OWNER)
        self.assertTrue(is_equal_to_as_set(bikes.raccess.view_users, [george, alva]))

    def test_resource_edit_users(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(is_equal_to_as_set(bikes.raccess.edit_users, [george]))
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.OWNER)
        self.assertTrue(is_equal_to_as_set(bikes.raccess.edit_users, [george, alva]))

    def test_resource_view_groups(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(bikes.raccess.view_groups, []))
        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(bikes.raccess.view_groups, [bikers]))

    def test_resource_edit_groups(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers
        self.assertTrue(is_equal_to_as_set(bikes.raccess.edit_groups, []))
        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(bikes.raccess.edit_groups, [bikers]))

    def test_resource_owners(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(is_equal_to_as_set(bikes.raccess.owners, [george]))
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.OWNER)
        self.assertTrue(is_equal_to_as_set(bikes.raccess.owners, [george, alva]))

    def test_resource_get_effective_privilege(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertEqual(bikes.raccess.get_effective_privilege(george), PrivilegeCodes.OWNER)
        self.assertEqual(bikes.raccess.get_effective_privilege(alva), PrivilegeCodes.NONE)
