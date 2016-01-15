__author__ = 'Alva'

# TODO: test that distinct is not necessary if Q() expressions are not present. 

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

def global_reset():
    UserResourcePrivilege.objects.all().delete()
    UserGroupPrivilege.objects.all().delete()
    GroupResourcePrivilege.objects.all().delete()
    UserAccess.objects.all().delete()
    GroupAccess.objects.all().delete()
    ResourceAccess.objects.all().delete()
    User.objects.all().delete()
    Group.objects.all().delete()
    BaseResource.objects.all().delete()

def match_lists_as_sets(l1, l2):
    """ return true if two lists contain the same content
    :param l1: first list
    :param l2: second list
    :return: whether lists match
    """
    return len(set(l1) & set(l2)) == len(set(l1))\
       and len(set(l1) | set(l2)) == len(set(l1))


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
        alva = self.alva
        bikes = self.bikes
        bikers = self.bikers
        self.assertTrue(match_lists_as_sets(george.uaccess.get_held_groups(), [bikers]))
        foo = george.uaccess.create_group('Foozball')
        self.assertTrue(match_lists_as_sets(george.uaccess.get_held_groups(), [foo, bikers]))

    def test_user_delete_group(self):
        george = self.george
        bikers = self.bikers
        self.assertTrue(match_lists_as_sets(george.uaccess.get_held_groups(), [bikers]))
        foo = george.uaccess.delete_group(bikers)
        self.assertTrue(match_lists_as_sets(george.uaccess.get_held_groups(), []))

    def test_user_get_held_groups(self):
        george = self.george
        bikers = self.bikers
        self.assertTrue(match_lists_as_sets(george.uaccess.get_held_groups(), [bikers]))
        # test_user_delete_group also tests this routine

    def test_user_get_owned_groups(self):
        george = self.george
        bikers = self.bikers 
        self.assertTrue(match_lists_as_sets(george.uaccess.get_owned_groups(), [bikers])) 

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
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_members(), [george]))
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_members(), [george, alva]))

    def test_user_unshare_group_with_user(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers 
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_members(), [george]))
        self.assertTrue(george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.VIEW))
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_members(), [george, alva]))
        george.uaccess.unshare_group_with_user(bikers, alva)
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_members(), [george]))

    def test_user_can_unshare_group_with_user(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers 
        self.assertFalse(george.uaccess.can_unshare_group_with_user(bikers, alva)) 
        self.assertTrue(george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.VIEW))
        self.assertTrue(george.uaccess.can_unshare_group_with_user(bikers, alva)) 

    def test_user_undo_share_group_with_user(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers 
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_members(), [george]))
        self.assertTrue(george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.VIEW))
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_members(), [george, alva]))
        self.assertTrue(george.uaccess.undo_share_group_with_user(bikers, alva))
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_members(), [george]))

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
        self.assertTrue(match_lists_as_sets(george.uaccess.get_group_undo_users(bikers), []))
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(george.uaccess.get_group_undo_users(bikers), [alva]))

    def test_user_get_group_unshare_users(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers 
        self.assertTrue(match_lists_as_sets(george.uaccess.get_group_unshare_users(bikers), []))
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(george.uaccess.get_group_unshare_users(bikers), [alva]))

    def test_user_get_held_resources(self):
        george = self.george
        bikes = self.bikes
        self.assertTrue(match_lists_as_sets(george.uaccess.get_held_resources(), [bikes]))
        trikes = hydroshare.create_resource(resource_type='GenericResource',
                                            owner=self.george,
                                            title='Trikes',
                                            metadata=[],)
        self.assertTrue(match_lists_as_sets(george.uaccess.get_held_resources(), [bikes, trikes]))

    def test_user_get_owned_resources(self):
        george = self.george
        bikes = self.bikes
        self.assertTrue(match_lists_as_sets(george.uaccess.get_owned_resources(), [bikes]))
        trikes = hydroshare.create_resource(resource_type='GenericResource',
                                            owner=self.george,
                                            title='Trikes',
                                            metadata=[],)
        self.assertTrue(match_lists_as_sets(george.uaccess.get_owned_resources(), [bikes, trikes]))

    def test_user_get_editable_resources(self):
        george = self.george
        bikes = self.bikes
        self.assertTrue(match_lists_as_sets(george.uaccess.get_editable_resources(), [bikes]))
        trikes = hydroshare.create_resource(resource_type='GenericResource',
                                            owner=self.george,
                                            title='Trikes',
                                            metadata=[],)
        self.assertTrue(match_lists_as_sets(george.uaccess.get_editable_resources(), [bikes, trikes]))

    def test_user_get_resources_with_explicit_access(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(match_lists_as_sets(
            george.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER), [bikes])) 
        self.assertTrue(match_lists_as_sets(
            alva.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER), [])) 

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
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_held_resources(), []))
        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_held_resources(), [bikes]))
        self.assertTrue(george.uaccess.undo_share_resource_with_group(bikes, bikers)) 
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_held_resources(), []))

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
        self.assertTrue(match_lists_as_sets(alva.uaccess.get_held_resources(), []))
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(alva.uaccess.get_held_resources(), [bikes]))

    def test_user_unshare_resource_with_user(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(match_lists_as_sets(alva.uaccess.get_held_resources(), []))
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(alva.uaccess.get_held_resources(), [bikes]))
        self.assertTrue(george.uaccess.unshare_resource_with_user(bikes, alva)) 
        self.assertTrue(match_lists_as_sets(alva.uaccess.get_held_resources(), []))

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
        self.assertTrue(match_lists_as_sets(alva.uaccess.get_held_resources(), []))
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(alva.uaccess.get_held_resources(), [bikes]))
        self.assertTrue(george.uaccess.undo_share_resource_with_user(bikes, alva)) 
        self.assertTrue(match_lists_as_sets(alva.uaccess.get_held_resources(), []))

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
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_held_resources(), []))
        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_held_resources(), [bikes]))

    def test_user_unshare_resource_with_group(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers 
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_held_resources(), []))
        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_held_resources(), [bikes]))
        self.assertTrue(george.uaccess.unshare_resource_with_group(bikes, bikers)) 
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_held_resources(), []))

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
        self.assertTrue(match_lists_as_sets(george.uaccess.get_resource_undo_users(bikes), []))
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(george.uaccess.get_resource_undo_users(bikes), [alva]))

    def test_user_get_resource_unshare_users(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(match_lists_as_sets(george.uaccess.get_resource_unshare_users(bikes), []))
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(george.uaccess.get_resource_unshare_users(bikes), [alva]))

    def test_user_get_resource_undo_groups(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers 
        self.assertTrue(match_lists_as_sets(george.uaccess.get_resource_undo_groups(bikes), []))
        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(george.uaccess.get_resource_undo_groups(bikes), [bikers]))

    def test_user_get_resource_unshare_groups(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers 
        self.assertTrue(match_lists_as_sets(george.uaccess.get_resource_unshare_groups(bikes), []))
        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(george.uaccess.get_resource_unshare_groups(bikes), [bikers]))

    def test_group_get_members(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_members(), [george])) 
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.CHANGE) 
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_members(), [george, alva])) 

    def test_group_get_held_resources(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers 
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_held_resources(), [])) 
        george.uaccess.share_resource_with_group(bikes, bikers,  PrivilegeCodes.CHANGE) 
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_held_resources(), [bikes])) 

    def test_group_get_editable_resources(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers 
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_editable_resources(), [])) 
        george.uaccess.share_resource_with_group(bikes, bikers,  PrivilegeCodes.CHANGE) 
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_editable_resources(), [bikes])) 

    def test_group_get_owners(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers 
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_owners(), [george])) 
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.OWNER)
        self.assertTrue(match_lists_as_sets(bikers.gaccess.get_owners(), [george, alva])) 

    def test_group_get_user_privilege(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers 
        self.assertEqual(bikers.gaccess.get_user_privilege(george), PrivilegeCodes.OWNER) 
        self.assertEqual(bikers.gaccess.get_user_privilege(alva), PrivilegeCodes.NONE) 

    def test_resource_get_holding_groups(self): 
        george = self.george
        bikes = self.bikes
        bikers = self.bikers 
        self.assertTrue(match_lists_as_sets(bikes.raccess.get_holding_groups(), [])) 
        george.uaccess.share_resource_with_group(bikes, bikers,  PrivilegeCodes.CHANGE) 
        self.assertTrue(match_lists_as_sets(bikes.raccess.get_holding_groups(), [bikers])) 

    def test_resource_get_holding_users(self): 
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(match_lists_as_sets(bikes.raccess.get_holding_users(), [george])) 
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(bikes.raccess.get_holding_users(), [george, alva])) 

    def test_resource_view_users(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(match_lists_as_sets(bikes.raccess.view_users, [george])) 
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.OWNER)
        self.assertTrue(match_lists_as_sets(bikes.raccess.view_users, [george, alva])) 

    def test_resource_edit_users(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(match_lists_as_sets(bikes.raccess.edit_users, [george])) 
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.OWNER)
        self.assertTrue(match_lists_as_sets(bikes.raccess.edit_users, [george, alva])) 

    def test_resource_view_groups(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers 
        self.assertTrue(match_lists_as_sets(bikes.raccess.view_groups, [])) 
        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.CHANGE)
        self.assertTrue(match_lists_as_sets(bikes.raccess.view_groups, [bikers])) 

    def test_resource_edit_groups(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers 
        self.assertTrue(match_lists_as_sets(bikes.raccess.edit_groups, [])) 
        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.CHANGE)
        self.assertTrue(match_lists_as_sets(bikes.raccess.edit_groups, [bikers])) 

    def test_resource_owners(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(match_lists_as_sets(bikes.raccess.owners, [george])) 
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.OWNER)
        self.assertTrue(match_lists_as_sets(bikes.raccess.owners, [george, alva])) 

    def test_resource_get_owners(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(match_lists_as_sets(bikes.raccess.get_owners(), [george])) 
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.OWNER)
        self.assertTrue(match_lists_as_sets(bikes.raccess.get_owners(), [george, alva])) 

    def test_resource_get_holders(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertTrue(match_lists_as_sets(bikes.raccess.get_holders(), [george])) 
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.OWNER)
        self.assertTrue(match_lists_as_sets(bikes.raccess.get_holders(), [george, alva])) 

    def test_resource_get_combined_privilege(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertEqual(bikes.raccess.get_combined_privilege(george), PrivilegeCodes.OWNER) 
        self.assertEqual(bikes.raccess.get_combined_privilege(alva), PrivilegeCodes.NONE) 

    def test_resource_get_group_privilege(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers 
        self.assertEqual(bikes.raccess.get_group_privilege(bikers), PrivilegeCodes.NONE) 
        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.CHANGE)
        self.assertEqual(bikes.raccess.get_group_privilege(bikers), PrivilegeCodes.CHANGE) 

    def test_resource_get_effective_privilege(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        self.assertEqual(bikes.raccess.get_effective_privilege(george), PrivilegeCodes.OWNER) 
        self.assertEqual(bikes.raccess.get_effective_privilege(alva), PrivilegeCodes.NONE) 


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

    def test_share(self):
        bikes = self.bikes
        harpers = self.harpers 
        bikers = self.bikers 
        george = self.george
        alva = self.alva
        john = self.john
        admin = self.admin 
        
        self.assertTrue(match_lists_as_sets(bikes.raccess.get_owners(), [george]))
        self.assertEqual(bikes.raccess.get_combined_privilege(alva), PrivilegeCodes.NONE)
        self.assertEqual(bikes.raccess.get_effective_privilege(alva), PrivilegeCodes.NONE)

        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.OWNER)

        self.assertTrue(match_lists_as_sets(bikes.raccess.get_holding_users(), [george, alva]))
        self.assertTrue(match_lists_as_sets(bikes.raccess.get_holders(), [george, alva]))
        self.assertTrue(match_lists_as_sets(bikes.raccess.get_holding_groups(), []))

        self.assertTrue(alva.uaccess.owns_resource(bikes))
        self.assertTrue(alva.uaccess.can_change_resource(bikes))
        self.assertTrue(alva.uaccess.can_view_resource(bikes))

        self.assertEqual(bikes.raccess.get_combined_privilege(alva), PrivilegeCodes.OWNER)
        self.assertEqual(bikes.raccess.get_effective_privilege(alva), PrivilegeCodes.OWNER)

        # test a user can downgrade (e.g., from OWNER to CHANGE) his/her access privilege
        alva.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.CHANGE)
        self.assertEqual(bikes.raccess.get_effective_privilege(alva), PrivilegeCodes.CHANGE)

        # test user 'alva'  has resource 'bikes' as one of the resources that he can edit
        self.assertTrue(bikes in alva.uaccess.get_editable_resources())

        george.uaccess.unshare_resource_with_user(bikes, alva)
        self.assertEqual(bikes.raccess.get_combined_privilege(alva), PrivilegeCodes.NONE)

        # test resource 'bikes' is not one of the resources that user 'alva'  can edit
        self.assertFalse(bikes in alva.uaccess.get_editable_resources())

        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.OWNER)
        self.assertEqual(bikes.raccess.get_combined_privilege(alva), PrivilegeCodes.NONE)
        george.uaccess.share_resource_with_group(bikes, bikers, PrivilegeCodes.VIEW)
        self.assertEqual(bikes.raccess.get_combined_privilege(alva), PrivilegeCodes.VIEW)
        george.uaccess.share_resource_with_group(bikes, harpers, PrivilegeCodes.CHANGE)

        # test that the group 'harpers' has resource 'bikes' as one of the editable resources
        self.assertTrue(bikes in harpers.gaccess.get_editable_resources())

        george.uaccess.share_group_with_user(harpers, alva, PrivilegeCodes.CHANGE)

        self.assertEqual(bikes.raccess.get_combined_privilege(alva), PrivilegeCodes.CHANGE)

        george.uaccess.unshare_group_with_user(harpers, alva)

        self.assertEqual(bikes.raccess.get_combined_privilege(alva), PrivilegeCodes.VIEW)

        george.uaccess.unshare_resource_with_group(bikes, harpers)

        # test the resource 'bikes' is not one of the editable resources for the group 'harpers
        self.assertFalse(bikes in harpers.gaccess.get_editable_resources())

        george.uaccess.unshare_group_with_user(bikers, alva)

        ## test upgrade privilege by non owners
        # let george (owner) grant change privilege to alva (non owner)
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.CHANGE)
        self.assertEqual(bikes.raccess.get_combined_privilege(alva), PrivilegeCodes.CHANGE)
        # let alva (non owner) grant view privilege to john (non owner)
        alva.uaccess.share_resource_with_user(bikes, self.john, PrivilegeCodes.VIEW)
        self.assertEqual(bikes.raccess.get_combined_privilege(self.john), PrivilegeCodes.VIEW)
        # let alva (non owner) grant change privilege (upgrade) to john (non owner)
        alva.uaccess.share_resource_with_user(bikes, self.john, PrivilegeCodes.CHANGE)
        self.assertEqual(bikes.raccess.get_combined_privilege(self.john), PrivilegeCodes.CHANGE)

        ## test for django admin - admin has not been given any permission on any resource by any user
        # test django admin has ownership permission over any resource even when not owning a resource
        self.assertFalse(admin.uaccess.owns_resource(bikes))
        self.assertEqual(bikes.raccess.get_combined_privilege(admin), PrivilegeCodes.OWNER)
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
        self.assertEqual(bikes.raccess.get_combined_privilege(alva),  PrivilegeCodes.OWNER)

        admin.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.CHANGE)
        self.assertEqual(bikes.raccess.get_combined_privilege(alva),  PrivilegeCodes.CHANGE)

        admin.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.VIEW)
        self.assertEqual(bikes.raccess.get_combined_privilege(alva),  PrivilegeCodes.VIEW)

        # test django admin can unshare a resource with a specific user
        self.assertTrue(admin.uaccess.unshare_resource_with_user(bikes, alva))
        self.assertEqual(bikes.raccess.get_combined_privilege(alva),  PrivilegeCodes.NONE)

        # test django admin can share a group with a user
        self.assertEqual(bikers.gaccess.get_members().count(), 1)
        self.assertFalse(admin.uaccess.owns_group(bikers))
        admin.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.OWNER)
        self.assertEqual(alva.uaccess.get_owned_groups().count(), 1)
        self.assertEqual(bikers.gaccess.get_members().count(), 2)

        # test django admin can share resource with a group
        self.assertFalse(admin.uaccess.can_share_resource_with_group(bikes, harpers, PrivilegeCodes.OWNER))
        self.assertTrue(admin.uaccess.can_share_resource_with_group(bikes, harpers, PrivilegeCodes.CHANGE))
        admin.uaccess.share_resource_with_group(bikes, harpers, PrivilegeCodes.CHANGE)
        self.assertTrue(bikes in harpers.gaccess.get_editable_resources())

        self.assertTrue(admin.uaccess.can_share_resource_with_group(bikes, harpers, PrivilegeCodes.VIEW))
        admin.uaccess.share_resource_with_group(bikes, harpers, PrivilegeCodes.VIEW)
        self.assertTrue(bikes in harpers.gaccess.get_held_resources())

        # test django admin can unshare a user with a group
        self.assertTrue(admin.uaccess.can_unshare_group_with_user(bikers, alva))
        admin.uaccess.unshare_group_with_user(bikers, alva)
        self.assertTrue(bikers.gaccess.get_members().count(), 1)
        self.assertEqual(alva.uaccess.get_owned_groups().count(), 0)

    def test_share_inactive_user(self):
        """
        Inactive grantor can't grant permission
        Inactive grantee can't be granted permission
        """
        john = self.john
        george = self.george 
        bikes = self.bikes  
        self.assertEqual(self.bikes.raccess.get_combined_privilege(self.alva), PrivilegeCodes.NONE)
        self.assertEqual(self.bikes.raccess.get_effective_privilege(self.alva), PrivilegeCodes.NONE)

        # inactive users can't be granted access
        # set john to an inactive user
        self.john.is_active = False
        self.john.save()

        with self.assertRaises(PermissionDenied):
            self.george.uaccess.share_resource_with_user(self.bikes, self.john, PrivilegeCodes.CHANGE)

        self.john.is_active = True
        self.john.save()
        ## inactive grantor can't grant access
        # let's first grant John access privilege
        self.george.uaccess.share_resource_with_user(self.bikes, self.john, PrivilegeCodes.CHANGE)
        self.assertEqual(self.bikes.raccess.get_combined_privilege(self.john), PrivilegeCodes.CHANGE)
        self.assertEqual(self.bikes.raccess.get_effective_privilege(self.john), PrivilegeCodes.CHANGE)
        self.john.is_active = False
        self.john.save()
        with self.assertRaises(PermissionDenied): 
            self.john.uaccess.share_resource_with_user(self.bikes, self.alva, PrivilegeCodes.VIEW)
        self.john.is_active = True
        self.john.save()


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


    def test_01_create_state(self):
        """User state is correct after creation"""
        # check that privileged user was created correctly
        self.assertEqual(self.admin.uaccess.user.username, 'admin')
        self.assertEqual(self.admin.uaccess.user.first_name, 'administrator')
        self.assertTrue(self.admin.is_active)

        # start as privileged user
        self.assertEqual(self.admin.uaccess.get_owned_resources().count(), 0)
        self.assertEqual(self.admin.uaccess.get_held_resources().count(), 0)
        self.assertEqual(self.admin.uaccess.get_owned_groups().count(), 0)
        self.assertEqual(self.admin.uaccess.get_held_groups().count(), 0)

        # check that unprivileged user was created correctly
        self.assertEqual(self.cat.uaccess.user.username, 'cat')
        self.assertEqual(self.cat.uaccess.user.first_name, 'not a dog')
        self.assertTrue(self.cat.is_active)

        # check that user cat owns and holds nothing
        self.assertEqual(self.cat.uaccess.get_owned_resources().count(), 0)
        self.assertEqual(self.cat.uaccess.get_held_resources().count(), 0)
        self.assertEqual(self.cat.uaccess.get_owned_groups().count(), 0)
        self.assertEqual(self.cat.uaccess.get_held_groups().count(), 0)


