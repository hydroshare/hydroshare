# coding=utf-8
import os
import tempfile
import shutil

from django.test import TransactionTestCase
from django.core.files.uploadedfile import UploadedFile
from django.contrib.auth.models import Group

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_file_types.utils import raster_extract_metadata
from hs_file_types.models import GeoRasterLogicalFile


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
        self.raster_file = 'hs_file_types/tests/{}'.format(self.raster_file_name)
        target_temp_raster_file = os.path.join(self.temp_dir, self.raster_file_name)
        shutil.copy(self.raster_file, target_temp_raster_file)
        self.raster_file_obj = open(target_temp_raster_file, 'r')

    def tearDown(self):
        super(RasterFileTypeMetaData, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_metadata_extraction(self):
        self.raster_file_obj = open(self.raster_file, 'r')
        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Raster File Type Metadata',
            files=(self.raster_file_obj,)
        )
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is associated with GenericLogicalFile by default
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
        # no metadata associated with generirclogicalfile
        self.assertEqual(res_file.logical_file.has_metadata, False)
        raster_extract_metadata(self.composite_resource, res_file.id, self.user)

        # test the resource now has 2 files (vrt file added as part of metadata extraction)
        self.assertEqual(self.composite_resource.files.all().count(), 2)

        # check that the 2 resource files are now associated with GeoRasterLogicalFile
        for res_file in self.composite_resource.files.all():
            self.assertEqual(res_file.logical_file_type_name, "GeoRasterLogicalFile")

        # check that the logicalfile is associated with 2 files
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        logical_file = res_file.logical_file
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
        # TODO: adjust these values to make the test pass
        self.assertEqual(box_coverage.value['northlimit'], 42.11071605314457)
        self.assertEqual(box_coverage.value['eastlimit'], -111.45699925047542)
        self.assertEqual(box_coverage.value['southlimit'], 41.66417975061928)
        self.assertEqual(box_coverage.value['westlimit'], -111.81761887121905)

        # testing extended metadata element: original coverage
        ori_coverage = logical_file.metadata.originalCoverage
        self.assertNotEqual(ori_coverage, None)

        # TODO: adjust these values to make the test pass
        self.assertEqual(ori_coverage.value['northlimit'], 4662392.446916306)
        self.assertEqual(ori_coverage.value['eastlimit'], 461954.01909127034)
        self.assertEqual(ori_coverage.value['southlimit'], 4612592.446916306)
        self.assertEqual(ori_coverage.value['westlimit'], 432404.01909127034)
        self.assertEqual(ori_coverage.value['units'], 'meter')
        self.assertEqual(ori_coverage.value['projection'],
                         'NAD83 / UTM zone 12N Transverse_Mercator')

        # testing extended metadata element: cell information
        cell_info = logical_file.metadata.cellInformation
        # TODO: adjust these values to make the test pass
        self.assertEqual(cell_info.rows, 1660)
        self.assertEqual(cell_info.columns, 985)
        self.assertEqual(cell_info.cellSizeXValue, 30.0)
        self.assertEqual(cell_info.cellSizeYValue, 30.0)
        self.assertEqual(cell_info.cellDataType, 'Float32')

        # testing extended metadata element: band information
        self.assertEqual(logical_file.metadata.bandInformation.count(), 1)
        band_info = logical_file.metadata.bandInformation.first()
        # TODO: adjust these values to make the test pass
        self.assertEqual(band_info.noDataValue, '-3.40282346639e+38')
        self.assertEqual(band_info.maximumValue, '3031.44311523')
        self.assertEqual(band_info.minimumValue, '1358.33459473')


