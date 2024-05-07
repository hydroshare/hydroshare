import os

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TransactionTestCase
from rest_framework.exceptions import ValidationError as DRF_ValidationError

from hs_core import hydroshare
from hs_core.models import Coverage, ResourceFile
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core.views.utils import remove_folder, move_or_rename_file_or_folder
from hs_file_types.models import (
    GeoFeatureLogicalFile,
    GenericLogicalFile,
    GenericFileMetaData,
    GeoFeatureFileMetaData,
)
from hs_file_types.enums import AggregationMetaFilePath
from hs_file_types.models.geofeature import FieldInformation, GeometryInformation, OriginalCoverageGeofeature
from .utils import (
    assert_geofeature_file_type_metadata,
    CompositeResourceTestMixin,
    get_path_with_no_file_extension,
    get_number_of_decimal_places,
)


class GeoFeatureFileTypeTest(MockIRODSTestCaseMixin, TransactionTestCase,
                             CompositeResourceTestMixin):
    def setUp(self):
        super(GeoFeatureFileTypeTest, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        self.res_title = 'Testing Geo Feature File Type'

        # data files to use for testing
        self.states_required_zip_file_name = 'states_required_files.zip'
        self.states_prj_file_name = 'states.prj'
        self.states_xml_file_name = 'states.shp.xml'
        self.states_shp_file_name = 'states.shp'
        self.states_dbf_file_name = 'states.dbf'
        self.states_shx_file_name = 'states.shx'
        self.osm_all_files_zip_file_name = 'gis.osm_adminareas_v06_all_files.zip'
        self.states_zip_invalid_file_name = 'states_invalid.zip'
        base_file_path = 'hs_file_types/tests/data/{}'
        self.states_required_zip_file = base_file_path.format(self.states_required_zip_file_name)
        self.states_prj_file = base_file_path.format(self.states_prj_file_name)
        self.states_xml_file = base_file_path.format(self.states_xml_file_name)
        self.states_shp_file = base_file_path.format(self.states_shp_file_name)
        self.states_dbf_file = base_file_path.format(self.states_dbf_file_name)
        self.states_shx_file = base_file_path.format(self.states_shx_file_name)
        self.osm_all_files_zip_file = base_file_path.format(self.osm_all_files_zip_file_name)
        self.states_zip_invalid_file = base_file_path.format(self.states_zip_invalid_file_name)

        self.allowance = 0.00001

    def test_create_aggregation_from_zip_file_required_1(self):
        # here we are using a zip file that has only the 3 required files for setting it
        # to Geo Feature file type which includes metadata extraction
        # the zip file that we are using to create an aggregation here is at the root of the
        # folder hierarchy

        self.create_composite_resource(self.states_required_zip_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        base_file_name, _ = os.path.splitext(res_file.file_name)
        # check that the resource file is not associated with any logical file type
        self.assertEqual(res_file.has_logical_file, False)

        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.extension, '.zip')

        # set the zip file to GeoFeatureLogicalFile type
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test file type and file type metadata
        assert_geofeature_file_type_metadata(self, expected_folder_name='')

        # there should not be any file level keywords
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.metadata.keywords, [])
        geo_aggr = GeoFeatureLogicalFile.objects.first()
        # check that there is one required missing metadata for the geographic feature aggregation
        missing_meta_elements = geo_aggr.metadata.get_required_missing_elements()
        self.assertEqual(len(missing_meta_elements), 1)
        # check spatial coverage is missing
        self.assertIn('Spatial Coverage', missing_meta_elements)

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()
        # there should be no GeoFeatureLogicalFile object at this point
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 0)
        # there should be no GeoFeatureFileMetaData object at this point
        self.assertEqual(GeoFeatureFileMetaData.objects.count(), 0)

    def test_create_aggregation_from_zip_file_required_2(self):
        # here we are using a zip file that has only the 3 required files for setting it
        # to Geo Feature file type which includes metadata extraction
        # the zip file that we are using to create an aggregation here is not at the root of the
        # folder hierarchy but in a folder - no new folder should be created as part of creating
        # this aggregation

        self.create_composite_resource()

        new_folder = 'geofeature_aggr'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the zip file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.states_required_zip_file,
                                  upload_folder=new_folder)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.file_folder, new_folder)

        # check that the resource file is not associated with any logical file type
        self.assertEqual(res_file.has_logical_file, False)
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 0)

        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.extension, '.zip')

        # set the zip file to GeoFeatureLogicalFile type
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test file type and file type metadata
        assert_geofeature_file_type_metadata(self, new_folder)

        for res_file in self.composite_resource.files.all():
            # test that each resource file is part of an aggregation (logical file)
            self.assertTrue(res_file.has_logical_file)
            # test that the each resource file has the same folder - no new folder was created
            self.assertEqual(res_file.file_folder, new_folder)

        # there should not be any file level keywords
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.metadata.keywords, [])
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()
        # there should be no GeoFeatureLogicalFile object at this point
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 0)
        # there should be no GeoFeatureFileMetaData object at this point
        self.assertEqual(GeoFeatureFileMetaData.objects.count(), 0)

    def test_create_aggregation_from_zip_file_all(self):
        # here we are using a zip file that has all the 15 files for setting it
        # to Geo Feature file type which includes metadata extraction
        # this zip file for creating aggregation is at the root of the folder hierarchy

        self.create_composite_resource(self.osm_all_files_zip_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        base_file_name, _ = os.path.splitext(res_file.file_name)
        # check that the resource file is not associated with any logical file type
        self.assertEqual(res_file.has_logical_file, False)

        # set the zip file to GeoFeatureLogicalFile type
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test files in the file type
        self.assertEqual(self.composite_resource.files.count(), 15)
        # check that there is no GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        # check that there is no GenericFileMetaData object
        self.assertEqual(GenericFileMetaData.objects.count(), 0)
        # check that there is one GeoFeatureLogicalFile object
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 1)
        logical_file = GeoFeatureLogicalFile.objects.first()
        self.assertEqual(logical_file.files.count(), 15)
        # check that the 3 resource files are now associated with GeoFeatureLogicalFile
        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.logical_file_type_name, "GeoFeatureLogicalFile")
            self.assertEqual(res_file.has_logical_file, True)
            self.assertTrue(isinstance(res_file.logical_file, GeoFeatureLogicalFile))

        # test extracted raster file type metadata
        # there should one resource level coverage
        self.assertEqual(self.composite_resource.metadata.coverages.count(), 1)
        self.assertEqual(logical_file.metadata.fieldinformations.all().count(), 7)
        self.assertEqual(logical_file.metadata.geometryinformation.featureCount, 87)
        self.assertEqual(logical_file.metadata.geometryinformation.geometryType, "POLYGON")
        self.assertEqual(logical_file.metadata.originalcoverage.datum, 'WGS_1984')
        self.assertTrue(abs(logical_file.metadata.originalcoverage.eastlimit
                            - 3.4520493) < self.allowance)
        self.assertTrue(abs(logical_file.metadata.originalcoverage.northlimit
                            - 45.0466382) < self.allowance)
        self.assertTrue(abs(logical_file.metadata.originalcoverage.southlimit
                            - 42.5732416) < self.allowance)
        self.assertTrue(abs(logical_file.metadata.originalcoverage.westlimit
                            - (-0.3263017)) < self.allowance)
        self.assertEqual(logical_file.metadata.originalcoverage.unit, 'degree')
        self.assertEqual(logical_file.metadata.originalcoverage.projection_name,
                         'WGS 84')

        # there should be file level keywords
        for key in ('Logan River', 'TauDEM'):
            self.assertIn(key, logical_file.metadata.keywords)
        self.assertEqual(len(logical_file.metadata.keywords), 2)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()
        # there should be no GeoFeatureLogicalFile object at this point
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 0)
        # there should be no GenericFileMetaData object at this point
        self.assertEqual(GeoFeatureFileMetaData.objects.count(), 0)

    def test_create_aggregation_from_shp_file_required_1(self):
        # here we are using a shp file that exists at the root of the folder hierarchy
        # for setting it to Geo Feature file type which includes metadata extraction

        self.create_composite_resource()

        # add the 3 required files to the resource at the above folder
        res_file = self.add_file_to_resource(file_to_add=self.states_shp_file)
        self.assertEqual(res_file.file_folder, '')
        res_file = self.add_file_to_resource(file_to_add=self.states_shx_file)
        self.assertEqual(res_file.file_folder, '')
        res_file = self.add_file_to_resource(file_to_add=self.states_dbf_file)
        self.assertEqual(res_file.file_folder, '')

        self.assertEqual(self.composite_resource.files.all().count(), 3)
        res_file = self.composite_resource.files.first()
        base_file_name, _ = os.path.splitext(res_file.file_name)
        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # set the shp file to GeoFeatureLogicalFile type
        shp_res_file = [f for f in self.composite_resource.files.all() if f.extension == '.shp'][0]
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, shp_res_file.id)

        # test files in the file type
        self.assertEqual(self.composite_resource.files.count(), 3)
        # check that there is no GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        # check that there is one GeoFeatureLogicalFile object
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 1)
        logical_file = GeoFeatureLogicalFile.objects.first()
        self.assertEqual(logical_file.files.count(), 3)
        # check that the 3 resource files are now associated with GeoFeatureLogicalFile
        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.logical_file_type_name, "GeoFeatureLogicalFile")
            self.assertEqual(res_file.has_logical_file, True)
            self.assertTrue(isinstance(res_file.logical_file, GeoFeatureLogicalFile))

        # test extracted raster file type metadata
        # there should not be any resource level coverage
        self.assertEqual(self.composite_resource.metadata.coverages.count(), 0)
        self.assertNotEqual(logical_file.metadata.geometryinformation, None)
        self.assertEqual(logical_file.metadata.geometryinformation.featureCount, 51)
        self.assertEqual(logical_file.metadata.geometryinformation.geometryType,
                         "MULTIPOLYGON")

        self.assertNotEqual(logical_file.metadata.originalcoverage, None)
        self.assertEqual(logical_file.metadata.originalcoverage.datum,
                         'unknown')
        self.assertEqual(logical_file.metadata.originalcoverage.projection_name,
                         'unknown')
        self.assertGreater(len(logical_file.metadata.originalcoverage.projection_string), 0)
        self.assertEqual(logical_file.metadata.originalcoverage.unit, 'unknown')
        expected_elimit = -66.9692712587578
        self.assertAlmostEqual(logical_file.metadata.originalcoverage.eastlimit, expected_elimit,
                               places=get_number_of_decimal_places(expected_elimit))
        expected_nlimit = 71.406235393967
        self.assertAlmostEqual(logical_file.metadata.originalcoverage.northlimit, expected_nlimit,
                               places=get_number_of_decimal_places(expected_nlimit))
        expected_slimit = 18.921786345087
        self.assertAlmostEqual(logical_file.metadata.originalcoverage.southlimit, expected_slimit,
                               places=get_number_of_decimal_places(expected_slimit))
        expected_wlimit = -178.217598362366
        self.assertAlmostEqual(logical_file.metadata.originalcoverage.westlimit, expected_wlimit,
                               places=get_number_of_decimal_places(expected_wlimit))

        # there should not be any file level keywords
        self.assertEqual(logical_file.metadata.keywords, [])
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()
        # there should be no GeoFeatureLogicalFile object at this point
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 0)
        # there should be no GenericFileMetaData object at this point
        self.assertEqual(GeoFeatureFileMetaData.objects.count(), 0)

    def test_create_aggregation_from_shp_file_required_2(self):
        # here we are using a shp file that exists in a folder
        # for setting it to Geo Feature file type which includes metadata extraction
        # no new folder should be created as part o creating this aggregation

        self.create_composite_resource()

        new_folder = 'geofeature_aggr'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the 3 required files to the resource at the above folder
        res_file = self.add_file_to_resource(file_to_add=self.states_shp_file,
                                             upload_folder=new_folder)
        self.assertEqual(res_file.file_folder, new_folder)
        res_file = self.add_file_to_resource(file_to_add=self.states_shx_file,
                                             upload_folder=new_folder)
        self.assertEqual(res_file.file_folder, new_folder)
        res_file = self.add_file_to_resource(file_to_add=self.states_dbf_file,
                                             upload_folder=new_folder)
        self.assertEqual(res_file.file_folder, new_folder)

        self.assertEqual(self.composite_resource.files.all().count(), 3)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 0)
        # set the shp file to GeoFeatureLogicalFile type
        shp_res_file = [f for f in self.composite_resource.files.all() if f.extension == '.shp'][0]
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, shp_res_file.id)
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 1)
        for res_file in self.composite_resource.files.all():
            # test that each resource file is part of an aggregation (logical file)
            self.assertTrue(res_file.has_logical_file)
            # test that the each resource file has the same folder - no new folder created
            self.assertEqual(res_file.file_folder, new_folder)

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_from_shp_file_required_3(self):
        # here we are using a shp file that exists in a folder
        # for setting it to Geo Feature file type which includes metadata extraction
        # The same folder contains another file that is not going to be part of the
        # geofeature aggregation a new folder should be created in this case to represent the
        # geofeature aggregation
        # location shp file before aggregation is created: my_folder/states.shp
        # location of another file before aggregation is created: my_folder/states_invalid.zip
        # location of shp file after aggregation is created: my_folder/states/states.shp
        # location of another file after aggregation is created: my_folder/states_invalid.zip

        self.create_composite_resource()

        new_folder = 'my_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the 3 required files to the resource at the above folder
        res_file = self.add_file_to_resource(file_to_add=self.states_shp_file,
                                             upload_folder=new_folder)
        self.assertEqual(res_file.file_folder, new_folder)
        res_file = self.add_file_to_resource(file_to_add=self.states_shx_file,
                                             upload_folder=new_folder)
        self.assertEqual(res_file.file_folder, new_folder)
        res_file = self.add_file_to_resource(file_to_add=self.states_dbf_file,
                                             upload_folder=new_folder)
        self.assertEqual(res_file.file_folder, new_folder)

        self.assertEqual(self.composite_resource.files.all().count(), 3)

        # add a file that is not related to aggregation
        res_file = self.add_file_to_resource(file_to_add=self.states_zip_invalid_file,
                                             upload_folder=new_folder)
        self.assertEqual(res_file.file_folder, new_folder)
        self.assertEqual(self.composite_resource.files.all().count(), 4)
        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 0)
        # set the shp file to GeoFeatureLogicalFile type
        shp_res_file = [f for f in self.composite_resource.files.all() if f.extension == '.shp'][0]
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, shp_res_file.id)
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 1)
        base_shp_file_base_name, _ = os.path.splitext(shp_res_file.file_name)
        shp_res_file = [f for f in self.composite_resource.files.all() if f.extension == '.shp'][0]
        logical_file = shp_res_file.logical_file
        self.assertEqual(logical_file.files.count(), 3)
        for res_file in logical_file.files.all():
            # test that the each resource file has the same folder - no new folder created
            self.assertEqual(res_file.file_folder, new_folder)
        self.assertEqual(self.composite_resource.files.all().count(), 4)

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_from_shp_file_required_4(self):
        # here we are using a shp file that exists in a folder
        # for setting it to Geo Feature file type which includes metadata extraction
        # The same folder contains another folder
        # a new folder should be created in this case to represent the
        # geofeature aggregation
        # location shp file before aggregation is created: my_folder/states.shp
        # location of another folder before aggregation is created: my_folder/another_folder
        # location of shp file after aggregation is created: my_folder/states/states.shp

        self.create_composite_resource()

        new_folder = 'my_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the 3 required files to the resource at the above folder
        res_file = self.add_file_to_resource(file_to_add=self.states_shp_file,
                                             upload_folder=new_folder)
        self.assertEqual(res_file.file_folder, new_folder)
        res_file = self.add_file_to_resource(file_to_add=self.states_shx_file,
                                             upload_folder=new_folder)
        self.assertEqual(res_file.file_folder, new_folder)
        res_file = self.add_file_to_resource(file_to_add=self.states_dbf_file,
                                             upload_folder=new_folder)
        self.assertEqual(res_file.file_folder, new_folder)

        another_folder = '{}/another_folder'.format(new_folder)
        ResourceFile.create_folder(self.composite_resource, another_folder)

        self.assertEqual(self.composite_resource.files.all().count(), 3)

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 0)
        # set the shp file to GeoFeatureLogicalFile type
        shp_res_file = [f for f in self.composite_resource.files.all() if f.extension == '.shp'][0]
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, shp_res_file.id)
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 1)
        base_shp_file_base_name, _ = os.path.splitext(shp_res_file.file_name)
        expected_file_folder = new_folder
        shp_res_file = [f for f in self.composite_resource.files.all() if f.extension == '.shp'][0]
        logical_file = shp_res_file.logical_file
        self.assertEqual(logical_file.files.count(), 3)
        for res_file in logical_file.files.all():
            # test that the each resource file has the same folder - no new folder created
            self.assertEqual(res_file.file_folder, expected_file_folder)

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_zip_invalid_set_file_type_to_geo_feature(self):
        # here we are using a invalid zip file that is missing the shx file
        # to set Geo Feature file type which should fail

        self.create_composite_resource(self.states_zip_invalid_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # set the tif file to GeoFeatureFile type
        with self.assertRaises(ValidationError):
            GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test file was rolled back
        self.assertEqual(self.composite_resource.files.count(), 1)
        # check that there is no GeoFeatureLogicalFile object
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 0)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_logical_file_delete(self):
        # test that when an instance GeoFeatureLogicalFile Type is deleted
        # all files associated with GeoFeatureLogicalFile is deleted

        self.create_composite_resource(self.states_required_zip_file)
        res_file = self.composite_resource.files.first()

        # extract metadata from the tif file
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test that we have one logical file of type GeoRasterFileType as a result
        # of metadata extraction
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 1)
        logical_file = GeoFeatureLogicalFile.objects.first()
        self.assertEqual(logical_file.files.all().count(), 3)
        self.assertEqual(self.composite_resource.files.all().count(), 3)
        self.assertEqual(set(self.composite_resource.files.all()),
                         set(logical_file.files.all()))

        # delete the logical file using the custom delete function - logical_delete()
        logical_file.logical_delete(self.user)
        self.assertEqual(self.composite_resource.files.all().count(), 0)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_remove_aggregation(self):
        # test that when an instance GeoFeatureLogicalFile (aggregation) is deleted
        # all resource files associated with that aggregation is not deleted but the associated
        # metadata is deleted

        self.create_composite_resource(self.states_required_zip_file)
        res_file = self.composite_resource.files.first()
        file_folder = res_file.file_folder
        base_file_name, _ = os.path.splitext(res_file.file_name)

        # set the zip file to GeoFeatureLogicalFile (aggregation) type
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test that we have one logical file (aggregation) of type GeoFeatureLogicalFile
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 1)
        self.assertEqual(GeoFeatureFileMetaData.objects.count(), 1)
        logical_file = GeoFeatureLogicalFile.objects.first()
        self.assertEqual(logical_file.files.all().count(), 3)
        self.assertEqual(self.composite_resource.files.all().count(), 3)
        self.assertEqual(set(self.composite_resource.files.all()),
                         set(logical_file.files.all()))

        # delete the aggregation (logical file) object using the remove_aggregation function
        logical_file.remove_aggregation()
        # test there is no GeoFeatureLogicalFile object
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 0)
        # test there is no GeoFeatureFileMetaData object
        self.assertEqual(GeoFeatureFileMetaData.objects.count(), 0)
        # check the files associated with the aggregation not deleted
        self.assertEqual(self.composite_resource.files.all().count(), 3)
        # check the file folder is not deleted
        for f in self.composite_resource.files.all():
            self.assertEqual(f.file_folder, file_folder)

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def _test_content_file_delete(self):
        # test that when any file in GeoFeatureLogicalFile type is deleted
        # all metadata associated with GeoFeatureLogicalFile is deleted
        # test for all 15 file extensions (this one test is kind of running 15 tests - takes a while to finish)

        for ext in GeoFeatureLogicalFile.get_allowed_storage_file_types():
            self._test_file_metadata_on_file_delete(ext=ext)

    def test_geofeature_file_type_folder_delete(self):
        # when  a file is set to geofeaturelogical file type
        # system automatically creates a folder using the name of the file
        # that was used to set the file type
        # Here we need to test that when that folder gets deleted, all files
        # in that folder gets deleted, the logicalfile object gets deleted and
        # the associated metadata objects get deleted

        self.create_composite_resource()
        new_folder = 'my_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the 3 required files to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.states_required_zip_file,
                                  upload_folder=new_folder)
        res_file = self.composite_resource.files.first()
        base_file_name, _ = os.path.splitext(res_file.file_name)

        # extract metadata from the zip file
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # test that we have one logical file of type GeoFeatureLogicalFile type as a result
        # of metadata extraction
        self.assertEqual(GeoFeatureFileMetaData.objects.count(), 1)
        # should have one GeoFeatureFileMetadata object
        self.assertEqual(GeoFeatureFileMetaData.objects.count(), 1)

        # there should be 3 content files
        self.assertEqual(self.composite_resource.files.count(), 3)
        # delete the folder for the logical file
        folder_path = "data/contents/{}".format(new_folder)
        remove_folder(self.user, self.composite_resource.short_id, folder_path)
        # there should be no content files
        self.assertEqual(self.composite_resource.files.count(), 0)
        # there should not be any logical file or file metadata object as a result
        # of folder deletion
        self.assertEqual(GeoFeatureFileMetaData.objects.count(), 0)
        self.assertEqual(GeoFeatureFileMetaData.objects.count(), 0)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_aggregation_file_rename(self):
        # test that a file can't renamed for any resource file
        # that's part of the GeoFeature logical file

        self.create_composite_resource()
        new_folder = 'my_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the 3 required files to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.states_required_zip_file,
                                  upload_folder=new_folder)
        res_file = self.composite_resource.files.first()
        base_file_name, _ = os.path.splitext(res_file.file_name)

        # create aggregation from the zip file
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # test renaming of files that are associated with aggregation raises exception
        self.assertEqual(self.composite_resource.files.count(), 3)

        src_path = 'data/contents/{}/states.shp'.format(new_folder)
        tgt_path = 'data/contents/{}/states-1.shp'.format(new_folder)
        with self.assertRaises(DRF_ValidationError):
            move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                          tgt_path)
        src_path = 'data/contents/{}/states.dbf'.format(new_folder)
        tgt_path = 'data/contents/{}/states-1.dbf'.format(new_folder)
        with self.assertRaises(DRF_ValidationError):
            move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                          tgt_path)

        src_path = 'data/contents/{}/states.shx'.format(new_folder)
        tgt_path = 'data/contents/{}/states-1.shx'.format(new_folder)
        with self.assertRaises(DRF_ValidationError):
            move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                          tgt_path)

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_aggregation_file_move(self):
        # test any resource file that's part of the GeoFeature logical file can't be moved

        self.create_composite_resource(self.states_required_zip_file)
        res_file = self.composite_resource.files.first()
        base_file_name, _ = os.path.splitext(res_file.file_name)
        # extract metadata from the tif file
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # test renaming of files that are associated with geo feature LFO - which should
        # raise exception
        self.assertEqual(self.composite_resource.files.count(), 3)
        new_folder = 'geofeature_aggr'
        ResourceFile.create_folder(self.composite_resource, new_folder)

        # moving any of the resource files to this new folder should raise exception
        tgt_path = 'data/contents/geofeature_aggr'
        for res_file in self.composite_resource.files.all():
            with self.assertRaises(DRF_ValidationError):
                src_path = os.path.join('data', 'contents', res_file.short_path)
                move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                              tgt_path)

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_aggregation_folder_rename(self):
        # test changes to aggregation name, aggregation metadata xml file path, and aggregation
        # resource map xml file path on folder name change

        self.create_composite_resource()
        new_folder = 'my_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the 3 required files to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.states_required_zip_file,
                                  upload_folder=new_folder)
        res_file = self.composite_resource.files.first()

        # create aggregation from the zip file
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        self.assertEqual(self.composite_resource.files.count(), 3)
        base_file_name, _ = os.path.splitext(res_file.file_name)
        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, new_folder)

        # test aggregation name
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        # test aggregation xml file paths
        shp_file_path = get_path_with_no_file_extension(logical_file.aggregation_name)
        expected_meta_file_path = '{0}{1}'.format(shp_file_path, AggregationMetaFilePath.METADATA_FILE_ENDSWITH)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_file_path)

        expected_map_file_path = '{0}{1}'.format(shp_file_path, AggregationMetaFilePath.RESMAP_FILE_ENDSWITH)
        self.assertEqual(logical_file.map_short_file_path, expected_map_file_path)

        # test renaming folder
        src_path = 'data/contents/{}'.format(new_folder)
        tgt_path = 'data/contents/{}_1'.format(new_folder)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, '{}_1'.format(new_folder))

        # test aggregation name update
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        # test aggregation xml file paths
        new_shp_file_path = get_path_with_no_file_extension(logical_file.aggregation_name)
        self.assertNotEqual(new_shp_file_path, shp_file_path)
        expected_meta_file_path = '{0}{1}'.format(new_shp_file_path,
                                                  AggregationMetaFilePath.METADATA_FILE_ENDSWITH)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_file_path)

        expected_map_file_path = '{0}{1}'.format(new_shp_file_path,
                                                 AggregationMetaFilePath.RESMAP_FILE_ENDSWITH)
        self.assertEqual(logical_file.map_short_file_path, expected_map_file_path)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_aggregation_parent_folder_rename(self):
        # test changes to aggregation name, aggregation metadata xml file path, and aggregation
        # resource map xml file path on aggregation folder parent folder name change

        self.create_composite_resource()
        new_folder = 'my_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the 3 required files to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.states_required_zip_file,
                                  upload_folder=new_folder)
        res_file = self.composite_resource.files.first()

        # create aggregation from the zip file
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # test renaming of files that are associated with aggregation raises exception
        self.assertEqual(self.composite_resource.files.count(), 3)
        base_file_name, _ = os.path.splitext(res_file.file_name)
        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, new_folder)

        # test aggregation name
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        # test aggregation xml file paths
        shp_file_path = get_path_with_no_file_extension(logical_file.aggregation_name)
        expected_meta_file_path = '{0}{1}'.format(shp_file_path, AggregationMetaFilePath.METADATA_FILE_ENDSWITH)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_file_path)

        expected_map_file_path = '{0}{1}'.format(shp_file_path, AggregationMetaFilePath.RESMAP_FILE_ENDSWITH)
        self.assertEqual(logical_file.map_short_file_path, expected_map_file_path)

        # create a folder to be the parent folder of the aggregation folder
        parent_folder = 'parent_folder'
        ResourceFile.create_folder(self.composite_resource, parent_folder)
        # move the aggregation folder to the parent folder
        src_path = 'data/contents/{}'.format(new_folder)
        tgt_path = 'data/contents/{0}/{1}'.format(parent_folder, new_folder)

        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        file_folder = '{0}/{1}'.format(parent_folder, new_folder)
        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, file_folder)

        # renaming parent folder
        parent_folder_rename = 'parent_folder_1'
        src_path = 'data/contents/{}'.format(parent_folder)
        tgt_path = 'data/contents/{}'.format(parent_folder_rename)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        file_folder = '{}/{}'.format(parent_folder_rename, new_folder)
        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, file_folder)

        # test aggregation name after folder rename
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        # test aggregation xml file paths after folder rename
        new_shp_file_path = get_path_with_no_file_extension(logical_file.aggregation_name)
        self.assertNotEqual(new_shp_file_path, shp_file_path)
        expected_meta_file_path = '{0}{1}'.format(new_shp_file_path,
                                                  AggregationMetaFilePath.METADATA_FILE_ENDSWITH)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_file_path)

        expected_map_file_path = '{0}{1}'.format(new_shp_file_path, AggregationMetaFilePath.RESMAP_FILE_ENDSWITH)
        self.assertEqual(logical_file.map_short_file_path, expected_map_file_path)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_aggregation_folder_move(self):
        # test changes to aggregation name, aggregation metadata xml file path, and aggregation
        # resource map xml file path on aggregation folder move

        self.create_composite_resource()
        new_folder = 'my_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the 3 required files to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.states_required_zip_file,
                                  upload_folder=new_folder)
        res_file = self.composite_resource.files.first()

        # create aggregation from the zip file
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        self.assertEqual(self.composite_resource.files.count(), 3)
        base_file_name, _ = os.path.splitext(res_file.file_name)
        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, new_folder)

        # test aggregation name
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        shp_file_path = get_path_with_no_file_extension(logical_file.aggregation_name)
        # test aggregation xml file paths
        expected_meta_file_path = '{0}{1}'.format(shp_file_path, AggregationMetaFilePath.METADATA_FILE_ENDSWITH)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_file_path)

        expected_map_file_path = '{0}{1}'.format(shp_file_path, AggregationMetaFilePath.RESMAP_FILE_ENDSWITH)
        self.assertEqual(logical_file.map_short_file_path, expected_map_file_path)

        # create a folder to move the aggregation folder there
        parent_folder = 'parent_folder'
        ResourceFile.create_folder(self.composite_resource, parent_folder)
        # move the aggregation folder to the parent folder
        src_path = 'data/contents/{}'.format(new_folder)
        tgt_path = 'data/contents/{}/{}'.format(parent_folder, new_folder)

        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        file_folder = '{}/{}'.format(parent_folder, new_folder)
        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, file_folder)

        # test aggregation name update
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        shp_file_path = get_path_with_no_file_extension(logical_file.aggregation_name)

        # test aggregation xml file paths
        expected_meta_file_path = '{0}{1}'.format(shp_file_path, AggregationMetaFilePath.METADATA_FILE_ENDSWITH)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_file_path)

        expected_map_file_path = '{0}{1}'.format(shp_file_path, AggregationMetaFilePath.RESMAP_FILE_ENDSWITH)
        self.assertEqual(logical_file.map_short_file_path, expected_map_file_path)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_file_metadata_on_resource_delete(self):
        # test that when the composite resource is deleted
        # all metadata associated with GeoFeatureLogicalFile Type is deleted

        self.create_composite_resource(self.states_required_zip_file)
        res_file = self.composite_resource.files.first()

        # extract metadata from the tif file
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test that we have one logical file of type GeoFeatureLogicalFile as a result
        # of metadata extraction
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 1)
        self.assertEqual(GeoFeatureFileMetaData.objects.count(), 1)

        # test that we have the metadata elements
        # there should be no Coverage objects
        self.assertEqual(Coverage.objects.count(), 0)
        self.assertEqual(GeometryInformation.objects.count(), 1)
        self.assertEqual(OriginalCoverageGeofeature.objects.count(), 1)
        self.assertEqual(FieldInformation.objects.count(), 5)

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        # delete resource
        hydroshare.delete_resource(self.composite_resource.short_id)

        # test that we have no logical file of type GeoFeatureLogicalFileType
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 0)
        self.assertEqual(GeoFeatureFileMetaData.objects.count(), 0)

        # test that all metadata deleted
        self.assertEqual(Coverage.objects.count(), 0)
        self.assertEqual(GeometryInformation.objects.count(), 0)
        self.assertEqual(OriginalCoverageGeofeature.objects.count(), 0)
        self.assertEqual(FieldInformation.objects.count(), 0)

    def _test_file_metadata_on_file_delete(self, ext):
        self.create_composite_resource(self.osm_all_files_zip_file)
        res_file = self.composite_resource.files.first()
        # set the zip file to GeoFeatureFile type
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test files in the file type
        self.assertEqual(self.composite_resource.files.count(), 15)
        # check that there is no GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        # check that there is one GeoFeatureLogicalFile object
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 1)
        # check that there is one GeoFeatureFileMetaData
        self.assertEqual(GeoFeatureFileMetaData.objects.count(), 1)
        logical_file = GeoFeatureLogicalFile.objects.first()
        self.assertEqual(logical_file.files.count(), 15)

        # one at the file level and one at the resource level
        self.assertEqual(Coverage.objects.count(), 2)
        self.assertEqual(FieldInformation.objects.count(), 7)
        self.assertEqual(GeometryInformation.objects.count(), 1)
        self.assertEqual(OriginalCoverageGeofeature.objects.count(), 1)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(len(logical_file.metadata.keywords), 2)
        for key in ('Logan River', 'TauDEM'):
            self.assertIn(key, logical_file.metadata.keywords)

        # delete content file specified by extension (ext parameter)
        res_file = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, ext)[0]
        hydroshare.delete_resource_file(self.composite_resource.short_id,
                                        res_file.id,
                                        self.user)
        # test that we don't have logical file of type GeoFeatureLogicalFile type
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 0)
        self.assertEqual(GeoFeatureFileMetaData.objects.count(), 0)

        # test that all metadata got deleted - there should be still1 coverage at the resource level
        self.assertEqual(self.composite_resource.metadata.coverages.all().count(), 1)
        self.assertEqual(Coverage.objects.count(), 1)
        self.assertEqual(FieldInformation.objects.count(), 0)
        self.assertEqual(GeometryInformation.objects.count(), 0)
        self.assertEqual(OriginalCoverageGeofeature.objects.count(), 0)

        # there should not be any files left
        self.assertEqual(self.composite_resource.files.count(), 0)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_main_file(self):
        self.create_composite_resource(self.states_required_zip_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # set the zip file to GeoFeatureLogicalFile type
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        self.assertEqual(1, GeoFeatureLogicalFile.objects.count())
        self.assertEqual(".shp", GeoFeatureLogicalFile.objects.first().get_main_file_type())
        self.assertEqual(self.states_shp_file_name,
                         GeoFeatureLogicalFile.objects.first().get_main_file.file_name)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()
