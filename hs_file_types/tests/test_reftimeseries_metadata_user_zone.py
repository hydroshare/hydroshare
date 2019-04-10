import os

from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.conf import settings

from hs_core import hydroshare
from hs_core.testing import TestCaseCommonUtilities
from utils import assert_ref_time_series_file_type_metadata
from hs_file_types.models import RefTimeseriesLogicalFile


class RefTimeSeriesFileTypeMetaDataTest(TestCaseCommonUtilities, TransactionTestCase):
    def setUp(self):
        super(RefTimeSeriesFileTypeMetaDataTest, self).setUp()
        super(RefTimeSeriesFileTypeMetaDataTest, self).assert_federated_irods_available()

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        super(RefTimeSeriesFileTypeMetaDataTest, self).create_irods_user_in_user_zone()

        self.refts_file_name = 'multi_sites_formatted_version1.0.refts.json'
        self.refts_file = 'hs_file_types/tests/{}'.format(self.refts_file_name)

        # transfer this valid tif file to user zone space for testing
        # only need to test that netcdf file stored in iRODS user zone space can be used to create a
        # composite resource and metadata can be extracted when the file type is set to netcdf file
        # type.
        # Other detailed tests don't need to be retested for irods user zone space scenario since
        # as long as the netcdf file in iRODS user zone space can be read with metadata extracted
        # correctly, other functionalities are done with the same common functions regardless of
        # where the netcdf file comes from, either from local disk or from a federated user zone
        irods_target_path = '/' + settings.HS_USER_IRODS_ZONE + '/home/' + self.user.username + '/'
        file_list_dict = {self.refts_file: irods_target_path + self.refts_file_name}
        super(RefTimeSeriesFileTypeMetaDataTest, self).save_files_to_user_zone(file_list_dict)

    def tearDown(self):
        super(RefTimeSeriesFileTypeMetaDataTest, self).tearDown()
        super(RefTimeSeriesFileTypeMetaDataTest, self).assert_federated_irods_available()
        super(RefTimeSeriesFileTypeMetaDataTest, self).delete_irods_user_in_user_zone()

    def test_refts_set_file_type_to_reftimeseries(self):
        super(RefTimeSeriesFileTypeMetaDataTest, self).assert_federated_irods_available()

        # here we are using a valid ref time series for setting it
        # to RefTimeseries file type which includes metadata extraction
        fed_test_file_full_path = '/{zone}/home/{username}/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, username=self.user.username,
            fname=self.refts_file_name)
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

        fed_file_path = "data/contents/{}".format(self.refts_file_name)
        self.assertEqual(os.path.join('data', 'contents', res_file.short_path), fed_file_path)

        # set the tif file to RefTimeseries file type
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        # test that the content of the json file is same is what we have
        # saved in json_file_content field of the file metadata object
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.metadata.json_file_content,
                         res_file.fed_resource_file.read())

        # test extracted ref time series file type metadata
        assert_ref_time_series_file_type_metadata(self)
        self.composite_resource.delete()
