import os
import unittest

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as DRF_ValidationError

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
        self.compliant_file_name_1 = "test-1.txt"
        self.compliant_file_name_2 = "tes-2.txt"
        self.compliant_non_english_file_name = "résumé-2.txt"

        # filename contains a space
        self.non_compliant_file_name_1 = "test 1.txt"
        # filename contains a characters '(' and ')'
        self.non_compliant_file_name_2 = "test-(2).txt"

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

    def test_add_complianct_files(self):
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
            file_list.append(f.resource_file.name.split('/')[-1])

        # check if the file name is in the list of files
        self.assertTrue(self.compliant_file_name_1 in file_list, f"{self.compliant_file_name_1} has not been added")
        self.assertTrue(self.compliant_file_name_2 in file_list, f"{self.compliant_file_name_2} has not been added")
        self.assertTrue(self.compliant_non_english_file_name in file_list,
                        f"{self.compliant_non_english_file_name} has not been added")

    def test_add_non_compliant_files(self):
        """Here we are testing when a file that has a name which doesn't meet hydroshare requirements is uploaded
        to a resource the upload operation should fail.
        """
        # resource should have no files
        self.assertEqual(self.res.files.all().count(), 0)

        # add one file that is not compliant
        with self.assertRaises(ValidationError):
            add_resource_files(self.res.short_id, self.non_compliant_file_1)

        # resource should have no files
        self.assertEqual(self.res.files.all().count(), 0)

        # add one file that is not compliant and another file that is compliant
        with self.assertRaises(ValidationError):
            add_resource_files(self.res.short_id, self.non_compliant_file_1, self.compliant_file_2)

        # resource should have no files
        self.assertEqual(self.res.files.all().count(), 0)

        # add 2 files - both non compliant
        with self.assertRaises(ValidationError):
            add_resource_files(self.res.short_id, self.non_compliant_file_1, self.non_compliant_file_2)

        # resource should have no files
        self.assertEqual(self.res.files.all().count(), 0)

    def test_create_resource_with_non_compliant_files(self):
        """Here we are creating a resource with a file that has non-compliant file name.
        Resource creation should fail.
        """
        self.assertEqual(CompositeResource.objects.count(), 1)

        # create a resource with a non-compliant file upload - should fail
        with self.assertRaises(ValidationError):
            create_resource(resource_type='CompositeResource',
                            owner=self.user,
                            title='Test Resource',
                            files=[self.non_compliant_file_1],
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
        tgt_path = f'data/contents/{self.non_compliant_file_name_1}'
        with self.assertRaises(DRF_ValidationError):
            move_or_rename_file_or_folder(self.user, self.res.short_id, src_path, tgt_path)

        res_file = self.res.files.all().first()
        self.assertNotEqual(res_file.file_name, self.non_compliant_file_name_1)

    def test_creating_non_compliant_folder(self):
        """Here we are testing when we try to create a folder with a name that doesn't meet hydroshare requirements,
        the folder creation should fail.
        """
        # folder name contains space - non-compliant
        new_folder = "my folder"
        with self.assertRaises(DRF_ValidationError):
            ResourceFile.create_folder(self.res, new_folder)

        # folder name contains symbol not allowed (allowed symbols are: '-', '.', and '_') - non-compliant
        new_folder = "my>folder"
        with self.assertRaises(DRF_ValidationError):
            ResourceFile.create_folder(self.res, new_folder)

        # folder name contains space at the start - non-compliant
        new_folder = " my-folder"
        with self.assertRaises(DRF_ValidationError):
            ResourceFile.create_folder(self.res, new_folder)

        # folder name contains space at the end - non-compliant
        new_folder = "my-folder "
        with self.assertRaises(DRF_ValidationError):
            ResourceFile.create_folder(self.res, new_folder)

        # folder path contains space - non-compliant
        multiple_folder_path = "folder-1/folder 2"
        with self.assertRaises(DRF_ValidationError):
            ResourceFile.create_folder(self.res, multiple_folder_path)

        multiple_folder_path = "folder-1/folder-2"
        ResourceFile.create_folder(self.res, multiple_folder_path)

        multiple_folder_path = "folder-1/.folder-2"
        ResourceFile.create_folder(self.res, multiple_folder_path)

    def test_folder_rename_non_compliant(self):
        """Here we are testing that when we try to rename a folder of a resource using a non-compliant folder name,
        the renaming of folder should fail.
        """

        new_folder = "my-folder"
        ResourceFile.create_folder(self.res, new_folder)

        # now rename the folder with non-compliant folder name - which should fail
        src_path = f'data/contents/{new_folder}'
        # folder name has a space - non-compliant
        tgt_path = f'data/contents/my folder'
        with self.assertRaises(DRF_ValidationError):
            move_or_rename_file_or_folder(self.user, self.res.short_id, src_path, tgt_path)

        # folder name has a symbol which is not allowed (allowed symbols are: '-', '.', and '_') - non-compliant
        tgt_path = f'data/contents/my=folder'
        with self.assertRaises(DRF_ValidationError):
            move_or_rename_file_or_folder(self.user, self.res.short_id, src_path, tgt_path)

        # folder name has a symbol which is not allowed (allowed symbols are: '-', '.', and '_') - non-compliant
        # symbol '.' is allowed only as the start character
        tgt_path = f'data/contents/my.folder'
        with self.assertRaises(DRF_ValidationError):
            move_or_rename_file_or_folder(self.user, self.res.short_id, src_path, tgt_path)

        tgt_path = f'data/contents/.my_folder'
        move_or_rename_file_or_folder(self.user, self.res.short_id, src_path, tgt_path)

        src_path = tgt_path
        tgt_path = f'data/contents/my_folder'
        move_or_rename_file_or_folder(self.user, self.res.short_id, src_path, tgt_path)

        src_path = tgt_path
        tgt_path = f'data/contents/my-folder'
        move_or_rename_file_or_folder(self.user, self.res.short_id, src_path, tgt_path)
