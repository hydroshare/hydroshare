import os

from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.conf import settings

from hs_core import hydroshare
from hs_core.testing import TestCaseCommonUtilities
from utils import assert_netcdf_file_type_metadata
from hs_file_types.models import NetCDFLogicalFile


class NetCDFFileTypeMetaDataTest(TestCaseCommonUtilities, TransactionTestCase):
    def setUp(self):
        super(NetCDFFileTypeMetaDataTest, self).setUp()
        super(NetCDFFileTypeMetaDataTest, self).assert_federated_irods_available()

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        super(NetCDFFileTypeMetaDataTest, self).create_irods_user_in_user_zone()

        self.netcdf_file_name = 'netcdf_valid.nc'
        self.netcdf_file = 'hs_file_types/tests/{}'.format(self.netcdf_file_name)

        # transfer this valid tif file to user zone space for testing
        # only need to test that netcdf file stored in iRODS user zone space can be used to create a
        # composite resource and metadata can be extracted when the file type is set to netcdf file
        # type.
        # Other detailed tests don't need to be retested for irods user zone space scenario since
        # as long as the netcdf file in iRODS user zone space can be read with metadata extracted
        # correctly, other functionalities are done with the same common functions regardless of
        # where the netcdf file comes from, either from local disk or from a federated user zone
        irods_target_path = '/' + settings.HS_USER_IRODS_ZONE + '/home/' + self.user.username + '/'
        file_list_dict = {self.netcdf_file: irods_target_path + self.netcdf_file_name}
        super(NetCDFFileTypeMetaDataTest, self).save_files_to_user_zone(file_list_dict)

    def tearDown(self):
        super(NetCDFFileTypeMetaDataTest, self).tearDown()
        super(NetCDFFileTypeMetaDataTest, self).assert_federated_irods_available()
        super(NetCDFFileTypeMetaDataTest, self).delete_irods_user_in_user_zone()

    def test_nc_set_file_type_to_netcdf(self):
        super(NetCDFFileTypeMetaDataTest, self).assert_federated_irods_available()

        # here we are using a valid netcdf file for setting it
        # to NetCDF file type which includes metadata extraction
        fed_test_file_full_path = '/{zone}/home/{username}/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, username=self.user.username,
            fname=self.netcdf_file_name)
        res_upload_files = []
        fed_res_path = hydroshare.utils.get_federated_zone_home_path(fed_test_file_full_path)
        res_title = 'Federated Composite Resource NetCDF File Type Testing'
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
        base_file_name, _ = os.path.splitext(res_file.file_name)
        expected_folder_name = base_file_name
        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        fed_file_path = "{}/{}".format(self.composite_resource.file_path, self.netcdf_file_name)
        self.assertEqual(res_file.storage_path, fed_file_path)

        # set the nc file to NetCDF file type
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test extracted netcdf file type metadata
        assert_netcdf_file_type_metadata(self, res_title, aggr_folder=expected_folder_name)
