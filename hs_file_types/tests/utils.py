from hs_core.hydroshare.utils import get_resource_file_name_and_extension
from hs_file_types.models import GeoRasterLogicalFile, GeoRasterFileMetaData, GenericLogicalFile


def assert_raster_file_type_metadata(self):
    # test the resource now has 2 files (vrt file added as part of metadata extraction)
    self.assertEqual(self.composite_resource.files.all().count(), 2)

    # check that the 2 resource files are now associated with GeoRasterLogicalFile
    for res_file in self.composite_resource.files.all():
        self.assertEqual(res_file.logical_file_type_name, "GeoRasterLogicalFile")
        self.assertEqual(res_file.has_logical_file, True)
        self.assertTrue(isinstance(res_file.logical_file, GeoRasterLogicalFile))

    # check that we put the 2 files in a new folder (small_logan)
    for res_file in self.composite_resource.files.all():
        file_path, base_file_name, _ = get_resource_file_name_and_extension(res_file)
        expected_file_path = "{}/data/contents/small_logan/{}"
        expected_file_path = expected_file_path.format(self.composite_resource.root_path,
                                                       base_file_name)
        self.assertEqual(file_path, expected_file_path)

    # check that there is no GenericLogicalFile object
    self.assertEqual(GenericLogicalFile.objects.count(), 0)
    # check that there is one GeoRasterLogicalFile object
    self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)

    res_file = self.composite_resource.files.first()
    # check that the logicalfile is associated with 2 files
    logical_file = res_file.logical_file
    self.assertEqual(logical_file.dataset_name, 'small_logan')
    self.assertEqual(logical_file.has_metadata, True)
    self.assertEqual(logical_file.files.all().count(), 2)
    self.assertEqual(set(self.composite_resource.files.all()),
                     set(logical_file.files.all()))

    # test that size property of the logical file is equal to sun of size of all files
    # that are part of the logical file
    self.assertEqual(logical_file.size, sum([f.size for f in logical_file.files.all()]))

    # test that there should be 1 object of type GeoRasterFileMetaData
    self.assertEqual(GeoRasterFileMetaData.objects.count(), 1)

    # test that the metadata associated with logical file id of type GeoRasterFileMetaData
    self.assertTrue(isinstance(logical_file.metadata, GeoRasterFileMetaData))

    # there should be 2 format elements associated with resource
    self.assertEqual(self.composite_resource.metadata.formats.all().count(), 2)
    self.assertEqual(
        self.composite_resource.metadata.formats.all().filter(value='application/vrt').count(),
        1)
    self.assertEqual(self.composite_resource.metadata.formats.all().filter(
        value='image/tiff').count(), 1)

    # test extracted metadata for the file type

    # geo raster file type should have all the metadata elements
    self.assertEqual(logical_file.metadata.has_all_required_elements(), True)

    # there should be 1 coverage element - box type
    self.assertNotEqual(logical_file.metadata.spatial_coverage, None)
    self.assertEqual(logical_file.metadata.spatial_coverage.type, 'box')

    box_coverage = logical_file.metadata.spatial_coverage
    self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
    self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
    self.assertEqual(box_coverage.value['northlimit'], 42.0500269597691)
    self.assertEqual(box_coverage.value['eastlimit'], -111.57773718106195)
    self.assertEqual(box_coverage.value['southlimit'], 41.98722286029891)
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
                     'NAD83 / UTM zone 12N')

    # testing extended metadata element: cell information
    cell_info = logical_file.metadata.cellInformation
    self.assertEqual(cell_info.rows, 230)
    self.assertEqual(cell_info.columns, 329)
    self.assertEqual(cell_info.cellSizeXValue, 30.0)
    self.assertEqual(cell_info.cellSizeYValue, 30.0)
    self.assertEqual(cell_info.cellDataType, 'Float32')

    # testing extended metadata element: band information
    self.assertEqual(logical_file.metadata.bandInformations.count(), 1)
    band_info = logical_file.metadata.bandInformations.first()
    self.assertEqual(band_info.noDataValue, '-3.40282346639e+38')
    self.assertEqual(band_info.maximumValue, '2880.00708008')
    self.assertEqual(band_info.minimumValue, '1870.63659668')
