import os
import tempfile
import shutil

from django.contrib.auth.models import Group
from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import UploadedFile

from hs_core import hydroshare
from hs_core.models import GenericResource
from hs_core.hydroshare import utils
from hs_access_control.models import PrivilegeCodes
from hs_geo_raster_resource.models import RasterResource, OriginalCoverage, CellInformation, \
    BandInformation
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

        # create a generic resource
        self.res_generic = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.owner,
            title='Test Generic Resource'
        )

        test_file1 = open('test1.txt', 'w')
        test_file1.write("Test text file in test1.txt")
        test_file1.close()
        test_file2 = open('test2.txt', 'w')
        test_file2.write("Test text file in test2.txt")
        test_file2.close()
        self.test_file1 = open('test1.txt', 'r')
        self.test_file2 = open('test2.txt', 'r')

        hydroshare.add_resource_files(self.res_generic.short_id, self.test_file1, self.test_file2)

        # create a generic empty resource with one license that prohibits derivation
        statement = 'This resource is shared under the Creative Commons Attribution-NoDerivs CC ' \
                    'BY-ND.'
        url = 'http://creativecommons.org/licenses/by-nd/4.0/'
        metadata = []
        metadata.append({'rights': {'statement': statement, 'url': url}})
        self.res_generic_lic_nd = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.owner,
            title='Test Generic Resource',
            metadata=metadata
        )

        # create a generic empty resource with another license that prohibits derivation
        statement = 'This resource is shared under the Creative Commons ' \
                    'Attribution-NoCommercial-NoDerivs CC BY-NC-ND.'
        url = 'http://creativecommons.org/licenses/by-nc-nd/4.0/'
        metadata = []
        metadata.append({'rights': {'statement': statement, 'url': url}})
        self.res_generic_lic_nc_nd = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.owner,
            title='Test Generic Resource',
            metadata=metadata
        )

        # create a raster resource that represents a specific resource type
        raster_file = 'hs_core/tests/data/cea.tif'
        temp_dir = tempfile.mkdtemp()
        self.temp_raster_file = os.path.join(temp_dir, 'cea.tif')
        shutil.copy(raster_file, self.temp_raster_file)
        self.raster_obj = open(self.temp_raster_file, 'r')
        files = [UploadedFile(file=self.raster_obj, name='cea.tif')]
        self.res_raster = hydroshare.create_resource(
            resource_type='RasterResource',
            owner=self.owner,
            title='Test Raster Resource',
            files=files,
            metadata=[]
        )
        # call the post creation process here for the metadata to be
        # extracted
        utils.resource_post_create_actions(resource=self.res_raster, user=self.owner, metadata=[])

    def tearDown(self):
        super(TestCopyResource, self).tearDown()
        if self.res_generic:
            self.res_generic.delete()
        if self.res_raster:
            self.res_raster.delete()
        if self.res_generic_lic_nd:
            self.res_generic_lic_nd.delete()
        if self.res_generic_lic_nc_nd:
            self.res_generic_lic_nc_nd.delete()
        self.test_file1.close()
        os.remove(self.test_file1.name)
        self.test_file2.close()
        os.remove(self.test_file2.name)

    def test_copy_generic_resource(self):
        # ensure a nonowner who does not have permission to view a resource cannot copy it
        with self.assertRaises(PermissionDenied):
            hydroshare.create_empty_resource(self.res_generic.short_id,
                                             self.nonowner,
                                             action='copy')
        # ensure resource cannot be copied if the license does not allow derivation by a non-owner
        with self.assertRaises(PermissionDenied):
            hydroshare.create_empty_resource(self.res_generic_lic_nd.short_id,
                                             self.nonowner,
                                             action='copy')

        with self.assertRaises(PermissionDenied):
            hydroshare.create_empty_resource(self.res_generic_lic_nc_nd.short_id,
                                             self.nonowner,
                                             action='copy')

        # add key/value metadata to original resource
        self.res_generic.extra_metadata = {'variable': 'temp', 'units': 'deg F'}
        self.res_generic.save()

        # give nonowner view privilege so nonowner can create a new copy of this resource
        self.owner.uaccess.share_resource_with_user(self.res_generic, self.nonowner,
                                                    PrivilegeCodes.VIEW)
        new_res_generic = hydroshare.create_empty_resource(self.res_generic.short_id,
                                                           self.nonowner,
                                                           action='copy')
        # test to make sure the new copied empty resource has no content files
        self.assertEqual(new_res_generic.files.all().count(), 0)

        new_res_generic = hydroshare.copy_resource(self.res_generic, new_res_generic)

        # test the new copied resource has the same resource type as the original resource
        self.assertTrue(isinstance(new_res_generic, GenericResource))

        # test the new copied resource has the correct content file with correct path copied over
        self.assertEqual(new_res_generic.files.all().count(), 2)
        # add each file of resource to list
        new_res_file_list = []
        for f in new_res_generic.files.all():
            new_res_file_list.append(f.resource_file.name)
        for f in self.res_generic.files.all():
            ori_res_no_id_file_path = f.resource_file.name[len(self.res_generic.short_id):]
            new_res_file_path = new_res_generic.short_id + ori_res_no_id_file_path
            self.assertIn(new_res_file_path, new_res_file_list,
                          msg='resource content path is not created correctly '
                              'for new copied resource')

        # test key/value metadata copied over
        self.assertEqual(new_res_generic.extra_metadata, self.res_generic.extra_metadata)
        # test science metadata elements are copied from the original resource to the new copied
        # resource
        self.assertEqual(new_res_generic.metadata.title.value,
                         self.res_generic.metadata.title.value,
                         msg='metadata title is not copied over to the new copied resource')
        self.assertEqual(new_res_generic.creator, self.nonowner,
                         msg='creator is not copied over to the new copied resource')

        # test to make sure a new unique identifier has been created for the new copied resource
        self.assertIsNotNone(
            new_res_generic.short_id,
            msg='Unique identifier has not been created for new copied resource.')
        self.assertNotEqual(new_res_generic.short_id, self.res_generic.short_id)

        # test to make sure the new copied resource has the correct identifier
        self.assertEqual(new_res_generic.metadata.identifiers.all().count(), 1,
                         msg="Number of identifier elements not equal to 1.")
        self.assertIn('hydroShareIdentifier',
                      [id.name for id in new_res_generic.metadata.identifiers.all()],
                      msg="hydroShareIdentifier name was not found for new copied resource.")
        id_url = '{}/resource/{}'.format(hydroshare.utils.current_site_url(),
                                         new_res_generic.short_id)
        self.assertIn(id_url, [id.url for id in new_res_generic.metadata.identifiers.all()],
                      msg="Identifier url was not found for new copied resource.")

        # test to make sure the new copied resource is linked with the original resource via
        # isDerivedFrom Source metadata element
        self.assertGreater(new_res_generic.metadata.sources.all().count(), 0,
                           msg="New copied resource does not has source element.")

        derived_from_value = '{}/resource/{}'.format(hydroshare.utils.current_site_url(),
                                                     self.res_generic.short_id)
        self.assertIn(derived_from_value,
                      [src.derived_from for src in new_res_generic.metadata.sources.all()],
                      msg="The original resource identifier is not set in isDerivedFrom Source "
                          "metadata element of the new copied resource")
        # make sure to clean up resource so that irods storage can be cleaned up
        if new_res_generic:
            new_res_generic.delete()

    def test_copy_raster_resource(self):
        # ensure a nonowner who does not have permission to view a resource cannot copy it
        with self.assertRaises(PermissionDenied):
            hydroshare.create_empty_resource(self.res_raster.short_id,
                                             self.nonowner,
                                             action='copy')
        # give nonowner view privilege so nonowner can create a new copy of this resource
        self.owner.uaccess.share_resource_with_user(self.res_raster, self.nonowner,
                                                    PrivilegeCodes.VIEW)

        new_res_raster = hydroshare.create_empty_resource(self.res_raster.short_id,
                                                          self.nonowner,
                                                          action='copy')
        new_res_raster = hydroshare.copy_resource(self.res_raster, new_res_raster)

        # test the new copied resource has the same resource type as the original resource
        self.assertTrue(isinstance(new_res_raster, RasterResource))

        # test science metadata elements are copied from the original resource to the new copied
        # resource
        self.assertTrue(new_res_raster.metadata.title.value == self.res_raster.metadata.title.value)
        self.assertTrue(new_res_raster.creator == self.nonowner)

        # test extended metadata elements are copied from the original resource to the new
        # copied resource
        self.assertTrue(OriginalCoverage.objects.filter(
            object_id=new_res_raster.metadata.id).exists())
        self.assertEqual(new_res_raster.metadata.originalCoverage.value,
                         self.res_raster.metadata.originalCoverage.value,
                         msg="OriginalCoverage of new copied resource is not equal to "
                             "that of the original resource")

        self.assertTrue(CellInformation.objects.filter(
            object_id=new_res_raster.metadata.id).exists())
        newcell = new_res_raster.metadata.cellInformation
        oldcell = self.res_raster.metadata.cellInformation
        self.assertEqual(newcell.rows, oldcell.rows,
                         msg="Rows of new copied resource is not equal to that of "
                             "the original resource")
        self.assertEqual(newcell.columns, oldcell.columns,
                         msg="Columns of new copied resource is not equal to that of the "
                             "original resource")
        self.assertEqual(newcell.cellSizeXValue, oldcell.cellSizeXValue,
                         msg="CellSizeXValue of new copied resource is not equal to "
                             "that of the original resource")
        self.assertEqual(newcell.cellSizeYValue, oldcell.cellSizeYValue,
                         msg="CellSizeYValue of new copied resource is not equal to "
                             "that of the original resource")
        self.assertEqual(newcell.cellDataType, oldcell.cellDataType,
                         msg="CellDataType of new copied resource is not equal to "
                             "that of the original resource")

        self.assertTrue(BandInformation.objects.filter(
            object_id=new_res_raster.metadata.id).exists())
        newband = new_res_raster.metadata.bandInformations.first()
        oldband = self.res_raster.metadata.bandInformations.first()
        self.assertEqual(newband.name, oldband.name,
                         msg="Band name of new copied resource is not equal to that of "
                             "the original resource")

        # test to make sure a new unique identifier has been created for the new copied resource
        self.assertIsNotNone(new_res_raster.short_id, msg='Unique identifier has not been '
                                                          'created for new copied resource.')
        self.assertNotEqual(new_res_raster.short_id, self.res_raster.short_id)

        # test to make sure the new copied resource has 2 content file
        # since an additional vrt file is created
        self.assertEqual(new_res_raster.files.all().count(), 2)

        # test to make sure the new copied resource has the correct identifier
        self.assertEqual(new_res_raster.metadata.identifiers.all().count(), 1,
                         msg="Number of identifier elements not equal to 1.")
        self.assertIn('hydroShareIdentifier',
                      [id.name for id in new_res_raster.metadata.identifiers.all()],
                      msg="hydroShareIdentifier name was not found for new copied resource.")
        id_url = '{}/resource/{}'.format(hydroshare.utils.current_site_url(),
                                         new_res_raster.short_id)
        self.assertIn(id_url, [id.url for id in new_res_raster.metadata.identifiers.all()],
                      msg="Identifier url was not found for new copied resource.")

        # test to make sure the new copied resource is linked with the original resource via
        # isDerivedFrom Source metadata element
        self.assertEqual(new_res_raster.metadata.sources.all().count(), 1,
                         msg="New copied resource does not has source element.")

        derived_from_value = '{}/resource/{}'.format(hydroshare.utils.current_site_url(),
                                                     self.res_raster.short_id)
        self.assertIn(derived_from_value,
                      [src.derived_from for src in new_res_raster.metadata.sources.all()],
                      msg="The original resource identifier is not set in isDerivedFrom Source "
                          "metadata element of the new copied resource")
        # make sure to clean up resource so that irods storage can be cleaned up
        if new_res_raster:
            new_res_raster.delete()

    def test_copy_composite_resource(self):
        """Test that logical file type objects gets copied along with the metadata that each
        logical file type object contains. Here we are not testing resource level metadata copy
        as that has been tested in separate unit tests"""

        self.raster_obj = open(self.temp_raster_file, 'r')
        files = [UploadedFile(file=self.raster_obj, name='cea.tif')]
        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.owner,
            title='Test Composite Resource',
            files=files,
            auto_aggregate=False
        )

        # run the resource post creation signal
        utils.resource_post_create_actions(resource=self.composite_resource, user=self.owner,
                                           metadata=self.composite_resource.metadata)

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

        # create a copy fo the composite resource
        new_composite_resource = hydroshare.create_empty_resource(self.composite_resource.short_id,
                                                                  self.nonowner,
                                                                  action='copy')
        new_composite_resource = hydroshare.copy_resource(self.composite_resource,
                                                          new_composite_resource)
        # check that there is 2 GeoRasterLogicalFile objects
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 2)

        # compare the 2 GeoRasterLogicalFile objects from the original resource and the new one
        orig_res_file = self.composite_resource.files.first()
        orig_geo_raster_lfo = orig_res_file.logical_file
        copy_res_file = new_composite_resource.files.first()
        copy_geo_raster_lfo = copy_res_file.logical_file

        # check that we put the 2 files in a new folder (cea)
        for res_file in self.composite_resource.files.all():
            file_path, base_file_name = res_file.full_path, res_file.file_name
            expected_file_path = "{}/data/contents/cea/{}"
            expected_file_path = expected_file_path.format(self.composite_resource.root_path,
                                                           base_file_name)
            self.assertEqual(file_path, expected_file_path)

        for res_file in new_composite_resource.files.all():
            file_path, base_file_name = res_file.full_path, res_file.file_name
            expected_file_path = "{}/data/contents/cea/{}"
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
