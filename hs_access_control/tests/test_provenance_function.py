__author__ = 'Alva'

import unittest
from django.http import Http404
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User, Group
from pprint import pprint

from hs_access_control.models import UserAccess, GroupAccess, ResourceAccess, \
    UserResourceProvenance, UserResourcePrivilege, \
    GroupResourceProvenance, GroupResourcePrivilege, \
    UserGroupProvenance, UserGroupPrivilege, \
    PrivilegeCodes, ProvenanceCodes

from hs_core import hydroshare
from hs_core.models import GenericResource, BaseResource
from hs_core.testing import MockIRODSTestCaseMixin

from hs_access_control.tests.utilities import *


def test_provenance_synchronization(self):
    for u in User.objects.all():
        for r in BaseResource.objects.all():
            prov = UserResourceProvenance.get_privilege(resource=r, user=u)
            priv = UserResourcePrivilege.get_privilege(resource=r, user=u)
            self.assertEqual(prov, priv)
    for u in User.objects.all():
        for g in Group.objects.all():
            prov = UserGroupProvenance.get_privilege(group=g, user=u)
            priv = UserGroupPrivilege.get_privilege(group=g, user=u)
            self.assertEqual(prov, priv)
    for g in Group.objects.all():
        for r in BaseResource.objects.all():
            prov = GroupResourceProvenance.get_privilege(resource=r, group=g)
            priv = GroupResourcePrivilege.get_privilege(resource=r, group=g)
            self.assertEqual(prov, priv)


def printGroupResourceState():
    print "==================================="
    print "GroupResourcePrivilege"
    priv = GroupResourcePrivilege.objects.all().order_by('group__id', 'resource__id')
    o = None
    for p in priv:
        if o is not None and (p.group != o.group or p.resource != o.resource):
            print "------------------------------"
        print(p)
        o = p
    print "==================================="
    print "GroupResourceProvenance"
    prov = GroupResourceProvenance.objects.all().order_by(
        'group__id', 'resource__id', 'start')
    o = None
    for p in prov:
        if o is not None and (p.group != o.group or p.resource != o.resource):
            print "------------------------------"
        current = GroupResourceProvenance.get_current_record(
            resource=p.resource, group=p.group)
        star = ''
        if current == p:
            star = 'CURRENT'
        print(p, star)
        o = p


def printUserResourceState():
    print "==================================="
    print "UserResourcePrivilege"
    priv = UserResourcePrivilege.objects.all().order_by('user__id', 'resource__id')
    o = None
    for p in priv:
        if o is not None and (p.user != o.user or p.resource != o.resource):
            print "------------------------------"
        print(p)
        o = p
    print "==================================="
    print "UserResourceProvenance"
    prov = UserResourceProvenance.objects.all().order_by(
        'user__id', 'resource__id', 'start')
    o = None
    for p in prov:
        if o is not None and (p.user != o.user or p.resource != o.resource):
            print "------------------------------"
        current = UserResourceProvenance.get_current_record(
            resource=p.resource, user=p.user)
        star = ''
        if current == p:
            star = 'CURRENT'
        print(p, star)
        o = p