class T03CreateResource(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(T03CreateResource, self).setUp()
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

    def test_01_create(self):
        """Resource creator has appropriate access"""
        cat = self.cat
        # check that user cat owns and holds nothing
        self.assertEqual(cat.uaccess.get_owned_resources().count(), 0)
        self.assertEqual(cat.uaccess.get_held_resources().count(), 0)
        self.assertEqual(cat.uaccess.get_owned_groups().count(), 0)
        self.assertEqual(cat.uaccess.get_held_groups().count(), 0)

        # create a resource
        holes = hydroshare.create_resource(resource_type='GenericResource',
                                           owner=cat,
                                           title='all about dog holes',
                                           metadata=[],)

        self.assertEqual(cat.uaccess.get_owned_resources().count(), 1)
        self.assertEqual(cat.uaccess.get_held_resources().count(), 1)
        self.assertEqual(cat.uaccess.get_owned_groups().count(), 0)
        self.assertEqual(cat.uaccess.get_held_groups().count(), 0)

        # metadata state
        # NOT ACCESS CONTROL: self.assertEqual(holes.metadata.title.value, 'all about dog holes')
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # unsharing with cat would violate owner constraint

        self.assertTrue(match_lists_as_sets([], cat.uaccess.get_resource_undo_users(holes)))
        self.assertTrue(match_lists_as_sets([], cat.uaccess.get_resource_unshare_users(holes)))
        self.assertFalse(cat.uaccess.can_unshare_resource_with_user(holes, cat))
        self.assertFalse(cat.uaccess.can_undo_share_resource_with_user(holes, cat))

    def test_02_isolate(self):
        """A user who didn't create a resource cannot access it"""
        cat = self.cat
        dog = self.dog
        holes = hydroshare.create_resource(resource_type='GenericResource',
                                           owner=cat,
                                           title='all about dog holes',
                                           metadata=[],)

        # check that resource was created
        self.assertEqual(cat.uaccess.get_owned_resources().count(), 1)
        self.assertEqual(cat.uaccess.get_held_resources().count(), 1)
        self.assertEqual(cat.uaccess.get_owned_groups().count(), 0)
        self.assertEqual(cat.uaccess.get_held_groups().count(), 0)

        # check that resource is not accessible to others
        self.assertEqual(dog.uaccess.get_owned_resources().count(), 0)
        self.assertEqual(dog.uaccess.get_held_resources().count(), 0)
        self.assertEqual(dog.uaccess.get_owned_groups().count(), 0)
        self.assertEqual(dog.uaccess.get_held_groups().count(), 0)

        # metadata should be the same as before
        # self.assertEqual(holes.metadata.title.value, 'all about dog holes')
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for non-owner
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))

        # composite django state for non-owner
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # test list access functions for unshare targets
        # these return empty because allowing this would violate the last owner rule
        self.assertTrue(match_lists_as_sets([], cat.uaccess.get_resource_undo_users(holes)))
        self.assertTrue(match_lists_as_sets([], cat.uaccess.get_resource_unshare_users(holes)))
        self.assertTrue(match_lists_as_sets([], dog.uaccess.get_resource_undo_users(holes)))
        self.assertTrue(match_lists_as_sets([], dog.uaccess.get_resource_unshare_users(holes)))

    def test_06_check_flag_immutable(self):
        """Resource owner can set and reset immutable flag"""
        cat = self.cat

        # create a resource
        holes = hydroshare.create_resource(resource_type='GenericResource',
                                           owner=cat,
                                           title='all about dog holes',
                                           metadata=[],)

        # metadata state
        # self.assertEqual(holes.metadata.title.value, 'all about dog holes')
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # make it immutable: what changes?
        holes.raccess.immutable = True
        holes.raccess.save()

        # metadata state
        # self.assertEqual(holes.metadata.title.value, 'all about dog holes')
        self.assertTrue(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertFalse(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # django admin access
        self.assertFalse(self.admin.uaccess.owns_resource(holes))
        self.assertFalse(self.admin.uaccess.can_change_resource(holes))
        self.assertTrue(self.admin.uaccess.can_view_resource(holes))
        self.assertTrue(self.admin.uaccess.can_change_resource_flags(holes))
        self.assertTrue(self.admin.uaccess.can_delete_resource(holes))
        self.assertTrue(self.admin.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(self.admin.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(self.admin.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # now no longer immutable
        holes.raccess.immutable = False
        holes.raccess.save()

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

    def test_07_check_flag_discoverable(self):
        """Resource owner can set and reset discoverable flag"""
        cat = self.cat

        # create a resource
        holes = hydroshare.create_resource(resource_type='GenericResource',
                                           owner=cat,
                                           title='all about dog holes',
                                           metadata=[],)

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # is it listed as discoverable?
        self.assertTrue(match_lists_as_sets([], GenericResource.discoverable_resources.all()))
        self.assertTrue(match_lists_as_sets([], GenericResource.public_resources.all()))

        # make it discoverable
        holes.raccess.discoverable = True
        holes.raccess.save()

        # is it listed as discoverable?
        self.assertTrue(match_lists_as_sets([holes], GenericResource.discoverable_resources.all()))
        self.assertTrue(match_lists_as_sets([], GenericResource.public_resources.all()))

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertTrue(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # make it not discoverable
        holes.raccess.discoverable = False
        holes.raccess.save()

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # django admin should have full access to any not discoverable  resource
        self.assertTrue(self.admin.uaccess.can_change_resource_flags(holes))
        self.assertTrue(self.admin.uaccess.can_delete_resource(holes))
        self.assertTrue(self.admin.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(self.admin.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(self.admin.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # TODO: test get_discoverable_resources and get_public_resources

    def test_08_check_flag_published(self):
        """Resource owner can set and reset published flag"""

        cat = self.cat

        # create a resource
        holes = hydroshare.create_resource(resource_type='GenericResource',
                                           owner=cat,
                                           title='all about dog holes',
                                           metadata=[],)

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # make it published
        holes.raccess.published = True
        holes.raccess.save()

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertTrue(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # django admin access for published resource
        self.assertFalse(self.admin.uaccess.owns_resource(holes))
        self.assertTrue(self.admin.uaccess.can_change_resource(holes))
        self.assertTrue(self.admin.uaccess.can_view_resource(holes))

        self.assertTrue(self.admin.uaccess.can_change_resource_flags(holes))
        self.assertTrue(self.admin.uaccess.can_delete_resource(holes))
        self.assertTrue(self.admin.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(self.admin.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(self.admin.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # make it not published
        holes.raccess.published = False
        holes.raccess.save()

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

    def test_09_check_flag_public(self):
        """Resource owner can set and reset public flag"""

        cat = self.cat

        # create a resource
        holes = hydroshare.create_resource(resource_type='GenericResource',
                                           owner=cat,
                                           title='all about dog holes',
                                           metadata=[],)

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # is it listed as discoverable?
        self.assertTrue(match_lists_as_sets([], GenericResource.discoverable_resources.all()))
        self.assertTrue(match_lists_as_sets([], GenericResource.public_resources.all()))

        # make it public
        holes.raccess.public = True
        holes.raccess.save()

        # is it listed as discoverable?
        self.assertTrue(match_lists_as_sets([holes], GenericResource.discoverable_resources.all()))
        self.assertTrue(match_lists_as_sets([holes], GenericResource.public_resources.all()))

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertTrue(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # make it not public
        holes.raccess.public = False
        holes.raccess.save()

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # django admin should have full access to any private resource
        self.assertFalse(self.admin.uaccess.owns_resource(holes))
        self.assertTrue(self.admin.uaccess.can_change_resource_flags(holes))
        self.assertTrue(self.admin.uaccess.can_delete_resource(holes))
        self.assertTrue(self.admin.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(self.admin.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(self.admin.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

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
        self.assertEqual(dog.uaccess.get_owned_groups().count(), 0)
        self.assertEqual(dog.uaccess.get_held_groups().count(), 0)

        # user 'dog' create a new group called 'arfers'
        arfers = dog.uaccess.create_group('arfers')

        self.assertEqual(dog.uaccess.get_owned_groups().count(), 1)
        self.assertEqual(dog.uaccess.get_held_groups().count(), 1)

        self.assertEqual(cat.uaccess.get_owned_groups().count(), 0)
        self.assertEqual(cat.uaccess.get_held_groups().count(), 0)

        self.assertTrue(match_lists_as_sets([arfers], dog.uaccess.get_owned_groups()))
        self.assertTrue(match_lists_as_sets([arfers], dog.uaccess.get_held_groups()))

        # check membership list
        self.assertEqual(arfers.gaccess.get_members().count(), 1)

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
        self.assertTrue(dog in arfers.gaccess.get_members())

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
        self.assertTrue(cat not in arfers.gaccess.get_members())

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
        self.assertEqual(dog.uaccess.get_owned_groups().count(), 1)
        self.assertEqual(dog.uaccess.get_held_groups().count(), 1)

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
        self.assertEqual(dog.uaccess.get_owned_groups().count(), 0)
        self.assertEqual(dog.uaccess.get_held_groups().count(), 0)


class T05ShareResource(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(T05ShareResource, self).setUp()
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

        # use this as non owner
        self.mouse = hydroshare.create_account(
            'mouse@gmail.com',
            username='mouse',
            first_name='first_name_mouse',
            last_name='last_name_mouse',
            superuser=False,
            groups=[]
        )
        self.holes = hydroshare.create_resource(resource_type='GenericResource',
                                                owner=self.cat,
                                                title='all about dog holes',
                                                metadata=[],)

        self.meowers = self.cat.uaccess.create_group('some random meowers')

    def test_01_resource_unshared_state(self):
        """Resources cannot be accessed by users with no access"""
        # dog should not have sharing privileges
        holes = self.holes
        cat = self.cat
        dog = self.dog

        # privilege of owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_holding_users()))
        self.assertTrue(match_lists_as_sets([], holes.raccess.get_holding_groups()))
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_holders()))

        self.assertTrue(match_lists_as_sets([cat], holes.raccess.owners))
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.edit_users))
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.view_users))
        self.assertTrue(match_lists_as_sets([], holes.raccess.view_groups))
        self.assertTrue(match_lists_as_sets([], holes.raccess.edit_groups))
        self.assertTrue(match_lists_as_sets([], cat.uaccess.get_resource_unshare_users(holes)))
        self.assertTrue(match_lists_as_sets([], cat.uaccess.get_resource_undo_users(holes)))
        self.assertTrue(match_lists_as_sets([], cat.uaccess.get_resource_unshare_groups(holes)))
        self.assertTrue(match_lists_as_sets([], cat.uaccess.get_resource_undo_groups(holes)))

        # metadata state
        self.assertFalse(holes.raccess.public)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.immutable)
        self.assertTrue(holes.raccess.shareable)

        # privilege of other user
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

    def test_02_share_resource_ownership(self):
        """Resources can be shared as OWNER by owner"""
        holes = self.holes
        dog = self.dog
        cat = self.cat

        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_holding_users()))
        self.assertTrue(match_lists_as_sets([], holes.raccess.get_holding_groups()))
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_holders()))
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.owners))
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.edit_users))
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.view_users))
        self.assertTrue(match_lists_as_sets([], holes.raccess.view_groups))
        self.assertTrue(match_lists_as_sets([], holes.raccess.edit_groups))
        self.assertTrue(match_lists_as_sets([], cat.uaccess.get_resource_unshare_users(holes)))
        self.assertTrue(match_lists_as_sets([], cat.uaccess.get_resource_undo_users(holes)))
        self.assertTrue(match_lists_as_sets([], cat.uaccess.get_resource_unshare_groups(holes)))
        self.assertTrue(match_lists_as_sets([], cat.uaccess.get_resource_undo_groups(holes)))

        self.assertEqual(holes.raccess.get_owners().count(), 1)
        self.assertEqual(holes.raccess.get_holders().count(), 1)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # share holes with dog as owner
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.OWNER)

        self.assertTrue(match_lists_as_sets([cat,dog], holes.raccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat,dog], holes.raccess.get_holding_users()))
        self.assertTrue(match_lists_as_sets([], holes.raccess.get_holding_groups()))
        self.assertTrue(match_lists_as_sets([cat,dog], holes.raccess.get_holders()))

        self.assertTrue(match_lists_as_sets([cat,dog], holes.raccess.owners))
        self.assertTrue(match_lists_as_sets([cat,dog], holes.raccess.edit_users))
        self.assertTrue(match_lists_as_sets([cat,dog], holes.raccess.view_users))
        self.assertTrue(match_lists_as_sets([], holes.raccess.view_groups))
        self.assertTrue(match_lists_as_sets([], holes.raccess.edit_groups))

        self.assertTrue(match_lists_as_sets([cat, dog], cat.uaccess.get_resource_unshare_users(holes)))
        # the answer to the following should be dog, but cat is self-shared with the resource. Fixed.
        self.assertTrue(match_lists_as_sets([dog], cat.uaccess.get_resource_undo_users(holes)))
        self.assertTrue(match_lists_as_sets([], cat.uaccess.get_resource_unshare_groups(holes)))
        self.assertTrue(match_lists_as_sets([], cat.uaccess.get_resource_undo_groups(holes)))

        self.assertEqual(holes.raccess.get_owners().count(), 2)
        self.assertEqual(holes.raccess.get_holding_users().count(), 2)
        self.assertEqual(holes.raccess.get_holders().count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertTrue(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(dog.uaccess.can_change_resource_flags(holes))
        self.assertTrue(dog.uaccess.can_delete_resource(holes))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # test for idempotence
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.OWNER)

        self.assertTrue(match_lists_as_sets([cat,dog], holes.raccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat,dog], holes.raccess.get_holding_users()))
        self.assertTrue(match_lists_as_sets([], holes.raccess.get_holding_groups()))
        self.assertTrue(match_lists_as_sets([cat,dog], holes.raccess.get_holders()))

        self.assertEqual(holes.raccess.get_owners().count(), 2)
        self.assertEqual(holes.raccess.get_holding_users().count(), 2)
        self.assertEqual(holes.raccess.get_holders().count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertTrue(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(dog.uaccess.can_change_resource_flags(holes))
        self.assertTrue(dog.uaccess.can_delete_resource(holes))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # recheck metadata state: should not have changed
        self.assertFalse(holes.raccess.public)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.immutable)
        self.assertTrue(holes.raccess.shareable)


    def test_03_share_resource_rw(self):
        """Resources can be shared as CHANGE by owner"""
        holes = self.holes
        dog = self.dog
        cat = self.cat

        # initial state
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_holding_users()))
        self.assertTrue(match_lists_as_sets([], holes.raccess.get_holding_groups()))
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_holders()))

        self.assertEqual(holes.raccess.get_owners().count(), 1)
        self.assertEqual(holes.raccess.get_holding_users().count(), 1)
        self.assertEqual(holes.raccess.get_holders().count(), 1)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        self.assertFalse(cat.uaccess.can_undo_share_resource_with_user(holes, dog))
        self.assertFalse(cat.uaccess.can_unshare_resource_with_user(holes, dog))
        self.assertTrue(match_lists_as_sets([], cat.uaccess.get_resource_undo_users(holes)))
        self.assertTrue(match_lists_as_sets([], cat.uaccess.get_resource_unshare_users(holes)))

        # share with dog at rw privilege
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(cat.uaccess.can_undo_share_resource_with_user(holes, dog))
        self.assertTrue(cat.uaccess.can_unshare_resource_with_user(holes, dog))
        self.assertTrue(match_lists_as_sets([dog], cat.uaccess.get_resource_undo_users(holes)))
        self.assertTrue(match_lists_as_sets([dog], cat.uaccess.get_resource_unshare_users(holes)))

        # initial state
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat, dog], holes.raccess.get_holding_users()))
        self.assertTrue(match_lists_as_sets([], holes.raccess.get_holding_groups()))
        self.assertTrue(match_lists_as_sets([cat, dog], holes.raccess.get_holders()))

        self.assertEqual(holes.raccess.get_owners().count(), 1)
        self.assertEqual(holes.raccess.get_holding_users().count(), 2)
        self.assertEqual(holes.raccess.get_holders().count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # test for idempotence of sharing
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.CHANGE)

        # check for unchanged configuration
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat, dog], holes.raccess.get_holding_users()))
        self.assertTrue(match_lists_as_sets([], holes.raccess.get_holding_groups()))
        self.assertTrue(match_lists_as_sets([cat, dog], holes.raccess.get_holders()))

        self.assertEqual(holes.raccess.get_owners().count(), 1)
        self.assertEqual(holes.raccess.get_holding_users().count(), 2)
        self.assertEqual(holes.raccess.get_holders().count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # recheck metadata state
        self.assertFalse(holes.raccess.public)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.immutable)
        self.assertTrue(holes.raccess.shareable)

    def test_04_share_resource_ro(self):
        """Resources can be shared as VIEW by owner"""
        holes = self.holes
        dog = self.dog
        cat = self.cat

        # initial state
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_holding_users()))
        self.assertTrue(match_lists_as_sets([], holes.raccess.get_holding_groups()))
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_holders()))

        self.assertEqual(holes.raccess.get_owners().count(), 1)
        self.assertEqual(holes.raccess.get_holding_users().count(), 1)
        self.assertEqual(holes.raccess.get_holders().count(), 1)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # share with view privilege
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.VIEW)

        # shared state
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat, dog], holes.raccess.get_holding_users()))
        self.assertTrue(match_lists_as_sets([], holes.raccess.get_holding_groups()))
        self.assertTrue(match_lists_as_sets([cat, dog], holes.raccess.get_holders()))

        self.assertEqual(holes.raccess.get_owners().count(), 1)
        self.assertEqual(holes.raccess.get_holding_users().count(), 2)
        self.assertEqual(holes.raccess.get_holders().count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # check for idempotence
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.VIEW)

        # same state
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat, dog], holes.raccess.get_holding_users()))
        self.assertTrue(match_lists_as_sets([], holes.raccess.get_holding_groups()))
        self.assertTrue(match_lists_as_sets([cat, dog], holes.raccess.get_holders()))

        self.assertEqual(holes.raccess.get_owners().count(), 1)
        self.assertEqual(holes.raccess.get_holding_users().count(), 2)
        self.assertEqual(holes.raccess.get_holders().count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # recheck metadata state
        self.assertFalse(holes.raccess.public)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.immutable)
        self.assertTrue(holes.raccess.shareable)

        # ensure that nothing changed
        self.assertFalse(holes.raccess.public)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.immutable)
        self.assertTrue(holes.raccess.shareable)

    def test_05_share_resource_downgrade_privilege(self):
        """Resource sharing privileges can be downgraded by owner"""
        holes = self.holes
        dog = self.dog
        cat = self.cat
        mouse = self.mouse
        # initial state
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_holding_users()))
        self.assertTrue(match_lists_as_sets([], holes.raccess.get_holding_groups()))
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_holders()))

        self.assertEqual(holes.raccess.get_owners().count(), 1)
        self.assertEqual(holes.raccess.get_holding_users().count(), 1)
        self.assertEqual(holes.raccess.get_holders().count(), 1)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # share as owner
        self.cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.OWNER)

        self.assertTrue(match_lists_as_sets([cat,dog], holes.raccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat,dog], holes.raccess.get_holding_users()))
        self.assertTrue(match_lists_as_sets([], holes.raccess.get_holding_groups()))
        self.assertTrue(match_lists_as_sets([cat,dog], holes.raccess.get_holders()))

        self.assertEqual(holes.raccess.get_owners().count(), 2)
        self.assertEqual(holes.raccess.get_holding_users().count(), 2)
        self.assertEqual(holes.raccess.get_holders().count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertTrue(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))
        # composite django state
        self.assertTrue(dog.uaccess.can_change_resource_flags(holes))
        self.assertTrue(dog.uaccess.can_delete_resource(holes))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # metadata state
        self.assertFalse(holes.raccess.public)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.immutable)
        self.assertTrue(holes.raccess.shareable)

        # downgrade from OWNER to CHANGE
        self.cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.CHANGE)

        # check for correctness
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat, dog], holes.raccess.get_holding_users()))
        self.assertTrue(match_lists_as_sets([], holes.raccess.get_holding_groups()))
        self.assertTrue(match_lists_as_sets([cat, dog], holes.raccess.get_holders()))

        self.assertEqual(holes.raccess.get_owners().count(), 1)
        self.assertEqual(holes.raccess.get_holding_users().count(), 2)
        self.assertEqual(holes.raccess.get_holders().count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # downgrade from CHANGE to VIEW
        self.cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.VIEW)
        # initial state
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat, dog], holes.raccess.get_holding_users()))
        self.assertTrue(match_lists_as_sets([], holes.raccess.get_holding_groups()))
        self.assertTrue(match_lists_as_sets([cat, dog], holes.raccess.get_holders()))

        self.assertEqual(holes.raccess.get_owners().count(), 1)
        self.assertEqual(holes.raccess.get_holding_users().count(), 2)
        self.assertEqual(holes.raccess.get_holders().count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # downgrade to no privilege
        self.cat.uaccess.unshare_resource_with_user(holes, dog)

        # initial state
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_holding_users()))
        self.assertTrue(match_lists_as_sets([], holes.raccess.get_holding_groups()))
        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_holders()))

        self.assertEqual(holes.raccess.get_owners().count(), 1)
        self.assertEqual(holes.raccess.get_holding_users().count(), 1)
        self.assertEqual(holes.raccess.get_holders().count(), 1)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # set edit privilege for mouse on holes
        self.cat.uaccess.share_resource_with_user(holes, mouse, PrivilegeCodes.CHANGE)
        self.assertEqual(self.holes.raccess.get_combined_privilege(self.mouse), PrivilegeCodes.CHANGE)

        # set edit privilege for dog on holes
        self.cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.CHANGE)
        self.assertEqual(self.holes.raccess.get_combined_privilege(self.dog), PrivilegeCodes.CHANGE)

        # non owner (mouse) should not be able to downgrade privilege of dog from edit/change
        # (originally granted by cat) to view
        with self.assertRaises(PermissionDenied): 
            self.mouse.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.VIEW)

        # non owner (mouse) should be able to downgrade privilege of a user (dog) originally granted by the same
        # non owner (mouse)
        self.cat.uaccess.unshare_resource_with_user(holes, dog)
        self.assertEqual(self.holes.raccess.get_combined_privilege(self.dog), PrivilegeCodes.NONE)
        self.mouse.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.CHANGE)
        self.assertEqual(self.holes.raccess.get_combined_privilege(self.dog), PrivilegeCodes.CHANGE)
        self.mouse.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.VIEW)
        self.assertEqual(self.holes.raccess.get_combined_privilege(self.dog), PrivilegeCodes.VIEW)

        # django admin should be able to downgrade privilege
        self.cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.OWNER)
        self.assertTrue(dog.uaccess.can_change_resource_flags(holes))
        self.assertTrue(dog.uaccess.owns_resource(holes))

        self.admin.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.CHANGE)
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.owns_resource(holes))

    def test_06_group_unshared_state(self):
        """Groups cannot be accessed by users with no access"""
        # dog should not have sharing privileges
        meowers = self.meowers
        cat = self.cat
        dog = self.dog

        # privilege of owner
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        self.assertTrue(match_lists_as_sets([cat], meowers.gaccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat], meowers.gaccess.get_members()))
        self.assertTrue(match_lists_as_sets([], meowers.gaccess.get_held_resources()))

        # NOT ACCESS CONTROL: self.assertEqual(meowers.name, 'some random meowers')
        self.assertTrue(meowers.gaccess.public)
        self.assertTrue(meowers.gaccess.discoverable)
        self.assertTrue(meowers.gaccess.shareable)

        # privilege of other user
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

    def test_07_share_group_ownership(self):
        """Groups can be shared as OWNER by owner"""
        meowers = self.meowers
        dog = self.dog
        cat = self.cat

        self.assertTrue(match_lists_as_sets([cat], meowers.gaccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat], meowers.gaccess.get_members()))
        self.assertTrue(match_lists_as_sets([], meowers.gaccess.get_held_resources()))

        self.assertEqual(meowers.gaccess.get_owners().count(), 1)
        self.assertEqual(meowers.gaccess.get_members().count(), 1)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # share meowers with dog as owner
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.OWNER)

        self.assertTrue(match_lists_as_sets([cat,dog], meowers.gaccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat,dog], meowers.gaccess.get_members()))
        self.assertTrue(match_lists_as_sets([], meowers.gaccess.get_held_resources()))

        self.assertEqual(meowers.gaccess.get_owners().count(), 2)
        self.assertEqual(meowers.gaccess.get_members().count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertTrue(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state
        self.assertTrue(dog.uaccess.can_change_group_flags(meowers))
        self.assertTrue(dog.uaccess.can_delete_group(meowers))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # test for idempotence
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.OWNER)

        self.assertTrue(match_lists_as_sets([cat,dog], meowers.gaccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat,dog], meowers.gaccess.get_members()))
        self.assertTrue(match_lists_as_sets([], meowers.gaccess.get_held_resources()))

        self.assertEqual(meowers.gaccess.get_owners().count(), 2)
        self.assertEqual(meowers.gaccess.get_members().count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertTrue(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))

        # composite django state
        self.assertTrue(dog.uaccess.can_change_group_flags(meowers))
        self.assertTrue(dog.uaccess.can_delete_group(meowers))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # recheck metadata state: should not have changed
        self.assertTrue(meowers.gaccess.public)
        self.assertTrue(meowers.gaccess.discoverable)
        self.assertTrue(meowers.gaccess.shareable)

    def test_08_share_group_rw(self):
        """Groups can be shared as CHANGE by owner"""
        meowers = self.meowers
        dog = self.dog
        cat = self.cat

        # initial state
        self.assertTrue(match_lists_as_sets([cat], meowers.gaccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat], meowers.gaccess.get_members()))
        self.assertTrue(match_lists_as_sets([], meowers.gaccess.get_held_resources()))

        self.assertEqual(meowers.gaccess.get_owners().count(), 1)
        self.assertEqual(meowers.gaccess.get_members().count(), 1)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # share with dog at rw privilege
        self.assertFalse(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertFalse(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        self.assertTrue(match_lists_as_sets([], cat.uaccess.get_group_undo_users(meowers)))
        self.assertTrue(match_lists_as_sets([], cat.uaccess.get_group_unshare_users(meowers)))

        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.CHANGE)

        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        self.assertTrue(match_lists_as_sets([dog], cat.uaccess.get_group_undo_users(meowers)))
        self.assertTrue(match_lists_as_sets([dog], cat.uaccess.get_group_unshare_users(meowers)))

        # check other state for this change
        self.assertTrue(match_lists_as_sets([cat], meowers.gaccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat, dog], meowers.gaccess.get_members()))
        self.assertTrue(match_lists_as_sets([], meowers.gaccess.get_held_resources()))

        self.assertEqual(meowers.gaccess.get_owners().count(), 1)
        self.assertEqual(meowers.gaccess.get_members().count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # test for idempotence of sharing
        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        # check for unchanged configuration
        self.assertTrue(match_lists_as_sets([cat], meowers.gaccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat, dog], meowers.gaccess.get_members()))
        self.assertTrue(match_lists_as_sets([], meowers.gaccess.get_held_resources()))

        self.assertEqual(meowers.gaccess.get_owners().count(), 1)
        self.assertEqual(meowers.gaccess.get_members().count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # recheck metadata state
        self.assertTrue(meowers.gaccess.public)
        self.assertTrue(meowers.gaccess.discoverable)
        self.assertTrue(meowers.gaccess.shareable)

    def test_09_share_group_ro(self):
        """Groups can be shared as VIEW by owner"""
        meowers = self.meowers
        dog = self.dog
        cat = self.cat

        # initial state
        self.assertTrue(match_lists_as_sets([cat], meowers.gaccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat], meowers.gaccess.get_members()))
        self.assertTrue(match_lists_as_sets([], meowers.gaccess.get_held_resources()))

        self.assertEqual(meowers.gaccess.get_owners().count(), 1)
        self.assertEqual(meowers.gaccess.get_members().count(), 1)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # share with view privilege
        self.assertFalse(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertFalse(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.VIEW)

        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        # shared state
        self.assertTrue(match_lists_as_sets([cat], meowers.gaccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat, dog], meowers.gaccess.get_members()))
        self.assertTrue(match_lists_as_sets([], meowers.gaccess.get_held_resources()))

        self.assertEqual(meowers.gaccess.get_owners().count(), 1)
        self.assertEqual(meowers.gaccess.get_members().count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # check for idempotence
        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.VIEW)
        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        # shared state
        self.assertTrue(match_lists_as_sets([cat], meowers.gaccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat, dog], meowers.gaccess.get_members()))
        self.assertTrue(match_lists_as_sets([], meowers.gaccess.get_held_resources()))

        self.assertEqual(meowers.gaccess.get_owners().count(), 1)
        self.assertEqual(meowers.gaccess.get_members().count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # recheck metadata state
        self.assertTrue(meowers.gaccess.public)
        self.assertTrue(meowers.gaccess.discoverable)
        self.assertTrue(meowers.gaccess.shareable)

    def test_10_share_group_downgrade_privilege(self):
        """Group sharing privileges can be downgraded by owner"""
        meowers = self.meowers
        dog = self.dog
        cat = self.cat

        # initial state
        self.assertTrue(match_lists_as_sets([cat], meowers.gaccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat], meowers.gaccess.get_members()))
        self.assertTrue(match_lists_as_sets([], meowers.gaccess.get_held_resources()))

        self.assertEqual(meowers.gaccess.get_owners().count(), 1)
        self.assertEqual(meowers.gaccess.get_members().count(), 1)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # share as owner
        self.assertFalse(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertFalse(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.OWNER)
        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        self.assertTrue(match_lists_as_sets([cat,dog], meowers.gaccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat,dog], meowers.gaccess.get_members()))
        self.assertTrue(match_lists_as_sets([], meowers.gaccess.get_held_resources()))

        self.assertEqual(meowers.gaccess.get_owners().count(), 2)
        self.assertEqual(meowers.gaccess.get_members().count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertTrue(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertTrue(dog.uaccess.can_change_group_flags(meowers))
        self.assertTrue(dog.uaccess.can_delete_group(meowers))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # metadata state
        self.assertTrue(meowers.gaccess.public)
        self.assertTrue(meowers.gaccess.discoverable)
        self.assertTrue(meowers.gaccess.shareable)

        # downgrade from OWNER to CHANGE
        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        # check for correctness
        self.assertTrue(match_lists_as_sets([cat], meowers.gaccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat, dog], meowers.gaccess.get_members()))
        self.assertTrue(match_lists_as_sets([], meowers.gaccess.get_held_resources()))

        self.assertEqual(meowers.gaccess.get_owners().count(), 1)
        self.assertEqual(meowers.gaccess.get_members().count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # downgrade from CHANGE to VIEW
        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.VIEW)
        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        # initial state
        self.assertTrue(match_lists_as_sets([cat], meowers.gaccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat, dog], meowers.gaccess.get_members()))
        self.assertTrue(match_lists_as_sets([], meowers.gaccess.get_held_resources()))

        self.assertEqual(meowers.gaccess.get_owners().count(), 1)
        self.assertEqual(meowers.gaccess.get_members().count(), 2)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # downgrade to no privilege
        self.assertTrue(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertTrue(cat.uaccess.can_unshare_group_with_user(meowers, dog))
        # TODO: test undo_share
        cat.uaccess.unshare_group_with_user(meowers, dog)
        self.assertFalse(cat.uaccess.can_undo_share_group_with_user(meowers, dog))
        self.assertFalse(cat.uaccess.can_unshare_group_with_user(meowers, dog))

        # back to initial state
        self.assertTrue(match_lists_as_sets([cat], meowers.gaccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat], meowers.gaccess.get_members()))
        self.assertTrue(match_lists_as_sets([], meowers.gaccess.get_held_resources()))

        self.assertEqual(meowers.gaccess.get_owners().count(), 1)
        self.assertEqual(meowers.gaccess.get_members().count(), 1)

        # simple privilege for cat
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))
        # composite django state
        self.assertTrue(cat.uaccess.can_change_group_flags(meowers))
        self.assertTrue(cat.uaccess.can_delete_group(meowers))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # simple privilege for dog
        self.assertFalse(dog.uaccess.owns_group(meowers))
        self.assertFalse(dog.uaccess.can_change_group(meowers))
        self.assertTrue(dog.uaccess.can_view_group(meowers))
        # composite django state
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.can_delete_group(meowers))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_group(meowers, PrivilegeCodes.VIEW))

        # admin too should be able to downgrade (e.g. from OWNER to CHANGE)
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.OWNER)
        self.assertTrue(dog.uaccess.owns_group(meowers))
        self.assertTrue(dog.uaccess.can_change_group_flags(meowers))

        self.admin.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.CHANGE)
        self.assertFalse(dog.uaccess.can_change_group_flags(meowers))
        self.assertFalse(dog.uaccess.owns_group(meowers))

    def test_11_resource_sharing_with_group(self):
        """Group cannot own a resource"""
        meowers = self.meowers
        holes = self.holes
        dog = self.dog
        cat = self.cat

        self.assertTrue(match_lists_as_sets([cat], meowers.gaccess.get_owners()))

        self.assertEqual(meowers.gaccess.get_owners().count(), 1)
        # make dog a co-owner
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.OWNER) # make dog a co-owner
        self.assertTrue(match_lists_as_sets([cat, dog], meowers.gaccess.get_owners()))
        self.assertEqual(meowers.gaccess.get_owners().count(), 2)
        # repeating the command should be idempotent
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.OWNER) # make dog a co-owner
        self.assertTrue(match_lists_as_sets([cat, dog], meowers.gaccess.get_owners()))
        self.assertEqual(meowers.gaccess.get_owners().count(), 2)

        self.assertTrue(match_lists_as_sets([cat], holes.raccess.get_owners()))

        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(cat.uaccess.can_unshare_resource_with_user(holes, dog))
        self.assertFalse(cat.uaccess.can_undo_share_resource_with_user(holes, dog))
        self.assertTrue(match_lists_as_sets([], cat.uaccess.get_resource_undo_users(holes)))

        self.assertTrue(match_lists_as_sets([], cat.uaccess.get_resource_unshare_users(holes)))

        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.OWNER)

        self.assertTrue(match_lists_as_sets([cat, dog], holes.raccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat, dog], holes.raccess.get_holders()))
        self.assertTrue(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.owns_group(meowers))

        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_unshare_resource_with_user(holes, dog))
        self.assertTrue(cat.uaccess.can_undo_share_resource_with_user(holes, dog))
        # dog is an owner; owner rule no longer applies!
        self.assertTrue(cat.uaccess.can_unshare_resource_with_user(holes, cat))
        self.assertFalse(cat.uaccess.can_undo_share_resource_with_user(holes, cat))
        self.assertTrue(dog.uaccess.can_unshare_resource_with_user(holes, dog))
        self.assertFalse(dog.uaccess.can_undo_share_resource_with_user(holes, dog))
        self.assertTrue(dog.uaccess.can_unshare_resource_with_user(holes, cat))
        self.assertFalse(dog.uaccess.can_undo_share_resource_with_user(holes, cat))

        # test list access functions for unshare targets
        self.assertTrue(match_lists_as_sets([dog], cat.uaccess.get_resource_undo_users(holes)))
        self.assertTrue(match_lists_as_sets([cat, dog], cat.uaccess.get_resource_unshare_users(holes)))

        # the following is correct only because  dog is an owner of holes
        self.assertTrue(match_lists_as_sets([cat], dog.uaccess.get_resource_undo_users(holes)))
        self.assertTrue(match_lists_as_sets([cat, dog], dog.uaccess.get_resource_unshare_users(holes)))

        # test idempotence of sharing
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.OWNER)
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(cat.uaccess.can_unshare_resource_with_user(holes, dog))
        self.assertTrue(cat.uaccess.can_undo_share_resource_with_user(holes, dog))
        self.assertTrue(match_lists_as_sets([cat, dog], holes.raccess.get_owners()))
        self.assertTrue(match_lists_as_sets([cat, dog], holes.raccess.get_holders()))
        self.assertTrue(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.owns_group(meowers))

        # owner dog of meowers tries to make holes owned by group meowers
        with self.assertRaises(PermissionDenied) as cm:
            dog.uaccess.share_resource_with_group(holes, meowers, PrivilegeCodes.OWNER)
        self.assertEqual(cm.exception.message, 'Groups cannot own resources')

        # even django admin can't make a group as the owner of a resource
        with self.assertRaises(PermissionDenied) as cm:
            self.admin.uaccess.share_resource_with_group(holes, meowers, PrivilegeCodes.OWNER)
        self.assertEqual(cm.exception.message, 'Groups cannot own resources')

    def test_12_resource_sharing_rw_with_group(self):
        """Resource can be shared as CHANGE with a group"""
        dog = self.dog
        cat = self.cat
        holes = self.holes
        meowers = self.meowers

        # now share something with dog via group meowers
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(match_lists_as_sets([cat, dog], meowers.gaccess.get_members().all()))

        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(cat.uaccess.can_unshare_resource_with_group(holes, meowers))
        self.assertFalse(cat.uaccess.can_undo_share_resource_with_group(holes, meowers))
        cat.uaccess.share_resource_with_group(holes, meowers, PrivilegeCodes.CHANGE)
        self.assertTrue(cat.uaccess.can_unshare_resource_with_group(holes, meowers))
        self.assertTrue(cat.uaccess.can_undo_share_resource_with_group(holes, meowers))
        self.assertTrue(match_lists_as_sets([cat, dog], holes.raccess.get_holders()))

        # simple sharing state
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertTrue(dog.uaccess.can_change_resource(holes))
        self.assertTrue(dog.uaccess.can_view_resource(holes))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))

        # turn off group sharing
        cat.uaccess.unshare_resource_with_group(holes, meowers)
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertTrue(cat.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(cat.uaccess.can_unshare_resource_with_group(holes, meowers))
        self.assertFalse(cat.uaccess.can_undo_share_resource_with_group(holes, meowers))

        # simple sharing state
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))

        # composite django state
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.OWNER))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.CHANGE))
        self.assertFalse(dog.uaccess.can_share_resource(holes, PrivilegeCodes.VIEW))


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
        self.assertTrue(cat in polyamory.gaccess.get_members())

        # ensure that this group was created and current user is a member
        self.assertTrue(match_lists_as_sets([polyamory], cat.uaccess.get_held_groups()))

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
        self.assertTrue(match_lists_as_sets([], dog.uaccess.get_held_groups()))

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


