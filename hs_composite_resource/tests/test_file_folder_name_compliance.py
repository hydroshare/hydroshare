import os
import unittest

from django.contrib.auth.models import Group, User
from django.core.exceptions import SuspiciousFileOperation

from hs_core.hydroshare.resource import add_resource_files, create_resource
from hs_core.hydroshare.users import create_account
from hs_core.models import ResourceFile
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core.views.utils import move_or_rename_file_or_folder
from ..models import CompositeResource


class TestAddResourceFiles(MockIRODSTestCaseMixin, unittest.TestCase):
    def setUp(self):
        super(TestAddResourceFiles, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = create_account(
            'shauntheta@gmail.com',
            username='shaun',
            first_name='Shaun',
            last_name='Livingston',
            superuser=False,
            groups=[]
        )

        # create a resource
        self.res = create_resource(resource_type='CompositeResource',
                                   owner=self.user,
                                   title='Test Resource',
                                   metadata=[], )

        # create files - filenames are compliant
        self.compliant_file_name_1 = "test 1.txt"
        self.compliant_file_name_2 = "tes-2.txt"
        self.compliant_non_english_file_name = "résumé-2.txt"
        self.bad_files = []
        for banned_symbol in ResourceFile.banned_symbols():
            if banned_symbol == '/':
                continue
            bad_file_name = f"my-test{banned_symbol}.txt"
            test_file = open(bad_file_name, 'w')
            test_file.write("Test text file name contains banned characters")
            test_file.close()
            test_file = open(bad_file_name, 'rb')
            self.bad_files.append(test_file)

        # filename contains a space at the start
        self.non_compliant_file_name_1 = " test-1.txt"
        # filename contains a space at the end
        self.non_compliant_file_name_2 = "test-2.txt "

        test_file = open(self.compliant_file_name_1, 'w')
        test_file.write("Test text file in test-1.txt")
        test_file.close()

        test_file = open(self.compliant_file_name_2, 'w')
        test_file.write("Test text file in test-2.txt")
        test_file.close()

        test_file = open(self.compliant_non_english_file_name, 'w')
        test_file.write("Test text file in résumé-2.txt")
        test_file.close()

        test_file = open(self.non_compliant_file_name_1, 'w')
        test_file.write("Test text file in test 1.txt")
        test_file.close()

        test_file = open(self.non_compliant_file_name_2, 'w')
        test_file.write("Test text file in test-(2).txt")
        test_file.close()

        # open files for read and upload
        self.compliant_file_1 = open(self.compliant_file_name_1, "rb")
        self.compliant_file_2 = open(self.compliant_file_name_2, "rb")
        self.compliant_non_english_file = open(self.compliant_non_english_file_name, "rb")

        self.non_compliant_file_1 = open(self.non_compliant_file_name_1, "rb")
        self.non_compliant_file_2 = open(self.non_compliant_file_name_2, "rb")

    def tearDown(self):
        super(TestAddResourceFiles, self).tearDown()
        self.res.delete()
        User.objects.all().delete()
        Group.objects.all().delete()
        CompositeResource.objects.all().delete()

        self.compliant_file_1.close()
        os.remove(self.compliant_file_1.name)

        self.compliant_file_2.close()
        os.remove(self.compliant_file_2.name)

        self.compliant_non_english_file.close()
        os.remove(self.compliant_non_english_file.name)

        self.non_compliant_file_1.close()
        os.remove(self.non_compliant_file_1.name)
        self.non_compliant_file_2.close()
        os.remove(self.non_compliant_file_2.name)

        for bad_file in self.bad_files:
            bad_file.close()
            os.remove(bad_file.name)

    def test_add_compliant_files(self):
        """Here we are adding files that have filename that meets hydroshare file naming constraints
         These files should be successfully added to the resource
         """
        # add files - this is the api we are testing
        add_resource_files(self.res.short_id, self.compliant_file_1, self.compliant_file_2,
                           self.compliant_non_english_file)

        # resource should have 3 files
        self.assertEqual(self.res.files.all().count(), 3)

        # add each file of resource to list
        file_list = []
        for f in self.res.files.all():
            file_list.append(f.short_path)
            print(f"added res filename:{f.short_path}")

        # check if the file name is in the list of files
        sanitized_file_name = self.compliant_file_name_1.replace(" ", "_")
        self.assertTrue(sanitized_file_name in file_list, f"{self.compliant_file_name_1} has not been added")
        self.assertTrue(self.compliant_file_name_2 in file_list, f"{self.compliant_file_name_2} has not been added")
        self.assertTrue(self.compliant_non_english_file_name in file_list,
                        f"{self.compliant_non_english_file_name} has not been added")

    def test_add_non_compliant_files(self):
        """Here we are testing when a file that has a name which doesn't meet hydroshare requirements is uploaded
        to a resource the upload operation should fail.
        """
        # resource should have no files
        self.assertEqual(self.res.files.all().count(), 0)
        self.assertGreater(len(self.bad_files), 0)
        for bad_test_file in self.bad_files:
            with self.assertRaises(SuspiciousFileOperation):
                add_resource_files(self.res.short_id, bad_test_file)

        # resource should have no files
        self.assertEqual(self.res.files.all().count(), 0)

        # add one file that is not compliant and another file that is compliant
        with self.assertRaises(SuspiciousFileOperation):
            add_resource_files(self.res.short_id, self.non_compliant_file_1, self.compliant_file_2)

        # resource should have no files
        self.assertEqual(self.res.files.all().count(), 0)

        # test adding each of the bad file should fail
        for bad_test_file in (self.non_compliant_file_1, self.non_compliant_file_2):
            with self.assertRaises(SuspiciousFileOperation):
                add_resource_files(self.res.short_id, bad_test_file)

        # add 2 files - both non compliant
        with self.assertRaises(SuspiciousFileOperation):
            add_resource_files(self.res.short_id, self.non_compliant_file_1, self.non_compliant_file_2)

        # resource should have no files
        self.assertEqual(self.res.files.all().count(), 0)

    def test_create_resource_with_non_compliant_files(self):
        """Here we are creating a resource with a file that has non-compliant file name (name with
        at least one banned character). Resource creation should fail.
        """
        self.assertEqual(CompositeResource.objects.count(), 1)

        # create a resource with a non-compliant file upload - should fail
        self.assertGreater(len(self.bad_files), 0)
        for bad_test_file in self.bad_files:
            with self.assertRaises(SuspiciousFileOperation):
                create_resource(resource_type='CompositeResource',
                                owner=self.user,
                                title='Test Resource',
                                files=[bad_test_file],
                                metadata=[], )

        self.assertEqual(CompositeResource.objects.count(), 1)

    def test_file_rename_non_compliant(self):
        """Here we are testing that when we try to rename a file of a resource using a non-compliant filename, the file
        renaming should fail
        """
        # add a file
        add_resource_files(self.res.short_id, self.compliant_file_1)

        # resource should have 1 file
        self.assertEqual(self.res.files.all().count(), 1)
        res_file = self.res.files.all().first()

        # now rename the file with non-compliant file name - which should fail
        src_path = f'data/contents/{res_file.file_name}'
        self.assertGreater(len(self.bad_files), 0)
        for bad_test_file in self.bad_files:
            tgt_path = f'data/contents/{bad_test_file.name}'
            with self.assertRaises(SuspiciousFileOperation):
                move_or_rename_file_or_folder(self.user, self.res.short_id, src_path, tgt_path)

        res_file = self.res.files.all().first()
        self.assertNotEqual(res_file.file_name, self.non_compliant_file_name_1)

    def test_creating_non_compliant_folder(self):
        """Here we are testing when we try to create a folder with a name that doesn't meet hydroshare requirements,
        the folder creation should fail.
        """
        # folder name contains any of these banned characters - non-compliant
        for banned_char in ResourceFile.banned_symbols():
            if banned_char == "/":
                continue
            new_folder = f"my{banned_char}folder"
            with self.assertRaises(SuspiciousFileOperation):
                ResourceFile.create_folder(self.res, new_folder)

        # folder name either is either '.' or '..' - non-compliant
        for new_folder in ("my folder/.", "another folder/.."):
            with self.assertRaises(SuspiciousFileOperation):
                ResourceFile.create_folder(self.res, new_folder)

        multiple_folder_path = ".folder-1/folder-2"
        ResourceFile.create_folder(self.res, multiple_folder_path)

        multiple_folder_path = "folder-1/.folder-2"
        ResourceFile.create_folder(self.res, multiple_folder_path)
        # folder name contains space at the start - still compliant
        new_folder = " my-folder-1"
        ResourceFile.create_folder(self.res, new_folder)

        # folder name contains space at the end - still compliant
        new_folder = "my-folder-2 "
        ResourceFile.create_folder(self.res, new_folder)

        # folder name contains space at the start and end - still compliant (system will trim the space)
        new_folder = " my-folder-3 "
        ResourceFile.create_folder(self.res, new_folder)

    def test_folder_rename_non_compliant(self):
        """Here we are testing that when we try to rename a folder of a resource using a non-compliant folder name,
        the renaming of folder should fail.
        """

        base_path = "data/contents"
        new_folder = "my-folder"
        ResourceFile.create_folder(self.res, new_folder)

        # now rename the folder with non-compliant folder name - which should fail
        src_path = f'{base_path}/{new_folder}'
        # folder name has banned characters - non-compliant
        for banned_char in ResourceFile.banned_symbols():
            if banned_char == "/":
                continue
            tgt_path = f'{base_path}/my{banned_char}folder'
            with self.assertRaises(SuspiciousFileOperation):
                move_or_rename_file_or_folder(self.user, self.res.short_id, src_path, tgt_path)

        # rename folder name is either '.' or '..' - non-compliant
        for rename_folder in (".", ".."):
            tgt_path = f'{base_path}/{rename_folder}'
            with self.assertRaises(SuspiciousFileOperation):
                move_or_rename_file_or_folder(self.user, self.res.short_id, src_path, tgt_path)

        tgt_path = f'{base_path}/.my_folder'
        move_or_rename_file_or_folder(self.user, self.res.short_id, src_path, tgt_path)

        src_path = tgt_path
        tgt_path = f'{base_path}/my_folder'
        move_or_rename_file_or_folder(self.user, self.res.short_id, src_path, tgt_path)

        src_path = tgt_path
        tgt_path = f'{base_path}/my-folder'
        move_or_rename_file_or_folder(self.user, self.res.short_id, src_path, tgt_path)

    def test_meets_preferred_naming_for_files_and_folders(self):
        """here we are testing the function check_for_preferred_path_name() of the resource class which gets
        a list of file/folder paths that do not meet the hydroshare preferred file/folder name convention"""

        base_path = "data/contents"
        add_resource_files(self.res.short_id, self.compliant_file_1)
        non_preferred_paths = self.res.get_non_preferred_path_names()
        res_file = self.res.files.first()
        self.assertEqual(non_preferred_paths, [])
        # now rename file to have a space - non preferred char
        src_path = f'{base_path}/{res_file.file_name}'
        file_name_with_space = 'my file.txt'
        tgt_path = f'{base_path}/{file_name_with_space}'
        move_or_rename_file_or_folder(self.user, self.res.short_id, src_path, tgt_path)
        non_preferred_paths = self.res.get_non_preferred_path_names()
        self.assertNotEqual(non_preferred_paths, [])
        self.assertEqual(len(non_preferred_paths), 1)
        self.assertIn(file_name_with_space, non_preferred_paths)
        res_file = self.res.files.first()
        src_path = f'{base_path}/{res_file.file_name}'
        file_name_with_no_space = 'my_file.txt'
        tgt_path = f'{base_path}/{file_name_with_no_space}'
        move_or_rename_file_or_folder(self.user, self.res.short_id, src_path, tgt_path)
        non_preferred_paths = self.res.get_non_preferred_path_names()
        self.assertEqual(non_preferred_paths, [])
        # create a folder with preferred chars
        preferred_folder = "test-folder"
        ResourceFile.create_folder(resource=self.res, folder=preferred_folder)
        non_preferred_paths = self.res.get_non_preferred_path_names()
        self.assertEqual(non_preferred_paths, [])
        # rename folder to be non preferred
        src_path = f'{base_path}/{preferred_folder}'
        non_preferred_folder = preferred_folder.replace('-', ' ')
        tgt_path = f'{base_path}/{non_preferred_folder}'
        move_or_rename_file_or_folder(self.user, self.res.short_id, src_path, tgt_path)
        non_preferred_paths = self.res.get_non_preferred_path_names()
        self.assertNotEqual(non_preferred_paths, [])
        self.assertEqual(len(non_preferred_paths), 1)
        self.assertIn(non_preferred_folder, non_preferred_paths)
        # test sub folders for non preferred folder names
        parent_folder = 'parent folder'
        child_folder = 'child folder'
        non_preferred_folders = f"{parent_folder}/{child_folder}"
        ResourceFile.create_folder(resource=self.res, folder=non_preferred_folders)
        non_preferred_paths = self.res.get_non_preferred_path_names()
        self.assertNotEqual(non_preferred_paths, [])
        self.assertEqual(len(non_preferred_paths), 3)
        self.assertIn(non_preferred_folder, non_preferred_paths)
        self.assertIn(parent_folder, non_preferred_paths)
        self.assertIn(non_preferred_folders, non_preferred_paths)
        grand_child_folder = 'grand child-folder'
        non_preferred_folders = f"{parent_folder}/{child_folder}/{grand_child_folder}"
        ResourceFile.create_folder(resource=self.res, folder=non_preferred_folders)
        non_preferred_paths = self.res.get_non_preferred_path_names()
        self.assertNotEqual(non_preferred_paths, [])
        self.assertEqual(len(non_preferred_paths), 4)
        self.assertIn(non_preferred_folder, non_preferred_paths)
        self.assertIn(parent_folder, non_preferred_paths)
        self.assertIn(non_preferred_folders, non_preferred_paths)
        non_preferred_folders = f"{parent_folder}/{child_folder}"
        self.assertIn(non_preferred_folders, non_preferred_paths)
