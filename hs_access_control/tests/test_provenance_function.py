from django.test import TestCase
from django.contrib.auth.models import Group, User

from hs_access_control.models import UserResourceProvenance, UserResourcePrivilege, \
    GroupResourceProvenance, GroupResourcePrivilege, \
    UserGroupProvenance, UserGroupPrivilege, \
    PrivilegeCodes

from hs_core import hydroshare
from hs_core.testing import MockS3TestCaseMixin
from hs_core.models import BaseResource

from hs_access_control.tests.utilities import global_reset, \
    is_equal_to_as_set, check_provenance_synchronization

__author__ = 'Alva'


class UnitTests(MockS3TestCaseMixin, TestCase):
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
            resource_type='CompositeResource',
            owner=self.george,
            title='Bikes',
            metadata=[],
        )

        # george creates a entity 'bikers'
        self.bikers = self.george.uaccess.create_group('Bikers', 'Of the human powered kind')

        # george creates a entity 'harps'
        self.harps = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.george,
            title='Harps',
            metadata=[],
        )

        # george creates a entity 'harpers'
        self.harpers = self.george.uaccess.create_group('Harpers', 'Without any ferries')

    def tearDown(self):
        super(UnitTests, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        BaseResource.objects.all().delete()

    def test_user_resource_provenance_crosstalk(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        harps = self.harps
        john = self.john

        # George grants Alva view privilege
        UserResourcePrivilege.share(
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
                UserResourcePrivilege.get_undo_users(
                    resource=bikes,
                    grantor=george),
                [alva]))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=alva)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # George grants Alva privilege
        UserResourcePrivilege.share(
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
                UserResourcePrivilege.get_undo_users(
                    resource=bikes,
                    grantor=george),
                [alva]))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=alva)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # Alva grants John privilege
        UserResourcePrivilege.share(
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
                UserResourcePrivilege.get_undo_users(
                    resource=bikes,
                    grantor=george),
                [alva]))
        self.assertTrue(
            is_equal_to_as_set(
                UserResourcePrivilege.get_undo_users(
                    resource=bikes,
                    grantor=alva),
                [john]))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=john)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, alva)

        # now George overrides Alva on John's privilege
        UserResourcePrivilege.share(
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
                UserResourcePrivilege.get_undo_users(
                    resource=bikes, grantor=george), [
                    alva, john]))
        self.assertTrue(
            is_equal_to_as_set(
                UserResourcePrivilege.get_undo_users(
                    resource=bikes,
                    grantor=alva),
                []))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=john)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # Crosstalk test: George grants Alva privilege over harps
        UserResourcePrivilege.share(
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
                UserResourcePrivilege.get_undo_users(
                    resource=bikes, grantor=george), [
                    alva, john]))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=alva)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.undone, False)
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
                UserResourcePrivilege.get_undo_users(
                    resource=harps,
                    grantor=george),
                [alva]))
        record = UserResourceProvenance.get_current_record(
            resource=harps, user=alva)
        self.assertEqual(record.resource, harps)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        check_provenance_synchronization(self)

    def test_user_group_provenance_crosstalk(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        harpers = self.harpers
        john = self.john

        # George grants Alva view privilege
        UserGroupPrivilege.share(
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
                UserGroupPrivilege.get_undo_users(
                    group=bikers,
                    grantor=george),
                [alva]))

        record = UserGroupProvenance.get_current_record(
            group=bikers, user=alva)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # George grants Alva privilege
        UserGroupPrivilege.share(
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
                UserGroupPrivilege.get_undo_users(
                    group=bikers,
                    grantor=george),
                [alva]))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=alva)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # Alva grants John privilege
        UserGroupPrivilege.share(
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
                UserGroupPrivilege.get_undo_users(
                    group=bikers,
                    grantor=george),
                [alva]))
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupPrivilege.get_undo_users(
                    group=bikers,
                    grantor=alva),
                [john]))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=john)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, alva)

        # now George overrides Alva on John's privilege
        UserGroupPrivilege.share(
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
                UserGroupPrivilege.get_undo_users(
                    group=bikers, grantor=george), [
                    alva, john]))
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupPrivilege.get_undo_users(
                    group=bikers,
                    grantor=alva),
                []))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=john)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # Crosstalk test: George grants Alva privilege over harpers
        UserGroupPrivilege.share(
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
                UserGroupPrivilege.get_undo_users(
                    group=bikers, grantor=george), [
                    alva, john]))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=alva)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.undone, False)
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
                UserGroupPrivilege.get_undo_users(
                    group=harpers,
                    grantor=george),
                [alva]))
        record = UserGroupProvenance.get_current_record(
            group=harpers, user=alva)
        self.assertEqual(record.group, harpers)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        check_provenance_synchronization(self)

    def test_group_resource_provenance_crosstalk(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers
        harps = self.harps
        harpers = self.harpers
        alva = self.alva

        # George grants Bikers view privilege
        GroupResourcePrivilege.share(
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
                GroupResourcePrivilege.get_undo_groups(
                    resource=bikes,
                    grantor=george),
                [bikers]))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=bikers)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # George grants Harpers change privilege
        GroupResourcePrivilege.share(
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
                GroupResourcePrivilege.get_undo_groups(
                    resource=bikes, grantor=george), [
                    bikers, harpers]))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=harpers)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, harpers)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # Alva downgrades Harpers privilege
        GroupResourcePrivilege.share(
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
                GroupResourcePrivilege.get_undo_groups(
                    resource=bikes,
                    grantor=george),
                [bikers]))
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourcePrivilege.get_undo_groups(
                    resource=bikes,
                    grantor=alva),
                [harpers]))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=harpers)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, harpers)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, alva)

        # now George overrides Alva on  Harpers privilege
        GroupResourcePrivilege.share(
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
                GroupResourcePrivilege.get_undo_groups(
                    resource=bikes, grantor=george), [
                    bikers, harpers]))
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourcePrivilege.get_undo_groups(
                    resource=bikes,
                    grantor=alva),
                []))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=harpers)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, harpers)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # Crosstalk test: George grants bikers privilege over harps
        GroupResourcePrivilege.share(
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
                GroupResourcePrivilege.get_undo_groups(
                    resource=bikes, grantor=george), [
                    bikers, harpers]))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=bikers)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.undone, False)
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
                GroupResourcePrivilege.get_undo_groups(
                    resource=harps,
                    grantor=george),
                [bikers]))
        record = GroupResourceProvenance.get_current_record(
            resource=harps, group=bikers)
        self.assertEqual(record.resource, harps)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        check_provenance_synchronization(self)

    def test_user_resource_provenance_undo_share(self):
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
                UserResourcePrivilege.get_undo_users(
                    resource=bikes,
                    grantor=george),
                []))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=alva)  # no record
        self.assertTrue(record is None)

        # George grants Alva view privilege
        UserResourcePrivilege.share(
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
                UserResourcePrivilege.get_undo_users(
                    resource=bikes,
                    grantor=george),
                [alva]))
        # update creates a record
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=alva)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # Roll back alva's privilege
        UserResourcePrivilege.undo_share(resource=bikes, user=alva, grantor=george)

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
                UserResourcePrivilege.get_undo_users(
                    resource=bikes,
                    grantor=george),
                []))
        # there is now a record
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=alva)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.NONE)
        self.assertEqual(record.undone, True)
        self.assertEqual(record.grantor, None)

        # George grants Alva privilege
        UserResourcePrivilege.share(
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
                UserResourcePrivilege.get_undo_users(
                    resource=bikes,
                    grantor=george),
                [alva]))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=alva)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # Alva grants John privilege
        UserResourcePrivilege.share(
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
                UserResourcePrivilege.get_undo_users(
                    resource=bikes,
                    grantor=george),
                [alva]))
        self.assertTrue(
            is_equal_to_as_set(
                UserResourcePrivilege.get_undo_users(
                    resource=bikes,
                    grantor=alva),
                [john]))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=john)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, alva)

        # now George overrides Alva on John's privilege
        UserResourcePrivilege.share(
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
                UserResourcePrivilege.get_undo_users(
                    resource=bikes, grantor=george), [
                    alva, john]))
        self.assertTrue(
            is_equal_to_as_set(
                UserResourcePrivilege.get_undo_users(
                    resource=bikes,
                    grantor=alva),
                []))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=john)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # George changes mind and rolls back change
        UserResourcePrivilege.undo_share(resource=bikes, user=john, grantor=george)

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
                UserResourcePrivilege.get_undo_users(
                    resource=bikes,
                    grantor=george),
                [alva]))
        self.assertTrue(
            is_equal_to_as_set(
                UserResourcePrivilege.get_undo_users(
                    resource=bikes,
                    grantor=alva),
                []))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=john)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.undone, True)
        self.assertEqual(record.grantor, alva)

        # Crosstalk test: George grants Alva privilege over harps
        UserResourcePrivilege.share(
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
                UserResourcePrivilege.get_undo_users(
                    resource=bikes,
                    grantor=george),
                [alva]))
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=john)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.undone, True)
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
                UserResourcePrivilege.get_undo_users(
                    resource=harps,
                    grantor=george),
                [alva]))
        record = UserResourceProvenance.get_current_record(
            resource=harps, user=alva)
        self.assertEqual(record.resource, harps)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # now roll back privilege over harps
        UserResourcePrivilege.undo_share(resource=harps, user=alva, grantor=george)

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
                UserResourcePrivilege.get_undo_users(
                    resource=harps,
                    grantor=george),
                []))
        record = UserResourceProvenance.get_current_record(
            resource=harps, user=alva)
        self.assertEqual(record.resource, harps)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.NONE)
        self.assertEqual(record.undone, True)
        self.assertEqual(record.grantor, None)

        check_provenance_synchronization(self)

    def test_user_group_provenance_undo_share(self):
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
                UserGroupPrivilege.get_undo_users(
                    group=bikers,
                    grantor=george),
                []))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=alva)  # no record
        self.assertTrue(record is None)

        # George grants Alva view privilege
        UserGroupPrivilege.share(
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
                UserGroupPrivilege.get_undo_users(
                    group=bikers,
                    grantor=george),
                [alva]))
        # update creates a record
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=alva)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # Roll back alva's privilege
        UserGroupPrivilege.undo_share(group=bikers, user=alva, grantor=george)

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
                UserGroupPrivilege.get_undo_users(
                    group=bikers,
                    grantor=george),
                []))
        # there is now a record
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=alva)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.NONE)
        self.assertEqual(record.undone, True)
        self.assertEqual(record.grantor, None)

        # George grants Alva privilege
        UserGroupPrivilege.share(
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
                UserGroupPrivilege.get_undo_users(
                    group=bikers,
                    grantor=george),
                [alva]))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=alva)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # Alva grants John privilege
        UserGroupPrivilege.share(
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
                UserGroupPrivilege.get_undo_users(
                    group=bikers,
                    grantor=george),
                [alva]))
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupPrivilege.get_undo_users(
                    group=bikers,
                    grantor=alva),
                [john]))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=john)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, alva)

        # now George overrides Alva on John's privilege
        UserGroupPrivilege.share(
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
                UserGroupPrivilege.get_undo_users(
                    group=bikers, grantor=george), [
                    alva, john]))
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupPrivilege.get_undo_users(
                    group=bikers,
                    grantor=alva),
                []))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=john)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # George changes mind and rolls back change
        UserGroupPrivilege.undo_share(group=bikers, user=john, grantor=george)

        # privilege has been rolled back
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
                UserGroupPrivilege.get_undo_users(
                    group=bikers,
                    grantor=george),
                [alva]))
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupPrivilege.get_undo_users(
                    group=bikers,
                    grantor=alva),
                []))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=john)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.undone, True)
        self.assertEqual(record.grantor, alva)

        # Crosstalk test: George grants Alva privilege over harpers
        UserGroupPrivilege.share(
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
                UserGroupPrivilege.get_undo_users(
                    group=bikers,
                    grantor=george),
                [alva]))
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=john)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, john)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.undone, True)
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
                UserGroupPrivilege.get_undo_users(
                    group=harpers,
                    grantor=george),
                [alva]))
        record = UserGroupProvenance.get_current_record(
            group=harpers, user=alva)
        self.assertEqual(record.group, harpers)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # now roll back privilege over harpers
        UserGroupPrivilege.undo_share(group=harpers, user=alva, grantor=george)

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
                UserGroupPrivilege.get_undo_users(
                    group=harpers,
                    grantor=george),
                []))
        record = UserGroupProvenance.get_current_record(
            group=harpers, user=alva)
        self.assertEqual(record.group, harpers)
        self.assertEqual(record.user, alva)
        self.assertEqual(record.privilege, PrivilegeCodes.NONE)
        self.assertEqual(record.undone, True)
        self.assertEqual(record.grantor, None)

        check_provenance_synchronization(self)

    def test_group_resource_provenance_undo_share(self):
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
                GroupResourcePrivilege.get_undo_groups(
                    resource=bikes,
                    grantor=george),
                []))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=bikers)  # no record
        self.assertTrue(record is None)

        # George grants bikers view privilege
        GroupResourcePrivilege.share(
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
                GroupResourcePrivilege.get_undo_groups(
                    resource=bikes,
                    grantor=george),
                [bikers]))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=bikers)  # update creates a record
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # Roll back bikers's privilege
        GroupResourcePrivilege.undo_share(resource=bikes, group=bikers, grantor=george)

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
                GroupResourcePrivilege.get_undo_groups(
                    resource=bikes,
                    grantor=george),
                []))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=bikers)  # there is now a record that is initial
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.privilege, PrivilegeCodes.NONE)
        self.assertEqual(record.undone, True)
        self.assertEqual(record.grantor, None)

        # George grants bikers privilege
        GroupResourcePrivilege.share(
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
                GroupResourcePrivilege.get_undo_groups(
                    resource=bikes,
                    grantor=george),
                [bikers]))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=bikers)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # Alva grants harpers privilege
        GroupResourcePrivilege.share(
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
                GroupResourcePrivilege.get_undo_groups(
                    resource=bikes,
                    grantor=george),
                [bikers]))
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourcePrivilege.get_undo_groups(
                    resource=bikes,
                    grantor=alva),
                [harpers]))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=harpers)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, harpers)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, alva)

        # now George overrides Alva on harpers' privilege
        GroupResourcePrivilege.share(
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
                GroupResourcePrivilege.get_undo_groups(
                    resource=bikes, grantor=george), [
                    bikers, harpers]))
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourcePrivilege.get_undo_groups(
                    resource=bikes,
                    grantor=alva),
                []))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=harpers)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, harpers)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # George changes mind and rolls back change
        GroupResourcePrivilege.undo_share(resource=bikes, group=harpers, grantor=george)

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
                GroupResourcePrivilege.get_undo_groups(
                    resource=bikes,
                    grantor=george),
                [bikers]))
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourcePrivilege.get_undo_groups(
                    resource=bikes,
                    grantor=alva),
                []))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=harpers)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, harpers)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.undone, True)
        self.assertEqual(record.grantor, alva)

        # Crosstalk test: George grants bikers privilege over harps
        GroupResourcePrivilege.share(
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
                GroupResourcePrivilege.get_undo_groups(
                    resource=bikes,
                    grantor=george),
                [bikers]))
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=harpers)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, harpers)
        self.assertEqual(record.privilege, PrivilegeCodes.CHANGE)
        self.assertEqual(record.undone, True)
        self.assertEqual(record.grantor, alva)

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
                GroupResourcePrivilege.get_undo_groups(
                    resource=harps,
                    grantor=george),
                [bikers]))
        record = GroupResourceProvenance.get_current_record(
            resource=harps, group=bikers)
        self.assertEqual(record.resource, harps)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.privilege, PrivilegeCodes.VIEW)
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # now roll back privilege over harps
        GroupResourcePrivilege.undo_share(resource=harps, group=bikers, grantor=george)

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
                GroupResourcePrivilege.get_undo_groups(
                    resource=harps,
                    grantor=george),
                []))
        record = GroupResourceProvenance.get_current_record(
            resource=harps, group=bikers)
        self.assertEqual(record.resource, harps)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.privilege, PrivilegeCodes.NONE)
        self.assertEqual(record.undone, True)
        self.assertEqual(record.grantor, None)

        check_provenance_synchronization(self)
