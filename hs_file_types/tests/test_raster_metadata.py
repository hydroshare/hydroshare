import os

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TransactionTestCase
from rest_framework.exceptions import ValidationError as DRF_ValidationError

from hs_core import hydroshare
from hs_core.models import Coverage, ResourceFile
from hs_core.testing import MockS3TestCaseMixin
from hs_core.views.utils import move_or_rename_file_or_folder
from hs_file_types.models import GenericLogicalFile, GeoRasterFileMetaData, GeoRasterLogicalFile
from hs_file_types.enums import AggregationMetaFilePath
from hs_file_types.models.raster import BandInformation, CellInformation, OriginalCoverageRaster
from .utils import CompositeResourceTestMixin, assert_raster_file_type_metadata, get_path_with_no_file_extension


class RasterFileTypeTest(MockS3TestCaseMixin, TransactionTestCase,
                         CompositeResourceTestMixin):
    def setUp(self):
        super(RasterFileTypeTest, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        self.res_title = 'Testing Raster File Type'

        # data files to use for testing
        self.logan_tif_1_file_name = 'logan1.tif'
        self.logan_tif_2_file_name = 'logan2.tif'
        self.logan_vrt_file_name = 'logan.vrt'
        self.logan_vrt_file_name2 = 'logan2.vrt'
        self.logan_tif_1_file = 'hs_file_types/tests/{}'.format(self.logan_tif_1_file_name)
        self.logan_tif_2_file = 'hs_file_types/tests/{}'.format(self.logan_tif_2_file_name)
        self.logan_vrt_file = 'hs_file_types/tests/{}'.format(self.logan_vrt_file_name)
        self.logan_vrt_file2 = 'hs_file_types/tests/{}'.format(self.logan_vrt_file_name2)

        self.raster_file_name = 'small_logan.tif'
        self.raster_zip_file_name = 'logan_vrt_small.zip'
        self.invalid_raster_file_name = 'raster_tif_invalid.tif'
        self.raster_with_coverage_crossing_dateline_name = 'raster_with_coverage_crossing_dateline.tif'
        self.invalid_raster_zip_file_name = 'bad_small_vrt.zip'
        self.raster_file = 'hs_file_types/tests/{}'.format(self.raster_file_name)
        self.raster_zip_file = 'hs_file_types/tests/{}'.format(self.raster_zip_file_name)
        self.invalid_raster_file = 'hs_file_types/tests/{}'.format(self.invalid_raster_file_name)
        self.raster_with_coverage_crossing_dateline_file = 'hs_file_types/tests/data/{}'.format(
            self.raster_with_coverage_crossing_dateline_name)
        self.invalid_raster_zip_file = 'hs_file_types/tests/{}'.format(
            self.invalid_raster_zip_file_name)

    def test_create_aggregation_from_tif_file_1(self):
        # here we are using a valid raster tif file that exists at the root of the folder
        # hierarchy for setting it to Geo Raster file type which includes metadata extraction
        # a new folder should be created as part of the aggregation creation where the resource
        # files of the aggregation should live
        # location of raster file before aggregation: small_logan.tif
        # location of raster file after aggregation: small_logan/small_logan.tif

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.raster_file)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # set the tif file to GeoRasterLogicalFile type
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        for res_file in self.composite_resource.files.all():
            print(res_file.short_path)
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        # test extracted raster file type metadata
        assert_raster_file_type_metadata(self, aggr_folder_path='')

        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertTrue(isinstance(logical_file, GeoRasterLogicalFile))
        self.assertTrue(logical_file.metadata, GeoRasterFileMetaData)

        # check that there are no required missing metadata for the raster aggregation
        self.assertEqual(len(logical_file.metadata.get_required_missing_elements()), 0)
        # check that the vrt file was generated
        self.assertEqual(logical_file.extra_data['vrt_created'], "True")
        # there should not be any file level keywords at this point
        self.assertEqual(logical_file.metadata.keywords, [])
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_from_tif_file_2(self):
        # here we are using a valid raster tif file that exists in a folder
        # for setting it to Geo Raster file type - no new
        # folder should be created in this case
        # raster file location before aggregation is created: /raster_aggr/small_logan.tif
        # raster file location after aggregation is created: /raster_aggr/small_logan.tif

        self.create_composite_resource()
        # create a folder to place the tif file before creating an aggregation from the tif file
        new_folder = 'raster_aggr'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        self.add_file_to_resource(file_to_add=self.raster_file, upload_folder=new_folder)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # set the tif file to GeoRasterLogicalFile type
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        # test extracted raster file type metadata
        assert_raster_file_type_metadata(self, aggr_folder_path=new_folder)

        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertTrue(isinstance(logical_file, GeoRasterLogicalFile))
        self.assertTrue(logical_file.metadata, GeoRasterFileMetaData)
        self.assertEqual(logical_file.extra_data['vrt_created'], "True")
        # there should not be any file level keywords at this point
        self.assertEqual(logical_file.metadata.keywords, [])
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_from_tif_file_3(self):
        # here we are using a valid raster tif file that exists in a folder
        # for setting it to Geo Raster file type. The same folder contains another file
        # that is not going to be part of the raster aggregation
        # location raster file before aggregation is created: /my_folder/small_logan.tif
        # location of another file before aggregation is created: /my_folder/raster_tif_invalid.tif
        # location of raster file after aggregation is created:
        # /my_folder/small_logan.tif
        # location of another file after aggregation is created: /my_folder/raster_tif_invalid.tif

        self.create_composite_resource()
        # create a folder to place the tif file before creating an aggregation from the tif file
        new_folder = 'my_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        self.add_file_to_resource(file_to_add=self.raster_file, upload_folder=new_folder)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # add another file to the same folder
        self.add_file_to_resource(file_to_add=self.invalid_raster_file, upload_folder=new_folder)
        self.assertEqual(self.composite_resource.files.all().count(), 2)

        # set the tif file to GeoRasterLogicalFile type
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        self.assertEqual(self.composite_resource.files.all().count(), 3)

        # test logical file/aggregation
        self.assertEqual(len(list(self.composite_resource.logical_files)), 1)
        logical_file = list(self.composite_resource.logical_files)[0]
        self.assertEqual(logical_file.files.count(), 2)
        self.assertEqual(logical_file.extra_data['vrt_created'], "True")
        base_tif_file_name, _ = os.path.splitext(self.raster_file_name)
        expected_file_folder = new_folder
        for res_file in logical_file.files.all():
            self.assertEqual(res_file.file_folder, expected_file_folder)
        self.assertTrue(isinstance(logical_file, GeoRasterLogicalFile))
        self.assertTrue(logical_file.metadata, GeoRasterFileMetaData)

        # test the location of the file that's not part of the raster aggregation
        other_res_file = None
        for res_file in self.composite_resource.files.all():
            if not res_file.has_logical_file:
                other_res_file = res_file
                break
        self.assertEqual(other_res_file.file_folder, new_folder)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_from_tif_file_4(self):
        # here we are using a valid raster tif file that exists in a folder
        # for setting it to Geo Raster file type. The same folder contains another folder
        # a new folder should be created in this case to represent the raster aggregation
        # location raster file before aggregation is created: /my_folder/small_logan.tif
        # location of another file before aggregation is created: /my_folder/another_folder
        # location of raster file after aggregation is created:
        # /my_folder/small_logan/small_logan.tif

        self.create_composite_resource()
        # create a folder to place the tif file before creating an aggregation from the tif file
        new_folder = 'my_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        another_folder = '{}/another_folder'.format(new_folder)
        ResourceFile.create_folder(self.composite_resource, another_folder)
        self.add_file_to_resource(file_to_add=self.raster_file, upload_folder=new_folder)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # set the tif file to GeoRasterLogicalFile type
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        self.assertEqual(self.composite_resource.files.all().count(), 2)

        # test logical file/aggregation
        self.assertEqual(len(list(self.composite_resource.logical_files)), 1)
        logical_file = list(self.composite_resource.logical_files)[0]
        self.assertEqual(logical_file.files.count(), 2)
        self.assertEqual(logical_file.extra_data['vrt_created'], "True")
        base_tif_file_name, _ = os.path.splitext(self.raster_file_name)
        expected_file_folder = '{}'.format(new_folder)
        for res_file in logical_file.files.all():
            self.assertEqual(res_file.file_folder, expected_file_folder)
        self.assertTrue(isinstance(logical_file, GeoRasterLogicalFile))
        self.assertTrue(logical_file.metadata, GeoRasterFileMetaData)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_from_tif_file_5(self):
        # here we are using a valid raster tif file that has spatial coverage longitude which crosses dateline

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.raster_with_coverage_crossing_dateline_file)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        self.assertEqual(GeoRasterFileMetaData.objects.count(), 0)

        # set the tif file to GeoRasterLogicalFile type
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        self.assertEqual(GeoRasterFileMetaData.objects.count(), 1)
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertTrue(isinstance(logical_file, GeoRasterLogicalFile))
        self.assertTrue(logical_file.metadata, GeoRasterFileMetaData)
        self.assertEqual(logical_file.extra_data['vrt_created'], "True")
        # there should not be any file level keywords at this point
        self.assertEqual(logical_file.metadata.keywords, [])
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_from_zip_file_1(self):
        # here we are using a valid raster zip file (contains 1 vrt file and 2 tif files) that exist at
        # the root of the folder hierarchy
        # for setting it to Geo Raster file type which includes metadata extraction
        # a new folder should be created in this case where the extracted files that are part of
        # the aggregation should exist
        # location of the zip file before aggregation: logan_vrt_small.zip
        # location of the tif file after aggregation: logan_vrt_small/small_logan.tif
        # location of the zip file after after aggregation: zip file should not exist

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.raster_zip_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)
        # set the zip file to GeoRasterFile type
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test aggregation
        base_file_name, _ = os.path.splitext(res_file.file_name)
        self._test_aggregation_from_zip_file(aggr_folder_path='')

        self.composite_resource.delete()

    def test_create_aggregation_from_zip_file_2(self):
        # here we are using a valid raster zip file (contains 1 vrt file and 2 tif files) that exist in a folder
        # for setting it to Geo Raster file type which includes metadata extraction
        # no new folder should be created in this case
        # location of the raster file before aggregation: raster-aggr/small_logan.tif
        # location of the raster file after aggregation: raster-aggr/small_logan.tif

        self.create_composite_resource()
        # create a folder to place the zip file before creating an aggregation from the zip file
        new_folder = 'raster_aggr'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        self.add_file_to_resource(file_to_add=self.raster_zip_file, upload_folder=new_folder)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # check that the resource file is not associated with any logical file
        # self.assertEqual(res_file.has_logical_file, False)
        # set the zip file to GeoRasterFile type
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test aggregation
        self._test_aggregation_from_zip_file(aggr_folder_path=new_folder)

        self.composite_resource.delete()

    def test_create_aggregation_from_multiple_tif_with_vrt(self):
        """Here we are testing when there are multiple tif files along with a vrt file at the same
        directory location, using one of the tif files to create an aggregation, should result in a
        new aggregation that contains all the tif files and the vrt file"""

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.logan_tif_1_file)
        self.add_file_to_resource(file_to_add=self.logan_tif_2_file)
        res_file_tif = self.composite_resource.files.first()
        self.add_file_to_resource(file_to_add=self.logan_vrt_file)

        self.assertEqual(self.composite_resource.files.all().count(), 3)

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file_tif.has_logical_file, False)

        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        # set the tif file to GeoRasterFile type
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file_tif.id)

        # test aggregation
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.has_logical_file, True)

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_aggregation_validation(self):
        """Tests when a tif file is listed by more than one vrt file, validation should block the creation of the
          aggregation with appropriate messaging"""

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.logan_tif_1_file)
        self.add_file_to_resource(file_to_add=self.logan_tif_2_file)
        res_file_tif = self.composite_resource.files.first()
        self.add_file_to_resource(file_to_add=self.logan_vrt_file)
        self.add_file_to_resource(file_to_add=self.logan_vrt_file2)

        self.assertEqual(self.composite_resource.files.all().count(), 4)

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file_tif.has_logical_file, False)

        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        # set the tif file to GeoRasterFile type
        with self.assertRaises(ValidationError) as validation_error:
            GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file_tif.id)
        print(validation_error.exception.message)
        self.assertTrue("is listed by more than one vrt file" in validation_error.exception.message)

        # test aggregation does not exist
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_from_multiple_tif_without_vrt(self):
        """Here we are testing when there are multiple tif files and no vrt file at the same
        directory location, using one of the tif files to create an aggregation, should result in a
        new aggregation that contains only the selected tif """

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.logan_tif_1_file)
        res_file_tif = self.composite_resource.files.first()
        self.add_file_to_resource(file_to_add=self.logan_tif_2_file)

        self.assertEqual(self.composite_resource.files.all().count(), 2)

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file_tif.has_logical_file, False)

        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        # set the tif file to GeoRasterFile type
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file_tif.id)

        # test aggregation
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        self.assertEqual(res_file_tif.file_name, self.logan_tif_1_file_name)
        for res_file in self.composite_resource.files.all():
            if res_file_tif.file_name == res_file.file_name or res_file.extension.lower() == '.vrt':
                self.assertEqual(res_file.has_logical_file, True)
            else:
                self.assertEqual(res_file.has_logical_file, False)

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_with_missing_tif_with_vrt(self):
        """Here we are testing when there is a vrt file, selecting a tif file from the same
        location for creating aggregation will fail if all tif files referenced in vrt file does
        not exist at that location """

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.logan_tif_1_file)
        res_file_tif = self.composite_resource.files.first()
        self.add_file_to_resource(file_to_add=self.logan_vrt_file)

        self.assertEqual(self.composite_resource.files.all().count(), 2)

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file_tif.has_logical_file, False)

        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        # set the tif file to GeoRasterFile type should raise exception
        with self.assertRaises(ValidationError):
            GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file_tif.id)

        # test aggregation
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_create_aggregation_with_extra_tif_with_vrt(self):
        """Here we are testing mutliple raster aggregations in the same folder.  Two aggregations
        are added to the composite resource in the same folder """

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.logan_tif_1_file)
        res_file_tif = self.composite_resource.files.first()
        self.add_file_to_resource(file_to_add=self.logan_tif_2_file)
        self.add_file_to_resource(file_to_add=self.logan_vrt_file)
        # add the extra tif file
        lone_tif_file = self.add_file_to_resource(file_to_add=self.raster_file)

        self.assertEqual(self.composite_resource.files.all().count(), 4)

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file_tif.has_logical_file, False)

        # test that raster aggregations may exist in the same folder next to each other
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file_tif.id)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, lone_tif_file.id)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 2)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_set_file_type_to_geo_raster_invalid_file_1(self):
        # here we are using an invalid raster tif file for setting it
        # to Geo Raster file type which should fail

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.invalid_raster_file)
        self._test_invalid_file()

        self.composite_resource.delete()

    def test_set_file_type_to_geo_raster_invalid_file_2(self):
        # here we are using a raster tif file for setting it
        # to Geo Raster file type which already been previously set to this file type - should fail

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.raster_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # set tif file to GeoRasterFileType
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # check that the resource file is associated with a logical file
        res_file = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, '.tif')[0]
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GeoRasterLogicalFile")

        # trying to set this tif file again to geo raster file type should raise
        # ValidationError
        with self.assertRaises(ValidationError):
            GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_set_file_type_to_geo_raster_invalid_file_3(self):
        # here we are using an invalid raster zip file (contains 2 vrt files and 2 tif files) for setting it
        # to Geo Raster file type - should fail

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.invalid_raster_zip_file)

        self._test_invalid_file()
        self.assertTrue(self.composite_resource.files.first().file_name.endswith('.zip'))
        self.composite_resource.delete()

    def test_metadata_CRUD(self):
        # this is test metadata related to GeoRasterLogicalFile

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.raster_file)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # extract metadata by setting to geo raster file type
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        res_file = self.composite_resource.files.first()

        # test that we can update raster specific metadata at the file level

        # test that we can update dataset_name of the logical file object
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.dataset_name, 'small_logan')
        logical_file.dataset_name = "big_logan"
        logical_file.save()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.dataset_name, 'big_logan')

        # delete default original coverage metadata
        self.assertNotEqual(logical_file.metadata.originalCoverage, None)
        logical_file.metadata.originalCoverage.delete()

        # create new original coverage metadata with meaningful value
        value = {"northlimit": 12, "projection": "transverse_mercator", "units": "meter",
                 "southlimit": 10,
                 "eastlimit": 23, "westlimit": 2}
        logical_file.metadata.create_element('originalcoverage', value=value)

        self.assertEqual(logical_file.metadata.originalCoverage.value, value)

        # multiple original coverage elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            logical_file.metadata.create_element('originalcoverage', value=value)

        # delete default cell information element
        self.assertNotEqual(logical_file.metadata.cellInformation, None)
        logical_file.metadata.cellInformation.delete()

        # create new cell information metadata with meaningful value
        logical_file.metadata.create_element('cellinformation', name='cellinfo',
                                             cellDataType='Float32',
                                             rows=1660, columns=985, cellSizeXValue=30.0,
                                             cellSizeYValue=30.0,
                                             )

        cell_info = logical_file.metadata.cellInformation
        self.assertEqual(cell_info.rows, 1660)
        self.assertEqual(cell_info.columns, 985)
        self.assertEqual(cell_info.cellSizeXValue, 30.0)
        self.assertEqual(cell_info.cellSizeYValue, 30.0)
        self.assertEqual(cell_info.cellDataType, 'Float32')
        # multiple cell Information elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            logical_file.metadata.create_element('cellinformation', name='cellinfo',
                                                 cellDataType='Float32',
                                                 rows=1660, columns=985,
                                                 cellSizeXValue=30.0, cellSizeYValue=30.0,
                                                 )
        # delete default band information element
        self.assertNotEqual(logical_file.metadata.bandInformations, None)
        logical_file.metadata.bandInformations.first().delete()

        # create band information element with meaningful value
        logical_file.metadata.create_element('bandinformation', name='bandinfo',
                                             variableName='diginal elevation',
                                             variableUnit='meter',
                                             method='this is method',
                                             comment='this is comment',
                                             maximumValue=1000, minimumValue=0,
                                             noDataValue=-9999)

        band_info = logical_file.metadata.bandInformations.first()
        self.assertEqual(band_info.name, 'bandinfo')
        self.assertEqual(band_info.variableName, 'diginal elevation')
        self.assertEqual(band_info.variableUnit, 'meter')
        self.assertEqual(band_info.method, 'this is method')
        self.assertEqual(band_info.comment, 'this is comment')
        self.assertEqual(band_info.maximumValue, '1000')
        self.assertEqual(band_info.minimumValue, '0')
        self.assertEqual(band_info.noDataValue, '-9999')

        # multiple band information elements are allowed
        logical_file.metadata.create_element('bandinformation', name='bandinfo',
                                             variableName='diginal elevation2',
                                             variableUnit='meter',
                                             method='this is method',
                                             comment='this is comment',
                                             maximumValue=1000, minimumValue=0,
                                             noDataValue=-9999)
        self.assertEqual(logical_file.metadata.bandInformations.all().count(), 2)

        # test metadata delete

        # original coverage deletion is not allowed
        with self.assertRaises(ValidationError):
            logical_file.metadata.delete_element('originalcoverage',
                                                 logical_file.metadata.originalCoverage.id)

        # cell information deletion is not allowed
        with self.assertRaises(ValidationError):
            logical_file.metadata.delete_element('cellinformation',
                                                 logical_file.metadata.cellInformation.id)

        # band information deletion is not allowed
        with self.assertRaises(ValidationError):
            logical_file.metadata.delete_element('bandinformation',
                                                 logical_file.metadata.bandInformations.first().id)

        # test metadata update

        # update original coverage element
        value_2 = {"northlimit": 12.5, "projection": "transverse_mercator", "units": "meter",
                   "southlimit": 10.5,
                   "eastlimit": 23.5, "westlimit": 2.5}
        logical_file.metadata.update_element('originalcoverage',
                                             logical_file.metadata.originalCoverage.id,
                                             value=value_2)

        self.assertEqual(logical_file.metadata.originalCoverage.value, value_2)

        # update cell info element
        logical_file.metadata.update_element('cellinformation',
                                             logical_file.metadata.cellInformation.id,
                                             name='cellinfo', cellDataType='Double',
                                             rows=166, columns=98,
                                             cellSizeXValue=3.0, cellSizeYValue=3.0,
                                             )

        cell_info = logical_file.metadata.cellInformation
        self.assertEqual(cell_info.rows, 166)
        self.assertEqual(cell_info.columns, 98)
        self.assertEqual(cell_info.cellSizeXValue, 3.0)
        self.assertEqual(cell_info.cellSizeYValue, 3.0)
        self.assertEqual(cell_info.cellDataType, 'Double')

        # update band info element
        logical_file.metadata.update_element('bandinformation',
                                             logical_file.metadata.bandInformations.first().id,
                                             name='bandinfo',
                                             variableName='precipitation',
                                             variableUnit='mm/h',
                                             method='this is method2',
                                             comment='this is comment2',
                                             maximumValue=1001, minimumValue=1,
                                             noDataValue=-9998
                                             )

        band_info = logical_file.metadata.bandInformations.first()
        self.assertEqual(band_info.name, 'bandinfo')
        self.assertEqual(band_info.variableName, 'precipitation')
        self.assertEqual(band_info.variableUnit, 'mm/h')
        self.assertEqual(band_info.method, 'this is method2')
        self.assertEqual(band_info.comment, 'this is comment2')
        self.assertEqual(band_info.maximumValue, '1001')
        self.assertEqual(band_info.minimumValue, '1')
        self.assertEqual(band_info.noDataValue, '-9998')

        # test extra_metadata for the logical file
        # there should be no key/value metadata at this point
        self.assertEqual(logical_file.metadata.extra_metadata, {})

        # create key/vale metadata
        logical_file.metadata.extra_metadata = {'key1': 'value 1', 'key2': 'value 2'}
        logical_file.metadata.save()
        self.assertEqual(logical_file.metadata.extra_metadata,
                         {'key1': 'value 1', 'key2': 'value 2'})

        # update key/value metadata
        logical_file.metadata.extra_metadata = {'key1': 'value 1', 'key2': 'value 2',
                                                'key 3': 'value3'}
        logical_file.metadata.save()
        self.assertEqual(logical_file.metadata.extra_metadata,
                         {'key1': 'value 1', 'key2': 'value 2', 'key 3': 'value3'})

        # delete key/value metadata
        logical_file.metadata.extra_metadata = {}
        logical_file.metadata.save()
        self.assertEqual(logical_file.metadata.extra_metadata, {})
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_file_metadata_on_file_delete(self):
        # test that when any file in GeoRasterLogicalFile type is deleted
        # all metadata associated with GeoRasterFileMetaData is deleted
        # test for both .tif and .vrt delete

        # test with deleting of 'tif' file
        self._test_file_metadata_on_file_delete(ext='.tif')
        self.composite_resource.delete()

        # test with deleting of 'vrt' file
        self._test_file_metadata_on_file_delete(ext='.vrt')
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_file_metadata_on_logical_file_delete(self):
        # test that when the GeoRasterFileType is deleted
        # all metadata associated with GeoRasterFileType is deleted

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.raster_file)
        res_file = self.composite_resource.files.first()

        # create raster aggregation using the tif file
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test that we have one logical file of type GeoRasterLogicalFileType as a result
        # of metadata extraction
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        self.assertEqual(GeoRasterFileMetaData.objects.count(), 1)

        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # test that we have the metadata elements
        # there should be 2 Coverage objects - one at the resource level and
        # the other one at the file type level
        self.assertEqual(Coverage.objects.count(), 2)
        self.assertEqual(self.composite_resource.metadata.coverages.all().count(), 1)
        self.assertEqual(logical_file.metadata.coverages.all().count(), 1)
        self.assertEqual(OriginalCoverageRaster.objects.count(), 1)
        self.assertEqual(CellInformation.objects.count(), 1)
        self.assertEqual(BandInformation.objects.count(), 1)

        # delete the logical file
        logical_file.logical_delete(self.user)
        # test that we have no logical file of type GeoRasterFileType
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        self.assertEqual(GeoRasterFileMetaData.objects.count(), 0)

        # test that all metadata deleted - with resource coverage should still exist
        self.assertEqual(Coverage.objects.count(), 1)
        self.assertEqual(OriginalCoverageRaster.objects.count(), 0)
        self.assertEqual(CellInformation.objects.count(), 0)
        self.assertEqual(BandInformation.objects.count(), 0)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_file_metadata_on_resource_delete(self):
        # test that when the composite resource is deleted
        # all metadata associated with GeoRasterFileType is deleted

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.raster_file)
        res_file = self.composite_resource.files.first()

        # create raster aggregation using the tif file
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test that we have one logical file of type GeoRasterFileType as a result
        # of metadata extraction
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        self.assertEqual(GeoRasterFileMetaData.objects.count(), 1)

        # test that we have the metadata elements
        # there should be 2 Coverage objects - one at the resource level and
        # the other one at the file type level
        self.assertEqual(Coverage.objects.count(), 2)
        self.assertEqual(OriginalCoverageRaster.objects.count(), 1)
        self.assertEqual(CellInformation.objects.count(), 1)
        self.assertEqual(BandInformation.objects.count(), 1)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())

        # delete resource
        hydroshare.delete_resource(self.composite_resource.short_id)

        # test that we have no logical file of type GeoRasterFileType
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        self.assertEqual(GeoRasterFileMetaData.objects.count(), 0)

        # test that all metadata deleted
        self.assertEqual(Coverage.objects.count(), 0)
        self.assertEqual(OriginalCoverageRaster.objects.count(), 0)
        self.assertEqual(CellInformation.objects.count(), 0)
        self.assertEqual(BandInformation.objects.count(), 0)

    def test_logical_file_delete(self):
        # test that when an instance GeoRasterFileType is deleted
        # all files associated with GeoRasterFileType is deleted

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.raster_file)
        res_file = self.composite_resource.files.first()

        # extract metadata from the tif file
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test that we have one logical file of type GeoRasterFileType as a result
        # of metadata extraction
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        logical_file = GeoRasterLogicalFile.objects.first()
        self.assertEqual(logical_file.files.all().count(), 2)
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        self.assertEqual(set(self.composite_resource.files.all()),
                         set(logical_file.files.all()))

        # delete the logical file using the custom delete function - logical_delete()
        logical_file.logical_delete(self.user)
        self.assertEqual(self.composite_resource.files.all().count(), 0)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_remove_aggregation_with_single_tif(self):
        # test that when an instance GeoRasterLogicalFile (aggregation) is deleted
        # all files associated with that aggregation is not deleted
        # (except the vt file if it was generated by the system) but the associated metadata is deleted

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.raster_file)
        res_tif_file = self.composite_resource.files.first()

        # set the tif file to GeoRasterLogicalFile (aggregation)
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_tif_file.id)

        # test that we have one logical file of type GeoRasterFileType
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        self.assertEqual(GeoRasterFileMetaData.objects.count(), 1)
        logical_file = GeoRasterLogicalFile.objects.first()
        self.assertEqual(logical_file.files.all().count(), 2)
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        self.assertEqual(set(self.composite_resource.files.all()),
                         set(logical_file.files.all()))

        # delete the aggregation (logical file) object using the remove_aggregation function
        self.assertEqual(logical_file.extra_data['vrt_created'], "True")
        logical_file.remove_aggregation()
        # test there is no GeoRasterLogicalFile object
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        # test there is no GeoRasterFileMetaData object
        self.assertEqual(GeoRasterFileMetaData.objects.count(), 0)
        # check the tif file is not deleted but the system generated vrt file is deleted
        self.assertEqual(self.composite_resource.files.count(), 1)
        self.assertFalse(self.composite_resource.files.first().file_name.endswith('.vrt'))
        self.assertEqual(self.composite_resource.files.first().file_name, res_tif_file.file_name)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_remove_aggregation_with_multiple_tif(self):
        """
        Test that when an instance of GeoRasterLogicalFile (aggregation) that was created with multiple tif files
        is deleted, none of the files (including the vrt) associated with that aggregation is deleted.
        But the associated metadata is deleted.
        """

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.logan_tif_1_file)
        res_file_tif = self.composite_resource.files.first()
        self.add_file_to_resource(file_to_add=self.logan_tif_2_file)
        self.add_file_to_resource(file_to_add=self.logan_vrt_file)

        # resource should have 3 files
        self.assertEqual(self.composite_resource.files.all().count(), 3)

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file_tif.has_logical_file, False)

        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        # set the tif file to GeoRasterLogicalFile type
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file_tif.id)

        # test aggregation
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        self.assertEqual(self.composite_resource.files.all().count(), 3)
        logical_file = GeoRasterLogicalFile.objects.first()
        # aggregation should have 3 files
        self.assertEqual(logical_file.files.all().count(), 3)
        # each of the resource files is part of the aggregation
        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.has_logical_file, True)

        # delete the aggregation (logical file) object using the remove_aggregation function
        self.assertEqual(logical_file.extra_data['vrt_created'], "False")
        logical_file.remove_aggregation()
        # test there is no GeoRasterLogicalFile object
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        # test there is no GeoRasterFileMetaData object
        self.assertEqual(GeoRasterFileMetaData.objects.count(), 0)
        # check that no file is deleted
        self.assertEqual(self.composite_resource.files.count(), 3)
        tif_file_count = 0
        vrt_file_count = 0
        for res_file in self.composite_resource.files.all():
            if res_file.extension.lower() == '.tif':
                tif_file_count += 1
            elif res_file.extension.lower() == '.vrt':
                vrt_file_count += 1
        self.assertEqual(tif_file_count, 2)
        self.assertEqual(vrt_file_count, 1)

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_content_file_delete(self):
        # test that when any file that is part of an instance GeoRasterFileType is deleted
        # all files associated with GeoRasterFileType is deleted

        # test deleting of tif file
        self._content_file_delete('.tif')

        # test deleting of vrt file
        self._content_file_delete('.vrt')

        self.composite_resource.delete()

    def test_aggregation_file_rename(self):
        # test that a file can't renamed for any resource file
        # that's part of the GeoRaster logical file

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.raster_file)
        res_file = self.composite_resource.files.first()

        # create aggregation from the tif file
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # test renaming of files that are associated with aggregation raises exception
        self.assertEqual(self.composite_resource.files.count(), 2)

        for res_file in self.composite_resource.files.all():
            base_file_name, ext = os.path.splitext(res_file.file_name)
            src_path = 'data/contents/{}'.format(res_file.file_name)
            new_file_name = 'some_raster{}'.format(ext)
            self.assertNotEqual(res_file.file_name, new_file_name)
            tgt_path = 'data/contents/{}'.format(new_file_name)
            with self.assertRaises(DRF_ValidationError):
                move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                              tgt_path)

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_aggregation_file_move(self):
        # test any resource file that's part of the GeoRaster logical file can't be moved

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.raster_file)
        res_file = self.composite_resource.files.first()

        # create the aggregation using the tif file
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # test renaming of files that are associated with raster LFO - which should raise exception
        self.assertEqual(self.composite_resource.files.count(), 2)

        new_folder = 'georaster_aggr'
        ResourceFile.create_folder(self.composite_resource, new_folder)

        # moving any of the resource files to this new folder should raise exception
        tgt_path = 'data/contents/{}'.format(new_folder)
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
        folder_for_raster = 'raster_folder'
        ResourceFile.create_folder(self.composite_resource, folder_for_raster)
        self.add_file_to_resource(file_to_add=self.raster_file, upload_folder=folder_for_raster)
        res_file = self.composite_resource.files.first()

        # create aggregation from the tif file
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        self.assertEqual(self.composite_resource.files.count(), 2)

        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, folder_for_raster)

        # test aggregation name
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        aggregation_name = logical_file.aggregation_name
        # test aggregation xml file paths
        vrt_file_path = get_path_with_no_file_extension(aggregation_name)
        expected_meta_file_path = '{0}{1}'.format(vrt_file_path, AggregationMetaFilePath.METADATA_FILE_ENDSWITH.value)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_file_path)

        expected_map_file_path = '{0}{1}'.format(vrt_file_path, AggregationMetaFilePath.RESMAP_FILE_ENDSWITH.value)
        self.assertEqual(logical_file.map_short_file_path, expected_map_file_path)

        # test renaming folder
        src_path = 'data/contents/{}'.format(folder_for_raster)
        tgt_path = 'data/contents/{}_1'.format(folder_for_raster)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, '{}_1'.format(folder_for_raster))

        # test aggregation name update
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertNotEqual(logical_file.aggregation_name, aggregation_name)
        aggregation_name = logical_file.aggregation_name

        # test aggregation xml file paths
        vrt_file_path = get_path_with_no_file_extension(aggregation_name)
        expected_meta_file_path = '{0}{1}'.format(vrt_file_path, AggregationMetaFilePath.METADATA_FILE_ENDSWITH.value)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_file_path)

        expected_map_file_path = '{0}{1}'.format(vrt_file_path, AggregationMetaFilePath.RESMAP_FILE_ENDSWITH.value)
        self.assertEqual(logical_file.map_short_file_path, expected_map_file_path)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_aggregation_parent_folder_rename(self):
        # test changes to aggregation name, aggregation metadata xml file path, and aggregation
        # resource map xml file path on aggregation folder parent folder name change

        self.create_composite_resource()
        folder_for_raster = 'raster_folder'
        ResourceFile.create_folder(self.composite_resource, folder_for_raster)
        self.add_file_to_resource(file_to_add=self.raster_file, upload_folder=folder_for_raster)
        res_file = self.composite_resource.files.first()
        base_file_name, ext = os.path.splitext(res_file.file_name)

        # create aggregation from the tif file
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # test renaming of files that are associated with aggregation raises exception
        self.assertEqual(self.composite_resource.files.count(), 2)

        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, folder_for_raster)

        # test aggregation name
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        aggregation_name = logical_file.aggregation_name
        # test aggregation xml file paths
        # test aggregation xml file paths
        vrt_file_path = get_path_with_no_file_extension(aggregation_name)
        expected_meta_file_path = '{0}{1}'.format(vrt_file_path, AggregationMetaFilePath.METADATA_FILE_ENDSWITH.value)
        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_file_path)

        expected_map_file_path = '{0}{1}'.format(vrt_file_path, AggregationMetaFilePath.RESMAP_FILE_ENDSWITH.value)
        self.assertEqual(logical_file.map_short_file_path, expected_map_file_path)

        # create a folder to be the parent folder of the aggregation folder
        parent_folder = 'parent_folder'
        ResourceFile.create_folder(self.composite_resource, parent_folder)
        # move the aggregation folder to the parent folder
        src_path = 'data/contents/{}'.format(folder_for_raster)
        tgt_path = 'data/contents/{0}/{1}'.format(parent_folder, folder_for_raster)

        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        file_folder = '{}/{}'.format(parent_folder, folder_for_raster)
        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, file_folder)

        # renaming parent folder
        parent_folder_rename = 'parent_folder_1'
        src_path = 'data/contents/{}'.format(parent_folder)
        tgt_path = 'data/contents/{}'.format(parent_folder_rename)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        file_folder = '{}/{}'.format(parent_folder_rename, folder_for_raster)
        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, file_folder)

        # test aggregation name after folder rename
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertNotEqual(logical_file.aggregation_name, aggregation_name)
        aggregation_name = logical_file.aggregation_name
        # test aggregation xml file paths after folder rename
        vrt_file_path = get_path_with_no_file_extension(aggregation_name)
        expected_meta_file_path = '{0}{1}'.format(vrt_file_path, AggregationMetaFilePath.METADATA_FILE_ENDSWITH.value)

        self.assertEqual(logical_file.metadata_short_file_path, expected_meta_file_path)
        expected_map_file_path = '{0}{1}'.format(vrt_file_path, AggregationMetaFilePath.RESMAP_FILE_ENDSWITH.value)

        self.assertEqual(logical_file.map_short_file_path, expected_map_file_path)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def test_aggregation_folder_move(self):
        # test changes to aggregation name, aggregation metadata xml file path, and aggregation
        # resource map xml file path on aggregation folder move

        self.create_composite_resource()
        folder_for_raster = 'raster_folder'
        ResourceFile.create_folder(self.composite_resource, folder_for_raster)
        self.add_file_to_resource(file_to_add=self.raster_file, upload_folder=folder_for_raster)
        res_file = self.composite_resource.files.first()

        # create aggregation from the tif file
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        self.assertEqual(self.composite_resource.files.count(), 2)

        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, folder_for_raster)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        aggregation_name = logical_file.aggregation_name
        metadata_short_file_path = logical_file.metadata_short_file_path
        map_short_file_path = logical_file.map_short_file_path
        # create a folder to move the aggregation folder there
        parent_folder = 'parent_folder'
        ResourceFile.create_folder(self.composite_resource, parent_folder)
        # move the aggregation folder to the parent folder
        src_path = 'data/contents/{}'.format(folder_for_raster)
        tgt_path = 'data/contents/{0}/{1}'.format(parent_folder, folder_for_raster)

        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id, src_path,
                                      tgt_path)

        file_folder = '{0}/{1}'.format(parent_folder, folder_for_raster)
        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.file_folder, file_folder)

        # test aggregation name update
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertNotEqual(logical_file.aggregation_name, aggregation_name)

        # test aggregation xml file paths
        self.assertNotEqual(logical_file.metadata_short_file_path, metadata_short_file_path)
        self.assertNotEqual(logical_file.map_short_file_path, map_short_file_path)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
        self.composite_resource.delete()

    def _test_file_metadata_on_file_delete(self, ext):

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.raster_file)
        res_file = self.composite_resource.files.first()
        self.assertEqual(Coverage.objects.count(), 0)
        # extract metadata from the tif file
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        self.assertEqual(Coverage.objects.count(), 2)
        # test that we have one logical file of type GeoRasterLogicalFile Type
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        self.assertEqual(GeoRasterFileMetaData.objects.count(), 1)

        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # there should be 1 coverage element of type spatial for the raster aggregation
        self.assertEqual(logical_file.metadata.coverages.all().count(), 1)
        self.assertEqual(logical_file.metadata.temporal_coverage, None)
        self.assertNotEqual(logical_file.metadata.spatial_coverage, None)
        self.assertNotEqual(logical_file.metadata.originalCoverage, None)
        self.assertNotEqual(logical_file.metadata.cellInformation, None)
        self.assertNotEqual(logical_file.metadata.bandInformations, None)

        # there should be 1 coverage for the resource
        self.assertEqual(self.composite_resource.metadata.coverages.all().count(), 1)
        # there should be 2 coverage objects - one at the resource level
        # and the other one at the file type level
        self.assertEqual(Coverage.objects.count(), 2)
        self.assertEqual(OriginalCoverageRaster.objects.count(), 1)
        self.assertEqual(CellInformation.objects.count(), 1)
        self.assertEqual(BandInformation.objects.count(), 1)

        # delete content file specified by extension (ext parameter)
        res_file_tif = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, ext)[0]
        hydroshare.delete_resource_file(self.composite_resource.short_id,
                                        res_file_tif.id,
                                        self.user)
        # test that we don't have logical file of type GeoRasterFileType
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        self.assertEqual(GeoRasterFileMetaData.objects.count(), 0)

        # test that all metadata deleted - with one coverage element at the resource level should
        # still exist
        self.assertEqual(Coverage.objects.count(), 1)
        self.assertEqual(OriginalCoverageRaster.objects.count(), 0)
        self.assertEqual(CellInformation.objects.count(), 0)
        self.assertEqual(BandInformation.objects.count(), 0)

    def _content_file_delete(self, ext):
        # test that when any file that is part of an instance GeoRasterFileType is deleted
        # all files associated with GeoRasterFileType is deleted

        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.raster_file)
        res_file = self.composite_resource.files.first()

        # extract metadata from the tif file
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)

        # delete the content file specified by the ext (file extension param)
        res_file_tif = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, ext)[0]
        hydroshare.delete_resource_file(self.composite_resource.short_id,
                                        res_file_tif.id,
                                        self.user)

        self.assertEqual(self.composite_resource.files.all().count(), 0)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())

    def _test_invalid_file(self):
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # trying to set this invalid tif file to geo raster file type should raise
        # ValidationError
        with self.assertRaises(ValidationError):
            GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test that no raster aggregation exists
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        # test that the invalid file did not get deleted
        self.assertEqual(self.composite_resource.files.all().count(), 1)

        # check that the resource file is not associated with logical file
        self.assertEqual(res_file.has_logical_file, False)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())

    def _test_aggregation_from_zip_file(self, aggr_folder_path):
        # test the resource now has 4 files (one vrt file and 2 tif files) and the original zip file
        self.assertEqual(self.composite_resource.files.all().count(), 4)
        tif_files = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, '.tif')
        self.assertEqual(len(tif_files), 2)
        vrt_files = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, '.vrt')
        self.assertEqual(len(vrt_files), 1)

        # check that the logicalfile is associated with 3 files
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        logical_file = GeoRasterLogicalFile.objects.first()
        self.assertEqual(logical_file.extra_data['vrt_created'], "False")
        res_file = self.composite_resource.files.first()
        expected_dataset_name, _ = os.path.splitext(res_file.file_name)

        self.assertEqual(logical_file.dataset_name, expected_dataset_name)
        self.assertEqual(logical_file.has_metadata, True)
        self.assertEqual(logical_file.files.all().count(), 3)
        self.assertEqual((self.composite_resource.files.count() - logical_file.files.count()), 1)

        # check that files in a folder
        if aggr_folder_path:
            for res_file in self.composite_resource.files.all():
                self.assertEqual(res_file.file_folder, aggr_folder_path)

        # check that there is no GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

        # test that size property of the logical file is equal to sun of size of all files
        # that are part of the logical file
        self.assertEqual(logical_file.size, sum([f.size for f in logical_file.files.all()]))

        # test extracted metadata for the file type
        # geo raster file type should have all the metadata elements
        self.assertEqual(logical_file.metadata.has_all_required_elements(), True)

        # there should be 1 coverage element - box type
        self.assertNotEqual(logical_file.metadata.spatial_coverage, None)
        self.assertEqual(logical_file.metadata.spatial_coverage.type, 'box')

        box_coverage = logical_file.metadata.spatial_coverage
        self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertAlmostEqual(box_coverage.value['northlimit'], 42.0500287857716, places=14)
        self.assertAlmostEqual(box_coverage.value['eastlimit'], -111.57737502643897, places=14)
        self.assertAlmostEqual(box_coverage.value['southlimit'], 41.98745777903126, places=14)
        self.assertAlmostEqual(box_coverage.value['westlimit'], -111.65768822411246, places=14)

        # testing additional metadata element: original coverage
        ori_coverage = logical_file.metadata.originalCoverage
        self.assertNotEqual(ori_coverage, None)
        self.assertEqual(ori_coverage.value['northlimit'], 4655492.446916306)
        self.assertEqual(ori_coverage.value['eastlimit'], 452174.01909127034)
        self.assertEqual(ori_coverage.value['southlimit'], 4648592.446916306)
        self.assertEqual(ori_coverage.value['westlimit'], 445574.01909127034)
        self.assertEqual(ori_coverage.value['units'], 'meter')
        self.assertEqual(ori_coverage.value['projection'],
                         'NAD83 / UTM zone 12N')

        # testing additional metadata element: cell information
        cell_info = logical_file.metadata.cellInformation
        self.assertEqual(cell_info.rows, 230)
        self.assertEqual(cell_info.columns, 220)
        self.assertEqual(cell_info.cellSizeXValue, 30.0)
        self.assertEqual(cell_info.cellSizeYValue, 30.0)
        self.assertEqual(cell_info.cellDataType, 'Float32')

        # testing additional metadata element: band information
        self.assertEqual(logical_file.metadata.bandInformations.count(), 1)
        band_info = logical_file.metadata.bandInformations.first()
        self.assertEqual(band_info.noDataValue, '-3.4028234663852886e+38')
        self.assertEqual(band_info.maximumValue, '2880.007080078125')
        self.assertEqual(band_info.minimumValue, '2274.958984375')

        self.assertFalse(self.composite_resource.dangling_aggregations_exist())

    def test_main_file(self):
        self.create_composite_resource()
        self.add_file_to_resource(file_to_add=self.raster_file)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        self.assertEqual(1, GeoRasterLogicalFile.objects.count())
        logical_file = GeoRasterLogicalFile.objects.first()
        self.assertEqual(logical_file.extra_data['vrt_created'], "True")
        self.assertEqual(".vrt", GeoRasterLogicalFile.objects.first().get_main_file_type())
        self.assertEqual("small_logan.vrt",
                         GeoRasterLogicalFile.objects.first().get_main_file.file_name)
        self.assertFalse(self.composite_resource.dangling_aggregations_exist())
