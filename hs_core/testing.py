import os

from django.conf import settings

from hs_core.models import ResourceFile
from hs_core.hydroshare import add_resource_files
from hs_core.views.utils import create_folder, move_or_rename_file_or_folder, zip_folder, \
    unzip_file, remove_folder
from django_irods.icommands import SessionException

import logging

logger = logging.getLogger('django')

class MockIRODSTestCaseMixin(object):
    def setUp(self):
        super(MockIRODSTestCaseMixin, self).setUp()
        # only mock up testing iRODS operations when local iRODS container is not used
        if settings.IRODS_HOST != 'data.local.org':
            from mock import patch
            self.irods_patchers = (
                patch("hs_core.hydroshare.hs_bagit.delete_bag"),
                patch("hs_core.hydroshare.hs_bagit.create_bag"),
                patch("hs_core.hydroshare.hs_bagit.create_bag_files"),
                patch("hs_core.tasks.create_bag_by_irods"),
                patch("hs_core.hydroshare.utils.copy_resource_files_and_AVUs"),
            )
            for patcher in self.irods_patchers:
                patcher.start()

    def tearDown(self):
        if settings.IRODS_HOST != 'data.local.org':
            for patcher in self.irods_patchers:
                patcher.stop()
        super(MockIRODSTestCaseMixin, self).tearDown()


