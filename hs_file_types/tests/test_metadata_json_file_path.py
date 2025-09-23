# coding=utf-8
import os

from django.contrib.auth.models import Group
from django.test import TransactionTestCase

from hs_core import hydroshare
from hs_core.models import ResourceFile
from hs_core.testing import MockS3TestCaseMixin
from hs_file_types.models import (
    GenericLogicalFile, GeoRasterLogicalFile, NetCDFLogicalFile,
    GeoFeatureLogicalFile, TimeSeriesLogicalFile, FileSetLogicalFile,
    ModelProgramLogicalFile, ModelInstanceLogicalFile, RefTimeseriesLogicalFile,
    CSVLogicalFile
)
from hs_file_types.enums import AggregationMetaFilePath
from .utils import CompositeResourceTestMixin


class MetadataJsonFilePathTest(MockS3TestCaseMixin, TransactionTestCase,
                               CompositeResourceTestMixin):
    def setUp(self):
        super(MetadataJsonFilePathTest, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        self.res_title = "Test Metadata JSON File Path"

        # Test files
        self.generic_file = 'hs_file_types/tests/generic_file.txt'
        self.raster_tif_file = 'hs_file_types/tests/small_logan.tif'
        self.netcdf_file = 'hs_file_types/tests/netcdf_valid.nc'
        self.geofeature_zip_file = 'hs_file_types/tests/data/states_required_files.zip'
        self.timeseries_csv_file = 'hs_file_types/tests/data/ODM2_Multi_Site_One_Variable_Test.csv'
        self.reftimeseries_file = 'hs_file_types/tests/multi_sites_formatted_version1.0.refts.json'
        self.csv_file = 'hs_file_types/tests/data/csv_with_header_and_data.csv'

    def test_generic_logical_file_metadata_json_file_path(self):
        """Test metadata_json_file_path property for GenericLogicalFile"""

        self.create_composite_resource(self.generic_file)
        res_file = self.composite_resource.files.first()

        # Set file to generic logical file type
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()  # Refresh to get logical file
        logical_file = res_file.logical_file

        # Test metadata_json_file_path
        expected_path = res_file.storage_path + AggregationMetaFilePath.METADATA_JSON_FILE_ENDSWITH.value
        self.assertEqual(logical_file.metadata_json_file_path, expected_path)

        self.composite_resource.delete()

    def test_georaster_logical_file_metadata_json_file_path(self):
        """Test metadata_json_file_path property for GeoRasterLogicalFile"""

        self.create_composite_resource(self.raster_tif_file)
        res_file = self.composite_resource.files.first()

        # Set file to georaster logical file type
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()  # Refresh to get logical file
        logical_file = res_file.logical_file

        # Test metadata_json_file_path
        primary_file = logical_file.get_primary_resource_file(logical_file.files.all())
        expected_path = primary_file.storage_path + AggregationMetaFilePath.METADATA_JSON_FILE_ENDSWITH.value
        self.assertEqual(logical_file.metadata_json_file_path, expected_path)

        self.composite_resource.delete()

    def test_netcdf_logical_file_metadata_json_file_path(self):
        """Test metadata_json_file_path property for NetCDFLogicalFile"""

        self.create_composite_resource(self.netcdf_file)
        res_file = self.composite_resource.files.first()

        # Set file to netcdf logical file type
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        # Test metadata_json_file_path
        nc_file = logical_file.get_primary_resource_file(logical_file.files.all())
        expected_path = nc_file.storage_path + AggregationMetaFilePath.METADATA_JSON_FILE_ENDSWITH.value
        self.assertEqual(logical_file.metadata_json_file_path, expected_path)

        self.composite_resource.delete()

    def test_geofeature_logical_file_metadata_json_file_path(self):
        """Test metadata_json_file_path property for GeoFeatureLogicalFile"""

        self.create_composite_resource(self.geofeature_zip_file)
        res_file = self.composite_resource.files.first()

        # Set file to geofeature logical file type
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # Get the logical file from the GeoFeatureLogicalFile objects
        logical_file = GeoFeatureLogicalFile.objects.first()

        # Test metadata_json_file_path
        primary_file = logical_file.get_primary_resource_file(logical_file.files.all())
        expected_path = primary_file.storage_path + AggregationMetaFilePath.METADATA_JSON_FILE_ENDSWITH.value
        self.assertEqual(logical_file.metadata_json_file_path, expected_path)

        self.composite_resource.delete()

    def test_timeseries_logical_file_metadata_json_file_path(self):
        """Test metadata_json_file_path property for TimeSeriesLogicalFile"""

        self.create_composite_resource(self.timeseries_csv_file)
        res_file = self.composite_resource.files.first()

        # Set file to timeseries logical file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # Get the logical file
        logical_file = TimeSeriesLogicalFile.objects.first()

        # Test metadata_json_file_path
        primary_file = logical_file.get_primary_resource_file(logical_file.files.all())
        expected_path = primary_file.storage_path + AggregationMetaFilePath.METADATA_JSON_FILE_ENDSWITH.value
        self.assertEqual(logical_file.metadata_json_file_path, expected_path)

        self.composite_resource.delete()

    def test_reftimeseries_logical_file_metadata_json_file_path(self):
        """Test metadata_json_file_path property for RefTimeseriesLogicalFile"""

        self.create_composite_resource(self.reftimeseries_file)
        res_file = self.composite_resource.files.first()

        # Set file to reftimeseries logical file type
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # Get the logical file from the RefTimeseriesLogicalFile objects
        logical_file = RefTimeseriesLogicalFile.objects.first()

        # Test metadata_json_file_path
        primary_file = logical_file.get_primary_resource_file(logical_file.files.all())
        expected_path = primary_file.storage_path + AggregationMetaFilePath.METADATA_JSON_FILE_ENDSWITH.value
        self.assertEqual(logical_file.metadata_json_file_path, expected_path)

        self.composite_resource.delete()

    def test_csv_logical_file_metadata_json_file_path(self):
        """Test metadata_json_file_path property for CSVLogicalFile"""

        self.create_composite_resource(self.csv_file)
        res_file = self.composite_resource.files.first()

        # Set file to csv logical file type
        CSVLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        # Test metadata_json_file_path
        primary_file = logical_file.get_primary_resource_file(logical_file.files.all())
        expected_path = primary_file.storage_path + AggregationMetaFilePath.METADATA_JSON_FILE_ENDSWITH.value
        self.assertEqual(logical_file.metadata_json_file_path, expected_path)

        self.composite_resource.delete()

    def test_fileset_logical_file_metadata_json_file_path(self):
        """Test metadata_json_file_path property for FileSetLogicalFile"""

        self.create_composite_resource()
        new_folder = 'fileset_folder'

        # Create a folder and add a file to it
        ResourceFile.create_folder(self.composite_resource, new_folder)
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=new_folder)

        # Set folder to fileset logical file type
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user, folder_path=new_folder)
        logical_file = FileSetLogicalFile.objects.first()

        # Test metadata_json_file_path
        expected_path = os.path.join(
            self.composite_resource.file_path,
            new_folder,
            AggregationMetaFilePath.METADATA_JSON_FILE_NAME.value
        )
        self.assertEqual(logical_file.metadata_json_file_path, expected_path)

        self.composite_resource.delete()

    def test_model_program_logical_file_metadata_json_file_path_single_file(self):
        """Test metadata_json_file_path property for ModelProgramLogicalFile with single file"""

        self.create_composite_resource(self.generic_file)
        res_file = self.composite_resource.files.first()

        # Set file to model program logical file type
        ModelProgramLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        # Test metadata_json_file_path for single file
        expected_path = res_file.storage_path + AggregationMetaFilePath.METADATA_JSON_FILE_ENDSWITH.value
        self.assertEqual(logical_file.metadata_json_file_path, expected_path)

        self.composite_resource.delete()

    def test_model_program_logical_file_metadata_json_file_path_folder(self):
        """Test metadata_json_file_path property for ModelProgramLogicalFile with folder"""

        self.create_composite_resource()
        new_folder = 'model_program_folder'

        # Create a folder and add a file to it
        ResourceFile.create_folder(self.composite_resource, new_folder)
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=new_folder)

        # Set folder to model program logical file type
        ModelProgramLogicalFile.set_file_type(self.composite_resource, self.user, folder_path=new_folder)
        logical_file = ModelProgramLogicalFile.objects.first()

        # Test metadata_json_file_path for folder
        expected_path = os.path.join(
            self.composite_resource.file_path,
            new_folder,
            AggregationMetaFilePath.METADATA_JSON_FILE_NAME.value
        )
        self.assertEqual(logical_file.metadata_json_file_path, expected_path)

        self.composite_resource.delete()

    def test_model_instance_logical_file_metadata_json_file_path_single_file(self):
        """Test metadata_json_file_path property for ModelInstanceLogicalFile with single file"""

        # First create a model program logical file
        self.create_composite_resource(self.generic_file)
        res_file = self.composite_resource.files.first()
        ModelProgramLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()
        model_program_logical_file = res_file.logical_file

        # Add another file for model instance
        self.add_file_to_resource(file_to_add=self.csv_file)
        mi_res_file = [f for f in self.composite_resource.files.all()
                       if f.file_name.endswith('.csv')][0]

        # Set file to model instance logical file type
        ModelInstanceLogicalFile.set_file_type(self.composite_resource, self.user, mi_res_file.id)
        mi_res_file = [f for f in self.composite_resource.files.all()
                       if f.file_name.endswith('.csv')][0]
        logical_file = mi_res_file.logical_file

        # Set the executed_by relationship
        logical_file.metadata.executed_by = model_program_logical_file
        logical_file.metadata.save()

        # Test metadata_json_file_path for single file
        expected_path = mi_res_file.storage_path + AggregationMetaFilePath.METADATA_JSON_FILE_ENDSWITH.value
        self.assertEqual(logical_file.metadata_json_file_path, expected_path)

        self.composite_resource.delete()

    def test_model_instance_logical_file_metadata_json_file_path_folder(self):
        """Test metadata_json_file_path property for ModelInstanceLogicalFile with folder"""

        # First create a model program logical file
        self.create_composite_resource(self.generic_file)
        res_file = self.composite_resource.files.first()
        ModelProgramLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()
        model_program_logical_file = res_file.logical_file

        # Create a folder and add a file to it for model instance
        new_folder = 'model_instance_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        self.add_file_to_resource(file_to_add=self.csv_file, upload_folder=new_folder)

        # Set folder to model instance logical file type
        ModelInstanceLogicalFile.set_file_type(self.composite_resource, self.user, folder_path=new_folder)
        logical_file = ModelInstanceLogicalFile.objects.filter(folder=new_folder).first()

        # Set the executed_by relationship
        logical_file.metadata.executed_by = model_program_logical_file
        logical_file.metadata.save()

        # Test metadata_json_file_path for folder
        expected_path = os.path.join(
            self.composite_resource.file_path,
            new_folder,
            AggregationMetaFilePath.METADATA_JSON_FILE_NAME.value
        )
        self.assertEqual(logical_file.metadata_json_file_path, expected_path)

        self.composite_resource.delete()
