import os
import tempfile
import shutil

from django.contrib.auth.models import Group
from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import UploadedFile

from hs_core import hydroshare
from hs_access_control.models import PrivilegeCodes
from hs_file_types.models import GeoRasterLogicalFile


class TestCopyResource(TestCase):
    def setUp(self):
        super(TestCopyResource, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        # create a user who is the owner of the resource to be copied
        self.owner = hydroshare.create_account(
            'owner@gmail.edu',
            username='owner',
            first_name='owner_firstname',
            last_name='owner_lastname',
            superuser=False,
            groups=[]
        )

        # create a user who is NOT the owner of the resource to be copied
        self.nonowner = hydroshare.create_account(
            'nonowner@gmail.com',
            username='nonowner',
            first_name='nonowner_firstname',
            last_name='nonowner_lastname',
            superuser=False,
            groups=[]
        )

    def tearDown(self):
        super(TestCopyResource, self).tearDown()

    def test_copy_composite_resource(self):
        """Test that logical file type objects gets copied along with the metadata that each
        logical file type object contains. Here we are not testing resource level metadata copy
        as that has been tested in separate unit tests"""

        self.raster_obj = open(self.temp_raster_file, 'rb')
        files = [UploadedFile(file=self.raster_obj, name='cea.tif')]
        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.owner,
            title='Test Composite Resource',
            files=files,
            auto_aggregate=False
        )

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with file type
        self.assertEqual(res_file.has_logical_file, False)

        # set the tif file to GeoRasterFile type
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.owner, res_file.id)

        # ensure a nonowner who does not have permission to view a resource cannot copy it
        with self.assertRaises(PermissionDenied):
            hydroshare.create_empty_resource(self.composite_resource.short_id,
                                             self.nonowner,
                                             action='copy')
        # give nonowner view privilege so nonowner can create a new copy of this resource
        self.owner.uaccess.share_resource_with_user(self.composite_resource, self.nonowner,
                                                    PrivilegeCodes.VIEW)

        orig_res_file = self.composite_resource.files.first()
        orig_geo_raster_lfo = orig_res_file.logical_file

        # add some key value metadata
        orig_geo_raster_lfo.metadata.extra_metadata = {'key-1': 'value-1', 'key-2': 'value-2'}

        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(self.composite_resource.short_id,
                                                                  self.nonowner,
                                                                  action='copy')
        new_composite_resource = hydroshare.copy_resource(self.composite_resource,
                                                          new_composite_resource)

        self.assertEqual(new_composite_resource.files.count(), 2)
        self.assertEqual(self.composite_resource.files.count(),
                         new_composite_resource.files.count())
        # check that there is 2 GeoRasterLogicalFile objects
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 2)

        # compare the 2 GeoRasterLogicalFile objects from the original resource and the new one
        orig_res_file = self.composite_resource.files.first()
        orig_geo_raster_lfo = orig_res_file.logical_file
        copy_res_file = new_composite_resource.files.first()
        copy_geo_raster_lfo = copy_res_file.logical_file

        # check that the 2 files are at the same location
        for res_file in self.composite_resource.files.all():
            file_path, base_file_name = res_file.full_path, res_file.file_name
            expected_file_path = "{}/data/contents/{}"
            expected_file_path = expected_file_path.format(self.composite_resource.root_path,
                                                           base_file_name)
            self.assertEqual(file_path, expected_file_path)

        for res_file in new_composite_resource.files.all():
            file_path, base_file_name = res_file.full_path, res_file.file_name
            expected_file_path = "{}/data/contents/{}"
            expected_file_path = expected_file_path.format(new_composite_resource.root_path,
                                                           base_file_name)
            self.assertEqual(file_path, expected_file_path)

        # both logical file objects should have 2 resource files
        self.assertEqual(orig_geo_raster_lfo.files.count(), copy_geo_raster_lfo.files.count())
        self.assertEqual(orig_geo_raster_lfo.files.count(), 2)

        # both logical file objects should have same dataset_name
        self.assertEqual(orig_geo_raster_lfo.dataset_name, copy_geo_raster_lfo.dataset_name)
        # both should have same key/value metadata
        self.assertEqual(orig_geo_raster_lfo.metadata.extra_metadata,
                         copy_geo_raster_lfo.metadata.extra_metadata)

        # both logical file objects should have same coverage metadata
        self.assertEqual(orig_geo_raster_lfo.metadata.coverages.count(),
                         copy_geo_raster_lfo.metadata.coverages.count())

        self.assertEqual(orig_geo_raster_lfo.metadata.coverages.count(), 1)
        org_spatial_coverage = orig_geo_raster_lfo.metadata.spatial_coverage
        copy_spatial_coverage = copy_geo_raster_lfo.metadata.spatial_coverage
        self.assertEqual(org_spatial_coverage.type, copy_spatial_coverage.type)
        self.assertEqual(org_spatial_coverage.type, 'box')
        self.assertEqual(org_spatial_coverage.value['projection'],
                         copy_spatial_coverage.value['projection'])
        self.assertEqual(org_spatial_coverage.value['units'],
                         copy_spatial_coverage.value['units'])
        self.assertEqual(org_spatial_coverage.value['northlimit'],
                         copy_spatial_coverage.value['northlimit'])
        self.assertEqual(org_spatial_coverage.value['eastlimit'],
                         copy_spatial_coverage.value['eastlimit'])
        self.assertEqual(org_spatial_coverage.value['southlimit'],
                         copy_spatial_coverage.value['southlimit'])
        self.assertEqual(org_spatial_coverage.value['westlimit'],
                         copy_spatial_coverage.value['westlimit'])

        # both logical file objects should have same original coverage
        org_orig_coverage = orig_geo_raster_lfo.metadata.originalCoverage
        copy_orig_coverage = copy_geo_raster_lfo.metadata.originalCoverage
        self.assertEqual(org_orig_coverage.value['projection'],
                         copy_orig_coverage.value['projection'])
        self.assertEqual(org_orig_coverage.value['units'],
                         copy_orig_coverage.value['units'])
        self.assertEqual(org_orig_coverage.value['northlimit'],
                         copy_orig_coverage.value['northlimit'])
        self.assertEqual(org_orig_coverage.value['eastlimit'],
                         copy_orig_coverage.value['eastlimit'])
        self.assertEqual(org_orig_coverage.value['southlimit'],
                         copy_orig_coverage.value['southlimit'])
        self.assertEqual(org_orig_coverage.value['westlimit'],
                         copy_orig_coverage.value['westlimit'])

        # both logical file objects should have same cell information metadata
        orig_cell_info = orig_geo_raster_lfo.metadata.cellInformation
        copy_cell_info = copy_geo_raster_lfo.metadata.cellInformation
        self.assertEqual(orig_cell_info.rows, copy_cell_info.rows)
        self.assertEqual(orig_cell_info.columns, copy_cell_info.columns)
        self.assertEqual(orig_cell_info.cellSizeXValue, copy_cell_info.cellSizeXValue)
        self.assertEqual(orig_cell_info.cellSizeYValue, copy_cell_info.cellSizeYValue)
        self.assertEqual(orig_cell_info.cellDataType, copy_cell_info.cellDataType)

        # both logical file objects should have same band information metadata
        self.assertEqual(orig_geo_raster_lfo.metadata.bandInformations.count(), 1)
        self.assertEqual(orig_geo_raster_lfo.metadata.bandInformations.count(),
                         copy_geo_raster_lfo.metadata.bandInformations.count())
        orig_band_info = orig_geo_raster_lfo.metadata.bandInformations.first()
        copy_band_info = copy_geo_raster_lfo.metadata.bandInformations.first()
        self.assertEqual(orig_band_info.noDataValue, copy_band_info.noDataValue)
        self.assertEqual(orig_band_info.maximumValue, copy_band_info.maximumValue)
        self.assertEqual(orig_band_info.minimumValue, copy_band_info.minimumValue)

        # make sure to clean up all created resources to clean up iRODS storage
        if self.composite_resource:
            self.composite_resource.delete()
        if new_composite_resource:
            new_composite_resource.delete()
