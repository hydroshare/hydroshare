import os
import tempfile
import shutil

from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.hydroshare.utils import resource_post_create_actions

from hs_file_types.models import TimeSeriesLogicalFile, GenericLogicalFile
from utils import assert_time_series_file_type_metadata


class TimeSeriesFileTypeMetaDataTest(MockIRODSTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(TimeSeriesFileTypeMetaDataTest, self).setUp()
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
            title='Test Time series File Type Metadata'
        )

        self.temp_dir = tempfile.mkdtemp()
        self.sqlite_file_name = 'ODM2_Multi_Site_One_Variable.sqlite'
        self.sqlite_file = 'hs_file_types/tests/data/{}'.format(self.sqlite_file_name)

        target_temp_sqlite_file = os.path.join(self.temp_dir, self.sqlite_file_name)
        shutil.copy(self.sqlite_file, target_temp_sqlite_file)
        self.sqlite_file_obj = open(target_temp_sqlite_file, 'r')

        self.sqlite_invalid_file_name = 'ODM2_invalid.sqlite'
        self.sqlite_invalid_file = 'hs_file_types/tests/data/{}'.format(
            self.sqlite_invalid_file_name)

        target_temp_sqlite_invalid_file = os.path.join(self.temp_dir, self.sqlite_invalid_file_name)
        shutil.copy(self.sqlite_invalid_file, target_temp_sqlite_invalid_file)

    def tearDown(self):
        super(TimeSeriesFileTypeMetaDataTest, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_sqlite_set_file_type_to_timeseries(self):
        # here we are using a valid sqlite file for setting it
        # to TimeSeries file type which includes metadata extraction
        self.sqlite_file_obj = open(self.sqlite_file, 'r')
        self._create_composite_resource(title='Untitled Resource')

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
        # check that there is one GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

        # check that there is no TimeSeriesLogicalFile object
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 0)

        # set the sqlite file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        # test extracted metadata
        assert_time_series_file_type_metadata(self)
        # test file level keywords
        # res_file = self.composite_resource.files.first()
        # logical_file = res_file.logical_file
        # self.assertEqual(len(logical_file.metadata.keywords), 1)
        # self.assertEqual(logical_file.metadata.keywords[0], 'Snow water equivalent')
        self.composite_resource.delete()

    def test_set_file_type_to_sqlite_invalid_file(self):
        # here we are using an invalid sqlite file for setting it
        # to TimeSeries file type which should fail
        self.sqlite_file_obj = open(self.sqlite_invalid_file, 'r')
        self._create_composite_resource()
        self._test_invalid_file()
        self.composite_resource.delete()

    def test_sqlite_metadata_update(self):
        # here we are using a valid sqlite file for setting it
        # to TimeSeries file type which includes metadata extraction
        # then we are testing update of the file level metadata elements
        self.sqlite_file_obj = open(self.sqlite_file, 'r')
        self._create_composite_resource(title='Untitled Resource')

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
        # check that there is one GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

        # check that there is no TimeSeriesLogicalFile object
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 0)

        # set the sqlite file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # test updating site element
        site = logical_file.metadata.sites.filter(site_code='USU-LBR-Paradise').first()
        self.assertNotEqual(site, None)
        site_name = 'Little Bear River at McMurdy Hollow near Paradise, Utah'
        self.assertEqual(site.site_name, site_name)
        self.assertEqual(site.elevation_m, 1445)
        self.assertEqual(site.elevation_datum, 'NGVD29')
        self.assertEqual(site.site_type, 'Stream')

        site_name = 'Little Bear River at Logan, Utah'
        site_data = {'site_name': site_name, 'elevation_m': site.elevation_m,
                     'elevation_datum': site.elevation_datum, 'site_type': site.site_type}
        logical_file.metadata.update_element('Site', site.id, **site_data)
        site = logical_file.metadata.sites.filter(site_code='USU-LBR-Paradise').first()
        self.assertEqual(site.site_name, site_name)

        # updating site lat/long should update the resource coverage as well as file level coverage
        box_coverage = self.composite_resource.metadata.coverages.all().filter(type='box').first()
        self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(box_coverage.value['northlimit'], 41.718473)
        self.assertEqual(box_coverage.value['eastlimit'], -111.799324)
        self.assertEqual(box_coverage.value['southlimit'], 41.495409)
        self.assertEqual(box_coverage.value['westlimit'], -111.946402)

        box_coverage = logical_file.metadata.spatial_coverage
        self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(box_coverage.value['northlimit'], 41.718473)
        self.assertEqual(box_coverage.value['eastlimit'], -111.799324)
        self.assertEqual(box_coverage.value['southlimit'], 41.495409)
        self.assertEqual(box_coverage.value['westlimit'], -111.946402)

        site_data['latitude'] = 40.7896
        logical_file.metadata.update_element('Site', site.id, **site_data)
        site = logical_file.metadata.sites.filter(site_code='USU-LBR-Paradise').first()
        self.assertEqual(site.latitude, 40.7896)

        # test that resource level coverage got updated
        box_coverage = self.composite_resource.metadata.coverages.all().filter(type='box').first()
        self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(box_coverage.value['northlimit'], 41.718473)
        self.assertEqual(box_coverage.value['eastlimit'], -111.799324)
        # this is the changed value for the southlimit as a result of changing the sit latitude
        self.assertEqual(box_coverage.value['southlimit'], 40.7896)
        self.assertEqual(box_coverage.value['westlimit'], -111.946402)

        # test that file level coverage got updated
        box_coverage = logical_file.metadata.spatial_coverage
        self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(box_coverage.value['northlimit'], 41.718473)
        self.assertEqual(box_coverage.value['eastlimit'], -111.799324)
        # this is the changed value for the southlimit as a result of changing the sit latitude
        self.assertEqual(box_coverage.value['southlimit'], 40.7896)
        self.assertEqual(box_coverage.value['westlimit'], -111.946402)

        # TODO: Test update of the rest of the time series metadata elements

        self.composite_resource.delete()

    def _create_composite_resource(self, title='Test Time series File Type Metadata'):
        uploaded_file = UploadedFile(file=self.sqlite_file_obj,
                                     name=os.path.basename(self.sqlite_file_obj.name))

        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title=title,
            files=(uploaded_file,)
        )

        # set the generic logical file as part of resource post create signal
        resource_post_create_actions(resource=self.composite_resource, user=self.user,
                                     metadata=self.composite_resource.metadata)

    def _test_invalid_file(self):
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is associated with the generic logical file
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")

        # trying to set this invalid tif file to NetCDF file type should raise
        # ValidationError
        with self.assertRaises(ValidationError):
            TimeSeriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)

        # test that the invalid file did not get deleted
        self.assertEqual(self.composite_resource.files.all().count(), 1)

        # check that the resource file is not associated with generic logical file
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
