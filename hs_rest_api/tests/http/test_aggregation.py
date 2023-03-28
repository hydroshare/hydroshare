import tempfile

from django.urls import reverse

from hs_core.models import ResourceFile
from hs_core.tests.api.rest.base import HSRESTTestCase
from hs_file_types.models import NetCDFLogicalFile
from hs_file_types.tests.utils import CompositeResourceTestMixin


class TestFileSetEndpoint(HSRESTTestCase, CompositeResourceTestMixin):

    def setUp(self):
        super(TestFileSetEndpoint, self).setUp()

        self.temp_dir = tempfile.mkdtemp()
        self.resources_to_delete = []

        self.res_title = "Test NetCDF File Type"
        self.logical_file_type_name = "NetCDFLogicalFile"
        base_file_path = 'hs_file_types/tests/{}'
        self.netcdf_file_name = 'netcdf_valid.nc'
        self.netcdf_file = base_file_path.format(self.netcdf_file_name)

    def test_move_aggregation(self):
        """Test that we can move an aggregation from one folder location to another through the api"""

        self.create_composite_resource()
        # upload the netcdf file
        self.add_file_to_resource(file_to_add=self.netcdf_file)
        # there should be one resource file
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # check that the resource file is not part of an aggregation
        self.assertEqual(res_file.has_logical_file, False)
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)

        # set nc file to NetCDF aggregation
        set_type_url = reverse('set_file_type_public', kwargs={"pk": self.composite_resource.short_id,
                                                               "file_path": res_file.short_path,
                                                               "hs_file_type": "NetCDF"})
        self.client.post(set_type_url, data={"folder_path": ""})
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        nc_aggr = NetCDFLogicalFile.objects.first()

        # create a folder where we will move the netcdf aggregation
        new_folder = 'netcdf_aggregation'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        move_aggr_url = reverse('move_aggregation_public', kwargs={"resource_id": self.composite_resource.short_id,
                                                                   "file_path": nc_aggr.aggregation_name,
                                                                   "tgt_path": new_folder,
                                                                   "hs_file_type": "NetCDFLogicalFile"})
        self.client.post(move_aggr_url, data={})
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        nc_aggr = NetCDFLogicalFile.objects.first()
        self.assertTrue(nc_aggr.aggregation_name.startswith(new_folder))

        # move the aggregation back to root of the resource
        move_aggr_url = reverse('move_aggregation_public', kwargs={"resource_id": self.composite_resource.short_id,
                                                                   "file_path": nc_aggr.aggregation_name,
                                                                   "tgt_path": "",
                                                                   "hs_file_type": "NetCDFLogicalFile"})
        self.client.post(move_aggr_url, data={})
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        nc_aggr = NetCDFLogicalFile.objects.first()
        self.assertFalse(nc_aggr.aggregation_name.startswith(new_folder))
