import os
import shutil
import tempfile

from django.contrib.auth.models import Group
from django.test import TransactionTestCase
from django.core.files.uploadedfile import UploadedFile
from unittest_parametrize import ParametrizedTestCase, parametrize, param

from hs_core.hydroshare.resource import add_resource_files
from hs_core import hydroshare
from hs_core.testing import MockS3TestCaseMixin
from hs_core.views.utils import create_folder


TEST_FILE_CONTENT = "test file content"


class TestReadmeResourceFile(MockS3TestCaseMixin, ParametrizedTestCase, TransactionTestCase):
    def setUp(self):
        super(TestReadmeResourceFile, self).setUp()
        self.composite_resource = None
        self.temp_dir = tempfile.mkdtemp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

    def tearDown(self):
        super(TestReadmeResourceFile, self).tearDown()
        if self.composite_resource:
            self.composite_resource.delete()
        shutil.rmtree(self.temp_dir)
    
    def _write_test_file(self, filename):
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as test_file:
            test_file.write(TEST_FILE_CONTENT)
        return file_path

    def _write_test_files(self, filenames):
        return [self._write_test_file(filename) for filename in filenames]

    @parametrize(
        "filenames,expected_file_count,readme_file_expected,expected_readme_file_name",
        [
            param(
                ["readme.txt"], 1, True, "readme.txt", id="txt_file",
            ),
            param(
                ["readme.md"], 1, True, "readme.md", id="md_file",
            ),
            param(
                ["README.TXT"], 1, True, "README.TXT", id="txt_file_uppercase",
            ),
            param(
                ["README.MD"], 1, True, "README.MD", id="md_file_uppercase",
            ),
            param(
                ["readme.txt", "readme.md"], 2, True, "readme.md", id="both_file_types",
            ),
            param(
                ["some.txt", "some.md"], 2, False, None, id="non_readme_files",
            ),
        ],
    )
    def test_root_level_readme_detection(
        self,
        filenames,
        expected_file_count,
        readme_file_expected,
        expected_readme_file_name,
    ):
        """Test readme file detection for root-level uploads."""

        self._create_composite_resource()
        files_to_add = self._write_test_files(filenames)
        # resource should not have any file at this point
        self.assertEqual(self.composite_resource.files.count(), 0)
        # resource has no readme file
        self.assertEqual(self.composite_resource.readme_file, None)
        self._add_files_to_resource(files_to_add)

        self.assertEqual(self.composite_resource.files.count(), expected_file_count)
        if readme_file_expected:
            self.assertIsNotNone(self.composite_resource.readme_file)
            self.assertIsNotNone(self.composite_resource.get_readme_file_content())
            self.assertEqual(self.composite_resource.readme_file.file_name, expected_readme_file_name)
        else:
            self.assertIsNone(self.composite_resource.readme_file)
            self.assertIsNone(self.composite_resource.get_readme_file_content())

    def test_readme_file_in_folder(self):
        """Test that when we upload a readme.txt or a readme.md file to a folder,
        such a file is NOT considered as the readme file of the resource"""

        self._create_composite_resource()
        readme_txt = self._write_test_file("readme.txt")
        readme_md = self._write_test_file("readme.md")
        # resource should not have any file at this point
        self.assertEqual(self.composite_resource.files.count(), 0)
        # create the folder
        new_folder_path = os.path.join("data", "contents", "my-new-folder")
        create_folder(self.composite_resource.short_id, new_folder_path)
        # add the readme.txt file to the resource at the folder 'my-new-folder'
        files_to_add = [readme_txt]
        self._add_files_to_resource(files_to_add, upload_folder=new_folder_path)
        # resource should have one file at this point
        self.assertEqual(self.composite_resource.files.count(), 1)
        # resource has no readme file
        self.assertEqual(self.composite_resource.readme_file, None)

        # add the readme.md file to the resource at the folder 'my-new-folder'
        files_to_add = [readme_md]
        self._add_files_to_resource(files_to_add, upload_folder=new_folder_path)
        # resource should have two files at this point
        self.assertEqual(self.composite_resource.files.count(), 2)
        # resource has no readme file
        self.assertEqual(self.composite_resource.readme_file, None)

    def test_readme_file_in_folder_empty_string(self):
        """Test that when a README.md file with file_folder as '' instead of None,
        this file is considered as the readme file of the resource"""

        self._create_composite_resource()
        readme_md_upper = self._write_test_file("README.MD")
        # resource should not have any file at this point
        self.assertEqual(self.composite_resource.files.count(), 0)
        # resource has no readme file
        self.assertEqual(self.composite_resource.readme_file, None)
        # add the README.MD file to the resource at the root level
        files_to_add = [readme_md_upper]
        self._add_files_to_resource(files_to_add)
        # resource should have one file at this point
        self.assertEqual(self.composite_resource.files.count(), 1)
        # Update the readme file_folder to an empty string
        file = self.composite_resource.files.first()
        file.file_folder = ''
        file.save()
        # resource has a readme file
        self.assertNotEqual(self.composite_resource.readme_file, None)
        self.assertNotEqual(self.composite_resource.get_readme_file_content(), None)

    def _create_composite_resource(self):
        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Readme File'
        )

    def _add_files_to_resource(self, files_to_add, upload_folder=''):
        files_to_upload = []
        for fl in files_to_add:
            file_to_upload = UploadedFile(file=open(fl, 'rb'), name=os.path.basename(fl))
            files_to_upload.append(file_to_upload)
        added_resource_files = add_resource_files(self.composite_resource.short_id,
                                                  *files_to_upload, folder=upload_folder)
        return added_resource_files
