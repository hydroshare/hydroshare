import os
import shutil
import tempfile
from datetime import date

from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import UploadedFile
from django.test import TransactionTestCase

from hs_access_control.models import PrivilegeCodes
from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_composite_resource.models import CompositeResource
from theme.models import QuotaMessage
from hs_core.hydroshare.utils import QuotaException

from hs_file_types.models import GeoRasterLogicalFile


class TestCopyResource(TransactionTestCase):
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

        # create a composite resource
        self.res = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.owner,
            title='Test Resource'
        )

        test_file1 = open('test1.txt', 'w')
        test_file1.write("Test text file in test1.txt")
        test_file1.close()
        test_file2 = open('test2.txt', 'w')
        test_file2.write("Test text file in test2.txt")
        test_file2.close()
        test_file3 = open('test3.txt', 'w')
        test_file3.write("Test text file in test3.txt")
        test_file3.close()
        self.test_file1 = open('test1.txt', 'rb')
        self.test_file2 = open('test2.txt', 'rb')
        self.test_file3 = open('test3.txt', 'rb')

        hydroshare.add_resource_files(self.res.short_id, self.test_file1, self.test_file2)

        # create a composite empty resource with one license that prohibits derivation
        statement = 'This resource is shared under the Creative Commons Attribution-NoDerivs CC ' \
                    'BY-ND.'
        url = 'http://creativecommons.org/licenses/by-nd/4.0/'
        metadata = []
        metadata.append({'rights': {'statement': statement, 'url': url}})
        self.res_composite_lic_nd = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.owner,
            title='Test Resource',
            metadata=metadata
        )

        # create a composite empty resource with another license that prohibits derivation
        statement = 'This resource is shared under the Creative Commons ' \
                    'Attribution-NoCommercial-NoDerivs CC BY-NC-ND.'
        url = 'http://creativecommons.org/licenses/by-nc-nd/4.0/'
        metadata = []
        metadata.append({'rights': {'statement': statement, 'url': url}})
        self.res_composite_lic_nc_nd = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.owner,
            title='Test Resource',
            metadata=metadata
        )

        raster_file = 'hs_core/tests/data/cea.tif'
        temp_dir = tempfile.mkdtemp()
        self.temp_raster_file = os.path.join(temp_dir, 'cea.tif')
        shutil.copy(raster_file, self.temp_raster_file)

    def tearDown(self):
        super(TestCopyResource, self).tearDown()
        if self.res:
            self.res.delete()
        if self.res_composite_lic_nd:
            self.res_composite_lic_nd.delete()
        if self.res_composite_lic_nc_nd:
            self.res_composite_lic_nc_nd.delete()
        self.test_file1.close()
        os.remove(self.test_file1.name)
        self.test_file2.close()
        os.remove(self.test_file2.name)
        self.test_file3.close()
        os.remove(self.test_file3.name)
        BaseResource.objects.all().delete()
        self.owner.delete()
        self.nonowner.delete()

    def test_copy_resource(self):
        # ensure a nonowner who does not have permission to view a resource cannot copy it
        with self.assertRaises(PermissionDenied):
            hydroshare.create_empty_resource(self.res.short_id,
                                             self.nonowner,
                                             action='copy')
        # ensure resource cannot be copied if the license does not allow derivation by a non-owner
        with self.assertRaises(PermissionDenied):
            hydroshare.create_empty_resource(self.res_composite_lic_nd.short_id,
                                             self.nonowner,
                                             action='copy')

        with self.assertRaises(PermissionDenied):
            hydroshare.create_empty_resource(self.res_composite_lic_nc_nd.short_id,
                                             self.nonowner,
                                             action='copy')

        # add key/value metadata to original resource
        self.res.extra_metadata = {'variable': 'temp', 'units': 'deg F'}
        self.res.save()

        # give nonowner view privilege so nonowner can create a new copy of this resource
        self.owner.uaccess.share_resource_with_user(self.res, self.nonowner,
                                                    PrivilegeCodes.VIEW)
        new_res = hydroshare.create_empty_resource(self.res.short_id,
                                                   self.nonowner,
                                                   action='copy')
        # test to make sure the new copied empty resource has no content files
        self.assertEqual(new_res.files.all().count(), 0)

        new_res = hydroshare.copy_resource(self.res, new_res)

        # test the new copied resource has the same resource type as the original resource
        self.assertTrue(isinstance(new_res, CompositeResource))

        # test the new copied resource has the correct content file with correct path copied over
        self.assertEqual(new_res.files.all().count(), 2)
        # add each file of resource to list
        new_res_file_list = []
        for f in new_res.files.all():
            new_res_file_list.append(f.resource_file.name)
        for f in self.res.files.all():
            ori_res_no_id_file_path = f.resource_file.name[len(self.res.short_id):]
            new_res_file_path = new_res.short_id + ori_res_no_id_file_path
            self.assertIn(new_res_file_path, new_res_file_list,
                          msg='resource content path is not created correctly '
                              'for new copied resource')

        # test key/value metadata copied over
        self.assertEqual(new_res.extra_metadata, self.res.extra_metadata)
        # test science metadata elements are copied from the original resource to the new copied
        # resource
        self.assertEqual(new_res.metadata.title.value,
                         self.res.metadata.title.value,
                         msg='metadata title is not copied over to the new copied resource')
        self.assertEqual(new_res.creator, self.nonowner,
                         msg='creator is not copied over to the new copied resource')

        # test to make sure a new unique identifier has been created for the new copied resource
        self.assertIsNotNone(
            new_res.short_id,
            msg='Unique identifier has not been created for new copied resource.')
        self.assertNotEqual(new_res.short_id, self.res.short_id)

        # test to make sure the new copied resource has the correct identifier
        self.assertEqual(new_res.metadata.identifiers.all().count(), 1,
                         msg="Number of identifier elements not equal to 1.")
        self.assertIn('hydroShareIdentifier',
                      [id.name for id in new_res.metadata.identifiers.all()],
                      msg="hydroShareIdentifier name was not found for new copied resource.")
        id_url = '{}/resource/{}'.format(hydroshare.utils.current_site_url(),
                                         new_res.short_id)
        self.assertIn(id_url, [id.url for id in new_res.metadata.identifiers.all()],
                      msg="Identifier url was not found for new copied resource.")

        # test to make sure the new copied resource is linked with the original resource via
        # 'source' type relation metadata element and contains the citation of the resource from which the copy was made
        relation_meta = new_res.metadata.relations.filter(type='source').first()
        derived_from = _get_relation_meta_derived_from(self.res)
        self.assertEqual(relation_meta.value, derived_from)

        # make sure to clean up resource so that S3 storage can be cleaned up
        if new_res:
            new_res.delete()

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

        # make sure to clean up all created resources to clean up S3 storage
        if self.composite_resource:
            self.composite_resource.delete()
        if new_composite_resource:
            new_composite_resource.delete()

    def test_copy_resource_over_quota(self):
        """
        Test case to ensure that copying a resource fails when the user's quota is exceeded.
        """
        # Set the user's quota to be over the limit
        if not QuotaMessage.objects.exists():
            QuotaMessage.objects.create()
        uquota = self.owner.quotas.first()
        uquota.save_allocated_value(1, "B")

        with self.assertRaises(QuotaException):
            hydroshare.add_file_to_resource(self.res, self.test_file3)
        uquota.save_allocated_value(20, "GB")

        # QuotaException should NOT be raised now that quota is not enforced
        hydroshare.add_file_to_resource(self.res, self.test_file3)


def _get_relation_meta_derived_from(resource):
    today = date.today().strftime("%m/%d/%Y")
    derived_from = "{}, accessed on: {}".format(resource.get_citation(), today)
    return derived_from
