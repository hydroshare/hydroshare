from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.test import RequestFactory

from rest_framework import status

from hs_core.testing import MockIRODSTestCaseMixin, ViewTestCase
from hs_core import hydroshare
from hs_composite_resource.views import update_resource_coverage
from hs_file_types.models import GeoRasterLogicalFile, NetCDFLogicalFile
from hs_file_types.tests.utils import CompositeResourceTestMixin


class TestUpdateResourceCoverageViewFunctions(MockIRODSTestCaseMixin, ViewTestCase,
                                              CompositeResourceTestMixin):
    def setUp(self):
        super(TestUpdateResourceCoverageViewFunctions, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.username = 'john'
        self.password = 'jhmypassword'
        self.user = hydroshare.create_account(
            'john@gmail.com',
            username=self.username,
            first_name='John',
            last_name='Clarson',
            superuser=False,
            password=self.password,
            groups=[]
        )

        self.factory = RequestFactory()
        self.res_title = 'Testing Composite Resource'

        self.raster_file_name = 'small_logan.tif'
        self.raster_file = 'hs_composite_resource/tests/data/{}'.format(self.raster_file_name)

        self.netcdf_file_name = 'netcdf_valid.nc'
        self.netcdf_file = 'hs_composite_resource/tests/data/{}'.format(self.netcdf_file_name)

    def test_update_resource_spatial_coverage(self):
        """Here we are testing the update of resource spatial coverage based on the
        spatial coverages from all the aggregations in the resource using the view function
        update_resource_coverage"""

        self.create_composite_resource(file_to_upload=self.raster_file)
        res_file = self.composite_resource.files.first()

        # set the tif file to GeoRasterLogicalFile type (aggregation)
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        url_params = {'resource_id': self.composite_resource.short_id,
                      'coverage_type': 'spatial'
                      }
        url = reverse('update_resource_coverage', kwargs=url_params)
        request = self.factory.post(url)
        request.user = self.user
        # this is the view function we are testing
        response = update_resource_coverage(request, resource_id=self.composite_resource.short_id,
                                            coverage_type='spatial')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.composite_resource.delete()

    def test_update_resource_temporal_coverage(self):
        """Here we are testing the update of resource temporal coverage based on the
        temporal coverages from all the aggregations in the resource using the view function
        update_resource_coverage"""

        self.create_composite_resource(file_to_upload=self.netcdf_file)
        res_file = self.composite_resource.files.first()

        # set the tif file to GeoRasterLogicalFile type (aggregation)
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        url_params = {'resource_id': self.composite_resource.short_id,
                      'coverage_type': 'temporal'
                      }
        url = reverse('update_resource_coverage', kwargs=url_params)
        request = self.factory.post(url)
        request.user = self.user
        # this is the view function we are testing
        response = update_resource_coverage(request, resource_id=self.composite_resource.short_id,
                                            coverage_type='temporal')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.composite_resource.delete()
