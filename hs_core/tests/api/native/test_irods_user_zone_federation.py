import os
from django.test import TransactionTestCase

from django.conf import settings
from django.contrib.auth.models import Group

from hs_core.models import BaseResource
from hs_core import hydroshare
from hs_core.testing import TestCaseCommonUtilities
from hs_core.tasks import update_quota_usage_task


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
        super(TestUserZoneIRODSFederation, self).assert_federated_irods_available()

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

        test_file = open(self.file_one, 'w')
        test_file.write("Test text file in file1.txt")
        test_file.close()
        test_file = open(self.file_two, 'w')
        test_file.write("Test text file in file2.txt")
        test_file.close()

        # transfer files to user zone space
        irods_target_path = '/' + settings.HS_USER_IRODS_ZONE + '/home/testuser/'
        file_list_dict = {}
        file_list_dict[self.file_one] = irods_target_path + self.file_one
        file_list_dict[self.file_two] = irods_target_path + self.file_two
        super(TestUserZoneIRODSFederation, self).save_files_to_user_zone(file_list_dict)

    def tearDown(self):
        super(TestUserZoneIRODSFederation, self).tearDown()
        # no need for further cleanup if federation testing is not setup in the first place
        super(TestUserZoneIRODSFederation, self).assert_federated_irods_available()

        # delete irods test user in user zone
        super(TestUserZoneIRODSFederation, self).delete_irods_user_in_user_zone()

        os.remove(self.file_one)
        os.remove(self.file_two)

    def test_resource_operations_in_user_zone(self):
        super(TestUserZoneIRODSFederation, self).assert_federated_irods_available()

        # test adding files from federated user zone to an empty resource
        # created in hydroshare zone
        res = hydroshare.resource.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='My Test Generic Resource in HydroShare Zone'
        )
        self.assertEqual(res.files.all().count(), 0,
                         msg="Number of content files is not equal to 0")
        fed_test_file1_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_one)
        fed_file2_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_two)
        hydroshare.add_resource_files(
            res.short_id,
            source_names=[fed_test_file1_full_path, fed_file2_full_path])
        # test resource has two files
        self.assertEqual(res.files.all().count(), 2,
                         msg="Number of content files is not equal to 2")

        user_path = '/{zone}/home/testuser/'.format(zone=settings.HS_USER_IRODS_ZONE)
        file_list = []
        for f in res.files.all():
            file_list.append(os.path.basename(f.storage_path))
        self.assertTrue(self.file_one in file_list,
                        msg='file 1 has not been added in the resource in hydroshare zone')
        self.assertTrue(self.file_two in file_list,
                        msg='file 2 has not been added in the resource in hydroshare zone')
        # test original file in user test zone still exist after adding it to the resource
        self.assertTrue(self.irods_storage.exists(user_path + self.file_one))
        self.assertTrue(self.irods_storage.exists(user_path + self.file_two))

        # test replication of this resource to user zone even if the bag_modified AVU for this
        # resource is wrongly set to False when the bag for this resource does not exist and
        # need to be recreated
        res.setAVU('bag_modified', 'false')
        hydroshare.resource.replicate_resource_bag_to_user_zone(self.user, res.short_id)
        self.assertTrue(self.irods_storage.exists(user_path + res.short_id + '.zip'),
                        msg='replicated resource bag is not in the user zone')

        # test resource deletion
        hydroshare.resource.delete_resource(res.short_id)
        self.assertEquals(BaseResource.objects.all().count(), 0,
                          msg='Number of resources not equal to 0')
        # test to make sure original files still exist after resource deletion
        self.assertTrue(self.irods_storage.exists(user_path + self.file_one))
        self.assertTrue(self.irods_storage.exists(user_path + self.file_two))

    def test_quota_update_in_fed_zones(self):
        super(TestUserZoneIRODSFederation, self).assert_federated_irods_available()

        # create a resource in the default HydroShare data iRODS zone for aggregated quota
        # update testing
        res = hydroshare.resource.create_resource(
            'GenericResource',
            self.user,
            'My Test Resource in Data Zone'
        )
        self.assertTrue(res.creator == self.user)
        self.assertTrue(res.get_quota_holder() == self.user)

        istorage = res.get_irods_storage()
        attname = self.user.username + '-usage'
        test_qsize = '2000000000'  # 2GB
        # this quota size AVU will be set by real time iRODS quota usage update micro-services.
        # For testing, setting it programmatically to test the quota size will be picked up
        # automatically when files are added into this resource
        # programmatically set quota size for the test user in data zone
        if not istorage.exists(settings.IRODS_BAGIT_PATH):
            istorage.session.run("imkdir", None, '-p', settings.IRODS_BAGIT_PATH)
        istorage.setAVU(settings.IRODS_BAGIT_PATH, attname, test_qsize)

        get_qsize = istorage.getAVU(settings.IRODS_BAGIT_PATH, attname)
        self.assertEqual(test_qsize, get_qsize)

        # Although the resource creation operation above will trigger quota update celery task,
        # in the test environment, celery task is not really executed, so have to test quota update
        # task explicitely here
        update_quota_usage_task(self.user.username)
        uquota = self.user.quotas.first()
        target_qsize = float(test_qsize)
        target_qsize = hydroshare.utils.convert_file_size_to_unit(target_qsize, uquota.unit)
        error = abs(uquota.used_value - target_qsize)
        self.assertLessEqual(error, 0.5, msg='error is ' + str(error))

        # delete test resources
        hydroshare.resource.delete_resource(res.short_id)
