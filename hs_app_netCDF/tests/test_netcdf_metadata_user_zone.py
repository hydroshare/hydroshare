from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.conf import settings

from hs_core import hydroshare
from hs_core.hydroshare import utils
from hs_core.models import CoreMetaData
from hs_core.testing import TestCaseCommonUtilities
from django_irods.storage import IrodsStorage


class TestNetcdfMetaData(TestCaseCommonUtilities, TransactionTestCase):
    def setUp(self):
        super(TestNetcdfMetaData, self).setUp()
        if not settings.REMOTE_USE_IRODS or settings.HS_USER_ZONE_HOST != 'users.local.org' \
                or settings.IRODS_HOST != 'data.local.org':
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

        super(TestNetcdfMetaData, self).create_irods_user_in_user_zone()

        self.netcdf_file_name = 'netcdf_valid.nc'
        self.netcdf_file = 'hs_app_netCDF/tests/{}'.format(self.netcdf_file_name)

        # transfer this valid netCDF file to user zone space for testing.
        # only need to test that netCDF file stored in iRODS user zone space can be used to create
        # a netcdf resource with metadata automatically extracted. Other relevant tests are
        # adding a netCDF file to an existing resource, deleting a file in a netCDF resource from
        # iRODS user zone, and deleting a resource stored in iRODS user zone. Other detailed tests
        # don't need to be retested for irods user zone space scenario since as long as the netCDF
        # file in iRODS user zone space can be read with metadata extracted correctly, other
        # functionalities are done with the same common functions regardless of where the netCDF
        # file comes from, either from local disk or from a federated user zone
        self.irods_storage = IrodsStorage('federated')
        irods_target_path = '/' + settings.HS_USER_IRODS_ZONE + '/home/' + self.user.username + '/'
        self.irods_storage.saveFile(self.netcdf_file,
                                    irods_target_path + self.netcdf_file_name)

    def tearDown(self):
        super(TestNetcdfMetaData, self).tearDown()
        if not settings.REMOTE_USE_IRODS or settings.HS_USER_ZONE_HOST != 'users.local.org' \
                or settings.IRODS_HOST != 'data.local.org':
            return
        super(TestNetcdfMetaData, self).delete_irods_user_in_user_zone()

    def test_metadata_in_user_zone(self):
        # only do federation testing when REMOTE_USE_IRODS is True and irods docker containers
        # are set up properly
        if not settings.REMOTE_USE_IRODS or settings.HS_USER_ZONE_HOST != 'users.local.org' \
                or settings.IRODS_HOST != 'data.local.org':
            return

        # test metadata extraction with resource creation with nc file coming from user zone space
        fed_test_file_full_path = '/{zone}/home/{username}/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, username=self.user.username,
            fname=self.netcdf_file_name)
        res_upload_files = []
        _, _, metadata, fed_res_path = utils.resource_pre_create_actions(
            resource_type='NetcdfResource',
            resource_title='Snow water equivalent estimation at TWDEF site from Oct 2009 to June '
                           '2010',
            page_redirect_url_key=None,
            files=res_upload_files,
            fed_res_file_names=[fed_test_file_full_path])
        self.resNetcdf = hydroshare.create_resource(
            'NetcdfResource',
            self.user,
            'Snow water equivalent estimation at TWDEF site from Oct 2009 to June 2010',
            files=res_upload_files,
            fed_res_file_names=[fed_test_file_full_path],
            fed_res_path=fed_res_path[0] if len(fed_res_path) == 1 else '',
            fed_copy_or_move='copy',
            metadata=metadata)
        super(TestNetcdfMetaData, self).netcdf_metadata_extraction()

        # test metadata is deleted after content file is deleted in user zone space
        # there should be 2 content files at this point
        self.assertEqual(self.resNetcdf.files.all().count(), 2)

        # there should be 2 format elements
        self.assertEqual(self.resNetcdf.metadata.formats.all().count(), 2)

        # delete content file now
        hydroshare.delete_resource_file(self.resNetcdf.short_id, self.netcdf_file_name, self.user)

        # there should no content file
        self.assertEqual(self.resNetcdf.files.all().count(), 0)

        # there should be a title element
        self.assertNotEqual(self.resNetcdf.metadata.title, None)

        # there should be abstract element
        self.assertNotEqual(self.resNetcdf.metadata.description, None)

        # there should be 2 creator element
        self.assertEqual(self.resNetcdf.metadata.creators.all().count(), 2)

        # there should be 1 contributor element
        self.assertEqual(self.resNetcdf.metadata.contributors.all().count(), 1)

        # there should be no coverage element
        self.assertEqual(self.resNetcdf.metadata.coverages.all().count(), 0)

        # there should be no format element
        self.assertEqual(self.resNetcdf.metadata.formats.all().count(), 0)

        # there should be subject element
        self.assertNotEqual(self.resNetcdf.metadata.subjects.all().count(), 0)

        # testing extended metadata elements
        self.assertEqual(self.resNetcdf.metadata.ori_coverage.all().count(), 0)
        self.assertEqual(self.resNetcdf.metadata.variables.all().count(), 0)

        # test metadata extraction with a valid nc file being added coming from user zone space
        res_add_files = []
        utils.resource_file_add_pre_process(resource=self.resNetcdf,
                                            files=res_add_files,
                                            user=self.user,
                                            fed_res_file_names=[fed_test_file_full_path])
        utils.resource_file_add_process(resource=self.resNetcdf,
                                        files=res_add_files,
                                        user=self.user,
                                        fed_res_file_names=[fed_test_file_full_path])

        super(TestNetcdfMetaData, self).netcdf_metadata_extraction()
        self.assertEqual(CoreMetaData.objects.all().count(), 1)
        # delete resource
        hydroshare.delete_resource(self.resNetcdf.short_id)
        self.assertEqual(CoreMetaData.objects.all().count(), 0)
