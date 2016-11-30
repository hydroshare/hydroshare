import os

from django.test import TransactionTestCase
from django.contrib.auth.models import User, Group

from hs_core import hydroshare
from hs_core.models import GenericResource, ResourceFile
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core.views.utils import create_folder, move_or_rename_file_or_folder, zip_folder, \
    unzip_file, remove_folder
from django_irods.icommands import SessionException


class TestResourceFileFolderOprsAPI(MockIRODSTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(TestResourceFileFolderOprsAPI, self).setUp()
        self.hydroshare_author_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user to be used for creating the resource
        self.user_creator = hydroshare.create_account(
            'creator@usu.edu',
            username='creator',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        self.new_res = hydroshare.create_resource(
            'GenericResource',
            self.user_creator,
            'My Test Resource'
        )

        # create three files
        test_file_name1 = 'file1.txt'
        test_file_name2 = 'file2.txt'
        test_file_name3 = 'file3.txt'

        test_file = open(test_file_name1, 'w')
        test_file.write("Test text file in file1.txt")
        test_file.close()

        test_file = open(test_file_name2, 'w')
        test_file.write("Test text file in file2.txt")
        test_file.close()

        test_file = open(test_file_name3, 'w')
        test_file.write("Test text file in file3.txt")
        test_file.close()

        self.test_file_1 = open(test_file_name1, 'r')
        self.test_file_2 = open(test_file_name2, 'r')
        self.test_file_3 = open(test_file_name3, 'r')

    def tearDown(self):
        super(TestResourceFileFolderOprsAPI, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        GenericResource.objects.all().delete()
        self.test_file_1.close()
        os.remove(self.test_file_1.name)
        self.test_file_2.close()
        os.remove(self.test_file_2.name)
        self.test_file_3.close()
        os.remove(self.test_file_3.name)

    def test_resource_file_folder_oprs(self):
        # resource should not have any files at this point
        self.assertEqual(self.new_res.files.all().count(), 0,
                         msg="resource file count didn't match")

        # add the three files to the resource
        hydroshare.add_resource_files(self.new_res.short_id, self.test_file_1, self.test_file_2,
                                      self.test_file_3)

        # resource should has only three files at this point
        self.assertEqual(self.new_res.files.all().count(), 3,
                         msg="resource file count didn't match")

        # create a folder, if folder is created successfully, no exception is raised, otherwise,
        # an iRODS exception will be raised which will be caught by the test runner and mark as
        # a test failure
        create_folder(self.new_res.short_id, 'data/contents/sub_test_dir')

        istorage = self.new_res.get_irods_storage()
        store = istorage.listdir(self.new_res.short_id + '/data/contents')
        self.assertIn('sub_test_dir', store[0], msg='resource does not contain sub folder created')

        # rename a file
        move_or_rename_file_or_folder(self.user_creator, self.new_res.short_id,
                                      'data/contents/file3.txt', 'data/contents/file3_new.txt')
        # move two files to the new folder
        move_or_rename_file_or_folder(self.user_creator, self.new_res.short_id,
                                      'data/contents/file1.txt',
                                      'data/contents/sub_test_dir/file1.txt')
        move_or_rename_file_or_folder(self.user_creator, self.new_res.short_id,
                                      'data/contents/file2.txt',
                                      'data/contents/sub_test_dir/file2.txt')

        updated_res_file_names = []
        for rf in ResourceFile.objects.filter(object_id=self.new_res.id):
            updated_res_file_names.append(rf.resource_file.name)
        self.assertIn(self.new_res.short_id + '/data/contents/file3_new.txt',
                      updated_res_file_names,
                      msg="resource does not contain the updated file file3_new.txt")
        self.assertNotIn(self.new_res.short_id + '/data/contents/file3.txt',
                         updated_res_file_names,
                         msg="resource still contains the old file file3.txt after renaming")
        self.assertIn(self.new_res.short_id + '/data/contents/sub_test_dir/file1.txt',
                      updated_res_file_names,
                      msg="resource does not contain file1.txt moved to a folder")
        self.assertNotIn(self.new_res.short_id + '/data/contents/file1.txt',
                         updated_res_file_names,
                         msg="resource still contains the old file1.txt after moving to a folder")
        self.assertIn(self.new_res.short_id + '/data/contents/sub_test_dir/file2.txt',
                      updated_res_file_names,
                      msg="resource does not contain file2.txt moved to a new folder")
        self.assertNotIn(self.new_res.short_id + '/data/contents/file2.txt',
                         updated_res_file_names,
                         msg="resource still contains the old file2.txt after moving to a folder")

        # zip the folder
        output_zip_fname, size = \
            zip_folder(self.user_creator, self.new_res.short_id, 'data/contents/sub_test_dir',
                       'sub_test_dir.zip', True)
        self.assertGreater(size, 0, msg='zipped file has a size of 0')
        # Now resource should contain only two files: file3_new.txt and sub_test_dir.zip
        # since the folder is zipped into sub_test_dir.zip with the folder deleted
        self.assertEqual(self.new_res.files.all().count(), 2,
                         msg="resource file count didn't match")

        # test unzip does not allow override of existing files
        # add an existing file in the zip to the resource
        hydroshare.add_resource_files(self.new_res.short_id, self.test_file_1)
        create_folder(self.new_res.short_id, 'data/contents/sub_test_dir')
        move_or_rename_file_or_folder(self.user_creator, self.new_res.short_id,
                                      'data/contents/file1.txt',
                                      'data/contents/sub_test_dir/file1.txt')
        # Now resource should contain three files: file3_new.txt, sub_test_dir.zip, and file1.txt
        self.assertEqual(self.new_res.files.all().count(), 3,
                         msg="resource file count didn't match")
        with self.assertRaises(SessionException):
            unzip_file(self.user_creator, self.new_res.short_id, 'data/contents/sub_test_dir.zip',
                       False)

        # Resource should still contain three files: file3_new.txt, sub_test_dir.zip, and file1.txt
        file_cnt = self.new_res.files.all().count()
        self.assertEqual(file_cnt, 3,
                         msg="resource file count didn't match - " + str(file_cnt) + " != 3")
        with self.assertRaises(SessionException):
            unzip_file(self.user_creator, self.new_res.short_id,
                       'data/contents/sub_test_dir.zip',
                       False)

        # test unzipping the file succeeds now after deleting the existing file
        remove_folder(self.user_creator, self.new_res.short_id, 'data/contents/sub_test_dir')
        # Now resource should contain two files: file3_new.txt and sub_test_dir.zip
        file_cnt = self.new_res.files.all().count()
        self.assertEqual(file_cnt, 2,
                         msg="resource file count didn't match - " + str(file_cnt) + " != 2")
        unzip_file(self.user_creator, self.new_res.short_id, 'data/contents/sub_test_dir.zip', True)
        # Now resource should contain three files: file1.txt, file2.txt, and file3_new.txt
        self.assertEqual(self.new_res.files.all().count(), 3,
                         msg="resource file count didn't match")
        updated_res_file_names = []
        for rf in ResourceFile.objects.filter(object_id=self.new_res.id):
            updated_res_file_names.append(rf.resource_file.name)
        self.assertNotIn(self.new_res.short_id + '/data/contents/sub_test_dir.zip',
                         updated_res_file_names,
                         msg="resource still contains the zip file after unzipping")
        self.assertIn(self.new_res.short_id + '/data/contents/sub_test_dir/file1.txt',
                      updated_res_file_names,
                      msg='resource does not contain unzipped file file1.txt')
        self.assertIn(self.new_res.short_id + '/data/contents/sub_test_dir/file2.txt',
                      updated_res_file_names,
                      msg='resource does not contain unzipped file file2.txt')
        self.assertIn(self.new_res.short_id + '/data/contents/file3_new.txt',
                      updated_res_file_names,
                      msg="resource does not contain untouched file3_new.txt after unzip")

        # rename a folder
        move_or_rename_file_or_folder(self.user_creator, self.new_res.short_id,
                                      'data/contents/sub_test_dir', 'data/contents/sub_dir')
        updated_res_file_names = []
        for rf in ResourceFile.objects.filter(object_id=self.new_res.id):
            updated_res_file_names.append(rf.resource_file.name)

        self.assertNotIn(self.new_res.short_id + '/data/contents/sub_test_dir/file1.txt',
                         updated_res_file_names,
                         msg="resource still contains file1.txt in the old folder after renaming")
        self.assertIn(self.new_res.short_id + '/data/contents/sub_dir/file1.txt',
                      updated_res_file_names,
                      msg="resource does not contain file1.txt in the new folder after renaming")
        self.assertNotIn(self.new_res.short_id + '/data/contents/sub_test_dir/file2.txt',
                         updated_res_file_names,
                         msg="resource still contains file2.txt in the old folder after renaming")
        self.assertIn(self.new_res.short_id + '/data/contents/sub_dir/file2.txt',
                      updated_res_file_names,
                      msg="resource does not contain file2.txt in the new folder after renaming")

        # remove a folder
        remove_folder(self.user_creator, self.new_res.short_id, 'data/contents/sub_dir')
        # Now resource only contains one file
        self.assertEqual(self.new_res.files.all().count(), 1,
                         msg="resource file count didn't match")
        res_fname = ResourceFile.objects.filter(object_id=self.new_res.id)[0].resource_file.name
        self.assertEqual(res_fname, self.new_res.short_id + '/data/contents/file3_new.txt')
