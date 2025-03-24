import unittest
from unittest.mock import MagicMock, PropertyMock
from hs_composite_resource.models import CompositeResource


class TestCompositeResource(unittest.TestCase):

    def setUp(self):
        self.resource = CompositeResource()

    def test_aggregation_types_empty(self):
        # Mock logical_files to return an empty list
        type(self.resource).logical_files = PropertyMock(return_value=[])
        self.assertEqual(self.resource.aggregation_types, [])

    def test_aggregation_types_single_type(self):
        # Mock logical_files to return a list with a single logical file
        logical_file = MagicMock()
        logical_file.type_name.return_value = 'GeoRasterLogicalFile'
        logical_file.get_aggregation_display_name.return_value = 'GeoRaster: Raster'
        type(self.resource).logical_files = PropertyMock(return_value=[logical_file])

        self.assertEqual(self.resource.aggregation_types, ['GeoRaster'])

    def test_aggregation_types_multiple_types(self):
        # Mock logical_files to return a list with multiple logical files
        logical_file1 = MagicMock()
        logical_file1.type_name.return_value = 'GeoRasterLogicalFile'
        logical_file1.get_aggregation_display_name.return_value = 'GeoRaster: Raster'

        logical_file2 = MagicMock()
        logical_file2.type_name.return_value = 'NetCDFLogicalFile'
        logical_file2.get_aggregation_display_name.return_value = 'NetCDF: NetCDF'

        type(self.resource).logical_files = PropertyMock(return_value=[logical_file1, logical_file2])

        self.assertEqual(self.resource.aggregation_types, ['GeoRaster', 'NetCDF'])

    def test_aggregation_types_duplicate_types(self):
        # Mock logical_files to return a list with duplicate logical files
        logical_file1 = MagicMock()
        logical_file1.type_name.return_value = 'GeoRasterLogicalFile'
        logical_file1.get_aggregation_display_name.return_value = 'GeoRaster: Raster'

        logical_file2 = MagicMock()
        logical_file2.type_name.return_value = 'GeoRasterLogicalFile'
        logical_file2.get_aggregation_display_name.return_value = 'GeoRaster: Raster'

        type(self.resource).logical_files = PropertyMock(return_value=[logical_file1, logical_file2])

        self.assertEqual(self.resource.aggregation_types, ['GeoRaster'])


if __name__ == '__main__':
    unittest.main()
