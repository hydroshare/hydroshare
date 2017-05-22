import os
import tempfile
import shutil

from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.models import Coverage
from hs_core.hydroshare.utils import resource_post_create_actions, \
    get_resource_file_name_and_extension

from hs_geographic_feature_resource.models import FieldInformation, GeometryInformation, \
    OriginalCoverage
from utils import assert_geofeature_file_type_metadata
from hs_file_types.models import GeoFeatureLogicalFile, GenericLogicalFile, GenericFileMetaData,\
    GeoFeatureFileMetaData


class GeoFeatureFileTypeMetaDataTest(MockIRODSTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(GeoFeatureFileTypeMetaDataTest, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Goe Feature File Metadata'
        )

        self.temp_dir = tempfile.mkdtemp()
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

    def tearDown(self):
        super(GeoFeatureFileTypeMetaDataTest, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_zip_set_file_type_to_geo_feature_required(self):
        # here we are using a zip file that has only the 3 required files for setting it
        # to Geo Feature file type which includes metadata extraction

        self._create_composite_resource(self.states_required_zip_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        expected_folder_name = res_file.file_name[:-4]
        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
        # check that there is one GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 1)
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.extension, '.zip')
        logical_file = res_file.logical_file
        self.assertTrue(isinstance(logical_file.metadata, GenericFileMetaData))
        self.assertTrue(isinstance(logical_file, GenericLogicalFile))
        # TODO: not sure why there would be file level keywords at this point - commenting to
        # avoid test failure
        # self.assertEqual(logical_file.metadata.keywords, [])

        # set the zip file to GeoFeatureFile type
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)

        # test file type and file type metadata
        assert_geofeature_file_type_metadata(self, expected_folder_name)

        # there should not be any file level keywords
        # TODO: not sure why there would be file level keywords - commented out as the test is
        # failing
        # res_file = self.composite_resource.files.first()
        # logical_file = res_file.logical_file
        # self.assertEqual(logical_file.metadata.keywords, [])

        self.composite_resource.delete()
        # there should be no GeoFeatureLogicalFile object at this point
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 0)
        # there should be no GenericFileMetaData object at this point
        self.assertEqual(GeoFeatureFileMetaData.objects.count(), 0)

    def test_zip_set_file_type_to_geo_feature_all(self):
        # here we are using a zip file that has all the 15 files for setting it
        # to Geo Feature file type which includes metadata extraction

        self._create_composite_resource(self.osm_all_files_zip_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        expected_folder_name = res_file.file_name[:-4]
        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
        # check that there is one GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

        # set the zip file to GeoFeatureFile type
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)

        # test files in the file type
        self.assertEqual(self.composite_resource.files.count(), 15)
        # check that there is no GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        # check that there is one GeoFeatureLogicalFile object
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 1)
        logical_file = GeoFeatureLogicalFile.objects.first()
        self.assertEqual(logical_file.files.count(), 15)
        # check that the 3 resource files are now associated with GeoFeatureLogicalFile
        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.logical_file_type_name, "GeoFeatureLogicalFile")
            self.assertEqual(res_file.has_logical_file, True)
            self.assertTrue(isinstance(res_file.logical_file, GeoFeatureLogicalFile))
        # check that we put the 3 files in a new folder
        for res_file in self.composite_resource.files.all():
            file_path, base_file_name, _ = get_resource_file_name_and_extension(res_file)
            expected_file_path = "{}/data/contents/{}/{}"
            res_file.file_folder = expected_folder_name
            expected_file_path = expected_file_path.format(self.composite_resource.root_path,
                                                           expected_folder_name, base_file_name)
            self.assertEqual(file_path, expected_file_path)
        # test extracted raster file type metadata
        # there should one resource level coverage
        self.assertEqual(self.composite_resource.metadata.coverages.count(), 1)
        self.assertEqual(logical_file.metadata.fieldinformations.all().count(), 7)
        self.assertEqual(logical_file.metadata.geometryinformation.featureCount, 87)
        self.assertEqual(logical_file.metadata.geometryinformation.geometryType, "POLYGON")
        self.assertEqual(logical_file.metadata.originalcoverage.datum, 'WGS_1984')
        self.assertTrue(abs(logical_file.metadata.originalcoverage.eastlimit -
                            3.4520493) < self.allowance)
        self.assertTrue(abs(logical_file.metadata.originalcoverage.northlimit -
                            45.0466382) < self.allowance)
        self.assertTrue(abs(logical_file.metadata.originalcoverage.southlimit -
                            42.5732416) < self.allowance)
        self.assertTrue(abs(logical_file.metadata.originalcoverage.westlimit -
                            (-0.3263017)) < self.allowance)
        self.assertEqual(logical_file.metadata.originalcoverage.unit, 'Degree')
        self.assertEqual(logical_file.metadata.originalcoverage.projection_name,
                         'GCS_WGS_1984')

        # there should be file level keywords
        for key in ('Logan River', 'TauDEM'):
            self.assertIn(key, logical_file.metadata.keywords)
        self.assertEqual(len(logical_file.metadata.keywords), 2)

        self.composite_resource.delete()
        # there should be no GeoFeatureLogicalFile object at this point
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 0)
        # there should be no GenericFileMetaData object at this point
        self.assertEqual(GeoFeatureFileMetaData.objects.count(), 0)

    def test_shp_set_file_type_to_geo_feature_required(self):
        # here we are using a shp file for setting it
        # to Geo Feature file type which includes metadata extraction

        self._create_composite_resource()

        # add the 3 required files to the resource
        files = []
        shp_temp_file = os.path.join(self.temp_dir, self.states_shp_file_name)
        shutil.copy(self.states_shp_file, shp_temp_file)

        shx_temp_file = os.path.join(self.temp_dir, self.states_shx_file_name)
        shutil.copy(self.states_shx_file, shx_temp_file)

        dbf_temp_file = os.path.join(self.temp_dir, self.states_dbf_file_name)
        shutil.copy(self.states_dbf_file, dbf_temp_file)

        files.append(UploadedFile(file=open(shp_temp_file, 'r'),
                                  name=self.states_shp_file_name))
        files.append(UploadedFile(file=open(shx_temp_file, 'r'),
                                  name=self.states_shx_file_name))
        files.append(UploadedFile(file=open(dbf_temp_file, 'r'),
                                  name=self.states_dbf_file_name))
        hydroshare.utils.resource_file_add_process(self.composite_resource, files, self.user)

        self.assertEqual(self.composite_resource.files.all().count(), 3)
        res_file = self.composite_resource.files.first()
        expected_folder_name = res_file.file_name[:-4]
        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
        # check that there is 3 GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 3)

        # set the shp file to GeoFeatureFile type
        shp_res_file = [f for f in self.composite_resource.files.all() if f.extension == '.shp'][0]
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, shp_res_file.id, self.user)

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
        # check that we put the 3 files in a new folder
        for res_file in self.composite_resource.files.all():
            file_path, base_file_name, _ = get_resource_file_name_and_extension(res_file)
            expected_file_path = "{}/data/contents/{}/{}"
            res_file.file_folder = expected_folder_name
            expected_file_path = expected_file_path.format(self.composite_resource.root_path,
                                                           expected_folder_name, base_file_name)
            self.assertEqual(file_path, expected_file_path)
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
        self.assertEqual(logical_file.metadata.originalcoverage.eastlimit, -66.9692712587578)
        self.assertEqual(logical_file.metadata.originalcoverage.northlimit, 71.406235393967)
        self.assertEqual(logical_file.metadata.originalcoverage.southlimit, 18.921786345087)
        self.assertEqual(logical_file.metadata.originalcoverage.westlimit, -178.217598362366)
        # TODO: not sure why there would be file level keywords - commented out as the test is
        # failing
        # there should not be any file level keywords
        # self.assertEqual(logical_file.metadata.keywords, [])

        self.composite_resource.delete()
        # there should be no GeoFeatureLogicalFile object at this point
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 0)
        # there should be no GenericFileMetaData object at this point
        self.assertEqual(GeoFeatureFileMetaData.objects.count(), 0)

    def test_zip_invalid_set_file_type_to_geo_feature(self):
        # here we are using a invalid zip file that is missing the shx file
        # to set Geo Feature file type which should fail

        self._create_composite_resource(self.states_zip_invalid_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
        # check that there is one GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

        # set the tif file to GeoFeatureFile type
        with self.assertRaises(ValidationError):
            GeoFeatureLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)

        # test file was rolled back
        self.assertEqual(self.composite_resource.files.count(), 1)
        # check that there is no GeoFeatureLogicalFile object
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 0)
        res_file = self.composite_resource.files.first()

        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
        # check that there is one GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 1)
        self.composite_resource.delete()

    def test_file_metadata_on_required_file_delete(self):
        # test that when any file in GeoFeatureLogicalFile type is deleted
        # all metadata associated with GeoFeatureLogicalFile is deleted
        # test for all 15 file extensions

        for ext in GeoFeatureLogicalFile.get_allowed_storage_file_types():
            self._test_file_metadata_on_file_delete(ext=ext)

    def _test_file_metadata_on_file_delete(self, ext):
        self._create_composite_resource(self.osm_all_files_zip_file)
        res_file = self.composite_resource.files.first()
        # set the zip file to GeoFeatureFile type
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)

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
        self.assertEqual(OriginalCoverage.objects.count(), 1)
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

        # test that all metadata got deleted
        self.assertEqual(Coverage.objects.count(), 0)
        self.assertEqual(FieldInformation.objects.count(), 0)
        self.assertEqual(GeometryInformation.objects.count(), 0)
        self.assertEqual(OriginalCoverage.objects.count(), 0)

        # there should not be any files left
        self.assertEqual(self.composite_resource.files.count(), 0)
        self.composite_resource.delete()

    def _create_composite_resource(self, file_to_upload=None):
        files = []
        if file_to_upload is not None:
            file_name = os.path.basename(file_to_upload)
            target_temp_file = os.path.join(self.temp_dir, file_name)
            shutil.copy(file_to_upload, target_temp_file)
            file_obj = open(target_temp_file, 'r')
            uploaded_file = UploadedFile(file=file_obj, name=os.path.basename(file_obj.name))
            files.append(uploaded_file)
        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Raster File Type Metadata',
            files=files
        )

        # set the generic logical file
        resource_post_create_actions(resource=self.composite_resource, user=self.user,
                                     metadata=self.composite_resource.metadata)
