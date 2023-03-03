from django.test import TestCase
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

from hs_access_control.models import UserResourceProvenance, UserResourcePrivilege, \
    GroupResourceProvenance, GroupResourcePrivilege, \
    UserGroupProvenance, UserGroupPrivilege, \
    PrivilegeCodes

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin

from hs_access_control.tests.utilities import is_equal_to_as_set, global_reset, \
    check_provenance_synchronization

__author__ = 'Alva'


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

        # george creates a entity 'bikes', so george is the quota holder initially
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

    def test_user_resource_provenance_crosstalk(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        harps = self.harps
        john = self.john

        # George grants Alva view privilege
        george.uaccess.share(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.VIEW)

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
        george.uaccess.share(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.CHANGE)

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
        alva.uaccess.share(
            resource=bikes,
            user=john,
            privilege=PrivilegeCodes.CHANGE)

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
        george.uaccess.share(
            resource=bikes,
            user=john,
            privilege=PrivilegeCodes.VIEW)

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
        george.uaccess.share(
            resource=harps,
            user=alva,
            privilege=PrivilegeCodes.VIEW)

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
        george.uaccess.share(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.VIEW)

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
        george.uaccess.share(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.CHANGE)

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
        alva.uaccess.share(
            group=bikers,
            user=john,
            privilege=PrivilegeCodes.CHANGE)

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
        george.uaccess.share(
            group=bikers,
            user=john,
            privilege=PrivilegeCodes.VIEW)

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
        george.uaccess.share(
            group=harpers,
            user=alva,
            privilege=PrivilegeCodes.VIEW)

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
        george.uaccess.share(
            resource=bikes,
            group=bikers,
            privilege=PrivilegeCodes.VIEW)

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
        george.uaccess.share(
            resource=bikes,
            group=harpers,
            privilege=PrivilegeCodes.CHANGE)

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

        # Alva is a harper
        george.uaccess.share(
            group=harpers,
            user=alva,
            privilege=PrivilegeCodes.CHANGE)

        # Alva can access bikes
        george.uaccess.share(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.CHANGE)

        # Alva downgrades Harpers privilege on bikes
        alva.uaccess.share(
            resource=bikes,
            group=harpers,
            privilege=PrivilegeCodes.VIEW)

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

        # now George overrides Alva on Harpers privilege
        george.uaccess.share(
            resource=bikes,
            group=harpers,
            privilege=PrivilegeCodes.CHANGE)

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
                    resource=bikes, grantor=george),
                [bikers, harpers]))
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
        self.assertEqual(record.undone, False)
        self.assertEqual(record.grantor, george)

        # Crosstalk test: George grants bikers privilege over harps
        george.uaccess.share(
            resource=harps,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE)

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
                    resource=bikes, grantor=george),
                [bikers, harpers]))
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
        george.uaccess.share(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.VIEW)

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
        george.uaccess.undo_share(resource=bikes, user=alva)

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
        george.uaccess.share(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.CHANGE)

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
        alva.uaccess.share(
            resource=bikes,
            user=john,
            privilege=PrivilegeCodes.CHANGE)

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
        george.uaccess.share(
            resource=bikes,
            user=john,
            privilege=PrivilegeCodes.VIEW)

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
        george.uaccess.undo_share(resource=bikes, user=john)

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
        george.uaccess.share(
            resource=harps,
            user=alva,
            privilege=PrivilegeCodes.VIEW)

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
        george.uaccess.undo_share(resource=harps, user=alva)

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
        george.uaccess.share(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.VIEW)

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
        george.uaccess.undo_share(group=bikers, user=alva)

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
        george.uaccess.share(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.CHANGE)

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
        alva.uaccess.share(
            group=bikers,
            user=john,
            privilege=PrivilegeCodes.CHANGE)

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
        george.uaccess.share(
            group=bikers,
            user=john,
            privilege=PrivilegeCodes.VIEW)

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
        george.uaccess.undo_share(group=bikers, user=john)

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
        george.uaccess.share(
            group=harpers,
            user=alva,
            privilege=PrivilegeCodes.VIEW)

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
        george.uaccess.undo_share(group=harpers, user=alva)

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
        george.uaccess.share(
            resource=bikes,
            group=bikers,
            privilege=PrivilegeCodes.VIEW)

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
        george.uaccess.undo_share(resource=bikes, group=bikers)

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
        george.uaccess.share(
            resource=bikes,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE)

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

        # George grants Alva privilege
        george.uaccess.share(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.CHANGE)

        # Alva is a harper
        george.uaccess.share(
            group=harpers,
            user=alva,
            privilege=PrivilegeCodes.CHANGE)

        # Alva grants harpers privilege
        alva.uaccess.share(
            resource=bikes,
            group=harpers,
            privilege=PrivilegeCodes.CHANGE)

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
        george.uaccess.share(
            resource=bikes,
            group=harpers,
            privilege=PrivilegeCodes.VIEW)

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
        george.uaccess.undo_share(resource=bikes, group=harpers)

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
        george.uaccess.share(
            resource=harps,
            group=bikers,
            privilege=PrivilegeCodes.VIEW)

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
        george.uaccess.undo_share(resource=harps, group=bikers)

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

    def test_exceptions(self):
        """ exceptions are raised when undo is not appropriate """
        george = self.george
        alva = self.alva
        bikers = self.bikers
        bikes = self.bikes

        with self.assertRaises(PermissionDenied):
            george.uaccess.undo_share_resource_with_user(bikes, alva)

        with self.assertRaises(PermissionDenied):
            george.uaccess.undo_share_resource_with_group(bikes, bikers)

        with self.assertRaises(PermissionDenied):
            george.uaccess.undo_share_group_with_user(bikers, alva)

        with self.assertRaises(PermissionDenied):
            george.uaccess.undo_share_resource_with_user(bikes, george)

        with self.assertRaises(PermissionDenied):
            george.uaccess.undo_share_group_with_user(bikers, george)

    def test_group_single_owner_preserve(self):
        george = self.george
        alva = self.alva
        bikers = self.bikers
        with self.assertRaises(PermissionDenied):
            george.uaccess.undo_share(group=bikers, user=george)

        # set up a subtle single-owner botch.
        george.uaccess.share(group=bikers, user=alva, privilege=PrivilegeCodes.OWNER)
        george.uaccess.unshare(group=bikers, user=george)
        alva.uaccess.share(group=bikers, user=george, privilege=PrivilegeCodes.OWNER)
        alva.uaccess.unshare(group=bikers, user=alva)
        # now alva is grantor for george, but george is single owner

        with self.assertRaises(PermissionDenied):
            alva.uaccess.undo_share(group=bikers, user=george)

    def test_resource_single_owner_preserve(self):
        george = self.george
        alva = self.alva
        bikes = self.bikes
        with self.assertRaises(PermissionDenied):
            george.uaccess.undo_share(resource=bikes, user=george)

        # set up a subtle single-owner botch.
        george.uaccess.share(resource=bikes, user=alva, privilege=PrivilegeCodes.OWNER)
        # transfer quota holder from george to alva since quota holder cannot be removed from
        # ownership
        bikes.set_quota_holder(george, alva)
        george.uaccess.unshare(resource=bikes, user=george)
        alva.uaccess.share(resource=bikes, user=george, privilege=PrivilegeCodes.OWNER)
        # alva transfer quota holder back to george in order to unshare himself
        bikes.set_quota_holder(alva, george)
        alva.uaccess.unshare(resource=bikes, user=alva)

        # now alva is grantor for george, but george is single owner also quota holder
        with self.assertRaises(PermissionDenied):
            alva.uaccess.undo_share(resource=bikes, user=george)
