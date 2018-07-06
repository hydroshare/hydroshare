from django.test import TransactionTestCase
from django.contrib.auth.models import Group

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.models import ResourceFile
from utils import CompositeResourceTestMixin
from hs_file_types.models import FileSetLogicalFile


class FileSetFileTypeTest(MockIRODSTestCaseMixin, TransactionTestCase,
                          CompositeResourceTestMixin):
    def setUp(self):
        super(FileSetFileTypeTest, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        self.res_title = "Test Generic File Type"
        self.logical_file_type_name = "FileSetLogicalFile"

        self.generic_file_name = 'generic_file.txt'
        self.json_file_name = 'multi_sites_formatted_version1.0.refts.json'
        self.generic_file = 'hs_file_types/tests/{}'.format(self.generic_file_name)
        self.json_file = 'hs_file_types/tests/{}'.format(self.json_file_name)

    def test_create_aggregation_1(self):
        """Test that we can create a fileset aggregation from a folder that contains one file """

        self.create_composite_resource()
        new_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=new_folder)
        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # file has a folder
        self.assertEqual(res_file.file_folder, new_folder)
        # check that the resource file is not part of an aggregation
        self.assertEqual(res_file.has_logical_file, False)
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)
        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user, folder_path=new_folder)
        res_file = self.composite_resource.files.first()
        # file has the same folder
        self.assertEqual(res_file.file_folder, new_folder)
        self.assertEqual(res_file.logical_file_type_name, self.logical_file_type_name)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        # aggregation dataset name should be same as the folder name
        self.assertEqual(res_file.logical_file.dataset_name, new_folder)

        self.composite_resource.delete()

    def test_create_aggregation_2(self):
        """Test that we can create a fileset aggregation from a folder that contains multiple
        files """

        self.create_composite_resource()
        new_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=new_folder)
        # add the the json file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.json_file, upload_folder=new_folder)
        # there should be two resource files
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        # both files are in a folder
        for r_file in self.composite_resource.files.all():
            self.assertEqual(r_file.file_folder, new_folder)
        # check that the resource files are not part of an aggregation
        for r_file in self.composite_resource.files.all():
            self.assertEqual(r_file.has_logical_file, False)

        self.assertEqual(FileSetLogicalFile.objects.count(), 0)

        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user, folder_path=new_folder)

        # both files are still in the same folder
        for r_file in self.composite_resource.files.all():
            self.assertEqual(r_file.file_folder, new_folder)

        # both resource files should be part of the fileset logical file
        for r_file in self.composite_resource.files.all():
            self.assertEqual(r_file.has_logical_file, True)
            self.assertEqual(r_file.logical_file_type_name, self.logical_file_type_name)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fileset_aggregation = FileSetLogicalFile.objects.first()
        self.assertEqual(fileset_aggregation.files.count(), 2)

        # aggregation dataset name should be same as the folder name
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.logical_file.dataset_name, new_folder)

        self.composite_resource.delete()

    def test_add_file_to_aggregation(self):
        """Test that when we add a file to a folder that represents a fileset aggregation,
        the newly added file becomes part of the aggregation """

        self.create_composite_resource()
        new_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=new_folder)

        # there should be one resource files
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # resource file is in a folder
        self.assertEqual(res_file.file_folder, new_folder)
        # check that the resource file is not part of an aggregation
        self.assertEqual(res_file.has_logical_file, False)

        self.assertEqual(FileSetLogicalFile.objects.count(), 0)

        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user, folder_path=new_folder)

        # resource file is still in the same folder
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.file_folder, new_folder)

        self.assertEqual(res_file.logical_file_type_name, self.logical_file_type_name)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        # aggregation dataset name should be same as the folder name
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.logical_file.dataset_name, new_folder)

        # add the the json file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.json_file, upload_folder=new_folder)
        # there should be two resource files
        self.assertEqual(self.composite_resource.files.all().count(), 2)

        # both resource files should be part of the fileset aggregation
        for r_file in self.composite_resource.files.all():
            self.assertEqual(r_file.has_logical_file, True)
            self.assertEqual(r_file.logical_file_type_name, self.logical_file_type_name)

        fileset_aggregation = FileSetLogicalFile.objects.first()
        self.assertEqual(fileset_aggregation.files.count(), 2)

        self.composite_resource.delete()

    def test_delete_file_in_aggregation_1(self):
        """Test that when we delete the only file in a fileset aggregation, the aggregation also
        gets deleted - but not the folder that represented the aggregation """

        self.create_composite_resource()
        new_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=new_folder)
        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # file has a folder
        self.assertEqual(res_file.file_folder, new_folder)
        # check that the resource file is not part of an aggregation
        self.assertEqual(res_file.has_logical_file, False)
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)
        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user, folder_path=new_folder)
        res_file = self.composite_resource.files.first()
        # file has the same folder
        self.assertEqual(res_file.file_folder, new_folder)
        self.assertEqual(res_file.logical_file_type_name, self.logical_file_type_name)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        # aggregation dataset name should be same as the folder name
        self.assertEqual(res_file.logical_file.dataset_name, new_folder)
        # delete the file
        hydroshare.delete_resource_file(self.composite_resource.short_id, res_file.id, self.user)
        # fileset aggregation should have been deleted
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)
        self.composite_resource.delete()

    def test_delete_file_in_aggregation_2(self):
        """Test that we delete one of the files of a fileset aggregation the aggregation doesn't
        get deleted """

        self.create_composite_resource()
        new_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=new_folder)
        # add the the json file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.json_file, upload_folder=new_folder)
        # there should be two resource files
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        # both files are in a folder
        for r_file in self.composite_resource.files.all():
            self.assertEqual(r_file.file_folder, new_folder)
        # check that the resource files are not part of an aggregation
        for r_file in self.composite_resource.files.all():
            self.assertEqual(r_file.has_logical_file, False)

        self.assertEqual(FileSetLogicalFile.objects.count(), 0)

        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user, folder_path=new_folder)

        # both files are still in the same folder
        for r_file in self.composite_resource.files.all():
            self.assertEqual(r_file.file_folder, new_folder)

        for r_file in self.composite_resource.files.all():
            self.assertEqual(r_file.has_logical_file, True)
            self.assertEqual(r_file.logical_file_type_name, self.logical_file_type_name)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        # aggregation dataset name should be same as the folder name
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.logical_file.dataset_name, new_folder)
        # delete the file
        hydroshare.delete_resource_file(self.composite_resource.short_id, res_file.id, self.user)
        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        # fileset aggregation should still be there
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)

        self.composite_resource.delete()
