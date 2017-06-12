from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.conf import settings

from hs_core import hydroshare
from hs_core.hydroshare.utils import resource_post_create_actions
from hs_core.testing import TestCaseCommonUtilities
from utils import assert_geofeature_file_type_metadata
from hs_file_types.models import GeoFeatureLogicalFile, GenericLogicalFile, GeoFeatureFileMetaData


class GeoFeatureFileTypeMetaDataTest(TestCaseCommonUtilities, TransactionTestCase):
    def setUp(self):
        super(GeoFeatureFileTypeMetaDataTest, self).setUp()
        if not super(GeoFeatureFileTypeMetaDataTest, self).is_federated_irods_available():
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

        super(GeoFeatureFileTypeMetaDataTest, self).create_irods_user_in_user_zone()

        base_file_path = 'hs_file_types/tests/data/{}'
        self.zip_file_name = 'states_required_files.zip'
        self.zip_file = base_file_path.format(self.zip_file_name)

        # transfer this valid zip file to user zone space for testing
        # only need to test that the zip file stored in iRODS user zone space can be used to
        # create a composite resource and metadata can be extracted when the file type is set to
        # geo feature file type.
        # Other detailed tests don't need to be retested for irods user zone space scenario since
        # as long as the tif file in iRODS user zone space can be read with metadata extracted
        # correctly, other functionalities are done with the same common functions regardless of
        # where the tif file comes from, either from local disk or from a federated user zone
        irods_target_path = '/' + settings.HS_USER_IRODS_ZONE + '/home/' + self.user.username + '/'
        file_list_dict = {self.zip_file: irods_target_path + self.zip_file_name}
        super(GeoFeatureFileTypeMetaDataTest, self).save_files_to_user_zone(file_list_dict)

    def tearDown(self):
        super(GeoFeatureFileTypeMetaDataTest, self).tearDown()
        if not super(GeoFeatureFileTypeMetaDataTest, self).is_federated_irods_available():
            return
        super(GeoFeatureFileTypeMetaDataTest, self).delete_irods_user_in_user_zone()

    def test_zip_set_file_type_to_geo_feature(self):
        # only do federation testing when REMOTE_USE_IRODS is True and irods docker containers
        # are set up properly
        if not super(GeoFeatureFileTypeMetaDataTest, self).is_federated_irods_available():
            return

        # here we are using a valid zip file for setting it
        # to Geo Feature file type which includes metadata extraction
        fed_test_file_full_path = '/{zone}/home/{username}/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, username=self.user.username,
            fname=self.zip_file_name)
        res_upload_files = []
        fed_res_path = hydroshare.utils.get_federated_zone_home_path(fed_test_file_full_path)
        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Federated Composite Resource Raster File Type Testing',
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
        expected_folder_name = res_file.file_name[:-4]
        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
        # check that there is one GenericLogicalFile object
        self.assertEqual(GenericLogicalFile.objects.count(), 1)
        fed_file_path = "{}/data/contents/{}".format(self.composite_resource.root_path,
                                                     self.zip_file_name)
        self.assertEqual(res_file.storage_path, fed_file_path)

        # set the zip file to GeoFeatureFile type
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        # test file type and file type extracted metadata
        assert_geofeature_file_type_metadata(self, expected_folder_name)
        self.composite_resource.delete()
        # there should be no GeoFeatureLogicalFile object at this point
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 0)
        # there should be no GenericFileMetaData object at this point
        self.assertEqual(GeoFeatureFileMetaData.objects.count(), 0)
