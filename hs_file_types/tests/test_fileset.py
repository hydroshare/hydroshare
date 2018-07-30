import os

from django.test import TransactionTestCase
from django.contrib.auth.models import Group

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.models import ResourceFile
from hs_core.views.utils import move_or_rename_file_or_folder
from utils import CompositeResourceTestMixin
from hs_file_types.models import FileSetLogicalFile, GenericLogicalFile, NetCDFLogicalFile


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
        self.netcdf_file_name = 'netcdf_valid.nc'
        self.netcdf_file = 'hs_file_types/tests/{}'.format(self.netcdf_file_name)

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

    def test_create_aggregation_3(self):
        """Test that we can create a fileset aggregation inside another fileset aggregation - nested
        fileset aggregations"""

        self.create_composite_resource()
        parent_fs_folder = 'parent_fileset_folder'
        ResourceFile.create_folder(self.composite_resource, parent_fs_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=parent_fs_folder)
        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # check that the resource file is not part of an aggregation
        self.assertEqual(res_file.has_logical_file, False)
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)
        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user,
                                         folder_path=parent_fs_folder)
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.logical_file_type_name, self.logical_file_type_name)
        # There should be one fileset aggregation associated with one resource file
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fs_aggregation = FileSetLogicalFile.objects.first()
        self.assertEqual(fs_aggregation.files.count(), 1)

        # create a folder inside fileset folder - new_folder
        child_fs_folder = '{}/child_fileset_folder'.format(parent_fs_folder)
        ResourceFile.create_folder(self.composite_resource, child_fs_folder)
        # add the the json file to the resource at the above sub folder
        self.add_file_to_resource(file_to_add=self.json_file, upload_folder=child_fs_folder)
        # there should be two resource files
        self.assertEqual(self.composite_resource.files.all().count(), 2)

        # set child folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user,
                                         folder_path=child_fs_folder)
        # There should be two fileset aggregations
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)
        json_res_file = ResourceFile.get(resource=self.composite_resource,
                                         file=self.json_file_name, folder=child_fs_folder)
        # the json file in the child folder should be part of a new fileset aggregation
        self.assertEqual(json_res_file.has_logical_file, True)
        self.assertEqual(json_res_file.file_folder, child_fs_folder)
        child_fs_aggr = json_res_file.logical_file
        self.assertEqual(child_fs_aggr.files.count(), 1)
        self.assertEqual(child_fs_aggr.files.first().file_name, self.json_file_name)

        txt_res_file = ResourceFile.get(resource=self.composite_resource,
                                        file=self.generic_file_name, folder=parent_fs_folder)
        # the txt file in the parent folder should be part of a different fileset aggregation
        self.assertEqual(txt_res_file.has_logical_file, True)
        self.assertEqual(txt_res_file.file_folder, parent_fs_folder)
        parent_fs_aggr = txt_res_file.logical_file
        self.assertEqual(parent_fs_aggr.files.count(), 1)
        self.assertEqual(parent_fs_aggr.files.first().file_name, self.generic_file_name)

        self.composite_resource.delete()

    def test_add_file_to_aggregation(self):
        """Test that when we add a file to a folder that represents a fileset aggregation,
        the newly added file becomes part of the aggregation """

        self.create_composite_resource()
        new_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=new_folder)

        # there should be one resource file
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

    def test_move_file_into_aggregation_1(self):
        """Test that when we move a file (that is not part of any aggregation) into a folder that
        represents a fileset aggregation, the moved file becomes part of the fileset aggregation """

        self.create_composite_resource()
        new_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=new_folder)

        # there should be one resource file
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

        # add the the json file to the resource at the root
        self.add_file_to_resource(file_to_add=self.json_file)
        # there should be two resource files
        self.assertEqual(self.composite_resource.files.all().count(), 2)

        # test that the json file is not part of any aggregation
        json_res_file = ResourceFile.get(resource=self.composite_resource, file=self.json_file_name)
        self.assertEqual(json_res_file.has_logical_file, False)

        # move the json file into the folder that represents fileset aggregation
        src_path = 'data/contents/{}'.format(self.json_file_name)
        tgt_path = 'data/contents/{0}/{1}'.format(new_folder, self.json_file_name)

        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        # both resource files should be part of the fileset aggregation
        for r_file in self.composite_resource.files.all():
            self.assertEqual(r_file.has_logical_file, True)
            self.assertEqual(r_file.logical_file_type_name, self.logical_file_type_name)

        fileset_aggregation = FileSetLogicalFile.objects.first()
        self.assertEqual(fileset_aggregation.files.count(), 2)

        self.composite_resource.delete()

    def test_move_file_into_aggregation_2(self):
        """Test that when we move a file (that is part of a single file aggregation) into a folder
        that represents a fileset aggregation, the moved file does not become part of the fileset
        aggregation - the moved file remains as part of the original single file aggregation """

        self.create_composite_resource()
        new_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=new_folder)

        # there should be one resource file
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

        # add the the json file to the resource at the root
        self.add_file_to_resource(file_to_add=self.json_file)
        # there should be two resource files
        self.assertEqual(self.composite_resource.files.all().count(), 2)

        # test that the json file is not part of any aggregation
        json_res_file = ResourceFile.get(resource=self.composite_resource, file=self.json_file_name)
        self.assertEqual(json_res_file.has_logical_file, False)

        # set the json file to GenericLogicalFile type
        GenericLogicalFile.set_file_type(self.composite_resource, self.user,
                                         file_id=json_res_file.id)

        # test that the json file is part of aggregation
        json_res_file = ResourceFile.get(resource=self.composite_resource, file=self.json_file_name)
        self.assertEqual(json_res_file.has_logical_file, True)
        self.assertEqual(json_res_file.logical_file_type_name, "GenericLogicalFile")
        self.assertEqual(GenericLogicalFile.objects.count(), 1)
        # move the json file into the folder that represents fileset aggregation
        src_path = 'data/contents/{}'.format(self.json_file_name)
        tgt_path = 'data/contents/{0}/{1}'.format(new_folder, self.json_file_name)

        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        # one resource file should be part of the fileset aggregation and the other one part
        # of generic aggregation (single file aggregation)
        for r_file in self.composite_resource.files.all():
            if r_file.extension.lower() == '.txt':
                self.assertEqual(r_file.logical_file_type_name, "FileSetLogicalFile")
            else:
                self.assertEqual(r_file.logical_file_type_name, "GenericLogicalFile")

        self.assertEqual(GenericLogicalFile.objects.count(), 1)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fileset_aggregation = FileSetLogicalFile.objects.first()
        self.assertEqual(fileset_aggregation.files.count(), 1)
        generic_aggregation = GenericLogicalFile.objects.first()
        self.assertEqual(generic_aggregation.files.count(), 1)

        self.composite_resource.delete()

    def test_move_file_from_aggregation(self):
        """Test that when we move a file out of a folder that represents a fileset aggregation,
        the moved file is no more part of that aggregation """

        self.create_composite_resource()
        new_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=new_folder)
        # add the the json file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.json_file, upload_folder=new_folder)

        # there should be two resource files
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)

        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user, folder_path=new_folder)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fileset_aggregation = FileSetLogicalFile.objects.first()
        self.assertEqual(fileset_aggregation.files.count(), 2)

        # both resource files should be part of the fileset aggregation
        for r_file in self.composite_resource.files.all():
            self.assertEqual(r_file.has_logical_file, True)
            self.assertEqual(r_file.logical_file_type_name, self.logical_file_type_name)

        # move the json file out of the aggregation folder into the root folder
        src_path = 'data/contents/{0}/{1}'.format(new_folder, self.json_file_name)
        tgt_path = 'data/contents/{}'.format(self.json_file_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        # test that the json file is not part of any aggregation
        json_res_file = ResourceFile.get(resource=self.composite_resource, file=self.json_file_name)
        self.assertEqual(json_res_file.has_logical_file, False)

        # fileset aggregation should have only one resource file
        fileset_aggregation = FileSetLogicalFile.objects.first()
        self.assertEqual(fileset_aggregation.files.count(), 1)

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
        """Test that when we delete one of the files of a fileset aggregation the aggregation
        doesn't get deleted """

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

    def test_create_folder_in_fileset(self):
        """Test that folders can be created inside a folder that represents a fileset
        aggregation and file added to the sub folder is going to be part of the fileset
        aggregation"""

        self.create_composite_resource()
        new_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=new_folder)
        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # check that the resource file is not part of an aggregation
        self.assertEqual(res_file.has_logical_file, False)
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)
        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user, folder_path=new_folder)
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.logical_file_type_name, self.logical_file_type_name)
        # There should be one fileset aggregation associated with one resource file
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fs_aggregation = FileSetLogicalFile.objects.first()
        self.assertEqual(fs_aggregation.files.count(), 1)

        # create a folder inside fileset_folder
        agg_sub_folder = 'fileset_folder/folder_1'
        ResourceFile.create_folder(self.composite_resource, agg_sub_folder)
        # add the the json file to the resource at the above sub folder
        self.add_file_to_resource(file_to_add=self.json_file, upload_folder=agg_sub_folder)
        # there should be two resource files
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        json_res_file = ResourceFile.get(resource=self.composite_resource,
                                         file=self.json_file_name, folder=agg_sub_folder)
        # the json file added to the sub folder should be part of the fileset aggregation
        self.assertEqual(json_res_file.has_logical_file, True)
        self.assertEqual(json_res_file.file_folder, agg_sub_folder)
        # There should be one fileset aggregation associated with both of the resource files
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fs_aggregation = FileSetLogicalFile.objects.first()
        self.assertEqual(fs_aggregation.files.count(), 2)

        # create a folder inside folder_1 - case of nested folders inside fileset folder
        agg_sub_folder = agg_sub_folder + '/folder_1_1'
        ResourceFile.create_folder(self.composite_resource, agg_sub_folder)
        # add the the json file to the resource at the above sub folder
        self.add_file_to_resource(file_to_add=self.json_file, upload_folder=agg_sub_folder)
        # there should be three resource files
        self.assertEqual(self.composite_resource.files.all().count(), 3)
        json_res_file = ResourceFile.get(resource=self.composite_resource,
                                         file=self.json_file_name, folder=agg_sub_folder)
        # the json file added to the sub folder should be part of the fileset aggregation
        self.assertEqual(json_res_file.has_logical_file, True)
        self.assertEqual(json_res_file.file_folder, agg_sub_folder)
        # There should be one fileset aggregation associated with all three resource files
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fs_aggregation = FileSetLogicalFile.objects.first()
        self.assertEqual(fs_aggregation.files.count(), 3)

        self.composite_resource.delete()

    def test_auto_netcdf_aggregation_creation(self):
        """Test that when a netcdf file is uploaded to a folder that represents a fileset,
        a netcdf aggregation is created automatically"""

        self.create_composite_resource()
        new_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=new_folder)
        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # check that the resource file is not part of an aggregation
        self.assertEqual(res_file.has_logical_file, False)
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)
        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user, folder_path=new_folder)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        self.assertEqual(FileSetLogicalFile.objects.first().files.count(), 1)

        # upload a netcdf file to the new_folder - folder that represents the above fileset
        # aggregation
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        self.add_files_to_resource(files_to_add=[self.netcdf_file], upload_folder=new_folder)
        # there should be three resource file - one generated by netcdf aggregation
        self.assertEqual(self.composite_resource.files.all().count(), 3)
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        nc_aggr_path = os.path.join(new_folder, self.netcdf_file_name[:-3])
        nc_res_file = ResourceFile.get(resource=self.composite_resource,
                                       file=self.netcdf_file_name, folder=nc_aggr_path)
        # the netcdf file added to the fileset folder should be part of a new netcdf aggregation
        self.assertEqual(nc_res_file.has_logical_file, True)
        self.assertEqual(NetCDFLogicalFile.objects.first().files.count(), 2)

        self.composite_resource.delete()

    def test_auto_raster_aggregation_creation(self):
        """Test that when a raster file is uploaded to a folder that represents a fileset,
        a raster aggregation is created automatically"""
        # TODO: implement this test
        pass

    def test_auto_geofeature_aggregation_creation(self):
        """Test that when files that represents a geofeature are uploaded to a folder that
        represents a fileset, a geofeature aggregation is created automatically"""
        # TODO: implement this test
        pass

    def test_auto_timeseries_aggregation_creation(self):
        """Test that when a sqlite file is uploaded to a folder that represents a fileset,
        a timeseries aggregation is created automatically"""
        # TODO: implement this test
        pass

    def test_auto_reftimeseries_aggregation_creation(self):
        """Test that when a ref tiemseries json file is uploaded to a folder that represents a
        fileset, a ref timeseries aggregation is created automatically"""
        # TODO: implement this test
        pass

    def test_remove_child_aggregation(self):
        """Test that when we remove a child fileset aggregation the files that are part of the
        child aggregation become part of the immediate parent fileset aggregation"""
        # TODO: implement this test
        pass
