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
        super(TestUserZoneIRODSFederation, self).assert_federated_irods_available()

        # delete irods test user in user zone
        super(TestUserZoneIRODSFederation, self).delete_irods_user_in_user_zone()

        os.remove(self.file_one)
        os.remove(self.file_two)
        os.remove(self.file_three)
        os.remove(self.file_to_be_deleted)

    def test_resource_operations_in_user_zone(self):
        super(TestUserZoneIRODSFederation, self).assert_federated_irods_available()
        # test resource creation and "move" option in federated user zone
        fed_test_file_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_to_be_deleted)
        res = hydroshare.resource.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='My Test Generic Resource in User Zone',
            source_names=[fed_test_file_full_path],
            move=True
        )

        self.assertEqual(res.files.all().count(), 1,
                         msg="Number of content files is not equal to 1")
        fed_path = '/{zone}/home/{user}'.format(zone=settings.HS_USER_IRODS_ZONE,
                                                user=settings.HS_LOCAL_PROXY_USER_IN_FED_ZONE)
        user_path = '/{zone}/home/testuser/'.format(zone=settings.HS_USER_IRODS_ZONE)
        self.assertEqual(res.resource_federation_path, fed_path)
        # test original file in user test zone is removed after resource creation
        # since True is used for move when creating the resource
        file_path_name = user_path + self.file_to_be_deleted
        self.assertFalse(self.irods_storage.exists(file_path_name))

        # test django_irods CopyFiles() with an iRODS resource name being passed in
        # as input parameter to verify the file gets copied to the pass-in iRODS resource
        istorage = res.get_irods_storage()
        src_path = os.path.join(res.root_path, 'data', 'contents', self.file_to_be_deleted)
        dest_path = file_path_name
        istorage.copyFiles(src_path, dest_path, settings.HS_IRODS_LOCAL_ZONE_DEF_RES)
        # assert file did get copied over
        self.assertTrue(self.irods_storage.exists(file_path_name))
        stdout = self.irods_storage.session.run("ils", None, "-l", file_path_name)[0].split()
        # assert copied file gets written to the iRODS resource being passed into copyFiles() call
        self.assertEqual(stdout[2], settings.HS_IRODS_LOCAL_ZONE_DEF_RES)

        # test resource file deletion
        res.files.all().delete()
        self.assertEqual(res.files.all().count(), 0,
                         msg="Number of content files is not equal to 0")

        # test add multiple files and 'copy' option in federated user zone
        fed_test_file1_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_one)
        fed_test_file2_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_two)
        hydroshare.add_resource_files(
            res.short_id,
            source_names=[fed_test_file1_full_path, fed_test_file2_full_path],
            move=False)
        # test resource has two files
        self.assertEqual(res.files.all().count(), 2,
                         msg="Number of content files is not equal to 2")

        file_list = []
        for f in res.files.all():
            file_list.append(f.storage_path.split('/')[-1])
        self.assertTrue(self.file_one in file_list,
                        msg='file 1 has not been added in the resource in user zone')
        self.assertTrue(self.file_two in file_list,
                        msg='file 2 has not been added in the resource in user zone')
        # test original two files in user test zone still exist after adding them to the resource
        # since False  is used for move when creating the resource
        self.assertTrue(self.irods_storage.exists(user_path + self.file_one))
        self.assertTrue(self.irods_storage.exists(user_path + self.file_two))

        # test resource deletion
        hydroshare.resource.delete_resource(res.short_id)
        self.assertEquals(BaseResource.objects.all().count(), 0,
                          msg='Number of resources not equal to 0')

        # test create new version resource in user zone
        fed_test_file1_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_one)
        ori_res = hydroshare.resource.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='My Original Generic Resource in User Zone',
            source_names=[fed_test_file1_full_path],
            move=False
        )
        # make sure ori_res is created in federated user zone
        fed_path = '/{zone}/home/{user}'.format(zone=settings.HS_USER_IRODS_ZONE,
                                                user=settings.HS_LOCAL_PROXY_USER_IN_FED_ZONE)
        self.assertEqual(ori_res.resource_federation_path, fed_path)
        self.assertEqual(ori_res.files.all().count(), 1,
                         msg="Number of content files is not equal to 1")

        new_res = hydroshare.create_empty_resource(ori_res.short_id, self.user)
        new_res = hydroshare.create_new_version_resource(ori_res, new_res, self.user)
        # only need to test file-related attributes
        # ensure new versioned resource is created in the same federation zone as original resource
        self.assertEqual(ori_res.resource_federation_path, new_res.resource_federation_path)
        # ensure new versioned resource has the same number of content files as original resource
        self.assertEqual(ori_res.files.all().count(), new_res.files.all().count())
        # delete resources to clean up
        hydroshare.resource.delete_resource(new_res.short_id)
        hydroshare.resource.delete_resource(ori_res.short_id)

        # test copy resource in user zone
        fed_test_file1_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_one)
        ori_res = hydroshare.resource.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='My Original Generic Resource in User Zone',
            source_names=[fed_test_file1_full_path],
            move=False
        )
        # make sure ori_res is created in federated user zone
        fed_path = '/{zone}/home/{user}'.format(zone=settings.HS_USER_IRODS_ZONE,
                                                user=settings.HS_LOCAL_PROXY_USER_IN_FED_ZONE)
        self.assertEqual(ori_res.resource_federation_path, fed_path)
        self.assertEqual(ori_res.files.all().count(), 1,
                         msg="Number of content files is not equal to 1")

        new_res = hydroshare.create_empty_resource(ori_res.short_id, self.user, action='copy')
        new_res = hydroshare.copy_resource(ori_res, new_res)
        # only need to test file-related attributes
        # ensure new copied resource is created in the same federation zone as original resource
        self.assertEqual(ori_res.resource_federation_path, new_res.resource_federation_path)
        # ensure new copied resource has the same number of content files as original resource
        self.assertEqual(ori_res.files.all().count(), new_res.files.all().count())
        # delete resources to clean up
        hydroshare.resource.delete_resource(new_res.short_id)
        hydroshare.resource.delete_resource(ori_res.short_id)

        # test folder operations in user zone
        fed_file1_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_one)
        fed_file2_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_two)
        fed_file3_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_three)
        self.res = hydroshare.resource.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='My Original Generic Resource in User Zone',
            source_names=[fed_file1_full_path, fed_file2_full_path, fed_file3_full_path],
            move=False
        )
        # make sure self.res is created in federated user zone
        fed_path = '/{zone}/home/{user}'.format(zone=settings.HS_USER_IRODS_ZONE,
                                                user=settings.HS_LOCAL_PROXY_USER_IN_FED_ZONE)
        self.assertEqual(self.res.resource_federation_path, fed_path)
        # resource should has only three files at this point
        self.assertEqual(self.res.files.all().count(), 3,
                         msg="resource file count didn't match")

        self.file_name_list = [self.file_one, self.file_two, self.file_three]
        super(TestUserZoneIRODSFederation, self).resource_file_oprs()

        # delete resources to clean up
        hydroshare.resource.delete_resource(self.res.short_id)

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
        hydroshare.add_resource_files(
            res.short_id,
            source_names=[fed_test_file1_full_path],
            move=False)
        # test resource has one file
        self.assertEqual(res.files.all().count(), 1,
                         msg="Number of content files is not equal to 1")

        file_list = []
        for f in res.files.all():
            file_list.append(os.path.basename(f.storage_path))
        self.assertTrue(self.file_one in file_list,
                        msg='file 1 has not been added in the resource in hydroshare zone')
        # test original file in user test zone still exist after adding it to the resource
        # since 'copy' is used for fed_copy_or_move when adding the file to the resource
        self.assertTrue(self.irods_storage.exists(user_path + self.file_one))

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
        # test to make sure original file still exist after resource deletion
        self.assertTrue(self.irods_storage.exists(user_path + self.file_one))

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

        # create a resource in federated user zone which should trigger quota usage update
        fed_test_file_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_one)
        fed_res = hydroshare.resource.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='My Test Generic Resource in User Zone',
            source_names=[fed_test_file_full_path]
        )
        self.assertEqual(fed_res.files.all().count(), 1,
                         msg="Number of content files is not equal to 1")

        self.assertTrue(fed_res.creator == self.user)
        self.assertTrue(fed_res.get_quota_holder() == self.user)

        fed_istorage = fed_res.get_irods_storage()
        # programmatically set quota size for the test user in user zone
        uz_bagit_path = os.path.join('/', settings.HS_USER_IRODS_ZONE, 'home',
                                     settings.HS_LOCAL_PROXY_USER_IN_FED_ZONE,
                                     settings.IRODS_BAGIT_PATH)
        if not fed_istorage.exists(uz_bagit_path):
            fed_istorage.session.run("imkdir", None, '-p', uz_bagit_path)
        fed_istorage.setAVU(uz_bagit_path, attname, test_qsize)
        super(TestUserZoneIRODSFederation, self).verify_user_quota_usage_avu_in_user_zone(
            attname, test_qsize)

        # Although the resource creation operation above will trigger quota update celery task,
        # in the test environment, celery task is not really executed, so have to test quota update
        # task explicitely here
        update_quota_usage_task(self.user.username)
        uquota = self.user.quotas.first()
        target_qsize = float(test_qsize) * 2
        target_qsize = hydroshare.utils.convert_file_size_to_unit(target_qsize, uquota.unit)
        error = abs(uquota.used_value - target_qsize)
        self.assertLessEqual(error, 0.5, msg='error is ' + str(error))

        # delete test resources
        hydroshare.resource.delete_resource(res.short_id)
        hydroshare.resource.delete_resource(fed_res.short_id)
