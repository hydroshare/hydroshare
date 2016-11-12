import os
from unittest import TestCase

from django.conf import settings
from django.contrib.auth.models import Group

from django_irods.icommands import SessionException
from django_irods.storage import IrodsStorage

from hs_core.models import BaseResource, ResourceFile
from hs_core.hydroshare import resource
from hs_core import hydroshare
from hs_core.views.utils import run_ssh_command
from theme.models import UserProfile
from hs_core.views.utils import create_folder, move_or_rename_file_or_folder, zip_folder, \
    unzip_file, remove_folder

class TestUserZoneIRODSFederation(TestCase):
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
        if not settings.REMOTE_USE_IRODS or settings.HS_USER_ZONE_HOST != 'users.local.org':
            return

        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = hydroshare.create_account(
            'test_user@email.com',
            username='testuser',
            first_name='some_first_name',
            last_name='some_last_name',
            password = 'testuser',
            superuser=False,
            groups=[self.hs_group]
        )

        # create corresponding irods account in user zone
        try:
            exec_cmd = "{0} {1} {2}".format(settings.HS_USER_ZONE_PROXY_USER_CREATE_USER_CMD,
                                            'testuser', 'testuser')
            output = run_ssh_command(host=settings.HS_USER_ZONE_HOST,
                                     uname=settings.HS_USER_ZONE_PROXY_USER,
                                     pwd=settings.HS_USER_ZONE_PROXY_USER_PWD,
                                     exec_cmd=exec_cmd)
            if output:
                if 'ERROR:' in output.upper():
                    # irods account failed to create
                    self.assertRaises(SessionException(-1, output, output))

            user_profile = UserProfile.objects.filter(user=self.user).first()
            user_profile.create_irods_user_account = True
            user_profile.save()
        except Exception as ex:
            self.assertRaises(SessionException(-1, ex.message, ex.message))

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
        self.irods_storage = IrodsStorage('federated')
        irods_target_path = '/' + settings.HS_USER_IRODS_ZONE + '/home/testuser/'
        self.irods_storage.saveFile(self.file_one, irods_target_path + self.file_one)
        self.irods_storage.saveFile(self.file_two, irods_target_path + self.file_two)
        self.irods_storage.saveFile(self.file_three, irods_target_path + self.file_three)
        self.irods_storage.saveFile(self.file_to_be_deleted,
                                    irods_target_path + self.file_to_be_deleted)

    def tearDown(self):
        super(TestUserZoneIRODSFederation, self).tearDown()
        # no need for further cleanup if federation testing is not setup in the first place
        if not settings.REMOTE_USE_IRODS or settings.HS_USER_ZONE_HOST != 'users.local.org':
            return

        # delete irods test user in user zone
        try:
            exec_cmd = "{0} {1}".format(settings.HS_USER_ZONE_PROXY_USER_DELETE_USER_CMD,
                                        'testuser')
            output = run_ssh_command(host=settings.HS_USER_ZONE_HOST,
                                     uname=settings.HS_USER_ZONE_PROXY_USER,
                                     pwd=settings.HS_USER_ZONE_PROXY_USER_PWD,
                                     exec_cmd=exec_cmd)
            if output:
                if 'ERROR:' in output.upper():
                    # there is an error from icommand run, report the error
                    self.assertRaises(SessionException(-1, output, output))

            user_profile = UserProfile.objects.filter(user=self.user).first()
            user_profile.create_irods_user_account = False
            user_profile.save()
        except Exception as ex:
            # there is an error from icommand run, report the error
            self.assertRaises(SessionException(-1, ex.message, ex.message))

        os.remove(self.file_one)
        os.remove(self.file_two)
        os.remove(self.file_three)
        os.remove(self.file_to_be_deleted)

    def test_resource_operations_in_user_zone(self):
        # test resource creation and "move" option in federated user zone
        fed_test_file_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_to_be_deleted)
        new_res = resource.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='My Test Generic Resource in User Zone',
            fed_res_file_names=[fed_test_file_full_path],
            fed_copy_or_move='move'
        )

        self.assertEqual(new_res.files.all().count(), 1,
                         msg="Number of content files is not equal to 1")
        fed_path = '/{zone}/home/{user}'.format(zone=settings.HS_USER_IRODS_ZONE,
                                                user=settings.HS_LOCAL_PROXY_USER_IN_FED_ZONE)
        user_path = '/{zone}/home/testuser/'.format(zone=settings.HS_USER_IRODS_ZONE)
        self.assertEqual(new_res.resource_federation_path, fed_path)
        # test original file in user test zone is removed after resource creation
        # since 'move' is used for fed_copy_or_move when creating the resource
        self.assertFalse(self.irods_storage.exists(user_path + self.file_to_be_deleted))

        # test resource file deletion
        new_res.files.all().delete()
        self.assertEqual(new_res.files.all().count(), 0,
                         msg="Number of content files is not equal to 0")

        # test add multiple files and 'copy' option in federated user zone
        fed_test_file1_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_one)
        fed_test_file2_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_two)
        hydroshare.add_resource_files(
            new_res.short_id,
            fed_res_file_names=[fed_test_file1_full_path, fed_test_file2_full_path],
            fed_copy_or_move='copy',
            fed_zone_home_path=new_res.resource_federation_path)
        # test resource has two files
        self.assertEqual(new_res.files.all().count(), 2,
                         msg="Number of content files is not equal to 2")

        file_list = []
        for f in new_res.files.all():
            file_list.append(f.fed_resource_file_name_or_path.split('/')[-1])
        self.assertTrue(self.file_one in file_list,
                        msg='file 1 has not been added in the resource in user zone')
        self.assertTrue(self.file_two in file_list,
                        msg='file 2 has not been added in the resource in user zone')
        # test original two files in user test zone still exist after adding them to the resource
        # since 'copy' is used for fed_copy_or_move when creating the resource
        self.assertTrue(self.irods_storage.exists(user_path + self.file_one))
        self.assertTrue(self.irods_storage.exists(user_path + self.file_two))

        # test resource deletion
        resource.delete_resource(new_res.short_id)
        self.assertEquals(BaseResource.objects.all().count(), 0,
                          msg='Number of resources not equal to 0')

        # test create new version resource in user zone
        fed_test_file1_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_one)
        ori_res = resource.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='My Original Generic Resource in User Zone',
            fed_res_file_names=[fed_test_file1_full_path],
            fed_copy_or_move='copy'
        )
        # make sure ori_res is created in federated user zone
        fed_path = '/{zone}/home/{user}'.format(zone=settings.HS_USER_IRODS_ZONE,
                                                user=settings.HS_LOCAL_PROXY_USER_IN_FED_ZONE)
        self.assertEqual(ori_res.resource_federation_path, fed_path)
        self.assertEqual(ori_res.files.all().count(), 1,
                         msg="Number of content files is not equal to 1")

        new_res = hydroshare.create_new_version_empty_resource(ori_res.short_id, self.user)
        new_res = hydroshare.create_new_version_resource(ori_res, new_res, self.user)
        # only need to test file-related attributes
        # ensure new versioned resource is created in the same federation zone as original resource
        self.assertEqual(ori_res.resource_federation_path, new_res.resource_federation_path)
        # ensure new versioned resource has the same number of content files as original resource
        self.assertEqual(ori_res.files.all().count(), new_res.files.all().count())
        # delete resources to clean up
        resource.delete_resource(new_res.short_id)
        resource.delete_resource(ori_res.short_id)

        # test folder operations in user zone
        fed_file1_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_one)
        fed_file2_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_two)
        fed_file3_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_three)
        new_res = resource.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='My Original Generic Resource in User Zone',
            fed_res_file_names=[fed_file1_full_path, fed_file2_full_path, fed_file3_full_path],
            fed_copy_or_move='copy'
        )
        # make sure new_res is created in federated user zone
        fed_path = '/{zone}/home/{user}'.format(zone=settings.HS_USER_IRODS_ZONE,
                                                user=settings.HS_LOCAL_PROXY_USER_IN_FED_ZONE)
        self.assertEqual(new_res.resource_federation_path, fed_path)
        # resource should has only three files at this point
        self.assertEqual(new_res.files.all().count(), 3,
                         msg="resource file count didn't match")
        create_folder(new_res.short_id, 'data/contents/sub_test_dir')
        istorage = new_res.get_irods_storage()
        store = istorage.listdir(new_res.short_id + '/data/contents')
        self.assertIn('sub_test_dir', store[0], msg='resource does not contain sub folder created')

        # rename a file
        move_or_rename_file_or_folder(self.user, new_res.short_id,
                                      'data/contents/file3.txt', 'data/contents/file3_new.txt')
        # move two files to the new folder
        move_or_rename_file_or_folder(self.user, new_res.short_id,
                                      'data/contents/file1.txt',
                                      'data/contents/sub_test_dir/file1.txt')
        move_or_rename_file_or_folder(self.user, new_res.short_id,
                                      'data/contents/file2.txt',
                                      'data/contents/sub_test_dir/file2.txt')

        updated_res_file_names = []
        for rf in ResourceFile.objects.filter(object_id=new_res.id):
            updated_res_file_names.append(rf.fed_resource_file_name_or_path)
        self.assertIn(new_res.short_id + '/data/contents/file3_new.txt',
                      updated_res_file_names,
                      msg="resource does not contain the updated file file3_new.txt")
        self.assertNotIn(new_res.short_id + '/data/contents/file3.txt',
                         updated_res_file_names,
                         msg="resource still contains the old file file3.txt after renaming")
        self.assertIn(new_res.short_id + '/data/contents/sub_test_dir/file1.txt',
                      updated_res_file_names,
                      msg="resource does not contain file1.txt moved to a folder")
        self.assertNotIn(new_res.short_id + '/data/contents/file1.txt',
                         updated_res_file_names,
                         msg="resource still contains the old file1.txt after moving to a folder")
        self.assertIn(new_res.short_id + '/data/contents/sub_test_dir/file2.txt',
                      updated_res_file_names,
                      msg="resource does not contain file2.txt moved to a new folder")
        self.assertNotIn(new_res.short_id + '/data/contents/file2.txt',
                         updated_res_file_names,
                         msg="resource still contains the old file2.txt after moving to a folder")

        # zip the folder
        output_zip_fname, size = \
            zip_folder(self.user, new_res.short_id, 'data/contents/sub_test_dir',
                       'sub_test_dir.zip', True)
        self.assertGreater(size, 0, msg='zipped file has a size of 0')
        # Now resource should contain only two files: file3_new.txt and sub_test_dir.zip
        # since the folder is zipped into sub_test_dir.zip with the folder deleted
        self.assertEqual(new_res.files.all().count(), 2,
                         msg="resource file count didn't match")

        # unzip the file
        unzip_file(self.user, new_res.short_id, 'data/contents/sub_test_dir.zip', True)
        # Now resource should contain three files: file1.txt, file2.txt, and file3_new.txt
        self.assertEqual(new_res.files.all().count(), 3,
                         msg="resource file count didn't match")
        updated_res_file_names = []
        for rf in ResourceFile.objects.filter(object_id=new_res.id):
            updated_res_file_names.append(rf.fed_resource_file_name_or_path)
        self.assertNotIn(new_res.short_id + '/data/contents/sub_test_dir.zip',
                         updated_res_file_names,
                         msg="resource still contains the zip file after unzipping")
        self.assertIn(new_res.short_id + '/data/contents/sub_test_dir/file1.txt',
                      updated_res_file_names,
                      msg='resource does not contain unzipped file file1.txt')
        self.assertIn(new_res.short_id + '/data/contents/sub_test_dir/file2.txt',
                      updated_res_file_names,
                      msg='resource does not contain unzipped file file2.txt')
        self.assertIn(new_res.short_id + '/data/contents/file3_new.txt',
                      updated_res_file_names,
                      msg="resource does not contain untouched file3_new.txt after unzip")

        # rename a folder
        move_or_rename_file_or_folder(self.user, new_res.short_id,
                                      'data/contents/sub_test_dir', 'data/contents/sub_dir')
        updated_res_file_names = []
        for rf in ResourceFile.objects.filter(object_id=new_res.id):
            updated_res_file_names.append(rf.fed_resource_file_name_or_path)

        self.assertNotIn(new_res.short_id + '/data/contents/sub_test_dir/file1.txt',
                         updated_res_file_names,
                         msg="resource still contains file1.txt in the old folder after renaming")
        self.assertIn(new_res.short_id + '/data/contents/sub_dir/file1.txt',
                      updated_res_file_names,
                      msg="resource does not contain file1.txt in the new folder after renaming")
        self.assertNotIn(new_res.short_id + '/data/contents/sub_test_dir/file2.txt',
                         updated_res_file_names,
                         msg="resource still contains file2.txt in the old folder after renaming")
        self.assertIn(new_res.short_id + '/data/contents/sub_dir/file2.txt',
                      updated_res_file_names,
                      msg="resource does not contain file2.txt in the new folder after renaming")

        # remove a folder
        remove_folder(self.user, new_res.short_id, 'data/contents/sub_dir')
        # Now resource only contains one file
        self.assertEqual(new_res.files.all().count(), 1,
                         msg="resource file count didn't match")
        res_fname = ResourceFile.objects.filter(
            object_id=new_res.id)[0].fed_resource_file_name_or_path
        self.assertEqual(res_fname, new_res.short_id + '/data/contents/file3_new.txt')

        # delete resources to clean up
        resource.delete_resource(new_res.short_id)
