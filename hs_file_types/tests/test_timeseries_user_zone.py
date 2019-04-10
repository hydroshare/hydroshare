import os

from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.conf import settings

from hs_core import hydroshare
from hs_core.testing import TestCaseCommonUtilities
from utils import assert_time_series_file_type_metadata
from hs_file_types.models import TimeSeriesLogicalFile


class TimeSeriesFileTypeTest(TestCaseCommonUtilities, TransactionTestCase):
    def setUp(self):
        super(TimeSeriesFileTypeTest, self).setUp()
        super(TimeSeriesFileTypeTest, self).assert_federated_irods_available()

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        super(TimeSeriesFileTypeTest, self).create_irods_user_in_user_zone()

        self.sqlite_file_name = 'ODM2_Multi_Site_One_Variable.sqlite'
        self.sqlite_file = 'hs_file_types/tests/data/{}'.format(self.sqlite_file_name)

        # transfer this valid sqlite file to user zone space for testing
        # only need to test that sqlite file stored in iRODS user zone space can be used to create a
        # composite resource and metadata can be extracted when the file type is set to timeseries
        # file type.
        # Other detailed tests don't need to be retested for irods user zone space scenario since
        # as long as the sqlite file in iRODS user zone space can be read with metadata extracted
        # correctly, other functionalities are done with the same common functions regardless of
        # where the sqlite file comes from, either from local disk or from a federated user zone
        irods_target_path = '/' + settings.HS_USER_IRODS_ZONE + '/home/' + self.user.username + '/'
        file_list_dict = {self.sqlite_file: irods_target_path + self.sqlite_file_name}
        super(TimeSeriesFileTypeTest, self).save_files_to_user_zone(file_list_dict)

    def tearDown(self):
        super(TimeSeriesFileTypeTest, self).tearDown()
        super(TimeSeriesFileTypeTest, self).assert_federated_irods_available()

        super(TimeSeriesFileTypeTest, self).delete_irods_user_in_user_zone()

    def test_nc_set_file_type_to_netcdf(self):
        # only do federation testing when REMOTE_USE_IRODS is True and irods docker containers
        # are set up properly
        super(TimeSeriesFileTypeTest, self).assert_federated_irods_available()

        # here we are using a valid netcdf file for setting it
        # to NetCDF file type which includes metadata extraction
        fed_test_file_full_path = '/{zone}/home/{username}/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, username=self.user.username,
            fname=self.sqlite_file_name)
        res_upload_files = []
        fed_res_path = hydroshare.utils.get_federated_zone_home_path(fed_test_file_full_path)
        res_title = 'Untitled resource'
        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title=res_title,
            files=res_upload_files,
            source_names=[fed_test_file_full_path],
            fed_res_path=fed_res_path,
            move=False,
            metadata=[],
            auto_aggregate=False
        )

        # test resource is created on federated zone
        self.assertNotEqual(self.composite_resource.resource_federation_path, '')

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        fed_file_path = "{}/{}".format(self.composite_resource.file_path, self.sqlite_file_name)
        self.assertEqual(res_file.storage_path, fed_file_path)

        # set the sqlite file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # test extracted metadata
        res_file = self.composite_resource.files.first()
        base_file_name, _ = os.path.splitext(res_file.file_name)
        expected_file_folder = base_file_name
        assert_time_series_file_type_metadata(self, expected_file_folder=expected_file_folder)
