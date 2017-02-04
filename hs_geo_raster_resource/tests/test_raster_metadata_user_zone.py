from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.conf import settings

from hs_core import hydroshare
from hs_core.hydroshare import utils
from hs_core.models import CoreMetaData
from hs_core.testing import TestCaseCommonUtilities


class TestRasterMetaData(TestCaseCommonUtilities, TransactionTestCase):
    def setUp(self):
        super(TestRasterMetaData, self).setUp()
        if not super(TestRasterMetaData, self).is_federated_irods_available():
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

        super(TestRasterMetaData, self).create_irods_user_in_user_zone()

        self.raster_tif_file_name = 'raster_tif_valid.tif'
        self.raster_tif_file = 'hs_geo_raster_resource/tests/{}'.format(self.raster_tif_file_name)
        # transfer this valid tif file to user zone space for testing
        # only need to test that tif file stored in iRODS user zone space can be used to create a
        # raster resource with metadata automatically extracted. Other relevant tests are
        # adding a tif file to an existing resource, deleting a file in a raster resource from
        # iRODS user zone, and deleting a resource stored in iRODS user zone. Other detailed tests
        # don't need to be retested for irods user zone space scenario since as long as the tif
        # file in iRODS user zone space can be read with metadata extracted correctly, other
        # functionalities are done with the same common functions regardless of where the tif file
        # comes from, either from local disk or from a federated user zone
        irods_target_path = '/' + settings.HS_USER_IRODS_ZONE + '/home/' + self.user.username + '/'
        file_list_dict = {self.raster_tif_file: irods_target_path + self.raster_tif_file_name}
        super(TestRasterMetaData, self).save_files_to_user_zone(file_list_dict)

    def tearDown(self):
        super(TestRasterMetaData, self).tearDown()
        if not super(TestRasterMetaData, self).is_federated_irods_available():
            return
        super(TestRasterMetaData, self).delete_irods_user_in_user_zone()

    def test_metadata_in_user_zone(self):
        # only do federation testing when REMOTE_USE_IRODS is True and irods docker containers
        # are set up properly
        if not super(TestRasterMetaData, self).is_federated_irods_available():
            return
        # test metadata extraction with resource creation with tif file coming from user zone space
        fed_test_file_full_path = '/{zone}/home/{username}/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, username=self.user.username,
            fname=self.raster_tif_file_name)
        res_upload_files = []
        fed_res_path = hydroshare.utils.get_federated_zone_home_path(fed_test_file_full_path)

        self.resRaster = hydroshare.create_resource(
            'RasterResource',
            self.user,
            'My Test Raster Resource',
            files=res_upload_files,
            fed_res_file_names=[fed_test_file_full_path],
            fed_res_path=fed_res_path,
            fed_copy_or_move='copy',
            metadata=[])

        # raster file validation and metadata extraction in post resource creation signal handler
        utils.resource_post_create_actions(resource=self.resRaster, user=self.user,
                                           metadata=[])
        super(TestRasterMetaData, self).raster_metadata_extraction()

        # test metadata is deleted after content file is deleted in user zone space
        # there should be 2 content file: tif file and vrt file at this point
        self.assertEqual(self.resRaster.files.all().count(), 2)

        # there should be 2 format elements
        self.assertEqual(self.resRaster.metadata.formats.all().count(), 2)
        self.assertEqual(self.resRaster.metadata.formats.all().filter(
            value='application/vrt').count(), 1)
        self.assertEqual(self.resRaster.metadata.formats.all().filter(
            value='image/tiff').count(), 1)

        # delete content file now
        hydroshare.delete_resource_file(self.resRaster.short_id, self.raster_tif_file_name,
                                        self.user)

        # there should be no content file
        self.assertEqual(self.resRaster.files.all().count(), 0)

        # there should be a title element
        self.assertNotEqual(self.resRaster.metadata.title, None)

        # there should be no abstract element
        self.assertEqual(self.resRaster.metadata.description, None)

        # there should be 1 creator element
        self.assertEqual(self.resRaster.metadata.creators.all().count(), 1)

        # there should be no contributor element
        self.assertEqual(self.resRaster.metadata.contributors.all().count(), 0)

        # there should be no coverage element
        self.assertEqual(self.resRaster.metadata.coverages.all().count(), 0)

        # there should be no format element
        self.assertEqual(self.resRaster.metadata.formats.all().count(), 0)

        # there should be no subject element
        self.assertEqual(self.resRaster.metadata.subjects.all().count(), 0)

        # testing extended metadata elements - there should be no extended metadata elements
        # at this point
        self.assertEqual(self.resRaster.metadata.originalCoverage, None)
        self.assertEqual(self.resRaster.metadata.cellInformation, None)
        self.assertEqual(self.resRaster.metadata.bandInformations.count(), 0)

        # test metadata extraction with a valid tif file being added coming from user zone space
        res_add_files = []
        # file validation and metadata extraction happen during post file add signal handler
        utils.resource_file_add_process(resource=self.resRaster,
                                        files=res_add_files,
                                        user=self.user,
                                        fed_res_file_names=[fed_test_file_full_path])
        super(TestRasterMetaData, self).raster_metadata_extraction()

        # test metadata deletion when deleting a resource in user zone space
        self.assertEqual(CoreMetaData.objects.all().count(), 1)

        # delete resource
        hydroshare.delete_resource(self.resRaster.short_id)

        # resource core metadata is deleted after resource deletion
        self.assertEqual(CoreMetaData.objects.all().count(), 0)

        # test adding file from user zone to existing empty resource in hydroshare zone
        # even there is no file uploaded to resource initially, there are default extended
        # automatically metadata created
        _, _, metadata, _ = utils.resource_pre_create_actions(
            resource_type='RasterResource',
            resource_title='My Test Raster Resource',
            page_redirect_url_key=None, metadata=None, )
        self.resRaster = hydroshare.create_resource(
            resource_type='RasterResource',
            owner=self.user,
            title='My Test Raster Resource',
            metadata=metadata
        )
        # test metadata extraction with a valid tif file being added coming from user zone space
        # file validation and metadata extraction happen during post file add signal handler
        utils.resource_file_add_process(resource=self.resRaster,
                                        files=[],
                                        user=self.user,
                                        fed_res_file_names=[fed_test_file_full_path])
        super(TestRasterMetaData, self).raster_metadata_extraction()

        # there should be 2 content file: tif file and vrt file at this point
        self.assertEqual(self.resRaster.files.all().count(), 2)
        # delete resource
        hydroshare.delete_resource(self.resRaster.short_id)
        # resource core metadata is deleted after resource deletion
        self.assertEqual(CoreMetaData.objects.all().count(), 0)