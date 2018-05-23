# coding=utf-8

from django.test import TransactionTestCase
from django.contrib.auth.models import Group

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.hydroshare.utils import resource_file_add_process

from hs_file_types.models import GeoRasterLogicalFile, NetCDFLogicalFile, \
    RefTimeseriesLogicalFile, GeoFeatureLogicalFile, TimeSeriesLogicalFile
from hs_file_types.tests.utils import CompositeResourceTestMixin


class CompositeResourceTestAutoAggregate(MockIRODSTestCaseMixin, TransactionTestCase,
                                         CompositeResourceTestMixin):
    def setUp(self):
        super(CompositeResourceTestAutoAggregate, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        self.res_title = 'Testing Composite Resource'
        self.test_file_path = 'hs_composite_resource/tests/data/{}'

    def tearDown(self):
        self.composite_resource.delete()

    def test_auto_aggregate_on_create_tif(self):
        """test that auto-aggregate works on resource create with .tif"""

        self.assertEqual(0, GeoRasterLogicalFile.objects.count())

        self.create_composite_resource(file_to_upload=self.test_file_path.format(
            "small_logan.tif"), auto_aggregate=True)

        self.assertEqual(1, GeoRasterLogicalFile.objects.count())

    def test_auto_aggregate_on_create_tiff(self):
        """test that auto-aggregate works on resource create with .tiff"""

        self.assertEqual(0, GeoRasterLogicalFile.objects.count())

        self.create_composite_resource(file_to_upload=self.test_file_path.format(
            "small_logan.tiff"), auto_aggregate=True)

        self.assertEqual(1, GeoRasterLogicalFile.objects.count())

    def test_auto_aggregate_on_create_nc(self):
        """test that auto-aggregate works on resource create with .nc"""

        self.assertEqual(0, NetCDFLogicalFile.objects.count())

        self.create_composite_resource(file_to_upload=self.test_file_path.format(
            "netcdf_valid.nc"), auto_aggregate=True)

        self.assertEqual(1, NetCDFLogicalFile.objects.count())

    def test_auto_aggregate_on_create_geo_feature(self):
        """test that auto-aggregate works on resource create with geo feature"""

        self.assertEqual(0, GeoFeatureLogicalFile.objects.count())

        self.create_composite_resource(file_to_upload=[
            self.test_file_path.format("watersheds.dbf"),
            self.test_file_path.format("watersheds.shp"),
            self.test_file_path.format("watersheds.shx")], auto_aggregate=True)

        self.assertEqual(1, GeoFeatureLogicalFile.objects.count())

    def test_auto_aggregate_on_create_refts(self):
        """test that auto-aggregate works on resource create with refts"""

        self.assertEqual(0, RefTimeseriesLogicalFile.objects.count())

        self.create_composite_resource(file_to_upload=[
            self.test_file_path.format("multi_sites_formatted_version1.0.refts.json")],
            auto_aggregate=True)

        self.assertEqual(1, RefTimeseriesLogicalFile.objects.count())

    def test_auto_aggregate_on_create_time_series(self):
        """test that auto-aggregate works on resource create with time series"""

        self.assertEqual(0, TimeSeriesLogicalFile.objects.count())

        self.create_composite_resource(file_to_upload=[
            self.test_file_path.format("ODM2.sqlite")],
            auto_aggregate=True)

        self.assertEqual(1, TimeSeriesLogicalFile.objects.count())

    def test_auto_aggregate_file_add_tif(self):
        """test that auto-aggregate works on tif file add"""

        self.create_composite_resource()

        self.assertEqual(0, GeoRasterLogicalFile.objects.count())

        # test add a file that auto-aggregates
        open_file = open(self.test_file_path.format("small_logan.tif"), 'r')
        resource_file_add_process(resource=self.composite_resource,
                                  files=(open_file,), user=self.user)

        self.assertEqual(1, GeoRasterLogicalFile.objects.count())

    def test_auto_aggregate_file_add_tiff(self):
        """test that auto-aggregate works on tiff file add"""

        self.create_composite_resource()

        self.assertEqual(0, GeoRasterLogicalFile.objects.count())

        # test add a file that auto-aggregates
        open_file = open(self.test_file_path.format("small_logan.tiff"), 'r')
        resource_file_add_process(resource=self.composite_resource,
                                  files=(open_file,), user=self.user)

        self.assertEqual(1, GeoRasterLogicalFile.objects.count())

    def test_auto_aggregate_file_add_sqlite(self):
        """test that auto-aggregate works on sqlite file add"""

        self.create_composite_resource()

        self.assertEqual(0, TimeSeriesLogicalFile.objects.count())

        # test add a file that auto-aggregates
        open_file = open(self.test_file_path.format("ODM2.sqlite"), 'r')
        resource_file_add_process(resource=self.composite_resource,
                                  files=(open_file,), user=self.user)

        self.assertEqual(1, TimeSeriesLogicalFile.objects.count())

    def test_auto_aggregate_file_add_refts(self):
        """test that auto-aggregate works on refts file add"""

        self.create_composite_resource()

        self.assertEqual(0, RefTimeseriesLogicalFile.objects.count())
        # test add a file that auto-aggregates
        open_file = open(self.test_file_path.format("multi_sites_formatted_version1.0.refts.json"),
                         'r')
        resource_file_add_process(resource=self.composite_resource,
                                  files=(open_file,), user=self.user)

        self.assertEqual(1, RefTimeseriesLogicalFile.objects.count())

    def test_auto_aggregate_file_add_nc(self):
        """test that auto-aggregate works on nc file add"""

        self.create_composite_resource()

        self.assertEqual(0, NetCDFLogicalFile.objects.count())
        # test add a file that auto-aggregates
        open_file = open(self.test_file_path.format("netcdf_valid.nc"), 'r')
        resource_file_add_process(resource=self.composite_resource,
                                  files=(open_file,), user=self.user)
        # because of auto aggregation, there should be 2 files

        self.assertEqual(1, NetCDFLogicalFile.objects.count())

    def test_auto_aggregate_file_add_geo_feature(self):
        """test that auto-aggregate works on geo feature file add"""

        self.create_composite_resource()

        self.assertEqual(0, GeoFeatureLogicalFile.objects.count())

        # test add a file that auto-aggregates
        dbf_file = open(self.test_file_path.format("watersheds.dbf"), 'r')
        shp_file = open(self.test_file_path.format("watersheds.shp"), 'r')
        shx_file = open(self.test_file_path.format("watersheds.shx"), 'r')
        resource_file_add_process(resource=self.composite_resource,
                                  files=(dbf_file, shp_file, shx_file), user=self.user)

        self.assertEqual(1, GeoFeatureLogicalFile.objects.count())