class T08ResourceFlags(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(T08ResourceFlags, self).setUp()
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

        self.bones = hydroshare.create_resource(resource_type='GenericResource',
                                                owner=self.dog,
                                                title='all about dog bones',
                                                metadata=[],)

        self.chewies = hydroshare.create_resource(resource_type='GenericResource',
                                                  owner=self.dog,
                                                  title='all about dog chewies',
                                                  metadata=[],)

    def test_01_default_flags(self):
        "Flag defaults are correct when resource is created"
        bones = self.bones

        # are resources created with correct defaults?
        self.assertFalse(bones.raccess.immutable)
        self.assertFalse(bones.raccess.public)
        self.assertFalse(bones.raccess.published)
        self.assertFalse(bones.raccess.discoverable)
        self.assertTrue(bones.raccess.shareable)

    def test_02_shareable(self):
        "Resource shareable flag enables resource sharing"
        cat = self.cat
        bones = self.bones
        dog = self.dog

        # make bones not shareable
        bones.raccess.shareable = False
        bones.raccess.save()

        # are resource flags correct?
        self.assertFalse(bones.raccess.immutable)
        self.assertFalse(bones.raccess.public)
        self.assertFalse(bones.raccess.published)
        self.assertFalse(bones.raccess.discoverable)
        self.assertFalse(bones.raccess.shareable)

        # dog is an owner, should be able to share even if shareable is False
        dog.uaccess.share_resource_with_user(bones, cat, PrivilegeCodes.VIEW)

        # should get some privilege, but not an owner of bones
        self.assertFalse(cat.uaccess.owns_resource(bones))
        self.assertFalse(cat.uaccess.can_change_resource(bones))
        self.assertTrue(cat.uaccess.can_view_resource(bones))

        # django admin should be able share even if shareable is False
        self.admin.uaccess.share_resource_with_user(bones, cat, PrivilegeCodes.CHANGE)

    def test_03_not_shareable(self):
        "Resource that is not shareable cannot be shared by non-owner"
        cat = self.cat
        dog = self.dog
        bones = self.bones
        bat = self.bat
        bones.raccess.shareable = False
        bones.raccess.save()

        dog.uaccess.share_resource_with_user(bones, cat, PrivilegeCodes.VIEW)

        # cat should not be able to reshare
        with self.assertRaises(PermissionDenied) as cm:
            cat.uaccess.share_resource_with_user(bones, bat, PrivilegeCodes.VIEW)
        self.assertEqual(cm.exception.message, 'User must own resource or have sharing privilege')

        # django admin still can share
        self.admin.uaccess.share_resource_with_user(bones, bat, PrivilegeCodes.VIEW)

    def test_04_transitive_sharing(self):
        """Resource shared with one user can be shared with another"""
        cat = self.cat
        dog = self.dog
        bones = self.bones
        bat = self.bat

        self.assertFalse(bones.raccess.immutable)
        self.assertFalse(bones.raccess.public)
        self.assertFalse(bones.raccess.published)
        self.assertFalse(bones.raccess.discoverable)
        self.assertTrue(bones.raccess.shareable)

        # first share
        dog.uaccess.share_resource_with_user(bones, cat, PrivilegeCodes.VIEW)
        self.assertFalse(cat.uaccess.owns_resource(bones))
        self.assertFalse(cat.uaccess.can_change_resource(bones))
        self.assertTrue(cat.uaccess.can_view_resource(bones))

        # now cat should be able to share with bat
        cat.uaccess.share_resource_with_user(bones, bat, PrivilegeCodes.VIEW)
        self.assertFalse(bat.uaccess.owns_resource(bones))
        self.assertFalse(bat.uaccess.can_change_resource(bones))
        self.assertTrue(bat.uaccess.can_view_resource(bones))

    def test_05_discoverable(self):
        """Resource can be made discoverable"""
        bones = self.bones

        # can I change discoverable?
        bones.raccess.discoverable = True
        bones.raccess.save()

        self.assertFalse(bones.raccess.immutable)
        self.assertFalse(bones.raccess.public)
        self.assertFalse(bones.raccess.published)
        self.assertTrue(bones.raccess.discoverable)
        self.assertTrue(bones.raccess.shareable)

        self.assertTrue(match_lists_as_sets([bones], GenericResource.discoverable_resources.all()))

    def test_06_not_discoverable(self):
        """Resource can be made not discoverable and not public"""
        bones = self.bones

        bones.raccess.discoverable = False
        bones.raccess.public = False
        bones.raccess.save()

        self.assertFalse(bones.raccess.immutable)
        self.assertFalse(bones.raccess.public)
        self.assertFalse(bones.raccess.published)
        self.assertFalse(bones.raccess.discoverable)
        self.assertTrue(bones.raccess.shareable)

        names = GenericResource.discoverable_resources.all()
        self.assertEqual(names.count(), 0)

    def test_07_immutable(self):
        """An immutable resource cannot be changed"""
        bones = self.bones
        dog = self.dog
        nobody = self.nobody

        bones.raccess.immutable = True
        bones.raccess.save()

        self.assertTrue(bones.raccess.immutable)
        self.assertFalse(bones.raccess.public)
        self.assertFalse(bones.raccess.published)
        self.assertFalse(bones.raccess.discoverable)
        self.assertTrue(bones.raccess.shareable)

        # ownership should survive downgrading to immutable; otherwise one cuts out ownership privilege completely
        self.assertTrue(dog.uaccess.owns_resource(bones))
        self.assertFalse(dog.uaccess.can_change_resource(bones))
        self.assertTrue(dog.uaccess.can_view_resource(bones))

        # even django admin should not be able to change an immutable resource
        self.assertFalse(self.admin.uaccess.can_change_resource(bones))
        self.assertTrue(self.admin.uaccess.can_view_resource(bones))

        # another user shouldn't be able to read it unless it's also public
        self.assertFalse(nobody.uaccess.owns_resource(bones))
        self.assertFalse(nobody.uaccess.can_change_resource(bones))
        self.assertFalse(nobody.uaccess.can_view_resource(bones))

        # undo immutable
        bones.raccess.immutable = False
        bones.raccess.save()

        self.assertFalse(bones.raccess.immutable)
        self.assertFalse(bones.raccess.public)
        self.assertFalse(bones.raccess.published)
        self.assertFalse(bones.raccess.discoverable)
        self.assertTrue(bones.raccess.shareable)

        # should restore readwrite to owner
        self.assertTrue(dog.uaccess.owns_resource(bones))
        self.assertTrue(dog.uaccess.can_change_resource(bones))
        self.assertTrue(dog.uaccess.can_view_resource(bones))

    def test_08_public(self):
        """Public resources show up in public listings"""
        chewies = self.chewies
        dog = self.dog
        nobody = self.nobody

        self.assertFalse(chewies.raccess.immutable)
        self.assertFalse(chewies.raccess.public)
        self.assertFalse(chewies.raccess.published)
        self.assertFalse(chewies.raccess.discoverable)
        self.assertTrue(chewies.raccess.shareable)

        chewies.raccess.public = True
        chewies.raccess.save()

        self.assertFalse(chewies.raccess.immutable)
        self.assertTrue(chewies.raccess.public)
        self.assertFalse(chewies.raccess.published)
        self.assertFalse(chewies.raccess.discoverable)
        self.assertTrue(chewies.raccess.shareable)

        self.assertTrue(match_lists_as_sets([chewies], GenericResource.public_resources.all()))
        self.assertTrue(match_lists_as_sets([chewies], GenericResource.discoverable_resources.all()))

        # can 'nobody' see the public resource owned by 'dog'
        # but not explicitly shared with 'nobody'.
        self.assertTrue(nobody.uaccess.can_view_resource(chewies))
        self.assertFalse(nobody.uaccess.can_change_resource(chewies))
        self.assertFalse(nobody.uaccess.owns_resource(chewies))

    def test_08_discoverable(self):
        """Discoverable resources show up in discoverable resource listings"""
        chewies = self.chewies
        nobody = self.nobody

        # test making a resource public
        self.assertFalse(chewies.raccess.immutable)
        self.assertFalse(chewies.raccess.public)
        self.assertFalse(chewies.raccess.published)
        self.assertFalse(chewies.raccess.discoverable)
        self.assertTrue(chewies.raccess.shareable)

        chewies.raccess.discoverable = True
        chewies.raccess.save()

        self.assertFalse(chewies.raccess.immutable)
        self.assertFalse(chewies.raccess.public)
        self.assertFalse(chewies.raccess.published)
        self.assertTrue(chewies.raccess.discoverable)
        self.assertTrue(chewies.raccess.shareable)

        # discoverable doesn't mean public
        # TODO: get_public_resources and get_discoverable_resources should be static methods
        self.assertTrue(match_lists_as_sets([], GenericResource.public_resources.all()))
        self.assertTrue(match_lists_as_sets([chewies], GenericResource.discoverable_resources.all()))

        # can 'nobody' see the public resource owned by 'dog' but not explicitly shared with 'nobody'.
        self.assertFalse(nobody.uaccess.owns_resource(chewies))
        self.assertFalse(nobody.uaccess.can_change_resource(chewies))
        self.assertFalse(nobody.uaccess.can_view_resource(chewies))

    def test_09_retract(self):
        """Retracted resources cannot be accessed"""
        chewies = self.chewies

        # test whether we can retract a resource
        resource_short_id = chewies.short_id
        hydroshare.delete_resource(chewies.short_id)

        with self.assertRaises(Http404):
            hydroshare.get_resource(resource_short_id)


class T09GroupSharing(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(T09GroupSharing, self).setUp()
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

    def test_00_defaults(self):
        """Defaults are correct when creating groups"""
        scratching = self.scratching
        felines = self.felines
        dog = self.dog
        cat = self.cat

        # TODO: check for group existence via uuid handle

        self.assertTrue(felines.gaccess.discoverable)
        self.assertTrue(felines.gaccess.public)
        self.assertTrue(felines.gaccess.shareable)

        self.assertTrue(dog.uaccess.owns_group(felines))
        self.assertTrue(dog.uaccess.can_change_group(felines))
        self.assertTrue(dog.uaccess.can_view_group(felines))

        self.assertTrue(dog.uaccess.can_view_resource(scratching))
        self.assertTrue(dog.uaccess.can_change_resource(scratching))
        self.assertTrue(dog.uaccess.owns_resource(scratching))

    def test_01_cannot_share_own(self):
        """Groups cannot 'own' resources"""
        scratching = self.scratching
        felines = self.felines
        dog = self.dog
        with self.assertRaises(PermissionDenied) as cm:
            dog.uaccess.share_resource_with_group(scratching, felines, PrivilegeCodes.OWNER)
        self.assertEqual(cm.exception.message, 'Groups cannot own resources')

    def test_02_share_rw(self):
        """An owner can share with CHANGE privileges"""
        scratching = self.scratching
        felines = self.felines
        dog = self.dog
        cat = self.cat
        nobody = self.nobody

        dog.uaccess.share_resource_with_group(scratching, felines, PrivilegeCodes.CHANGE)

        # is the resource just shared with this group?
        self.assertEqual(felines.gaccess.get_held_resources().count(), 1)
        self.assertTrue(match_lists_as_sets([scratching], felines.gaccess.get_held_resources()))

        # check that flags haven't changed
        self.assertTrue(felines.gaccess.discoverable)
        self.assertTrue(felines.gaccess.public)
        self.assertTrue(cat.uaccess.can_view_group(felines))
        self.assertFalse(cat.uaccess.can_change_group(felines))
        self.assertFalse(cat.uaccess.owns_group(felines))

        self.assertFalse(cat.uaccess.owns_resource(scratching))
        self.assertTrue(cat.uaccess.can_change_resource(scratching))
        self.assertTrue(cat.uaccess.can_view_resource(scratching))

        # todo: check advanced sharing semantics:
        # should be able to unshare anything one shared.

        with self.assertRaises(PermissionDenied) as cm:
            nobody.uaccess.unshare_resource_with_group(scratching, felines)
        self.assertEqual(cm.exception.message, 'Insufficient privilege to unshare resource')

        dog.uaccess.unshare_resource_with_group(scratching, felines)
        self.assertEqual(felines.gaccess.get_held_resources().count(), 0)


class T10GroupFlags(MockIRODSTestCaseMixin, TestCase):
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
        self.assertEqual(felines.gaccess.get_owners().count(), 1)

        # try to downgrade your own privilege
        with self.assertRaises(PermissionDenied) as cm:
            dog.uaccess.share_group_with_user(felines, dog, PrivilegeCodes.VIEW)
        self.assertEqual(cm.exception.message, 'Cannot remove last owner of group')

    def test_01_remove_last_owner_of_resource(self):
        """Cannot remove last owner of a resource"""
        scratching = self.scratching
        dog = self.dog
        self.assertTrue(dog.uaccess.owns_resource(scratching))
        self.assertEqual(scratching.raccess.get_owners().count(), 1)

        # try to downgrade your own privilege
        with self.assertRaises(PermissionDenied) as cm:
            dog.uaccess.share_resource_with_user(scratching, dog, PrivilegeCodes.VIEW)
        self.assertEqual(cm.exception.message, 'Cannot remove last owner of resource')


class T13Delete(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(T13Delete, self).setUp()
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

        self.wombat = hydroshare.create_account(
            'wombat@gmail.com',
            username='wombat',
            first_name='some random ombat',
            last_name='last_name_wombat',
            superuser=False,
            groups=[]
        )

        self.verdi = hydroshare.create_resource(resource_type='GenericResource',
                                                owner=self.dog,
                                                title='Guiseppe Verdi',
                                                metadata=[],)

        self.operas = self.dog.uaccess.create_group("operas")
        self.dog.uaccess.share_resource_with_user(self.verdi, self.cat, PrivilegeCodes.CHANGE)
        self.dog.uaccess.share_resource_with_group(self.verdi, self.operas, PrivilegeCodes.CHANGE)
        self.singers = self.dog.uaccess.create_group('singers')
        self.dog.uaccess.share_group_with_user(self.singers, self.cat, PrivilegeCodes.CHANGE)

    # def test_01_delete_resource(self):
    #     """Delete works for resources: privileges are deleted with resource"""
    #     verdi = self.verdi
    #     dog = self.dog
    #     self.assertTrue(dog.uaccess.can_delete_resource(verdi))
    #     hydroshare.delete_resource(verdi.short_id)
    #     self.assertFalse(dog.uaccess.can_delete_resource(verdi))

    def test_02_delete_group(self):
        """Delete works for groups: privileges are deleted with group"""

        dog = self.dog
        singers = self.singers
        self.assertTrue(dog.uaccess.can_delete_group(singers))
        dog.uaccess.delete_group(singers)
        self.assertFalse(dog.uaccess.can_delete_group(singers))


class T15CreateGroup(MockIRODSTestCaseMixin, TestCase):
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
        """Defaults for group ownership are correct"""
        cat = self.cat
        meowers = self.meowers
        self.assertTrue(cat.uaccess.owns_group(meowers))
        self.assertTrue(cat.uaccess.can_change_group(meowers))
        self.assertTrue(cat.uaccess.can_view_group(meowers))
        self.assertTrue(meowers.gaccess.public)
        self.assertTrue(meowers.gaccess.discoverable)
        self.assertTrue(meowers.gaccess.shareable)

    def test_02_default_group_isolation(self):
        """Users with no contact with the group have appropriate permissions"""
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
        """Can make a group not public"""
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
        """Can make a group not discoverable"""
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
        """Resources cannot be accessed by users with no access"""
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
        self.assertTrue(match_lists_as_sets(foo, [r1_resource, r2_resource, r3_resource]))
        foo = A_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
        self.assertTrue(match_lists_as_sets(foo, []))
        foo = A_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(foo, []))
        foo = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)
        self.assertTrue(match_lists_as_sets(foo, [r1_resource, r2_resource, r3_resource]))
        foo = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
        self.assertTrue(match_lists_as_sets(foo, []))
        foo = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(foo, []))

        A_user.uaccess.share_resource_with_user(r1_resource, B_user, PrivilegeCodes.OWNER)
        A_user.uaccess.share_resource_with_user(r2_resource, B_user, PrivilegeCodes.CHANGE)
        A_user.uaccess.share_resource_with_user(r3_resource, B_user, PrivilegeCodes.VIEW)
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)
        self.assertTrue(match_lists_as_sets(foo, [r1_resource]))
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
        self.assertTrue(match_lists_as_sets(foo, [r2_resource]))
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(foo, [r3_resource]))

        # higher privileges are deleted when lower privileges are granted
        C_user.uaccess.share_resource_with_user(r1_resource, B_user, PrivilegeCodes.VIEW)
        C_user.uaccess.share_resource_with_user(r2_resource, B_user, PrivilegeCodes.VIEW)
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)
        self.assertTrue(match_lists_as_sets(foo, []))    # [r1_resource]
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
        self.assertTrue(match_lists_as_sets(foo, []))    # [r2_resource]
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)

        self.assertTrue(match_lists_as_sets(foo, [r1_resource, r2_resource, r3_resource]))
        C_user.uaccess.share_resource_with_user(r1_resource, B_user, PrivilegeCodes.CHANGE)
        C_user.uaccess.share_resource_with_user(r2_resource, B_user, PrivilegeCodes.CHANGE)
        C_user.uaccess.share_resource_with_user(r3_resource, B_user, PrivilegeCodes.CHANGE)

        # higher privilege gets deleted when a lower privilege is granted
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)
        self.assertTrue(match_lists_as_sets(foo, []))    # [r1_resource]
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
        self.assertTrue(match_lists_as_sets(foo, [r1_resource, r2_resource, r3_resource]))
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(foo, []))

        # go from lower privilege to higher
        C_user.uaccess.share_resource_with_user(r1_resource, B_user, PrivilegeCodes.VIEW)
        C_user.uaccess.share_resource_with_user(r2_resource, B_user, PrivilegeCodes.VIEW)
        C_user.uaccess.share_resource_with_user(r3_resource, B_user, PrivilegeCodes.VIEW)

        A_user.uaccess.share_resource_with_user(r1_resource, B_user, PrivilegeCodes.CHANGE)
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
        self.assertTrue(match_lists_as_sets(foo, [r1_resource]))
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(foo, [r2_resource, r3_resource]))

        A_user.uaccess.share_resource_with_user(r1_resource, B_user, PrivilegeCodes.OWNER)
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)
        self.assertTrue(match_lists_as_sets(foo, [r1_resource]))
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(foo, [r2_resource, r3_resource]))

        # go lower to higher
        C_user.uaccess.share_resource_with_user(r1_resource, B_user, PrivilegeCodes.VIEW)
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)
        self.assertTrue(match_lists_as_sets(foo, []))
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
        self.assertTrue(match_lists_as_sets(foo, []))
        foo = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
        self.assertTrue(match_lists_as_sets(foo, [r1_resource, r2_resource, r3_resource]))

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
        """All user routines raise PermissionDenied if user is inactive"""
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
            foo = cat.uaccess.get_held_groups()
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.get_owned_groups()
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.owns_group(felines)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.can_change_group(felines)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.can_view_group(felines)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.can_view_group_metadata(felines)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.can_change_group_flags(felines)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.can_delete_group(felines)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.can_share_group(felines, PrivilegeCodes.VIEW)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.share_group_with_user(felines, dog, PrivilegeCodes.VIEW)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.unshare_group_with_user(felines, dog)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.can_unshare_group_with_user(felines, dog)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.undo_share_group_with_user(felines, dog)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.can_undo_share_group_with_user(felines, dog)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.get_group_undo_users(felines)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.get_group_unshare_users(felines)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.get_held_resources()
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.get_owned_resources()
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.get_editable_resources()
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.owns_resource(scratching)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.can_change_resource(scratching)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.can_change_resource_flags(scratching)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.can_view_resource(scratching)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.can_delete_resource(scratching)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.can_share_resource(scratching, PrivilegeCodes.VIEW)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.can_share_resource_with_group(scratching, felines, PrivilegeCodes.VIEW)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.undo_share_resource_with_group(scratching, felines)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.can_undo_share_resource_with_group(scratching, felines)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.share_resource_with_user(scratching, dog, PrivilegeCodes.VIEW)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.unshare_resource_with_user(scratching, dog)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.can_unshare_resource_with_user(scratching, dog)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.undo_share_resource_with_user(scratching, dog)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.can_undo_share_resource_with_user(scratching, dog)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.share_resource_with_group(scratching, felines, PrivilegeCodes.VIEW)
        with self.assertRaises(PermissionDenied): 
            cat.uaccess.unshare_resource_with_group(scratching, felines)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.can_unshare_resource_with_group(scratching, felines)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.get_resource_undo_users(scratching)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.get_resource_unshare_users(scratching)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.get_resource_undo_groups(scratching)
        with self.assertRaises(PermissionDenied): 
            foo = cat.uaccess.get_resource_unshare_groups(scratching)

    def test_01_reporting(self):
        """User records disappear when user is inactive"""
        scratching = self.scratching
        felines = self.felines
        dog = self.dog
        cat = self.cat

        cat.uaccess.share_resource_with_user(scratching, dog, PrivilegeCodes.OWNER) 
        cat.uaccess.share_group_with_user(felines, dog, PrivilegeCodes.OWNER) 

        self.assertTrue(match_lists_as_sets(cat.uaccess.get_group_unshare_users(felines), [cat, dog]))
        self.assertTrue(match_lists_as_sets(cat.uaccess.get_group_undo_users(felines), [dog]))
        self.assertTrue(match_lists_as_sets(cat.uaccess.get_resource_undo_users(scratching), [dog]))
        self.assertTrue(match_lists_as_sets(cat.uaccess.get_resource_unshare_users(scratching), [cat, dog]))

        self.assertTrue(match_lists_as_sets(felines.gaccess.get_members(), [cat, dog]))
        self.assertTrue(match_lists_as_sets(felines.gaccess.get_owners(), [cat, dog]))

        self.assertTrue(match_lists_as_sets(scratching.raccess.get_holding_users(), [cat, dog]))
        self.assertTrue(match_lists_as_sets(scratching.raccess.view_users, [cat, dog]))
        self.assertTrue(match_lists_as_sets(scratching.raccess.edit_users, [cat, dog]))
        self.assertTrue(match_lists_as_sets(scratching.raccess.owners, [cat, dog]))
        self.assertTrue(match_lists_as_sets(scratching.raccess.get_owners(), [cat, dog]))
        self.assertTrue(match_lists_as_sets(scratching.raccess.get_holders(), [cat, dog]))

        dog.is_active=False
        dog.save()

        self.assertTrue(match_lists_as_sets(cat.uaccess.get_group_unshare_users(felines), []))
        self.assertTrue(match_lists_as_sets(cat.uaccess.get_group_undo_users(felines), []))
        self.assertTrue(match_lists_as_sets(cat.uaccess.get_resource_undo_users(scratching), []))
        self.assertTrue(match_lists_as_sets(cat.uaccess.get_resource_unshare_users(scratching), []))

        self.assertTrue(match_lists_as_sets(felines.gaccess.get_members(), [cat]))
        self.assertTrue(match_lists_as_sets(felines.gaccess.get_owners(), [cat]))

        self.assertTrue(match_lists_as_sets(scratching.raccess.get_holding_users(), [cat]))
        self.assertTrue(match_lists_as_sets(scratching.raccess.view_users, [cat]))
        self.assertTrue(match_lists_as_sets(scratching.raccess.edit_users, [cat]))
        self.assertTrue(match_lists_as_sets(scratching.raccess.owners, [cat]))
        self.assertTrue(match_lists_as_sets(scratching.raccess.get_owners(), [cat]))
        self.assertTrue(match_lists_as_sets(scratching.raccess.get_holders(), [cat]))

