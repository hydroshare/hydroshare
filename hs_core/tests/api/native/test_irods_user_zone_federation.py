import os
from django.test import TransactionTestCase

from django.conf import settings
from django.contrib.auth.models import Group

from hs_core.hydroshare import resource
from hs_core import hydroshare
from hs_core.testing import TestCaseCommonUtilities
from hs_core.tasks import update_quota_usage_task
from hs_core.hydroshare.utils import convert_file_size_to_unit


class TestUserZoneIRODSFederation(TestCaseCommonUtilities, TransactionTestCase):
    """
    This TestCase class tests all federation zone related functionalities for generic resource,
    in particular, only file operation-related functionalities need to be tested, including
    creating resources in the federated user zone, adding files to resources in the user zone,
    creating a new version of a resource in the user zone, deleting resources in the user zone,
    and folder-related operations to the resources in the user zone. Federation zone related
    functionalities for specific resource types need to be tested in specific resource type unit
    tests just to make sure metadata extraction works to extract metadata from files coming from
    a federated user zone.
    """
    def setUp(self):
        super(TestUserZoneIRODSFederation, self).setUp()
        # only do federation testing when REMOTE_USE_IRODS is True and irods docker containers
        # are set up properly
        if not super(TestUserZoneIRODSFederation, self).is_federated_irods_available():
            return

        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = hydroshare.create_account(
            'test_user@email.com',
            username='testuser',
            first_name='some_first_name',
            last_name='some_last_name',
            password='testuser',
            superuser=False,
            groups=[self.hs_group]
        )

        # create corresponding irods account in user zone
        super(TestUserZoneIRODSFederation, self).create_irods_user_in_user_zone()

        # create files
        self.file_one = "file1.txt"
        self.file_two = "file2.txt"
        self.file_three = "file3.txt"
        self.file_to_be_deleted = "file_to_be_deleted.txt"

        test_file = open(self.file_one, 'w')
        test_file.write("Test text file in file1.txt")
        test_file.close()
        test_file = open(self.file_two, 'w')
        test_file.write("Test text file in file2.txt")
        test_file.close()
        test_file = open(self.file_three, 'w')
        test_file.write("Test text file in file3.txt")
        test_file.close()
        test_file = open(self.file_to_be_deleted, 'w')
        test_file.write("Test text file which will be deleted after resource creation")
        test_file.close()

        # transfer files to user zone space
        irods_target_path = '/' + settings.HS_USER_IRODS_ZONE + '/home/testuser/'
        file_list_dict = {}
        file_list_dict[self.file_one] = irods_target_path + self.file_one
        file_list_dict[self.file_two] = irods_target_path + self.file_two
        file_list_dict[self.file_three] = irods_target_path + self.file_three
        file_list_dict[self.file_to_be_deleted] = irods_target_path + self.file_to_be_deleted
        super(TestUserZoneIRODSFederation, self).save_files_to_user_zone(file_list_dict)

    def tearDown(self):
        super(TestUserZoneIRODSFederation, self).tearDown()
        # no need for further cleanup if federation testing is not setup in the first place
        if not super(TestUserZoneIRODSFederation, self).is_federated_irods_available():
            return

        # delete irods test user in user zone
        super(TestUserZoneIRODSFederation, self).delete_irods_user_in_user_zone()

        os.remove(self.file_one)
        os.remove(self.file_two)
        os.remove(self.file_three)
        os.remove(self.file_to_be_deleted)

    def test_quota_update_in_fed_zones(self):
        # only do federation testing when REMOTE_USE_IRODS is True and irods docker containers
        # are set up properly
        if not super(TestUserZoneIRODSFederation, self).is_federated_irods_available():
            return
        # create a resource in the default HydroShare data iRODS zone for aggregated quota
        # update testing
        res = resource.create_resource(
            'GenericResource',
            self.user,
            'My Test Resource in Data Zone'
        )
        self.assertTrue(res.creator == self.user)
        self.assertTrue(res.get_quota_holder() == self.user)

        # IRODS PROXY USER DOES NOT HAVE PERMISSION TO SET USER TYPE AVU ON IT since only rodsadmin
        # can set up user type AVUs. As a result, use docker exec subprocess to set user type AVU
        # using rodsadmin for testing purpose
        attname = self.user.username + '-quota'
        test_qsize = '2000000000'  # 2GB
        # this quota size AVU will be set by real time iRODS quota usage update micro-services.
        # For testing, setting it programmatically to test the quota size will be picked up
        # automatically when files are added into this resource
        data_proxy_name = settings.IRODS_USERNAME + '#' + settings.IRODS_ZONE
        super(TestUserZoneIRODSFederation, self).set_user_type_avu(data_proxy_name, attname,
                                                                   test_qsize)
        istorage = res.get_irods_storage()
        get_qsize = istorage.getAVU(data_proxy_name, attname, type='-u')
        self.assertEqual(test_qsize, get_qsize)

        user_proxy_name = settings.HS_LOCAL_PROXY_USER_IN_FED_ZONE + '#' + \
                          settings.HS_USER_IRODS_ZONE
        super(TestUserZoneIRODSFederation, self).set_user_type_avu(user_proxy_name, attname,
                                                                   str(test_qsize))
        super(TestUserZoneIRODSFederation, self).verify_user_quota_usage_avu_in_user_zone(
            attname, test_qsize)

        # create a resource in federated user zone which should trigger quota usage update
        fed_test_file_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_one)
        fed_res = resource.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='My Test Generic Resource in User Zone',
            source_names=[fed_test_file_full_path]
        )
        self.assertEqual(fed_res.files.all().count(), 1,
                         msg="Number of content files is not equal to 1")

        self.assertTrue(fed_res.creator == self.user)
        self.assertTrue(fed_res.get_quota_holder() == self.user)

        # Although the resource creation operation above will trigger quota update celery task,
        # in the test environment, celery task is not really executed, so have to test quota update
        # task explicitely here
        update_quota_usage_task(self.user.username)
        uquota = self.user.quotas.first()
        target_qsize = convert_file_size_to_unit(float(test_qsize) * 2, uquota.unit)
        error = abs(uquota.used_value - target_qsize)
        self.assertLessEqual(error, 0.5, msg='error is ' + str(error))

        # delete test resources
        resource.delete_resource(res.short_id)
        resource.delete_resource(fed_res.short_id)
