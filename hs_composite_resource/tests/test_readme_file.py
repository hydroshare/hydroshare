import os

from django.contrib.auth.models import Group
from django.test import TransactionTestCase
from django.core.files.uploadedfile import UploadedFile

from hs_core.hydroshare.resource import add_resource_files
from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core.views.utils import create_folder


class TestReadmeResourceFile(MockIRODSTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(TestReadmeResourceFile, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )
        # create readme files
        self.readme_txt = "readme.txt"
        self.README_TXT = "README.TXT"
        self.readme_md = "readme.md"
        self.README_MD = "README.MD"
        self.some_txt = "some.txt"
        self.some_md = "some.md"

        self.readme_txt_file = open(self.readme_txt, 'w')
        self.readme_txt_file.write("This is a readme text file")
        self.readme_txt_file.close()

        self.README_TXT_file = open(self.README_TXT, 'w')
        self.README_TXT_file.write("This is a readme text file with file name in uppercase")
        self.README_TXT_file.close()

        self.README_MD_file = open(self.README_MD, 'w')
        self.README_MD_file.write("##This is a readme markdown file file name in uppercase")
        self.README_MD_file.close()

        self.readme_md_file = open(self.readme_md, 'w')
        self.readme_md_file.write("##This is a readme markdown file")
        self.readme_md_file.close()

        self.some_txt_file = open(self.some_txt, 'w')
        self.some_txt_file.write("This is NOT a readme text file")
        self.some_txt_file.close()

        self.some_md_file = open(self.some_md, 'w')
        self.some_md_file.write("##This is NOT a readme markdown file")
        self.some_md_file.close()

    def tearDown(self):
        super(TestReadmeResourceFile, self).tearDown()
        if self.composite_resource:
            self.composite_resource.delete()
        self.readme_txt_file.close()
        os.remove(self.readme_txt_file.name)
        self.readme_md_file.close()
        os.remove(self.readme_md_file.name)
        self.some_txt_file.close()
        os.remove(self.some_txt_file.name)
        self.some_md_file.close()
        os.remove(self.some_md_file.name)

    def test_readme_file_1(self):
        """Test that when we upload a readme.txt file to the root,
        this file is considered as the readme file of the resource"""

        self._create_composite_resource()
        # resource should not have any file at this point
        self.assertEqual(self.composite_resource.files.count(), 0)
        # resource has no readme file
        self.assertEqual(self.composite_resource.readme_file, None)
        # add the readme.txt file to the resource at the root level
        files_to_add = [self.readme_txt]
        self._add_files_to_resource(files_to_add)
        # resource should have one file at this point
        self.assertEqual(self.composite_resource.files.count(), 1)
        # resource has a readme file
        self.assertNotEqual(self.composite_resource.readme_file, None)
        self.assertNotEqual(self.composite_resource.get_readme_file_content(), None)

    def test_readme_file_2(self):
        """Test that when we upload a readme.md file to the root,
        this file is considered as the readme file of the resource"""

        self._create_composite_resource()
        # resource should not have any file at this point
        self.assertEqual(self.composite_resource.files.count(), 0)
        # resource has no readme file
        self.assertEqual(self.composite_resource.readme_file, None)
        # add the readme.md file to the resource at the root level
        files_to_add = [self.readme_md]
        self._add_files_to_resource(files_to_add)
        # resource should have one file at this point
        self.assertEqual(self.composite_resource.files.count(), 1)
        # resource has a readme file
        self.assertNotEqual(self.composite_resource.readme_file, None)
        self.assertNotEqual(self.composite_resource.get_readme_file_content(), None)

    def test_readme_file_3(self):
        """Test that when we upload a readme.txt file and readme.md file to the root,
        the readme.md file is considered as the readme file for the resource"""

        self._create_composite_resource()
        # resource should not have any file at this point
        self.assertEqual(self.composite_resource.files.count(), 0)
        # resource has no readme file
        self.assertEqual(self.composite_resource.readme_file, None)
        # add the readme.txt file to the resource at the root level
        files_to_add = [self.readme_txt]
        self._add_files_to_resource(files_to_add)
        # add the readme.md file to the resource at the root level
        files_to_add = [self.readme_md]
        self._add_files_to_resource(files_to_add)
        # resource should have two files at this point
        self.assertEqual(self.composite_resource.files.count(), 2)
        # resource has a readme file
        self.assertNotEqual(self.composite_resource.readme_file, None)
        self.assertNotEqual(self.composite_resource.get_readme_file_content(), None)
        # check that the readme.md file is the readme file for the resource
        self.assertEqual(self.composite_resource.readme_file.file_name, 'readme.md')

    def test_readme_file_4(self):
        """Test that when we upload a readme.txt or a readme.md file to a folder,
        such a file is NOT considered as the readme file of the resource"""

        self._create_composite_resource()
        # resource should not have any file at this point
        self.assertEqual(self.composite_resource.files.count(), 0)
        # create the folder
        new_folder_path = os.path.join("data", "contents", "my-new-folder")
        create_folder(self.composite_resource.short_id, new_folder_path)
        # add the readme.txt file to the resource at the folder 'my-new-folder'
        files_to_add = [self.readme_txt]
        self._add_files_to_resource(files_to_add, upload_folder=new_folder_path)
        # resource should have one file at this point
        self.assertEqual(self.composite_resource.files.count(), 1)
        # resource has no readme file
        self.assertEqual(self.composite_resource.readme_file, None)

        # add the readme.md file to the resource at the folder 'my-new-folder'
        files_to_add = [self.readme_md]
        self._add_files_to_resource(files_to_add, upload_folder=new_folder_path)
        # resource should have two files at this point
        self.assertEqual(self.composite_resource.files.count(), 2)
        # resource has no readme file
        self.assertEqual(self.composite_resource.readme_file, None)

    def test_readme_file_5(self):
        """Test that when we upload a txt file or md file that does not have file name as
        'readme.txt' or 'readme.md' to the root folder,
        such a file is NOT considered as the readme file of the resource"""

        self._create_composite_resource()
        # resource should not have any file at this point
        self.assertEqual(self.composite_resource.files.count(), 0)
        # resource has no readme file
        self.assertEqual(self.composite_resource.readme_file, None)

        # add the some.txt file to the resource at the root level
        files_to_add = [self.some_txt]
        self._add_files_to_resource(files_to_add)
        # resource should have one file at this point
        self.assertEqual(self.composite_resource.files.count(), 1)
        # resource has no readme file
        self.assertEqual(self.composite_resource.readme_file, None)

        # add the some.md file to the resource at the root level
        files_to_add = [self.some_md]
        self._add_files_to_resource(files_to_add)
        # resource should have two files at this point
        self.assertEqual(self.composite_resource.files.count(), 2)
        # resource has no readme file
        self.assertEqual(self.composite_resource.readme_file, None)

    def test_readme_file_6(self):
        """Test that when we upload a README.TXT (file name all in uppercase) to the root,
        this file is considered as the readme file of the resource"""

        self._create_composite_resource()
        # resource should not have any file at this point
        self.assertEqual(self.composite_resource.files.count(), 0)
        # resource has no readme file
        self.assertEqual(self.composite_resource.readme_file, None)
        # add the README.TXT file to the resource at the root level
        files_to_add = [self.README_TXT]
        self._add_files_to_resource(files_to_add)
        # resource should have one file at this point
        self.assertEqual(self.composite_resource.files.count(), 1)
        # resource has a readme file
        self.assertNotEqual(self.composite_resource.readme_file, None)
        self.assertNotEqual(self.composite_resource.get_readme_file_content(), None)

    def test_readme_file_7(self):
        """Test that when we upload a README.MD (file name all in uppercase) to the root,
        this file is considered as the readme file of the resource"""

        self._create_composite_resource()
        # resource should not have any file at this point
        self.assertEqual(self.composite_resource.files.count(), 0)
        # resource has no readme file
        self.assertEqual(self.composite_resource.readme_file, None)
        # add the README.MD file to the resource at the root level
        files_to_add = [self.README_MD]
        self._add_files_to_resource(files_to_add)
        # resource should have one file at this point
        self.assertEqual(self.composite_resource.files.count(), 1)
        # resource has a readme file
        self.assertNotEqual(self.composite_resource.readme_file, None)
        self.assertNotEqual(self.composite_resource.get_readme_file_content(), None)

    def _create_composite_resource(self):
        self.composite_resource = hydroshare.create_resource(
             resource_type='CompositeResource',
             owner=self.user,
             title='Test Readme File'
         )

    def _add_files_to_resource(self, files_to_add, upload_folder=None):
        files_to_upload = []
        for fl in files_to_add:
            file_to_upload = UploadedFile(file=open(fl, 'rb'), name=os.path.basename(fl))
            files_to_upload.append(file_to_upload)
        added_resource_files = add_resource_files(self.composite_resource.short_id,
                                                  *files_to_upload, folder=upload_folder)
        return added_resource_files
