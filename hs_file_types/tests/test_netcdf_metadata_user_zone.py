from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.conf import settings

from hs_core import hydroshare
from hs_core.hydroshare.utils import resource_post_create_actions
from hs_core.testing import TestCaseCommonUtilities
from utils import assert_netcdf_file_type_metadata
from hs_file_types.models import NetCDFLogicalFile, GenericLogicalFile


class NetCDFFileTypeMetaDataTest(TestCaseCommonUtilities, TransactionTestCase):
    def setUp(self):
        super(NetCDFFileTypeMetaDataTest, self).setUp()
        if not super(NetCDFFileTypeMetaDataTest, self).is_federated_irods_available():
            return

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
        if not super(NetCDFFileTypeMetaDataTest, self).is_federated_irods_available():
            return
        super(NetCDFFileTypeMetaDataTest, self).delete_irods_user_in_user_zone()

    def test_nc_set_file_type_to_netcdf(self):
        # only do federation testing when REMOTE_USE_IRODS is True and irods docker containers
        # are set up properly
        if not super(NetCDFFileTypeMetaDataTest, self).is_federated_irods_available():
            return

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
            metadata=[]
        )

        # test resource is created on federated zone
        self.assertNotEqual(self.composite_resource.resource_federation_path, '')

        # set the logical file -which get sets as part of the post resource creation signal
        resource_post_create_actions(resource=self.composite_resource, user=self.user,
                                     metadata=self.composite_resource.metadata)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
        # check that there is one GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 1)
        fed_file_path = "data/contents/{}".format(self.netcdf_file_name)
        self.assertEqual(res_file.root_path, fed_file_path)

        # set the tif file to NetCDF file type
        NetCDFLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)

        # test extracted netcdf file type metadata
        assert_netcdf_file_type_metadata(self, res_title)