def printUserGroupState():
    print "==================================="
    print "UserGroupPrivilege"
    priv = UserGroupPrivilege.objects.all().order_by('user__id', 'group__id')
    o = None
    for p in priv:
        if o is not None and (p.user != o.user or p.group != o.group):
            print "------------------------------"
        pprint(p)
        o = p
    print "==================================="
    print "UserGroupProvenance"
    prov = UserGroupProvenance.objects.all().order_by(
        'user__id', 'group__id', 'start')
    o = None
    for p in prov:
        if o is not None and (p.user != o.user or p.group != o.group):
            print "------------------------------"
        current = UserGroupProvenance.get_current_record(
            group=p.group, user=p.user)
        star = ''
        if current == p:
            star = 'CURRENT'
        print(p, star)
        o = p


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

        # george creates a entity 'bikes'
        self.bikes = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.george,
            title='Bikes',
            metadata=[],
        )

        # george creates a entity 'bikers'
        self.bikers = self.george.uaccess.create_group('Bikers')

        # george creates a entity 'harps'
        self.harps = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.george,
            title='Harps',
            metadata=[],
        )

        # george creates a entity 'harpers'
        self.harpers = self.george.uaccess.create_group('Harpers')

    def test_user_resource_provenance_crosstalk(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        harps = self.harps
        john = self.john
        # George grants Alva view privilege
        UserResourceProvenance.update(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.VIEW)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.VIEW)
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=bikes,
                    grantor=george),
                [alva]))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=alva)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.grantor, george)

        # George grants Alva privilege
        UserResourceProvenance.update(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)

        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=bikes,
                    grantor=george),
                [alva]))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=alva)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.grantor, george)

        # Alva grants John privilege
        UserResourceProvenance.update(
            resource=bikes,
            user=john,
            privilege=PrivilegeCodes.CHANGE,
            grantor=alva)

        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=john),
            PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=bikes,
                user=john),
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=bikes,
                    grantor=george),
                [alva]))
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=bikes,
                    grantor=alva),
                [john]))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=john)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.grantor, alva)

        # now George overrides Alva on John's privilege
        UserResourceProvenance.update(
            resource=bikes,
            user=john,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)

        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=john),
            PrivilegeCodes.VIEW)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=bikes,
                user=john),
            PrivilegeCodes.VIEW)
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=bikes, grantor=george), [
                    alva, john]))
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=bikes,
                    grantor=alva),
                []))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=john)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.grantor, george)

        # Crosstalk test: George grants Alva privilege over harps
        UserResourceProvenance.update(
            resource=harps,
            user=alva,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)

        # old privileges didn't change
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=bikes, grantor=george), [
                    alva, john]))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=alva)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.grantor, george)

        # check new privileges: should be independent.
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=harps,
                user=alva),
            PrivilegeCodes.VIEW)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=harps,
                user=alva),
            PrivilegeCodes.VIEW)
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=harps,
                    grantor=george),
                [alva]))
        record = UserResourceProvenance.get_current_record(
            resource=harps, user=alva)
        self.assertEqual(record.resource, harps)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.grantor, george)
        prov = UserResourceProvenance.objects.all().order_by('start')
        # print "after test_user_resource_provenance_crosstalk"
        # printUserResourceState()
        test_provenance_synchronization(self)

    def test_user_group_provenance_crosstalk(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        harpers = self.harpers
        john = self.john
        # George grants Alva view privilege
        UserGroupProvenance.update(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)

        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.VIEW)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.VIEW)
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=bikers,
                    grantor=george),
                [alva]))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=alva)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.grantor, george)

        # George grants Alva privilege
        UserGroupProvenance.update(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)

        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=bikers,
                    grantor=george),
                [alva]))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=alva)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.grantor, george)

        # Alva grants John privilege
        UserGroupProvenance.update(
            group=bikers,
            user=john,
            privilege=PrivilegeCodes.CHANGE,
            grantor=alva)

        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=john),
            PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=bikers,
                user=john),
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=bikers,
                    grantor=george),
                [alva]))
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=bikers,
                    grantor=alva),
                [john]))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=john)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.grantor, alva)

        # now George overrides Alva on John's privilege
        UserGroupProvenance.update(
            group=bikers,
            user=john,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)

        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=john),
            PrivilegeCodes.VIEW)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=bikers,
                user=john),
            PrivilegeCodes.VIEW)
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=bikers, grantor=george), [
                    alva, john]))
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=bikers,
                    grantor=alva),
                []))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=john)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.grantor, george)

        # Crosstalk test: George grants Alva privilege over harpers
        UserGroupProvenance.update(
            group=harpers,
            user=alva,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)

        # old privileges didn't change
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=bikers, grantor=george), [
                    alva, john]))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=alva)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.grantor, george)

        # check new privileges: should be independent of old privileges
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=harpers,
                user=alva),
            PrivilegeCodes.VIEW)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=harpers,
                user=alva),
            PrivilegeCodes.VIEW)
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=harpers,
                    grantor=george),
                [alva]))
        record = UserGroupProvenance.get_current_record(
            group=harpers, user=alva)
        self.assertEqual(record.group, harpers)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.grantor, george)
        prov = UserGroupProvenance.objects.all().order_by('start')
        # print "after test_user_group_provenance_crosstalk"
        # printUserGroupState()
        test_provenance_synchronization(self)

    def test_group_resource_provenance_crosstalk(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers
        harps = self.harps
        harpers = self.harpers
        alva = self.alva

        # George grants Bikers view privilege
        GroupResourceProvenance.update(
            resource=bikes,
            group=bikers,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)

        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.VIEW)
        self.assertEqual(
            GroupResourcePrivilege.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.VIEW)

        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=bikes,
                    grantor=george),
                [bikers]))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=bikers)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.grantor, george)

        # George grants Harpers change privilege
        GroupResourceProvenance.update(
            resource=bikes,
            group=harpers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)

        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=harpers),
            PrivilegeCodes.CHANGE)
        self.assertEqual(
            GroupResourcePrivilege.get_privilege(
                resource=bikes,
                group=harpers),
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=bikes, grantor=george), [
                    bikers, harpers]))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=harpers)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, harpers)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.grantor, george)

        # Alva downgrades Harpers privilege
        GroupResourceProvenance.update(
            resource=bikes,
            group=harpers,
            privilege=PrivilegeCodes.VIEW,
            grantor=alva)

        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=harpers),
            PrivilegeCodes.VIEW)
        self.assertEqual(
            GroupResourcePrivilege.get_privilege(
                resource=bikes,
                group=harpers),
            PrivilegeCodes.VIEW)
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=bikes,
                    grantor=george),
                i[bikers]))
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=bikes,
                    grantor=alva),
                [harpers]))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=harpers)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, harpers)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.grantor, alva)

        # now George overrides Alva on  Harpers privilege
        GroupResourceProvenance.update(
            resource=bikes,
            group=harpers,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)

        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=harpers),
            PrivilegeCodes.VIEW)
        self.assertEqual(
            GroupResourcePrivilege.get_privilege(
                resource=bikes,
                group=harpers),
            PrivilegeCodes.VIEW)
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=bikes, grantor=george), [
                    bikers, harpers]))
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=bikes,
                    grantor=alva),
                []))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=harpers)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, harpers)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.grantor, george)

        # Crosstalk test: George grants bikers privilege over harps
        GroupResourceProvenance.update(
            resource=harps,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)

        # old privileges didn't change
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.VIEW)
        self.assertEqual(
            GroupResourcePrivilege.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.VIEW)
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=bikes, grantor=george), [
                    bikers, harpers]))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=bikers)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.grantor, george)

        # check new privileges: should be independent.
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=harps,
                group=bikers),
            PrivilegeCodes.CHANGE)
        self.assertEqual(
            GroupResourcePrivilege.get_privilege(
                resource=harps,
                group=bikers),
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=harps,
                    grantor=george),
                [bikers]))
        record = GroupResourceProvenance.get_current_record(
            resource=harps, group=bikers)
        self.assertEqual(record.resource, harps)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.grantor, george)
        prov = GroupResourceProvenance.objects.all().order_by('start')
        # print "after test_group_resource_provenance_crosstalk"
        # printGroupResourceState()
        test_provenance_synchronization(self)

    def test_user_resource_provenance_rollback(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        harps = self.harps
        john = self.john

        # initial state: no undo to do.
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.NONE)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.NONE)
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=bikes,
                    grantor=george),
                []))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=alva)  # no record
        self.assertTrue(record is None)

        # George grants Alva view privilege
        UserResourceProvenance.update(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)

        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.VIEW)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.VIEW)
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=bikes,
                    grantor=george),
                [alva]))
        # update creates a record
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=alva)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.grantor, george)

        # Roll back alva's privilege
        UserResourceProvenance.rollback(resource=bikes, user=alva)

        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.NONE)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.NONE)
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=bikes,
                    grantor=george),
                []))
        # there is now a record
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=alva)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.NONE)
        self.assertEqual(record.grantor, george)

        # George grants Alva privilege
        UserResourceProvenance.update(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=bikes,
                    grantor=george),
                [alva]))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=alva)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.grantor, george)

        # Alva grants John privilege
        UserResourceProvenance.update(
            resource=bikes,
            user=john,
            privilege=PrivilegeCodes.CHANGE,
            grantor=alva)
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=john),
            PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=bikes,
                user=john),
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=bikes,
                    grantor=george),
                [alva]))
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=bikes,
                    grantor=alva),
                [john]))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=john)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.grantor, alva)

        # now George overrides Alva on John's privilege
        UserResourceProvenance.update(
            resource=bikes,
            user=john,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)

        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=john),
            PrivilegeCodes.VIEW)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=bikes,
                user=john),
            PrivilegeCodes.VIEW)
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=bikes, grantor=george), [
                    alva, john]))
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=bikes,
                    grantor=alva),
                []))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=john)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.grantor, george)

        # George changes mind and rolls back change
        UserResourceProvenance.rollback(resource=bikes, user=john)

        # privilege has been rolled back
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=john),
            PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=bikes,
                user=john),
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=bikes,
                    grantor=george),
                [alva]))
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=bikes,
                    grantor=alva),
                [john]))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=john)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.grantor, alva)

        # Crosstalk test: George grants Alva privilege over harps
        UserResourceProvenance.update(
            resource=harps,
            user=alva,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)

        # old privileges didn't change
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=john),
            PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=bikes,
                user=john),
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=bikes,
                    grantor=george),
                [alva]))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=john)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.grantor, alva)

        # check new privileges: should be independent.
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=harps,
                user=alva),
            PrivilegeCodes.VIEW)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=harps,
                user=alva),
            PrivilegeCodes.VIEW)
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=harps,
                    grantor=george),
                [alva]))
        record = UserResourceProvenance.get_current_record(
            resource=harps, user=alva)
        self.assertEqual(record.resource, harps)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.grantor, george)

        # now roll back privilege over harps
        UserResourceProvenance.rollback(resource=harps, user=alva)

        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=harps,
                user=alva),
            PrivilegeCodes.NONE)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=harps,
                user=alva),
            PrivilegeCodes.NONE)
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_rollback_users(
                    resource=harps,
                    grantor=george),
                []))
        record = UserResourceProvenance.get_current_record(
            resource=harps, user=alva)
        self.assertEqual(record.resource, harps)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.NONE)
        self.assertEqual(record.grantor, george)

        # print "after test_user_resource_provenance_rollback"
        # printUserResourceState()
        test_provenance_synchronization(self)

    def test_user_group_provenance_rollback(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        harpers = self.harpers
        john = self.john

        # initial state: no undo to do.
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.NONE)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.NONE)
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=bikers,
                    grantor=george),
                []))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=alva)  # no record
        self.assertTrue(record is None)

        # George grants Alva view privilege
        UserGroupProvenance.update(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.VIEW)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.VIEW)
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=bikers,
                    grantor=george),
                [alva]))
        # update creates a record
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=alva)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.grantor, george)

        # Roll back alva's privilege
        UserGroupProvenance.rollback(group=bikers, user=alva)

        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.NONE)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.NONE)
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=bikers,
                    grantor=george),
                []))
        # there is now a record
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=alva)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.NONE)
        self.assertEqual(record.grantor, george)

        # George grants Alva privilege
        UserGroupProvenance.update(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=bikers,
                    grantor=george),
                [alva]))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=alva)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.grantor, george)

        # Alva grants John privilege
        UserGroupProvenance.update(
            group=bikers,
            user=john,
            privilege=PrivilegeCodes.CHANGE,
            grantor=alva)
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=john),
            PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=bikers,
                user=john),
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=bikers,
                    grantor=george),
                [alva]))
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=bikers,
                    grantor=alva),
                [john]))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=john)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.grantor, alva)

        # now George overrides Alva on John's privilege
        UserGroupProvenance.update(
            group=bikers,
            user=john,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=john),
            PrivilegeCodes.VIEW)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=bikers,
                user=john),
            PrivilegeCodes.VIEW)
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=bikers, grantor=george), [
                    alva, john]))
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=bikers,
                    grantor=alva),
                []))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=john)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.grantor, george)

        # George changes mind and rolls back change
        UserGroupProvenance.rollback(group=bikers, user=john)

        # privilege has been rolled back
        # prov = UserGroupProvenance.objects.all().order_by('start')
        # for p in prov:
        #     pprint(p)
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=john),
            PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=bikers,
                user=john),
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=bikers,
                    grantor=george),
                [alva]))
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=bikers,
                    grantor=alva),
                [john]))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=john)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.grantor, alva)

        # Crosstalk test: George grants Alva privilege over harpers
        UserGroupProvenance.update(
            group=harpers,
            user=alva,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)

        # old privileges didn't change
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=john),
            PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=bikers,
                user=john),
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=bikers,
                    grantor=george),
                [alva]))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=john)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.grantor, alva)

        # check new privileges: should be independent.
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=harpers,
                user=alva),
            PrivilegeCodes.VIEW)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=harpers,
                user=alva),
            PrivilegeCodes.VIEW)
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=harpers,
                    grantor=george),
                [alva]))
        record = UserGroupProvenance.get_current_record(
            group=harpers, user=alva)
        self.assertEqual(record.group, harpers)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.grantor, george)

        # now roll back privilege over harpers
        UserGroupProvenance.rollback(group=harpers, user=alva)

        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=harpers,
                user=alva),
            PrivilegeCodes.NONE)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=harpers,
                user=alva),
            PrivilegeCodes.NONE)
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_rollback_users(
                    group=harpers,
                    grantor=george),
                []))
        record = UserGroupProvenance.get_current_record(
            group=harpers, user=alva)
        self.assertEqual(record.group, harpers)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.NONE)
        self.assertEqual(record.grantor, george)

        # print "after test_user_group_provenance_rollback"
        # printUserGroupState()
        test_provenance_synchronization(self)

    def test_group_resource_provenance_rollback(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        bikes = self.bikes
        harps = self.harps
        harpers = self.harpers

        # initial state: no undo to do.
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.NONE)
        self.assertEqual(
            GroupResourcePrivilege.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.NONE)
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=bikes,
                    grantor=george),
                []))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=bikers)  # no record
        self.assertTrue(record is None)

        # George grants bikers view privilege
        GroupResourceProvenance.update(
            resource=bikes,
            group=bikers,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)

        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.VIEW)
        self.assertEqual(
            GroupResourcePrivilege.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.VIEW)
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=bikes,
                    grantor=george),
                [bikers]))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=bikers)  # update creates a record
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.grantor, george)
        self.assertEqual(record.state, ProvenanceCodes.ACTIVE)

        # Roll back bikers's privilege
        GroupResourceProvenance.rollback(resource=bikes, group=bikers)

        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.NONE)
        self.assertEqual(
            GroupResourcePrivilege.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.NONE)
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=bikes,
                    grantor=george),
                []))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=bikers)  # there is now a record that is initial
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.privilege, PrivilegeCodes.NONE)
        self.assertEqual(record.grantor, george)
        self.assertEqual(record.state, ProvenanceCodes.INITIAL)

        # George grants bikers privilege
        GroupResourceProvenance.update(
            resource=bikes,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)

        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.CHANGE)
        self.assertEqual(
            GroupResourcePrivilege.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=bikes,
                    grantor=george),
                [bikers]))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=bikers)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.grantor, george)
        self.assertEqual(record.state, ProvenanceCodes.ACTIVE)

        # Alva grants harpers privilege
        GroupResourceProvenance.update(
            resource=bikes,
            group=harpers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=alva)

        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=harpers),
            PrivilegeCodes.CHANGE)
        self.assertEqual(
            GroupResourcePrivilege.get_privilege(
                resource=bikes,
                group=harpers),
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=bikes,
                    grantor=george),
                [bikers]))
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=bikes,
                    grantor=alva),
                [harpers]))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=harpers)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, harpers)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.grantor, alva)
        self.assertEqual(record.state, ProvenanceCodes.ACTIVE)

        # now George overrides Alva on harpers' privilege
        GroupResourceProvenance.update(
            resource=bikes,
            group=harpers,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)

        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=harpers),
            PrivilegeCodes.VIEW)
        self.assertEqual(
            GroupResourcePrivilege.get_privilege(
                resource=bikes,
                group=harpers),
            PrivilegeCodes.VIEW)
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=bikes, grantor=george), [
                    bikers, harpers]))
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=bikes,
                    grantor=alva),
                []))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=harpers)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, harpers)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.grantor, george)
        self.assertEqual(record.state, ProvenanceCodes.ACTIVE)

        # George changes mind and rolls back change
        GroupResourceProvenance.rollback(resource=bikes, group=harpers)

        # privilege has been rolled back
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=harpers),
            PrivilegeCodes.CHANGE)
        self.assertEqual(
            GroupResourcePrivilege.get_privilege(
                resource=bikes,
                group=harpers),
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=bikes,
                    grantor=george),
                [bikers]))
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=bikes,
                    grantor=alva),
                [harpers]))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=harpers)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, harpers)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.grantor, alva)
        self.assertEqual(record.state, ProvenanceCodes.RESTORED)

        # Crosstalk test: George grants bikers privilege over harps
        GroupResourceProvenance.update(
            resource=harps,
            group=bikers,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)

        # old privileges didn't change
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=harpers),
            PrivilegeCodes.CHANGE)
        self.assertEqual(
            GroupResourcePrivilege.get_privilege(
                resource=bikes,
                group=harpers),
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=bikes,
                    grantor=george),
                [bikers]))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=harpers)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, harpers)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.grantor, alva)
        self.assertEqual(record.state, ProvenanceCodes.RESTORED)

        # check new privileges: should be independent.
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=harps,
                group=bikers),
            PrivilegeCodes.VIEW)
        self.assertEqual(
            GroupResourcePrivilege.get_privilege(
                resource=harps,
                group=bikers),
            PrivilegeCodes.VIEW)
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=harps,
                    grantor=george),
                [bikers]))
        record = GroupResourceProvenance.get_current_record(
            resource=harps, group=bikers)
        self.assertEqual(record.resource, harps)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.grantor, george)
        self.assertEqual(record.state, ProvenanceCodes.ACTIVE)

        # now roll back privilege over harps
        GroupResourceProvenance.rollback(resource=harps, group=bikers)

        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=harps,
                group=bikers),
            PrivilegeCodes.NONE)
        self.assertEqual(
            GroupResourcePrivilege.get_privilege(
                resource=harps,
                group=bikers),
            PrivilegeCodes.NONE)
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_rollback_groups(
                    resource=harps,
                    grantor=george),
                []))
        record = GroupResourceProvenance.get_current_record(
            resource=harps, group=bikers)
        self.assertEqual(record.resource, harps)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.privilege, PrivilegeCodes.NONE)
        self.assertEqual(record.grantor, george)
        self.assertEqual(record.state, ProvenanceCodes.INITIAL)

        # print "after test_group_resource_provenance_rollback"
        # printGroupResourceState()
        test_provenance_synchronization(self)
