# coding=utf-8
import os
import tempfile
import shutil

from django.test import TransactionTestCase
from django.db import IntegrityError
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.models import Coverage

from hs_file_types.utils import set_file_to_geo_raster_file_type
from hs_file_types.models import GeoRasterLogicalFile

from hs_geo_raster_resource.models import OriginalCoverage, CellInformation, BandInformation


class RasterFileTypeMetaData(MockIRODSTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(RasterFileTypeMetaData, self).setUp()
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
            title='Test Raster File Metadata'
        )

        self.temp_dir = tempfile.mkdtemp()
        self.raster_file_name = 'small_logan.tif'
        self.invalid_raster_file_name = 'raster_tif_invalid.tif'
        self.raster_file = 'hs_file_types/tests/{}'.format(self.raster_file_name)
        self.invalid_raster_file = 'hs_file_types/tests/{}'.format(self.invalid_raster_file_name)
        target_temp_raster_file = os.path.join(self.temp_dir, self.raster_file_name)
        shutil.copy(self.raster_file, target_temp_raster_file)
        self.raster_file_obj = open(target_temp_raster_file, 'r')

        target_temp_raster_file = os.path.join(self.temp_dir, self.invalid_raster_file_name)
        shutil.copy(self.invalid_raster_file, target_temp_raster_file)
        self.invalid_raster_file_obj = open(target_temp_raster_file, 'r')

    def tearDown(self):
        super(RasterFileTypeMetaData, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_tif_set_file_type_to_geo_raster(self):
        # here we are using a valid raster tif file for setting it
        # to Geo Raster file type which includes metadata extraction
        self.raster_file_obj = open(self.raster_file, 'r')
        self._create_composite_resource()

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)
        set_file_to_geo_raster_file_type(self.composite_resource, res_file.id, self.user)

        # test the resource now has 2 files (vrt file added as part of metadata extraction)
        self.assertEqual(self.composite_resource.files.all().count(), 2)

        # check that the 2 resource files are now associated with GeoRasterLogicalFile
        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.logical_file_type_name, "GeoRasterLogicalFile")
            self.assertEqual(res_file.has_logical_file, True)
            self.assertTrue(isinstance(res_file.logical_file, GeoRasterLogicalFile))

        # check that the logicalfile is associated with 2 files
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.dataset_name, 'small_logan')
        self.assertEqual(logical_file.has_metadata, True)
        self.assertEqual(logical_file.files.all().count(), 2)
        self.assertEqual(set(self.composite_resource.files.all()),
                         set(logical_file.files.all()))

        # there should be 2 format elements associated with resource
        self.assertEqual(self.composite_resource.metadata.formats.all().count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.formats.all().filter(value='application/vrt').count(),
            1)
        self.assertEqual(self.composite_resource.metadata.formats.all().filter(
            value='image/tiff').count(), 1)

        # test extracted metadata for the file type

        # there should be 1 coverage element - box type
        self.assertEqual(logical_file.metadata.coverages.all().count(), 1)
        self.assertEqual(logical_file.metadata.coverages.all().filter(type='box').count(), 1)

        box_coverage = logical_file.metadata.coverages.all().filter(type='box').first()
        self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(box_coverage.value['northlimit'], 42.049364058252266)
        self.assertEqual(box_coverage.value['eastlimit'], -111.57773718106195)
        self.assertEqual(box_coverage.value['southlimit'], 41.987884327209976)
        self.assertEqual(box_coverage.value['westlimit'], -111.69756293084055)

        # testing extended metadata element: original coverage
        ori_coverage = logical_file.metadata.originalCoverage
        self.assertNotEqual(ori_coverage, None)
        self.assertEqual(ori_coverage.value['northlimit'], 4655492.446916306)
        self.assertEqual(ori_coverage.value['eastlimit'], 452144.01909127034)
        self.assertEqual(ori_coverage.value['southlimit'], 4648592.446916306)
        self.assertEqual(ori_coverage.value['westlimit'], 442274.01909127034)
        self.assertEqual(ori_coverage.value['units'], 'meter')
        self.assertEqual(ori_coverage.value['projection'],
                         'NAD83 / UTM zone 12N Transverse_Mercator')

        # testing extended metadata element: cell information
        cell_info = logical_file.metadata.cellInformation
        self.assertEqual(cell_info.rows, 230)
        self.assertEqual(cell_info.columns, 329)
        self.assertEqual(cell_info.cellSizeXValue, 30.0)
        self.assertEqual(cell_info.cellSizeYValue, 30.0)
        self.assertEqual(cell_info.cellDataType, 'Float32')

        # testing extended metadata element: band information
        self.assertEqual(logical_file.metadata.bandInformation.count(), 1)
        band_info = logical_file.metadata.bandInformation.first()
        self.assertEqual(band_info.noDataValue, '-3.40282346639e+38')
        self.assertEqual(band_info.maximumValue, '2880.00708008')
        self.assertEqual(band_info.minimumValue, '1870.63659668')

    def test_zip_set_file_type_to_geo_raster(self):
        # here we are using a valid raster zip file for setting it
        # to Geo Raster file type which includes metadata extraction
        # TODO: implement this after I have a small zip file
        pass

    def test_set_file_type_to_geo_raster_invalid_file_1(self):
        # here we are using an invalid raster tif file for setting it
        # to Geo Raster file type which should fail
        self.raster_file_obj = open(self.invalid_raster_file, 'r')
        self._create_composite_resource()

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # trying to set this invalid tif file to geo raster file type should raise
        # ValidationError
        with self.assertRaises(ValidationError):
            set_file_to_geo_raster_file_type(self.composite_resource, res_file.id, self.user)

        # test that the invalid file did not get deleted
        self.assertEqual(self.composite_resource.files.all().count(), 1)

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

    def test_set_file_type_to_geo_raster_invalid_file_2(self):
        # here we are using a raster tif file for setting it
        # to Geo Raster file type which already been previously set to this file type - should fail
        self.raster_file_obj = open(self.raster_file, 'r')
        self._create_composite_resource()

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # set tif file to GeoRasterFileType
        set_file_to_geo_raster_file_type(self.composite_resource, res_file.id, self.user)

        # check that the resource file is associated with a logical file
        res_file = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, '.tif')[0]
        self.assertEqual(res_file.has_logical_file, True)

        # trying to set this tif file again to geo raster file type should raise
        # ValidationError
        with self.assertRaises(ValidationError):
            set_file_to_geo_raster_file_type(self.composite_resource, res_file.id, self.user)

    def test_metadata_CRUD(self):
        self.raster_file_obj = open(self.raster_file, 'r')
        self._create_composite_resource()

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # extract metadata by setting to geo raster file type
        set_file_to_geo_raster_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()

        # test that we can update raster specific metadata at the file level

        # delete default original coverage metadata
        logical_file = res_file.logical_file
        self.assertNotEquals(logical_file.metadata.originalCoverage, None)
        logical_file.metadata.originalCoverage.delete()

        # create new original coverage metadata with meaningful value
        value = {"northlimit": 12, "projection": "transverse_mercator", "units": "meter",
                 "southlimit": 10,
                 "eastlimit": 23, "westlimit": 2}
        logical_file.metadata.create_element('originalcoverage', value=value)

        self.assertEquals(logical_file.metadata.originalCoverage.value, value)

        # multiple original coverage elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            logical_file.metadata.create_element('originalcoverage', value=value)

        # delete default cell information element
        self.assertNotEquals(logical_file.metadata.cellInformation, None)
        logical_file.metadata.cellInformation.delete()

        # create new cell information metadata with meaningful value
        logical_file.metadata.create_element('cellinformation', name='cellinfo',
                                             cellDataType='Float32',
                                             rows=1660, columns=985, cellSizeXValue=30.0,
                                             cellSizeYValue=30.0,
                                             )

        cell_info = logical_file.metadata.cellInformation
        self.assertEquals(cell_info.rows, 1660)
        self.assertEquals(cell_info.columns, 985)
        self.assertEquals(cell_info.cellSizeXValue, 30.0)
        self.assertEquals(cell_info.cellSizeYValue, 30.0)
        self.assertEquals(cell_info.cellDataType, 'Float32')
        # multiple cell Information elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            logical_file.metadata.create_element('cellinformation', name='cellinfo',
                                                 cellDataType='Float32',
                                                 rows=1660, columns=985,
                                                 cellSizeXValue=30.0, cellSizeYValue=30.0,
                                                 )
        # delete default band information element
        self.assertNotEquals(logical_file.metadata.bandInformation, None)
        logical_file.metadata.bandInformation.first().delete()

        # create band information element with meaningful value
        logical_file.metadata.create_element('bandinformation', name='bandinfo',
                                             variableName='diginal elevation',
                                             variableUnit='meter',
                                             method='this is method',
                                             comment='this is comment',
                                             maximumValue=1000, minimumValue=0,
                                             noDataValue=-9999)

        band_info = logical_file.metadata.bandInformation.first()
        self.assertEquals(band_info.name, 'bandinfo')
        self.assertEquals(band_info.variableName, 'diginal elevation')
        self.assertEquals(band_info.variableUnit, 'meter')
        self.assertEquals(band_info.method, 'this is method')
        self.assertEquals(band_info.comment, 'this is comment')
        self.assertEquals(band_info.maximumValue, '1000')
        self.assertEquals(band_info.minimumValue, '0')
        self.assertEquals(band_info.noDataValue, '-9999')

        # multiple band information elements are allowed
        logical_file.metadata.create_element('bandinformation', name='bandinfo',
                                             variableName='diginal elevation2',
                                             variableUnit='meter',
                                             method='this is method',
                                             comment='this is comment',
                                             maximumValue=1000, minimumValue=0,
                                             noDataValue=-9999)
        self.assertEquals(logical_file.metadata.bandInformation.all().count(), 2)

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
                                                logical_file.metadata.bandInformation.first().id)

        # test metadata update

        # update original coverage element
        value_2 = {"northlimit": 12.5, "projection": "transverse_mercator", "units": "meter",
                   "southlimit": 10.5,
                   "eastlimit": 23.5, "westlimit": 2.5}
        logical_file.metadata.update_element('originalcoverage',
                                             logical_file.metadata.originalCoverage.id,
                                             value=value_2)

        self.assertEquals(logical_file.metadata.originalCoverage.value, value_2)

        # update cell info element
        logical_file.metadata.update_element('cellinformation',
                                             logical_file.metadata.cellInformation.id,
                                             name='cellinfo', cellDataType='Double',
                                             rows=166, columns=98,
                                             cellSizeXValue=3.0, cellSizeYValue=3.0,
                                            )

        cell_info = logical_file.metadata.cellInformation
        self.assertEquals(cell_info.rows, 166)
        self.assertEquals(cell_info.columns, 98)
        self.assertEquals(cell_info.cellSizeXValue, 3.0)
        self.assertEquals(cell_info.cellSizeYValue, 3.0)
        self.assertEquals(cell_info.cellDataType, 'Double')

        # update band info element
        logical_file.metadata.update_element('bandinformation',
                                             logical_file.metadata.bandInformation.first().id,
                                             name='bandinfo',
                                             variableName='precipitation',
                                             variableUnit='mm/h',
                                             method='this is method2',
                                             comment='this is comment2',
                                             maximumValue=1001, minimumValue=1,
                                             noDataValue=-9998
                                             )

        band_info = logical_file.metadata.bandInformation.first()
        self.assertEquals(band_info.name, 'bandinfo')
        self.assertEquals(band_info.variableName, 'precipitation')
        self.assertEquals(band_info.variableUnit, 'mm/h')
        self.assertEquals(band_info.method, 'this is method2')
        self.assertEquals(band_info.comment, 'this is comment2')
        self.assertEquals(band_info.maximumValue, '1001')
        self.assertEquals(band_info.minimumValue, '1')
        self.assertEquals(band_info.noDataValue, '-9998')

    def test_file_metadata_on_file_delete(self):
        # test that when any file in GeorasterFileType is deleted
        # all metadata associated with GeoRasterFileType is deleted
        # test for both .tif and .vrt delete

        # test with deleting of 'tif' file
        self._test_file_metadata_on_file_delete(ext='.tif')

        # test with deleting of 'vrt' file
        self._test_file_metadata_on_file_delete(ext='.vrt')

    def test_file_metadata_on_logical_file_delete(self):
        # test that when the GeorasterFileType is deleted
        # all metadata associated with GeoRasterFileType is deleted
        self.raster_file_obj = open(self.raster_file, 'r')
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()

        # extract metadata from the tif file
        set_file_to_geo_raster_file_type(self.composite_resource, res_file.id, self.user)

        # test that we have one logical file of type GeoRasterFileType as a result
        # of metadata extraction
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)

        # test that we have the metadata elements
        self.assertEqual(Coverage.objects.count(), 1)
        self.assertEqual(OriginalCoverage.objects.count(), 1)
        self.assertEqual(CellInformation.objects.count(), 1)
        self.assertEqual(BandInformation.objects.count(), 1)

        # delete the logical file
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        logical_file.logical_delete(self.user)
        # test that we have no logical file of type GeoRasterFileType
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)

        # test that all metadata deleted
        self.assertEqual(Coverage.objects.count(), 0)
        self.assertEqual(OriginalCoverage.objects.count(), 0)
        self.assertEqual(CellInformation.objects.count(), 0)
        self.assertEqual(BandInformation.objects.count(), 0)

    def test_file_metadata_on_resource_delete(self):
        # test that when the composite resource is deleted
        # all metadata associated with GeoRasterFileType is deleted
        self.raster_file_obj = open(self.raster_file, 'r')
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()

        # extract metadata from the tif file
        set_file_to_geo_raster_file_type(self.composite_resource, res_file.id, self.user)

        # test that we have one logical file of type GeoRasterFileType as a result
        # of metadata extraction
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)

        # test that we have the metadata elements
        self.assertEqual(Coverage.objects.count(), 1)
        self.assertEqual(OriginalCoverage.objects.count(), 1)
        self.assertEqual(CellInformation.objects.count(), 1)
        self.assertEqual(BandInformation.objects.count(), 1)

        # delete resource
        hydroshare.delete_resource(self.composite_resource.short_id)

        # test that we have no logical file of type GeoRasterFileType
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)

        # test that all metadata deleted
        self.assertEqual(Coverage.objects.count(), 0)
        self.assertEqual(OriginalCoverage.objects.count(), 0)
        self.assertEqual(CellInformation.objects.count(), 0)
        self.assertEqual(BandInformation.objects.count(), 0)

    def test_logical_file_delete(self):
        # test that when an instance GeoRasterFileType is deleted
        # all files associated with GeoRasterFileType is deleted
        self.raster_file_obj = open(self.raster_file, 'r')
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()

        # extract metadata from the tif file
        set_file_to_geo_raster_file_type(self.composite_resource, res_file.id, self.user)

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

    def test_content_file_delete(self):
        # test that when any file that is part of an instance GeoRasterFileType is deleted
        # all files associated with GeoRasterFileType is deleted

        # test deleting of tif file
        self._content_file_delete('.tif')

        # test deleting of vrt file
        self._content_file_delete('.vrt')

    def test_metadata_element_html(self):
        # here we are testing the get_html() function of the metadata element
        # we have implemented get_html() for only CellInformation element
        self.raster_file_obj = open(self.raster_file, 'r')
        self._create_composite_resource()

        res_file = self.composite_resource.files.first()
        # extract metadata
        set_file_to_geo_raster_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()

        # test the get_html() for CellInformation element
        cellinfo_html = u'<div class="col-xs-12 col-sm-6" style="margin-bottom:40px;">' \
                        u'<legend>Cell Information</legend><table class="custom-table">' \
                        u'<tbody><tr><th class="text-muted">Rows</th>' \
                        u'<td>230</td></tr><tr>' \
                        u'<th class="text-muted">Columns</th><td>329</td></tr><tr>' \
                        u'<th class="text-muted">Cell Size X Value</th><td>30.0</td></tr><tr>' \
                        u'<th class="text-muted">Cell Size Y Value</th><td>30.0</td></tr>' \
                        u'<tr><th class="text-muted">Cell Data Type</th><td>Float32</td></tr>' \
                        u'</tbody></table></div>'
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.metadata.cellInformation.get_html(pretty=False),
                         cellinfo_html)

    def _create_composite_resource(self):
        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Raster File Type Metadata',
            files=(self.raster_file_obj,)
        )

    def _test_file_metadata_on_file_delete(self, ext):
        self.raster_file_obj = open(self.raster_file, 'r')
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()

        # extract metadata from the tif file
        set_file_to_geo_raster_file_type(self.composite_resource, res_file.id, self.user)

        # test that we have one logical file of type GeoRasterFileType
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)

        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # there should be 1 coverage element
        self.assertEqual(logical_file.metadata.coverages.all().count(), 1)
        self.assertNotEqual(logical_file.metadata.originalCoverage, None)
        self.assertNotEqual(logical_file.metadata.cellInformation, None)
        self.assertNotEqual(logical_file.metadata.bandInformation, None)

        self.assertEqual(Coverage.objects.count(), 1)
        self.assertEqual(OriginalCoverage.objects.count(), 1)
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

        # test that all metadata deleted
        self.assertEqual(Coverage.objects.count(), 0)
        self.assertEqual(OriginalCoverage.objects.count(), 0)
        self.assertEqual(CellInformation.objects.count(), 0)
        self.assertEqual(BandInformation.objects.count(), 0)

    def _content_file_delete(self, ext):
        # test that when any file that is part of an instance GeoRasterFileType is deleted
        # all files associated with GeoRasterFileType is deleted
        self.raster_file_obj = open(self.raster_file, 'r')
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()

        # extract metadata from the tif file
        set_file_to_geo_raster_file_type(self.composite_resource, res_file.id, self.user)
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
