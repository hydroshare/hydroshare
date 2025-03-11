import os

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TransactionTestCase

from hs_core import hydroshare
from hs_core.models import ResourceFile
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core.views.utils import move_or_rename_file_or_folder, remove_folder
from hs_file_types.models import FileSetLogicalFile, GenericLogicalFile, NetCDFLogicalFile, \
    GeoRasterLogicalFile, GeoFeatureLogicalFile, TimeSeriesLogicalFile, RefTimeseriesLogicalFile, \
    ModelProgramLogicalFile, CSVLogicalFile
from .utils import CompositeResourceTestMixin


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
        base_file_path = 'hs_file_types/tests/{}'
        self.generic_file_name = 'generic_file.txt'
        self.generic_file = base_file_path.format(self.generic_file_name)

        self.json_file_name = 'multi_sites_formatted_version1.0.refts.json'
        self.json_file = base_file_path.format(self.json_file_name)

        self.netcdf_file_name = 'netcdf_valid.nc'
        self.netcdf_file = base_file_path.format(self.netcdf_file_name)

        base_data_file_path = 'hs_file_types/tests/data/{}'
        self.raster_file_name = 'small_logan.tif'
        self.raster_file = 'hs_file_types/tests/{}'.format(self.raster_file_name)
        self.sqlite_file_name = 'ODM2_Multi_Site_One_Variable.sqlite'
        self.sqlite_file = base_data_file_path.format(self.sqlite_file_name)

        self.states_prj_file_name = 'states.prj'
        self.states_prj_file = base_data_file_path.format(self.states_prj_file_name)
        self.states_shp_file_name = 'states.shp'
        self.states_shp_file = base_data_file_path.format(self.states_shp_file_name)
        self.states_dbf_file_name = 'states.dbf'
        self.states_dbf_file = base_data_file_path.format(self.states_dbf_file_name)
        self.states_shx_file_name = 'states.shx'
        self.states_shx_file = base_data_file_path.format(self.states_shx_file_name)

        self.csv_file_name = "csv_with_header_and_data.csv"
        self.csv_file = base_data_file_path.format(self.csv_file_name)

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
        # check that there are no missing metadata for the fileset aggregation
        fs_aggr = FileSetLogicalFile.objects.first()
        self.assertEqual(len(fs_aggr.metadata.get_required_missing_elements()), 0)

        # aggregation dataset name should be same as the folder name
        self.assertEqual(res_file.logical_file.dataset_name, new_folder)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
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
        # check that there are no missing required metadata for the fileset aggregation
        self.assertEqual(len(fileset_aggregation.metadata.get_required_missing_elements()), 0)

        # aggregation dataset name should be same as the folder name
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.logical_file.dataset_name, new_folder)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_3(self):
        """Test that we can create a fileset aggregation from a folder that contains no files
        but contains another aggregation"""

        self.create_composite_resource()
        # there should be no resource file at this point
        self.assertEqual(self.composite_resource.files.all().count(), 0)
        parent_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, parent_folder)
        raster_child_folder = '{}/raster_folder'.format(parent_folder)
        ResourceFile.create_folder(self.composite_resource, raster_child_folder)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        # upload a raster tif file to the child folder to auto create a raster aggregation there
        self.add_files_to_resource(files_to_add=[self.raster_file],
                                   upload_folder=raster_child_folder)
        # there should be two resource file - one generated by raster aggregation
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        # check that none of the resource files are in parent folder
        for fl in self.composite_resource.files.all():
            self.assertNotEqual(fl.file_folder, parent_folder)

        # test now that we can create a fileset aggregation from the parent folder
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user,
                                         folder_path=parent_folder)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        # check that there are no missing required metadata for the fileset aggregation
        fs_aggr = FileSetLogicalFile.objects.first()
        self.assertEqual(len(fs_aggr.metadata.get_required_missing_elements()), 0)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_4(self):
        """Test that we can create a fileset aggregation from a folder that contains file(s)
        and contains aggregation(s)"""

        self.create_composite_resource()
        # there should be no resource file at this point
        self.assertEqual(self.composite_resource.files.all().count(), 0)
        parent_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, parent_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=parent_folder)
        # there should be one resource file at this point
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        raster_child_folder = '{}/raster_folder'.format(parent_folder)
        ResourceFile.create_folder(self.composite_resource, raster_child_folder)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        # upload a raster tif file to the child folder to auto create a raster aggregation there
        self.add_files_to_resource(files_to_add=[self.raster_file],
                                   upload_folder=raster_child_folder)
        # there should be three resource file - one extra file generated by raster aggregation
        self.assertEqual(self.composite_resource.files.all().count(), 3)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)

        # test now that we can create a fileset aggregation from the parent folder
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user,
                                         folder_path=parent_folder)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        # check that there are no missing required metadata for the fileset aggregation
        fs_aggr = FileSetLogicalFile.objects.first()
        self.assertEqual(len(fs_aggr.metadata.get_required_missing_elements()), 0)
        self.assertEqual(FileSetLogicalFile.objects.first().files.count(), 1)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_5(self):
        """Test that we can create a fileset aggregation from a folder that contains file(s)
        and contains an empty folder"""

        self.create_composite_resource()
        # there should be no resource file at this point
        self.assertEqual(self.composite_resource.files.all().count(), 0)
        parent_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, parent_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=parent_folder)
        # there should be one resource file at this point
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        empty_child_folder = '{}/empty_folder'.format(parent_folder)
        ResourceFile.create_folder(self.composite_resource, empty_child_folder)

        # test now that we can create a fileset aggregation from the parent folder
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user,
                                         folder_path=parent_folder)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        # check that there are no missing required metadata for the fileset aggregation
        fs_aggr = FileSetLogicalFile.objects.first()
        self.assertEqual(len(fs_aggr.metadata.get_required_missing_elements()), 0)
        self.assertEqual(FileSetLogicalFile.objects.first().files.count(), 1)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_6(self):
        """Test that we can create a fileset aggregation from a folder that contains file(s)
        and contains a non-empty folder (folder that contains a file)"""

        self.create_composite_resource()
        # there should be no resource file at this point
        self.assertEqual(self.composite_resource.files.all().count(), 0)
        parent_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, parent_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=parent_folder)
        # there should be one resource file at this point
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        non_empty_child_folder = '{}/non_empty_folder'.format(parent_folder)
        ResourceFile.create_folder(self.composite_resource, non_empty_child_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file,
                                  upload_folder=non_empty_child_folder)

        # there should be two resource file at this point
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        # test now that we can create a fileset aggregation from the parent folder
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user,
                                         folder_path=parent_folder)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        # check that there are no missing required metadata for the fileset aggregation
        fs_aggr = FileSetLogicalFile.objects.first()
        self.assertEqual(len(fs_aggr.metadata.get_required_missing_elements()), 0)
        self.assertEqual(FileSetLogicalFile.objects.first().files.count(), 2)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_7(self):
        """Test that we can create a fileset aggregation inside another fileset aggregation - nested
        fileset aggregations"""

        self._create_nested_fileset_aggregations()
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_fileset_aggregation_not_allowed_inside_model_program_aggregation(self):
        """Test that we can't create a fileset aggregation inside a model program aggregation"""

        self.create_composite_resource()
        # there should be no resource file at this point
        self.assertEqual(self.composite_resource.files.all().count(), 0)
        parent_folder = 'mp_folder'
        ResourceFile.create_folder(self.composite_resource, parent_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=parent_folder)
        # there should be one resource file at this point
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        child_folder = '{}/sub_folder'.format(parent_folder)
        ResourceFile.create_folder(self.composite_resource, child_folder)
        # add the the prj file to the resource at the sub folder
        self.add_file_to_resource(file_to_add=self.states_prj_file, upload_folder=child_folder)
        # there should be two resource file at this point
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        # set the parent folder to model program aggregation
        ModelProgramLogicalFile.set_file_type(resource=self.composite_resource, user=self.user,
                                              folder_path=parent_folder)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, parent_folder)
        # now try to set the child folder to fileset aggregation - which should fail
        with self.assertRaises(ValidationError):
            FileSetLogicalFile.set_file_type(self.composite_resource, self.user,
                                             folder_path=child_folder)
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_add_file_to_aggregation(self):
        """Test that when we add a file (file that is not suitable for auto aggregation creation)
         to a folder that represents a fileset aggregation, the newly added file becomes part of
         the aggregation """

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
        # check that there are no missing required metadata for the fileset aggregation
        self.assertEqual(len(fileset_aggregation.metadata.get_required_missing_elements()), 0)
        assert fileset_aggregation.metadata.is_dirty
        self.assertEqual(fileset_aggregation.files.count(), 2)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
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
        # check that there are no missing metadata for the fileset aggregation
        self.assertEqual(len(fileset_aggregation.metadata.get_required_missing_elements()), 0)
        assert fileset_aggregation.metadata.is_dirty
        self.assertEqual(fileset_aggregation.files.count(), 2)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
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
        assert fileset_aggregation.metadata.is_dirty
        self.assertEqual(fileset_aggregation.files.count(), 1)
        generic_aggregation = GenericLogicalFile.objects.first()
        assert generic_aggregation.metadata.is_dirty
        self.assertEqual(generic_aggregation.files.count(), 1)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
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
        # check that there are no missing required metadata for the fileset aggregation
        self.assertEqual(len(fileset_aggregation.metadata.get_required_missing_elements()), 0)
        assert fileset_aggregation.metadata.is_dirty
        self.assertEqual(fileset_aggregation.files.count(), 1)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_empty_fileset(self):
        """Test that when we delete the only resource file of a fileset aggregation,
        the aggregation doesn't get deleted - leaves an aggregation without any content
        files (empty fileset)
        """

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
        fs_aggr = self.composite_resource.get_aggregation_by_name(new_folder)
        self.assertEqual(fs_aggr.files.count(), 1)
        # check that there are no missing required metadata for the fileset aggregation
        self.assertEqual(len(fs_aggr.metadata.get_required_missing_elements()), 0)

        # aggregation dataset name should be same as the folder name
        self.assertEqual(res_file.logical_file.dataset_name, new_folder)
        # delete the file
        hydroshare.delete_resource_file(self.composite_resource.short_id, res_file.id, self.user)
        # fileset aggregation still should exists
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fs_aggr = self.composite_resource.get_aggregation_by_name(new_folder)
        assert fs_aggr.metadata.is_dirty
        self.assertEqual(fs_aggr.files.count(), 0)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_delete_file_in_aggregation(self):
        """Test that we can delete one of the files of a fileset aggregation"""

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
        fileset_aggregation = FileSetLogicalFile.objects.first()
        # check that there are no missing required metadata for the fileset aggregation
        self.assertEqual(len(fileset_aggregation.metadata.get_required_missing_elements()), 0)
        assert fileset_aggregation.metadata.is_dirty
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_delete_aggregation_in_fileset_1(self):
        """Test that we can delete an aggregation (raster) that's inside the fileset aggregation
        """

        self._create_fileset_aggregation()
        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        # there should be one fileset aggregation
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fs_aggr = FileSetLogicalFile.objects.first()
        # fileset aggregation should have only one file
        self.assertEqual(fs_aggr.files.count(), 1)
        fs_aggr_path = fs_aggr.aggregation_name
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        raster_folder_path = '{}/raster_folder'.format(fs_aggr_path)
        ResourceFile.create_folder(self.composite_resource, raster_folder_path)
        # upload a raster tif file to the new_folder - folder that represents the above fileset
        # aggregation
        self.add_files_to_resource(files_to_add=[self.raster_file],
                                   upload_folder=raster_folder_path)
        # there should be three resource file - one generated by raster aggregation
        self.assertEqual(self.composite_resource.files.all().count(), 3)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        # delete the folder that represents the raster aggregation
        raster_folder_path = "data/contents/{}".format(raster_folder_path)
        remove_folder(self.user, self.composite_resource.short_id, raster_folder_path)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        # there should be 1 resource files
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        # fileset aggregation should still be there
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fileset_aggregation = FileSetLogicalFile.objects.first()
        # check that there are no missing required metadata for the fileset aggregation
        self.assertEqual(len(fileset_aggregation.metadata.get_required_missing_elements()), 0)
        assert fileset_aggregation.metadata.is_dirty
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_delete_aggregation_in_fileset_2(self):
        """Test that we can delete a fileset that's inside the fileset aggregation (nested)
        """

        self._create_nested_fileset_aggregations()
        # there should be 2 fileset aggregations
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)
        parent_fs_folder = 'parent_fileset_folder'
        child_fs_folder_path = 'data/contents/{}/child_fileset_folder'.format(parent_fs_folder)
        # delete the child fileset folder
        remove_folder(self.user, self.composite_resource.short_id, child_fs_folder_path)
        # there should be 1 fileset aggregation
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fileset_aggregation = FileSetLogicalFile.objects.first()
        # check that there are no missing required metadata for the fileset aggregation
        self.assertEqual(len(fileset_aggregation.metadata.get_required_missing_elements()), 0)
        assert fileset_aggregation.metadata.is_dirty
        self.composite_resource.get_aggregation_by_name(parent_fs_folder)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
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
        # the json file added to the sub folder should be part of the fileset aggregation
        json_res_file = ResourceFile.get(resource=self.composite_resource,
                                         file=self.json_file_name, folder=agg_sub_folder)
        self.assertEqual(json_res_file.has_logical_file, True)
        self.assertEqual(json_res_file.file_folder, agg_sub_folder)
        # There should be one fileset aggregation associated with all three resource files
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fs_aggregation = FileSetLogicalFile.objects.first()
        assert fs_aggregation.metadata.is_dirty
        self.assertEqual(fs_aggregation.files.count(), 3)
        # check that there are no missing required metadata for the fileset aggregation
        self.assertEqual(len(fs_aggregation.metadata.get_required_missing_elements()), 0)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_delete_folder_in_fileset(self):
        """Test that we can delete a folder (contains a file) that is part of a fileset
        aggregation - test that the fileset aggregation doesn't get deleted"""

        self._create_fileset_aggregation()
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        fileset_folder = self.composite_resource.files.first().file_folder
        new_folder = '{}/normal_folder'.format(fileset_folder)
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=new_folder)
        # there should be two resource files
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        # delete the folder new_folder
        folder_path = "data/contents/{}".format(new_folder)
        remove_folder(self.user, self.composite_resource.short_id, folder_path)
        # there should be still the fileset aggregation
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fileset_aggregation = FileSetLogicalFile.objects.first()
        assert fileset_aggregation.metadata.is_dirty
        self.composite_resource.get_aggregation_by_name(fileset_folder)
        # check that there are no missing required metadata for the fileset aggregation
        self.assertEqual(len(fileset_aggregation.metadata.get_required_missing_elements()), 0)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_delete_folder_containing_fileset(self):
        """Test that we can delete a folder that contains a fileset
        aggregation - test that the fileset aggregation gets deleted"""

        self.create_composite_resource()
        # there should be no resource file
        self.assertEqual(self.composite_resource.files.all().count(), 0)
        normal_folder = 'normal_folder'
        fileset_folder = '{}/fileset_folder'.format(normal_folder)
        ResourceFile.create_folder(self.composite_resource, fileset_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=fileset_folder)
        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        # create a fileset aggregation using the fileset_folder
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user,
                                         folder_path=fileset_folder)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        # check that there are no missing required metadata for the fileset aggregation
        fs_aggr = FileSetLogicalFile.objects.first()
        self.assertEqual(len(fs_aggr.metadata.get_required_missing_elements()), 0)
        # delete the folder normal_folder (contains the fileset aggregation)
        folder_path = "data/contents/{}".format(normal_folder)
        remove_folder(self.user, self.composite_resource.short_id, folder_path)
        # there should be no fileset aggregation
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)
        # there should be no resource file
        self.assertEqual(self.composite_resource.files.all().count(), 0)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_delete_fileset_folder(self):
        """Test that we can delete a folder that represents a fileset
        aggregation - test that the fileset aggregation gets deleted as well as any nested aggregations"""

        self.create_composite_resource()
        # there should be no resource file
        self.assertEqual(self.composite_resource.files.all().count(), 0)
        fileset_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, fileset_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=fileset_folder)
        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # create generic aggregation
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

        # create a fileset aggregation using the fileset_folder
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user,
                                         folder_path=fileset_folder)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        # delete the folder normal_folder (contains the fileset aggregation)
        folder_path = "data/contents/{}".format(fileset_folder)
        remove_folder(self.user, self.composite_resource.short_id, folder_path)
        # there should be no fileset aggregation
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)
        # there should be no resource file
        self.assertEqual(self.composite_resource.files.all().count(), 0)
        # check that the folder got deleted from irods
        istorage = self.composite_resource.get_irods_storage()
        full_folder_path = os.path.join(self.composite_resource.file_path, fileset_folder)
        self.assertFalse(istorage.exists(full_folder_path))

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_single_file_type_in_fileset(self):
        """Test that we can create a single file aggregation from a file that is part of a
        fileset aggregation """

        self._create_fileset_aggregation()
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        # no single file aggregation at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        res_file = self.composite_resource.files.first()
        # test that the resource file is part of the fileset aggregation
        self.assertEqual(res_file.logical_file_type_name, 'FileSetLogicalFile')
        # create a single file aggregation
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()
        # there should be one single file aggregation at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 1)
        fileset_aggregation = FileSetLogicalFile.objects.first()
        assert fileset_aggregation.metadata.is_dirty
        # check that there are no missing required metadata for the fileset aggregation
        self.assertEqual(len(fileset_aggregation.metadata.get_required_missing_elements()), 0)
        # test that the resource file is now part of the single file aggregation
        self.assertEqual(res_file.logical_file_type_name, 'GenericLogicalFile')
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_auto_netcdf_aggregation_creation(self):
        """Test that when a netcdf file is uploaded to a folder that represents a fileset,
        a netcdf aggregation is created automatically"""

        self._create_fileset_aggregation()
        fs_aggr_path = FileSetLogicalFile.objects.first().aggregation_name

        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        # upload a netcdf file to the new_folder - folder that represents the above fileset
        # aggregation
        self.add_files_to_resource(files_to_add=[self.netcdf_file], upload_folder=fs_aggr_path)
        # there should be three resource file - one generated by netcdf aggregation
        self.assertEqual(self.composite_resource.files.all().count(), 3)
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        fileset_aggregation = FileSetLogicalFile.objects.first()
        assert fileset_aggregation.metadata.is_dirty
        # check that there are no missing required metadata for the fileset aggregation
        self.assertEqual(len(fileset_aggregation.metadata.get_required_missing_elements()), 0)
        # the netcdf file added to the fileset folder should be part of a new netcdf aggregation
        nc_res_file = ResourceFile.get(resource=self.composite_resource,
                                       file=self.netcdf_file_name, folder=fs_aggr_path)
        self.assertEqual(nc_res_file.has_logical_file, True)
        # the netcdf aggregation should contain 2 files - nc and the txt files
        self.assertEqual(NetCDFLogicalFile.objects.first().files.count(), 2)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_auto_raster_aggregation_creation(self):
        """Test that when a raster file (.tif) is uploaded to a folder that represents a fileset,
        a raster aggregation is created automatically"""

        self._create_fileset_aggregation()
        fs_aggr_path = FileSetLogicalFile.objects.first().aggregation_name
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        # upload a raster tif file to the new_folder - folder that represents the above fileset
        # aggregation
        self.add_files_to_resource(files_to_add=[self.raster_file], upload_folder=fs_aggr_path)
        # there should be three resource file - one generated by raster aggregation
        self.assertEqual(self.composite_resource.files.all().count(), 3)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        fileset_aggregation = FileSetLogicalFile.objects.first()
        assert fileset_aggregation.metadata.is_dirty
        # check that there are no missing required metadata for the fileset aggregation
        self.assertEqual(len(fileset_aggregation.metadata.get_required_missing_elements()), 0)
        # the tif file added to the fileset folder should be part of a new raster aggregation
        raster_res_file = ResourceFile.get(resource=self.composite_resource,
                                           file=self.raster_file_name, folder=fs_aggr_path)
        self.assertEqual(raster_res_file.has_logical_file, True)
        # the raster aggregation should contain 2 files (tif and vrt)
        self.assertEqual(GeoRasterLogicalFile.objects.first().files.count(), 2)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_auto_geofeature_aggregation_creation(self):
        """Test that when files that represents a geofeature are uploaded to a folder that
        represents a fileset, a geofeature aggregation is created automatically"""

        self._create_fileset_aggregation()
        fs_aggr_path = FileSetLogicalFile.objects.first().aggregation_name
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 0)
        # upload all 4 geo feature files the new_folder - folder that represents the above fileset
        # aggregation
        geo_feature_files = [self.states_shp_file, self.states_shx_file, self.states_dbf_file,
                             self.states_prj_file]
        self.add_files_to_resource(files_to_add=geo_feature_files, upload_folder=fs_aggr_path)
        # there should be 5 resource files
        self.assertEqual(self.composite_resource.files.all().count(), 5)
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 1)
        fileset_aggregation = FileSetLogicalFile.objects.first()
        assert fileset_aggregation.metadata.is_dirty
        # check that there are no missing required metadata for the fileset aggregation
        self.assertEqual(len(fileset_aggregation.metadata.get_required_missing_elements()), 0)
        # the shp file added to the fileset folder should be part of a new geofeature
        # aggregation
        shp_res_file = ResourceFile.get(resource=self.composite_resource,
                                        file=self.states_shp_file_name, folder=fs_aggr_path)
        self.assertEqual(shp_res_file.has_logical_file, True)

        # the geofeature aggregation should contain five files
        self.assertEqual(GeoFeatureLogicalFile.objects.first().files.count(), 4)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_auto_timeseries_aggregation_creation(self):
        """Test that when a sqlite file is uploaded to a folder that represents a fileset,
        a timeseries aggregation is created automatically"""

        self._create_fileset_aggregation()
        fs_aggr_path = FileSetLogicalFile.objects.first().aggregation_name
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 0)
        # upload a sqlite file to the new_folder - folder that represents the above fileset
        # aggregation
        self.add_files_to_resource(files_to_add=[self.sqlite_file], upload_folder=fs_aggr_path)
        # there should be two resource files
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 1)
        fileset_aggregation = FileSetLogicalFile.objects.first()
        assert fileset_aggregation.metadata.is_dirty
        # check that there are no missing required metadata for the fileset aggregation
        self.assertEqual(len(fileset_aggregation.metadata.get_required_missing_elements()), 0)
        # the sqlite file added to the fileset folder should be part of a new timeseries aggregation
        sqlite_res_file = ResourceFile.get(resource=self.composite_resource,
                                           file=self.sqlite_file_name, folder=fs_aggr_path)
        self.assertEqual(sqlite_res_file.has_logical_file, True)
        # the timeseries aggregation should contain one file
        self.assertEqual(TimeSeriesLogicalFile.objects.first().files.count(), 1)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_auto_reftimeseries_aggregation_creation(self):
        """Test that when a ref tiemseries json file is uploaded to a folder that represents a
        fileset, a ref timeseries aggregation is created automatically"""

        self._create_fileset_aggregation()
        fs_aggr_path = FileSetLogicalFile.objects.first().aggregation_name
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 0)
        # upload a ts json file to the new_folder - folder that represents the above fileset
        # aggregation
        self.add_files_to_resource(files_to_add=[self.json_file], upload_folder=fs_aggr_path)
        # there should be two resource files
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 1)
        fileset_aggregation = FileSetLogicalFile.objects.first()
        assert fileset_aggregation.metadata.is_dirty
        # check that there are no missing required metadata for the fileset aggregation
        self.assertEqual(len(fileset_aggregation.metadata.get_required_missing_elements()), 0)
        # the json file added to the fileset folder should be part of a new ref timeseries
        # aggregation
        json_res_file = ResourceFile.get(resource=self.composite_resource,
                                         file=self.json_file_name, folder=fs_aggr_path)
        self.assertEqual(json_res_file.has_logical_file, True)
        # the ref timeseries aggregation should contain one file
        self.assertEqual(RefTimeseriesLogicalFile.objects.first().files.count(), 1)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_auto_csv_aggregation_creation(self):
        """Here we are testing when a csv file is uploaded to a folder representing a fileset aggregation
        a csv aggregation is created automatically"""

        self._create_fileset_aggregation()
        fs_aggr_path = FileSetLogicalFile.objects.first().aggregation_name
        self.assertEqual(CSVLogicalFile.objects.count(), 0)
        # upload the scv file to the fileset folder
        self.add_files_to_resource(files_to_add=[self.csv_file], upload_folder=fs_aggr_path)
        # there should be two resource files
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        self.assertEqual(CSVLogicalFile.objects.count(), 1)
        fileset_aggregation = FileSetLogicalFile.objects.first()
        assert fileset_aggregation.metadata.is_dirty
        # check that there are no missing required metadata for the fileset aggregation
        self.assertEqual(len(fileset_aggregation.metadata.get_required_missing_elements()), 0)
        # the csv file added to the fileset folder should be part of a new csv
        # aggregation
        csv_res_file = ResourceFile.get(resource=self.composite_resource,
                                        file=self.csv_file_name, folder=fs_aggr_path)
        self.assertEqual(csv_res_file.has_logical_file, True)
        # the csv aggregation should contain one file
        self.assertEqual(CSVLogicalFile.objects.first().files.count(), 1)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_rename_aggregation_1(self):
        """Testing that we can rename a folder that represents a fileset aggregation"""
        self._create_fileset_aggregation()
        # There should be now one fileset aggregation
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fs_aggr = FileSetLogicalFile.objects.first()
        self.assertEqual(fs_aggr.folder, 'fileset_folder')
        # rename fileset aggregation name
        new_folder = 'fileset_folder_1'
        src_path = 'data/contents/{}'.format(fs_aggr.folder)
        tgt_path = 'data/contents/{}'.format(new_folder)

        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fs_aggr = FileSetLogicalFile.objects.first()
        assert fs_aggr.metadata.is_dirty
        # check that there are no missing required metadata for the fileset aggregation
        self.assertEqual(len(fs_aggr.metadata.get_required_missing_elements()), 0)
        self.assertEqual(fs_aggr.folder, new_folder)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_rename_aggregation_2(self):
        """Testing that we can rename a folder that represents a fileset aggregation that
        exists within another fileset aggregation - nested fileset aggregation
        """

        self._create_nested_fileset_aggregations()

        parent_fs_folder = 'parent_fileset_folder'
        child_fs_folder = '{}/child_fileset_folder'.format(parent_fs_folder)
        # There should be 2 fileset aggregations
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)
        fs_aggr_child = FileSetLogicalFile.objects.filter(folder=child_fs_folder).first()

        # rename fileset aggregation name for the child fileset aggregation
        new_child_fs_folder = '{}/child_fileset_folder_1'.format(parent_fs_folder)
        src_path = 'data/contents/{}'.format(fs_aggr_child.folder)
        tgt_path = 'data/contents/{}'.format(new_child_fs_folder)

        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)
        for fs_aggr in FileSetLogicalFile.objects.all():
            assert fs_aggr.metadata.is_dirty
            # check that there are no missing required metadata for the fileset aggregation
            self.assertEqual(len(fs_aggr.metadata.get_required_missing_elements()), 0)

        self.assertEqual(FileSetLogicalFile.objects.filter(folder=new_child_fs_folder).count(), 1)
        self.assertEqual(FileSetLogicalFile.objects.filter(folder=parent_fs_folder).count(), 1)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_rename_aggregation_3(self):
        """Testing that we can rename a folder that represents a fileset aggregation that
        contains another fileset aggregation - nested fileset aggregation
        Also changing the folder name for a parent fileset aggregation should update the
        folder path for the nested fileset aggregation
        """

        self._create_nested_fileset_aggregations()

        # remove the nested fileset aggregation
        parent_fs_folder = 'parent_fileset_folder'
        child_fs_folder = '{}/child_fileset_folder'.format(parent_fs_folder)
        # There should be 2 fileset aggregations
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)
        fs_aggr_parent = FileSetLogicalFile.objects.filter(folder=parent_fs_folder).first()
        self.assertEqual(FileSetLogicalFile.objects.filter(folder=child_fs_folder).count(), 1)

        # rename fileset aggregation name for the parent fileset aggregation
        new_parent_fs_folder = parent_fs_folder + '_1'
        src_path = 'data/contents/{}'.format(fs_aggr_parent.folder)
        tgt_path = 'data/contents/{}'.format(new_parent_fs_folder)

        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        # new expected folder path of the child fileset aggregation
        new_child_fs_folder = '{}/child_fileset_folder'.format(new_parent_fs_folder)
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)
        for fs_aggr in FileSetLogicalFile.objects.all():
            assert fs_aggr.metadata.is_dirty
            # check that there are no missing required metadata for the fileset aggregation
            self.assertEqual(len(fs_aggr.metadata.get_required_missing_elements()), 0)

        self.assertEqual(FileSetLogicalFile.objects.filter(folder=new_parent_fs_folder).count(), 1)
        self.assertEqual(FileSetLogicalFile.objects.filter(folder=new_child_fs_folder).count(), 1)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_rename_aggregation_4(self):
        """Testing that when we rename a folder (normal folder) that contains nested fileset
        aggregations, the folder path of each of the fileset aggregations gets updated accordingly
        """

        self.create_composite_resource()
        root_folder = 'normal_folder'
        parent_fs_folder = '{}/parent_fileset_folder'.format(root_folder)
        ResourceFile.create_folder(self.composite_resource, parent_fs_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=parent_fs_folder)
        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user,
                                         folder_path=parent_fs_folder)
        # There should be one fileset aggregation associated with one resource file
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)

        # create a folder inside fileset folder - parent_fs_folder
        child_fs_folder = '{}/child_fileset_folder'.format(parent_fs_folder)
        ResourceFile.create_folder(self.composite_resource, child_fs_folder)
        # add the the json file to the resource at the above sub folder
        self.add_file_to_resource(file_to_add=self.json_file, upload_folder=child_fs_folder)
        # there should be two resource files
        self.assertEqual(self.composite_resource.files.all().count(), 2)

        # set child folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user,
                                         folder_path=child_fs_folder)

        # There should be 2 fileset aggregations
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)
        self.assertEqual(FileSetLogicalFile.objects.filter(folder=child_fs_folder).count(), 1)

        # rename the root_folder
        new_root_folder = root_folder + '_1'
        src_path = 'data/contents/{}'.format(root_folder)
        tgt_path = 'data/contents/{}'.format(new_root_folder)

        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        # new expected folder path of the parent fileset aggregation
        new_parent_fs_folder = '{}/parent_fileset_folder'.format(new_root_folder)
        # new expected folder path of the child fileset aggregation
        new_child_fs_folder = '{}/child_fileset_folder'.format(new_parent_fs_folder)
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)
        for fs_aggr in FileSetLogicalFile.objects.all():
            assert fs_aggr.metadata.is_dirty
            # check that there are no missing required metadata for the fileset aggregation
            self.assertEqual(len(fs_aggr.metadata.get_required_missing_elements()), 0)

        self.assertEqual(FileSetLogicalFile.objects.filter(folder=new_parent_fs_folder).count(), 1)
        self.assertEqual(FileSetLogicalFile.objects.filter(folder=new_child_fs_folder).count(), 1)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_move_fileset_into_another_fileset(self):
        """Testing that we can move a fileset folder to another fileset folder
        """

        self.create_composite_resource()
        fs_1_folder = 'fs_1_folder'
        ResourceFile.create_folder(self.composite_resource, fs_1_folder)
        # add the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=fs_1_folder)
        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user,
                                         folder_path=fs_1_folder)
        # There should be one fileset aggregation associated with one resource file
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)

        # create a another folder for the 2nd fileset aggregation
        fs_2_folder = 'fs_2_folder'
        ResourceFile.create_folder(self.composite_resource, fs_2_folder)
        # add the json file to the resource at the above sub folder
        self.add_file_to_resource(file_to_add=self.json_file, upload_folder=fs_2_folder)
        # there should be two resource files
        self.assertEqual(self.composite_resource.files.all().count(), 2)

        # set 2nd folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user,
                                         folder_path=fs_2_folder)

        # There should be 2 fileset aggregations now
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)
        self.assertEqual(FileSetLogicalFile.objects.filter(folder=fs_1_folder).count(), 1)
        self.assertEqual(FileSetLogicalFile.objects.filter(folder=fs_2_folder).count(), 1)

        # move the 2nd fileset folder inside the 1st fileset folder
        src_path = 'data/contents/{}'.format(fs_2_folder)
        tgt_path = 'data/contents/{}/{}'.format(fs_1_folder, fs_2_folder)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        # new expected folder path of the 2nd fileset aggregation
        new_fs2_folder = '{}/{}'.format(fs_1_folder, fs_2_folder)
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)
        for fs_aggr in FileSetLogicalFile.objects.all():
            assert fs_aggr.metadata.is_dirty
            # check that there are no missing required metadata for the fileset aggregation
            self.assertEqual(len(fs_aggr.metadata.get_required_missing_elements()), 0)

        self.assertEqual(FileSetLogicalFile.objects.filter(folder=fs_1_folder).count(), 1)
        self.assertEqual(FileSetLogicalFile.objects.filter(folder=new_fs2_folder).count(), 1)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_move_folder_into_fileset_folder(self):
        """Test that when a folder is moved into a fileset folder, all files in the moved folder become part of the
        fileset aggregation
        """

        self.create_composite_resource()
        fs_folder = 'fs_folder'
        ResourceFile.create_folder(self.composite_resource, fs_folder)
        # add the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=fs_folder)
        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user,
                                         folder_path=fs_folder)
        # There should be one fileset aggregation associated with one resource file
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)

        # create a another folder for the 2nd fileset aggregation
        non_fs_folder = 'non_fs_folder'
        ResourceFile.create_folder(self.composite_resource, non_fs_folder)
        # add the json file to the resource at the above sub folder
        self.add_file_to_resource(file_to_add=self.json_file, upload_folder=non_fs_folder)
        # there should be two resource files
        self.assertEqual(self.composite_resource.files.all().count(), 2)

        # There should be still 1 fileset aggregations
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        self.assertEqual(FileSetLogicalFile.objects.filter(folder=fs_folder).count(), 1)

        # move the 2nd non fileset folder inside the fileset folder
        src_path = 'data/contents/{}'.format(non_fs_folder)
        tgt_path = 'data/contents/{}/{}'.format(fs_folder, non_fs_folder)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        # both resource files should be part of the fileset aggregation
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        for r_file in self.composite_resource.files.all():
            self.assertEqual(r_file.has_logical_file, True)
            self.assertEqual(r_file.logical_file_type_name, self.logical_file_type_name)

        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fileset_aggregation = FileSetLogicalFile.objects.first()
        # check that there are no missing metadata for the fileset aggregation
        self.assertEqual(len(fileset_aggregation.metadata.get_required_missing_elements()), 0)
        assert fileset_aggregation.metadata.is_dirty
        self.assertEqual(fileset_aggregation.files.count(), 2)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_move_folder_out_of_fileset_folder(self):
        """Test that when a folder is moved out of a fileset folder, all files in the moved folder are no more
        associated with fileset aggregation
        """
        self.create_composite_resource()
        fs_folder = 'fs_folder'
        ResourceFile.create_folder(self.composite_resource, fs_folder)
        # add the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=fs_folder)
        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        # make a sub folder inside the fileset folder
        sub_folder_name = 'sub_folder'
        sub_folder = '{}/{}'.format(fs_folder, sub_folder_name)
        ResourceFile.create_folder(self.composite_resource, sub_folder)
        # add the json file to the resource at the above sub folder
        self.add_file_to_resource(file_to_add=self.json_file, upload_folder=sub_folder)
        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user,
                                         folder_path=fs_folder)
        # There should be one fileset aggregation associated with one resource file
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fileset_aggregation = FileSetLogicalFile.objects.first()
        # both resource files should be part of the fileset aggregation
        self.assertEqual(fileset_aggregation.files.count(), 2)
        # there should be two resource files
        self.assertEqual(self.composite_resource.files.all().count(), 2)

        # both resource files should be part of the fileset aggregation
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        for r_file in self.composite_resource.files.all():
            self.assertEqual(r_file.has_logical_file, True)
            self.assertEqual(r_file.logical_file_type_name, self.logical_file_type_name)

        # move the sub folder out of the fileset folder to the root of the resource
        src_path = 'data/contents/{}'.format(sub_folder)
        tgt_path = 'data/contents/{}'.format(sub_folder_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        # there should be two resource files
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fileset_aggregation = FileSetLogicalFile.objects.first()
        # check only one file is part of the fileset aggregation
        self.assertEqual(fileset_aggregation.files.count(), 1)
        # check that there are no missing metadata for the fileset aggregation
        self.assertEqual(len(fileset_aggregation.metadata.get_required_missing_elements()), 0)
        assert fileset_aggregation.metadata.is_dirty
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_remove_aggregation(self):
        """Test that we can remove fileset aggregation that lives at the root"""

        # no fileset aggregation at this point
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)
        # create a fileset aggregation at the the root
        self._create_fileset_aggregation()
        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # There should be now one fileset aggregation
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fs_aggr = FileSetLogicalFile.objects.first()
        self.assertTrue(res_file.has_logical_file)
        # remove fileset aggregation
        fs_aggr.remove_aggregation()
        # There should be no fileset aggregation
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)
        res_file = self.composite_resource.files.first()
        self.assertFalse(res_file.has_logical_file)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_remove_child_fs_aggregation(self):
        """Test that when we remove a child fileset aggregation the files that are part of the
        child aggregation become part of the immediate parent fileset aggregation"""

        self._create_nested_fileset_aggregations()

        # remove the nested fileset aggregation
        parent_fs_folder = 'parent_fileset_folder'
        child_fs_folder = '{}/child_fileset_folder'.format(parent_fs_folder)
        json_res_file = ResourceFile.get(resource=self.composite_resource,
                                         file=self.json_file_name, folder=child_fs_folder)
        child_fs_aggr = json_res_file.logical_file
        child_fs_aggr.remove_aggregation()
        # There should be now one fileset aggregation
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        parent_fs_aggr = FileSetLogicalFile.objects.first()
        assert parent_fs_aggr.metadata.is_dirty
        # parent fs aggregation should have 2 resource files now
        self.assertEqual(parent_fs_aggr.files.count(), 2)
        json_res_file = ResourceFile.get(resource=self.composite_resource,
                                         file=self.json_file_name, folder=child_fs_folder)
        txt_res_file = ResourceFile.get(resource=self.composite_resource,
                                        file=self.generic_file_name, folder=parent_fs_folder)
        self.assertEqual(json_res_file.logical_file, txt_res_file.logical_file)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_remove_child_aggregation(self):
        """Test that when we remove any child aggregation (e.g., raster aggregation) of a fileset
        aggregation (parent aggregation), the files that are part of the child aggregation
        become part of the parent fileset aggregation"""

        self._create_fileset_aggregation()
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fs_aggr = FileSetLogicalFile.objects.first()
        # there should be one resource file that is part of the fileset aggregation
        self.assertEqual(fs_aggr.files.count(), 1)
        fs_aggr_path = fs_aggr.aggregation_name
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        # upload a raster tif file to the new_folder - folder that represents the above fileset
        # aggregation
        self.add_files_to_resource(files_to_add=[self.raster_file], upload_folder=fs_aggr_path)
        # there should be three resource file - one generated by raster aggregation
        self.assertEqual(self.composite_resource.files.all().count(), 3)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        # the tif file added to the fileset folder should be part of a new raster aggregation
        raster_res_file = ResourceFile.get(resource=self.composite_resource,
                                           file=self.raster_file_name, folder=fs_aggr_path)
        self.assertEqual(raster_res_file.has_logical_file, True)
        # the raster aggregation should contain 2 files (tif and vrt)
        self.assertEqual(GeoRasterLogicalFile.objects.first().files.count(), 2)
        raster_aggr = raster_res_file.logical_file
        # remove raster aggregation and test that the raster (tif file only) is now part of the fileset
        # aggregation - raster remove aggregation deletes the system generated vrt file
        raster_aggr.remove_aggregation()
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fs_aggr = FileSetLogicalFile.objects.first()
        assert fs_aggr.metadata.is_dirty
        # there should be now two resource files that are part of the fileset aggregation
        self.assertEqual(fs_aggr.files.count(), 2)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_remove_grand_child_aggregation(self):
        """Test that when we remove any child aggregation (e.g., raster aggregation) of a fileset
        aggregation (parent aggregation), the files that are part of the child aggregation
        become part of the immediate parent fileset aggregation"""

        # create nested fileset aggregations
        self._create_nested_fileset_aggregations()
        parent_fs_folder = 'parent_fileset_folder'
        child_fs_folder = '{}/child_fileset_folder'.format(parent_fs_folder)
        # there should be two resource file
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)
        # each of the fileset aggregation should have one resource file
        parent_fs_aggr = self.composite_resource.get_aggregation_by_name(parent_fs_folder)
        self.assertEqual(parent_fs_aggr.files.count(), 1)
        child_fs_aggr = self.composite_resource.get_aggregation_by_name(child_fs_folder)
        self.assertEqual(child_fs_aggr.files.count(), 1)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        # upload a raster tif file to the child_fs_folder - folder that represents the child fileset
        # aggregation - which should auto generate the raster aggregation
        self.add_files_to_resource(files_to_add=[self.raster_file], upload_folder=child_fs_folder)
        # there should be four resource file - one generated by raster aggregation
        self.assertEqual(self.composite_resource.files.all().count(), 4)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        assert child_fs_aggr.metadata.is_dirty
        assert parent_fs_aggr.metadata.is_dirty

        # the tif file added to the fileset folder should be part of a new raster aggregation
        raster_res_file = ResourceFile.get(resource=self.composite_resource,
                                           file=self.raster_file_name, folder=child_fs_folder)
        self.assertEqual(raster_res_file.has_logical_file, True)
        raster_aggr = raster_res_file.logical_file
        # remove raster aggregation - this should make the tif raster file part of the child
        # fileset aggregation - note raster remove aggregation deletes the system generated vtrt file
        raster_aggr.remove_aggregation()
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        # child fileset aggregation should have two resource files
        self.assertEqual(child_fs_aggr.files.count(), 2)
        assert child_fs_aggr.metadata.is_dirty
        # parent fileset aggregation - no change
        self.assertEqual(parent_fs_aggr.files.count(), 1)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_auto_update_temporal_coverage_from_children_1(self):
        """Here we are testing fileset level temporal coverage auto update when
        a contained aggregation temporal coverage gets created as part of that aggregation creation
        provided the fileset aggregation has no temporal coverage prior to the child aggregation
        creation
        """
        self._create_fileset_aggregation()
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fs_aggr = FileSetLogicalFile.objects.first()
        # fileset aggregation should not have any temporal coverage at this point
        self.assertEqual(fs_aggr.metadata.temporal_coverage, None)
        fs_aggr_path = fs_aggr.aggregation_name
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        # upload a netcdf file to the new_folder - folder that represents the above fileset
        # aggregation
        self.add_files_to_resource(files_to_add=[self.netcdf_file], upload_folder=fs_aggr_path)
        # netcdf child aggregation should have been created
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        nc_aggr = NetCDFLogicalFile.objects.first()
        self.assertTrue(nc_aggr.has_parent)
        # netcdf aggregation should have temporal coverage
        self.assertNotEqual(nc_aggr.metadata.temporal_coverage, None)

        # fileset aggregation should now have temporal coverage
        self.assertNotEqual(fs_aggr.metadata.temporal_coverage, None)
        # temporal coverage of the fileset aggregation should match with that of the contained
        # netcdf aggregation
        for temp_date in ('start', 'end'):
            self.assertEqual(fs_aggr.metadata.temporal_coverage.value[temp_date],
                             nc_aggr.metadata.temporal_coverage.value[temp_date])
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_auto_update_temporal_coverage_from_children_2(self):
        """Here we are testing fileset level temporal coverage auto update does not happen when
        a contained aggregation temporal coverage gets created as part of that aggregation creation
        provided the fileset aggregation has temporal coverage prior to the child aggregation
        creation
        """
        self._create_fileset_aggregation()
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fs_aggr = FileSetLogicalFile.objects.first()
        # fileset aggregation should not have any temporal coverage at this point
        self.assertEqual(fs_aggr.metadata.temporal_coverage, None)
        # create temporal coverage for file set
        value_dict = {'name': 'Name for period coverage', 'start': '1/1/2018', 'end': '12/12/2018'}
        fs_aggr.metadata.create_element('coverage', type='period', value=value_dict)
        # fileset aggregation should temporal coverage at this point
        self.assertNotEqual(fs_aggr.metadata.temporal_coverage, None)
        fs_aggr_path = fs_aggr.aggregation_name
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        # upload a netcdf file to the new_folder - folder that represents the above fileset
        # aggregation
        self.add_files_to_resource(files_to_add=[self.netcdf_file], upload_folder=fs_aggr_path)
        # netcdf child aggregation should have been created
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        nc_aggr = NetCDFLogicalFile.objects.first()
        self.assertTrue(nc_aggr.has_parent)
        # netcdf aggregation should have temporal coverage
        self.assertNotEqual(nc_aggr.metadata.temporal_coverage, None)

        # temporal coverage of the fileset aggregation should NOT match with that of the contained
        # netcdf aggregation
        for temp_date in ('start', 'end'):
            self.assertNotEqual(fs_aggr.metadata.temporal_coverage.value[temp_date],
                                nc_aggr.metadata.temporal_coverage.value[temp_date])
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_auto_update_spatial_coverage_from_children_1(self):
        """Here we are testing fileset level spatial coverage auto update when
        a contained aggregation spatial coverage gets created as part of that aggregation creation
        provided the fileset aggregation has no spatial coverage prior to the child aggregation
        creation
        """
        self._create_fileset_aggregation()
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fs_aggr = FileSetLogicalFile.objects.first()
        # fileset aggregation should not have any spatial coverage at this point
        self.assertEqual(fs_aggr.metadata.spatial_coverage, None)
        fs_aggr_path = fs_aggr.aggregation_name
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        # upload a raster tif file to the new_folder - folder that represents the above fileset
        # aggregation
        self.add_files_to_resource(files_to_add=[self.raster_file], upload_folder=fs_aggr_path)
        # raster child aggregation should have been created
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        raster_aggr = GeoRasterLogicalFile.objects.first()
        self.assertTrue(raster_aggr.has_parent)
        # raster aggregation should have spatial coverage
        self.assertNotEqual(raster_aggr.metadata.spatial_coverage, None)

        # fileset aggregation should now have spatial coverage
        self.assertNotEqual(fs_aggr.metadata.spatial_coverage, None)
        # spatial coverage of the fileset aggregation should match with that of the contained
        # raster aggregation
        for limit in ('northlimit', 'eastlimit', 'southlimit', 'westlimit'):
            self.assertEqual(fs_aggr.metadata.spatial_coverage.value[limit],
                             raster_aggr.metadata.spatial_coverage.value[limit])
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_auto_update_spatial_coverage_from_children_2(self):
        """Here we are testing fileset level spatial coverage auto update does not happen
        when a 2nd child aggregation is created with spatial coverage - since auto update has
        already set fileset spatial coverage when the 1st child aggregation is created"""

        self._create_fileset_aggregation()
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fs_aggr = FileSetLogicalFile.objects.first()
        fs_aggr_path = fs_aggr.aggregation_name
        # fileset aggregation should not have any spatial coverage at this point
        self.assertEqual(fs_aggr.metadata.spatial_coverage, None)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        # upload a raster tif file to the new_folder - folder that represents the above fileset
        # aggregation
        self.add_files_to_resource(files_to_add=[self.raster_file], upload_folder=fs_aggr_path)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        raster_aggr = GeoRasterLogicalFile.objects.first()
        self.assertTrue(raster_aggr.has_parent)
        # raster aggregation should have spatial coverage
        self.assertNotEqual(raster_aggr.metadata.spatial_coverage, None)

        # update fileset aggregation spatial coverage from contained raster aggregation
        # fs_aggr.update_spatial_coverage()
        # fileset aggregation should now have spatial coverage
        self.assertNotEqual(fs_aggr.metadata.spatial_coverage, None)
        self.assertAlmostEqual(fs_aggr.metadata.spatial_coverage.value['northlimit'], 42.05002695977342, places=14)
        self.assertAlmostEqual(fs_aggr.metadata.spatial_coverage.value['eastlimit'], -111.577737181062, places=14)
        self.assertAlmostEqual(fs_aggr.metadata.spatial_coverage.value['southlimit'], 41.98722286030317, places=14)
        self.assertAlmostEqual(fs_aggr.metadata.spatial_coverage.value['westlimit'], -111.6975629308406, places=14)

        # upload a nc file to the new_folder - folder that represents the above fileset
        # aggregation
        self.add_files_to_resource(files_to_add=[self.netcdf_file], upload_folder=fs_aggr_path)
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        nc_aggr = NetCDFLogicalFile.objects.first()
        self.assertTrue(nc_aggr.has_parent)
        # nc aggregation should have spatial coverage
        self.assertNotEqual(nc_aggr.metadata.spatial_coverage, None)

        # test that fileset aggregation spatial coverage didn't get updated as a result of nc
        # aggregation creation.
        for limit in ('northlimit', 'eastlimit', 'southlimit', 'westlimit'):
            self.assertEqual(fs_aggr.metadata.spatial_coverage.value[limit],
                             raster_aggr.metadata.spatial_coverage.value[limit])
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_update_spatial_coverage_from_children(self):
        """Here we are testing fileset level spatial coverage update using the spatial data from the
        contained (children) aggregations - two child aggregations"""

        self._create_fileset_aggregation()
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fs_aggr = FileSetLogicalFile.objects.first()
        fs_aggr_path = fs_aggr.aggregation_name
        # fileset aggregation should not have any spatial coverage at this point
        self.assertEqual(fs_aggr.metadata.spatial_coverage, None)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        # upload a raster tif file to the new_folder - folder that represents the above fileset
        # aggregation
        self.add_files_to_resource(files_to_add=[self.raster_file], upload_folder=fs_aggr_path)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        raster_aggr = GeoRasterLogicalFile.objects.first()
        self.assertTrue(raster_aggr.has_parent)
        # raster aggregation should have spatial coverage
        self.assertNotEqual(raster_aggr.metadata.spatial_coverage, None)
        # fileset aggregation should have spatial coverage at this point due to auto update
        self.assertNotEqual(fs_aggr.metadata.spatial_coverage, None)

        # fileset aggregation should now have spatial coverage
        self.assertNotEqual(fs_aggr.metadata.spatial_coverage, None)
        self.assertEqual(fs_aggr.metadata.spatial_coverage.value['northlimit'], 42.050026959773426)
        self.assertEqual(fs_aggr.metadata.spatial_coverage.value['eastlimit'], -111.577737181062)
        self.assertEqual(fs_aggr.metadata.spatial_coverage.value['southlimit'], 41.98722286030317)
        self.assertEqual(fs_aggr.metadata.spatial_coverage.value['westlimit'], -111.6975629308406)

        # upload a nc file to the new_folder - folder that represents the above fileset
        # aggregation
        self.add_files_to_resource(files_to_add=[self.netcdf_file], upload_folder=fs_aggr_path)
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        nc_aggr = NetCDFLogicalFile.objects.first()
        self.assertTrue(nc_aggr.has_parent)
        # nc aggregation should have spatial coverage
        self.assertNotEqual(nc_aggr.metadata.spatial_coverage, None)

        # update fileset aggregation spatial coverage from the contained 2 aggregations
        fs_aggr.update_spatial_coverage()
        # test fileset aggregation spatial coverage data
        self.assertEqual(fs_aggr.metadata.spatial_coverage.value['northlimit'], 42.050026959773426)
        self.assertEqual(fs_aggr.metadata.spatial_coverage.value['eastlimit'], -111.5059403684569)
        self.assertEqual(fs_aggr.metadata.spatial_coverage.value['southlimit'], 41.86390807452128)
        self.assertEqual(fs_aggr.metadata.spatial_coverage.value['westlimit'], -111.6975629308406)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_delete_aggregation_coverage(self):
        """Here we are testing deleting of temporal and spatial coverage for a file set aggregation
        """

        self._create_fileset_aggregation()
        fs_aggr = FileSetLogicalFile.objects.first()

        # test deleting spatial coverage
        self.assertEqual(fs_aggr.metadata.spatial_coverage, None)
        value_dict = {'east': '56.45678', 'north': '12.6789', 'units': 'Decimal degree'}
        fs_aggr.metadata.create_element('coverage', type='point', value=value_dict)
        self.assertTrue(fs_aggr.metadata.is_dirty)
        fs_aggr.metadata.is_dirty = False
        fs_aggr.metadata.save()
        self.assertNotEqual(fs_aggr.metadata.spatial_coverage, None)
        fs_aggr.metadata.delete_element('coverage', fs_aggr.metadata.spatial_coverage.id)
        self.assertEqual(fs_aggr.metadata.spatial_coverage, None)
        self.assertTrue(fs_aggr.metadata.is_dirty)

        # test deleting temporal coverage
        self.assertEqual(fs_aggr.metadata.temporal_coverage, None)
        value_dict = {'name': 'Name for period coverage', 'start': '1/1/2000', 'end': '12/12/2012'}
        fs_aggr.metadata.create_element('coverage', type='period', value=value_dict)
        self.assertNotEqual(fs_aggr.metadata.temporal_coverage, None)
        self.assertTrue(fs_aggr.metadata.is_dirty)
        fs_aggr.metadata.is_dirty = False
        fs_aggr.metadata.save()
        fs_aggr.metadata.delete_element('coverage', fs_aggr.metadata.temporal_coverage.id)
        self.assertEqual(fs_aggr.metadata.temporal_coverage, None)
        self.assertTrue(fs_aggr.metadata.is_dirty)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def _create_fileset_aggregation(self):
        self.create_composite_resource()
        new_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=new_folder)

        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user, folder_path=new_folder)

    def _create_nested_fileset_aggregations(self):
        self.create_composite_resource()
        parent_fs_folder = 'parent_fileset_folder'
        ResourceFile.create_folder(self.composite_resource, parent_fs_folder)
        # add the txt file to the resource at the above folder
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
        # add the json file to the resource at the above sub folder
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