class TestCaseCommonUtilities(object):
    def resource_file_oprs(self):
        """
        This is a common test utility function to be called by both regular folder operation
        testing and federated zone folder operation testing.
        Make sure the calling TestCase object has the following attributes defined before calling
        this method:
        self.res: resource that has been created that contains files listed in file_name_list
        self.user: owner of the resource
        self.file_name_list: a list of three file names that have been added to the res object
        self.test_file_1 needs to be present for the calling object for doing regular folder
        operations without involving federated zone so that the same opened file can be readded
        to the resource for testing the case where zipping cannot overwrite existing file
        """

        user = self.user
        res = self.res
        file_name_list = self.file_name_list
        # create a folder, if folder is created successfully, no exception is raised, otherwise,
        # an iRODS exception will be raised which will be caught by the test runner and mark as
        # a test failure
        create_folder(res.short_id, 'data/contents/sub_test_dir')
        istorage = res.get_irods_storage()
        if res.resource_federation_path:
            res_path = os.path.join(res.resource_federation_path, res.short_id, 'data', 'contents')
            store = istorage.listdir(res_path)
        else:
            store = istorage.listdir(res.short_id + '/data/contents')
        self.assertIn('sub_test_dir', store[0], msg='resource does not contain sub folder created')

        # rename the third file in file_name_list
        move_or_rename_file_or_folder(user, res.short_id,
                                      'data/contents/' + file_name_list[2],
                                      'data/contents/new_' + file_name_list[2])
        # move the first two files in file_name_list to the new folder
        move_or_rename_file_or_folder(user, res.short_id,
                                      'data/contents/' + file_name_list[0],
                                      'data/contents/sub_test_dir/' + file_name_list[0])
        move_or_rename_file_or_folder(user, res.short_id,
                                      'data/contents/' + file_name_list[1],
                                      'data/contents/sub_test_dir/' + file_name_list[1])

        updated_res_file_names = []
        for rf in ResourceFile.objects.filter(object_id=res.id):
            if res.resource_federation_path:
                updated_res_file_names.append(rf.fed_resource_file_name_or_path)
            else:
                updated_res_file_names.append(rf.resource_file.name)

        if res.resource_federation_path:
            path_prefix = 'data/contents/'
        else:
            path_prefix = res.short_id + '/data/contents/'
        logger.debug('in testing.py, updated_res_file_names='+' '.join(updated_res_file_names))
        self.assertIn(path_prefix + 'new_' + file_name_list[2], updated_res_file_names,
                      msg="resource does not contain the updated file new_" + file_name_list[2])
        self.assertNotIn(path_prefix + file_name_list[2], updated_res_file_names,
                         msg='resource still contains the old file ' + file_name_list[2] +
                             ' after renaming')
        self.assertIn(path_prefix + 'sub_test_dir/' + file_name_list[0], updated_res_file_names,
                      msg='resource does not contain ' + file_name_list[0] + ' moved to a folder')
        self.assertNotIn(path_prefix + file_name_list[0], updated_res_file_names,
                         msg='resource still contains the old ' + file_name_list[0] +
                             'after moving to a folder')
        self.assertIn(path_prefix + 'sub_test_dir/' + file_name_list[1], updated_res_file_names,
                      msg='resource does not contain ' + file_name_list[1] + 'moved to a new folder')
        self.assertNotIn(path_prefix + file_name_list[1], updated_res_file_names,
                         msg='resource still contains the old ' + file_name_list[1] +
                             ' after moving to a folder')

        # zip the folder
        output_zip_fname, size = \
            zip_folder(user, res.short_id, 'data/contents/sub_test_dir',
                       'sub_test_dir.zip', True)
        self.assertGreater(size, 0, msg='zipped file has a size of 0')
        # Now resource should contain only two files: new_file3.txt and sub_test_dir.zip
        # since the folder is zipped into sub_test_dir.zip with the folder deleted
        self.assertEqual(res.files.all().count(), 2,
                         msg="resource file count didn't match-")

        # test unzip does not allow override of existing files
        # add an existing file in the zip to the resource
        if res.resource_federation_path:
            fed_test_file1_full_path = '/{zone}/home/{uname}/{fname}'.format(
                zone=settings.HS_USER_IRODS_ZONE, uname=user.username, fname=file_name_list[0])
            add_resource_files(res.short_id, fed_res_file_names=[fed_test_file1_full_path],
                               fed_copy_or_move='copy',
                               fed_zone_home_path=res.resource_federation_path)

        else:
            add_resource_files(res.short_id, self.test_file_1)

        create_folder(res.short_id, 'data/contents/sub_test_dir')
        move_or_rename_file_or_folder(user, res.short_id,
                                      'data/contents/' + file_name_list[0],
                                      'data/contents/sub_test_dir/' + file_name_list[0])
        # Now resource should contain three files: file3_new.txt, sub_test_dir.zip, and file1.txt
        self.assertEqual(res.files.all().count(), 3, msg="resource file count didn't match")
        with self.assertRaises(SessionException):
            unzip_file(user, res.short_id, 'data/contents/sub_test_dir.zip', False)

        # Resource should still contain three files: file3_new.txt, sub_test_dir.zip, and file1.txt
        file_cnt = res.files.all().count()
        self.assertEqual(file_cnt, 3, msg="resource file count didn't match - " +
                                          str(file_cnt) + " != 3")

        # test unzipping the file succeeds now after deleting the existing file
        remove_folder(user, res.short_id, 'data/contents/sub_test_dir')
        # Now resource should contain two files: file3_new.txt and sub_test_dir.zip
        file_cnt = res.files.all().count()
        self.assertEqual(file_cnt, 2, msg="resource file count didn't match - " +
                                          str(file_cnt) + " != 2")
        unzip_file(user, res.short_id, 'data/contents/sub_test_dir.zip', True)
        # Now resource should contain three files: file1.txt, file2.txt, and file3_new.txt
        self.assertEqual(res.files.all().count(), 3, msg="resource file count didn't match")
        updated_res_file_names = []
        for rf in ResourceFile.objects.filter(object_id=res.id):
            if res.resource_federation_path:
                updated_res_file_names.append(rf.fed_resource_file_name_or_path)
            else:
                updated_res_file_names.append(rf.resource_file.name)
        self.assertNotIn(path_prefix + 'sub_test_dir.zip', updated_res_file_names,
                         msg="resource still contains the zip file after unzipping")
        self.assertIn(path_prefix + 'sub_test_dir/' + file_name_list[0], updated_res_file_names,
                      msg='resource does not contain unzipped file ' + file_name_list[0])
        self.assertIn(path_prefix + 'sub_test_dir/' + file_name_list[1], updated_res_file_names,
                      msg='resource does not contain unzipped file ' + file_name_list[1])
        self.assertIn(path_prefix + 'new_' + file_name_list[2], updated_res_file_names,
                      msg='resource does not contain unzipped file new_' + file_name_list[2])

        # rename a folder
        move_or_rename_file_or_folder(user, res.short_id,
                                      'data/contents/sub_test_dir', 'data/contents/sub_dir')
        updated_res_file_names = []
        for rf in ResourceFile.objects.filter(object_id=res.id):
            if res.resource_federation_path:
                updated_res_file_names.append(rf.fed_resource_file_name_or_path)
            else:
                updated_res_file_names.append(rf.resource_file.name)

        self.assertNotIn(path_prefix + 'sub_test_dir/' + file_name_list[0], updated_res_file_names,
                         msg='resource still contains ' + file_name_list[0] +
                             ' in the old folder after renaming')
        self.assertIn(path_prefix + 'sub_dir/' + file_name_list[0], updated_res_file_names,
                      msg='resource does not contain ' + file_name_list[0] +
                          ' in the new folder after renaming')
        self.assertNotIn(path_prefix + 'sub_test_dir/' + file_name_list[1], updated_res_file_names,
                         msg='resource still contains ' + file_name_list[1] +
                             ' in the old folder after renaming')
        self.assertIn(path_prefix + 'sub_dir/' + file_name_list[1], updated_res_file_names,
                      msg='resource does not contain ' + file_name_list[1] +
                          ' in the new folder after renaming')

        # remove a folder
        remove_folder(user, res.short_id, 'data/contents/sub_dir')
        # Now resource only contains one file
        self.assertEqual(res.files.all().count(), 1, msg="resource file count didn't match")
        if res.resource_federation_path:
            res_fname = ResourceFile.objects.filter(
                object_id=res.id)[0].fed_resource_file_name_or_path
        else:
            res_fname = ResourceFile.objects.filter(object_id=res.id)[0].resource_file.name
        self.assertEqual(res_fname, path_prefix + 'new_' + file_name_list[2])
