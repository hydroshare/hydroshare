import os

from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin, TestCaseCommonUtilities

from hs_core.models import ResourceFile


class TestResourceFileAPI(MockIRODSTestCaseMixin,
                          TestCaseCommonUtilities, TransactionTestCase):
    def setUp(self):
        self.hydroshare_author_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user to be used for creating the resource
        self.user = hydroshare.create_account(
            'creator@usu.edu',
            username='creator',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        self.res = hydroshare.create_resource(
            'GenericResource',
            self.user,
            'My Test Resource'
        )

        # create three files
        self.test_file_name1 = 'file1.txt'
        self.test_file_name2 = 'file2.txt'
        self.test_file_name3 = 'file3.txt'
        self.file_name_list = [self.test_file_name1, self.test_file_name2, self.test_file_name3]

        # put predictable contents into these
        test_file = open(self.test_file_name1, 'w')
        test_file.write("Test text file in file1.txt")
        test_file.close()

        test_file = open(self.test_file_name2, 'w')
        test_file.write("Test text file in file2.txt")
        test_file.close()

        test_file = open(self.test_file_name3, 'w')
        test_file.write("Test text file in file3.txt")
        test_file.close()

        self.test_file_1 = open(self.test_file_name1, 'r')
        self.test_file_2 = open(self.test_file_name2, 'r')
        self.test_file_3 = open(self.test_file_name3, 'r')

    def tearDown(self):
        self.test_file_1.close()
        os.remove(self.test_file_1.name)
        self.test_file_2.close()
        os.remove(self.test_file_2.name)
        self.test_file_3.close()
        os.remove(self.test_file_3.name)

    def test_unfederated_root_path_setting(self):
        """ an unfederated file in the root folder has the proper state after state changes """
        # resource should not have any files at this point
        self.assertEqual(self.res.files.all().count(), 0,
                         msg="resource file count didn't match")

        # add one file to the resource
        hydroshare.add_resource_files(self.res.short_id, self.test_file_1)

        # resource should has only one file at this point
        self.assertEqual(self.res.files.all().count(), 1,
                         msg="resource file count didn't match")

        # get the handle of the file created above
        resfile = self.res.files.all()[0]

        # determine where that file should live
        shortpath = os.path.join(self.res.short_id, "data",
                                 "contents", "file1.txt")

        self.assertEqual(resfile.file_folder, None)
        self.assertEqual(resfile.storage_path, shortpath)

        # try setting to an unqualified name; should qualify it
        resfile.set_storage_path("file1.txt")
        # should match computed path
        self.assertEqual(resfile.file_folder, None)
        self.assertEqual(resfile.storage_path, shortpath)
        # now try to change that path to what it is already
        resfile.set_storage_path(shortpath)
        # should match computed path
        self.assertEqual(resfile.file_folder, None)
        self.assertEqual(resfile.storage_path, shortpath)

        # should throw out a variety of invalid paths
        # TODO: how to eliminate this particular error.
        # dumbpath = 'x' + shortpath
        # with self.assertRaises(ValidationError):
        #     resfile.set_storage_path(dumbpath)
        # self.assertEqual(resfile.file_folder, None)
        # self.assertEqual(resfile.resource_file.name, shortpath)

        dumbpath = self.res.short_id + "file1.txt"
        with self.assertRaises(ValidationError):
            resfile.set_storage_path(dumbpath)
        self.assertEqual(resfile.file_folder, None)
        self.assertEqual(resfile.resource_file.name, shortpath)

        # delete resources to clean up
        hydroshare.delete_resource(self.res.short_id)

    def test_unfederated_folder_path_setting(self):
        """ an unfederated file in the root folder has the proper state after state changes """
        # resource should not have any files at this point
        self.assertEqual(self.res.files.all().count(), 0,
                         msg="resource file count didn't match")

        ResourceFile.create_folder(self.res, 'foo')

        # add one file to the resource
        hydroshare.add_resource_files(self.res.short_id, self.test_file_1)

        # resource should has only one file at this point
        self.assertEqual(self.res.files.all().count(), 1,
                         msg="resource file count didn't match")

        # get the handle of the file created above
        resfile = self.res.files.all()[0]

        # determine where that file should live
        shortpath = os.path.join(self.res.short_id, "data",
                                 "contents", "file1.txt")

        self.assertEqual(resfile.file_folder, "foo")
        self.assertEqual(resfile.storage_path, shortpath)

        # try setting to an unqualified name; should qualify it
        resfile.set_storage_path("file1.txt")
        # should match computed path
        self.assertEqual(resfile.file_folder, "foo")
        self.assertEqual(resfile.storage_path, shortpath)
        # now try to change that path to what it is already
        resfile.set_storage_path(shortpath)
        # should match computed path
        self.assertEqual(resfile.file_folder, None)
        self.assertEqual(resfile.storage_path, shortpath)

        # should throw out a variety of invalid paths
        # TODO: how to eliminate this particular error.
        # dumbpath = 'x' + shortpath
        # with self.assertRaises(ValidationError):
        #     resfile.set_storage_path(dumbpath)
        # self.assertEqual(resfile.file_folder, None)
        # self.assertEqual(resfile.resource_file.name, shortpath)

        dumbpath = self.res.short_id + "file1.txt"
        with self.assertRaises(ValidationError):
            resfile.set_storage_path(dumbpath)
        self.assertEqual(resfile.file_folder, "foo")
        self.assertEqual(resfile.resource_file.name, shortpath)

        # clean up after folder test
        ResourceFile.remove_folder(self.res, 'foo')

        # delete resources to clean up
        hydroshare.delete_resource(self.res.short_id)
