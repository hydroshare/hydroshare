from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from hs_core.models import ResourceFile, CoreMetaData
from hs_core import hydroshare
from hs_core.testing import TestCaseCommonUtilities


class TestGeoFeature(TestCaseCommonUtilities, TransactionTestCase):
    def setUp(self):
        super(TestGeoFeature, self).setUp()
        if not super(TestGeoFeature, self).is_federated_irods_available():
            return
        self.group, _ = Group.objects.get_or_create(name='xDCIShare Author')
        self.user = hydroshare.create_account(
            'zhiyu.li@byu.edu',
            username='drew',
            first_name='Zhiyu',
            last_name='Li',
            superuser=False,
            groups=[self.group]
        )
        super(TestGeoFeature, self).create_irods_user_in_user_zone()

        self.allowance = 0.00001

        # transfer this valid zip file to user zone space for testing.
        # only need to test that file stored in iRODS user zone space can be used to create
        # a geo-feature resource with metadata automatically extracted. Other relevant tests are
        # adding a file to an existing resource, deleting a file in a resource from
        # iRODS user zone, and deleting a resource stored in iRODS user zone. Other detailed tests
        # don't need to be retested for irods user zone space scenario since as long as the
        # file in iRODS user zone space can be read with metadata extracted correctly, other
        # functionalities are done with the same common functions regardless of where the
        # file comes from, either from local disk or from a federated user zone
        irods_target_path = '/' + settings.HS_USER_IRODS_ZONE + '/home/' + self.user.username + '/'
        self.valid_file_name = 'states_shp_sample.zip'
        self.valid_file = 'hs_geographic_feature_resource/tests/{}'.format(self.valid_file_name)
        self.valid_file_name2 = 'gis.osm_adminareas_v06_with_folder.zip'
        self.valid_file2 = 'hs_geographic_feature_resource/tests/{}'.format(self.valid_file_name2)
        file_list_dict = {}
        file_list_dict[self.valid_file] = irods_target_path + self.valid_file_name
        file_list_dict[self.valid_file2] = irods_target_path + self.valid_file_name2
        super(TestGeoFeature, self).save_files_to_user_zone(file_list_dict)

    def tearDown(self):
        super(TestGeoFeature, self).tearDown()
        if not super(TestGeoFeature, self).is_federated_irods_available():
            return
        super(TestGeoFeature, self).delete_irods_user_in_user_zone()

    def test_metadata_in_user_zone(self):
        # only do federation testing when REMOTE_USE_IRODS is True and irods docker containers
        # are set up properly
        if not super(TestGeoFeature, self).is_federated_irods_available():
            return
        # test metadata extraction with resource creation with file coming from user zone space
        resource_type = "GeographicFeatureResource"
        fed_test_file_full_path = '/{zone}/home/{username}/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, username=self.user.username,
            fname=self.valid_file_name)
        res_upload_files = []
        res_title = "test title"
        url_key = "page_redirect_url"
        page_url_dict, res_title, metadata, fed_res_path = \
            hydroshare.utils.resource_pre_create_actions(
                resource_type=resource_type, files=res_upload_files, resource_title=res_title,
                page_redirect_url_key=url_key, source_names=[fed_test_file_full_path])

        for item_dict in metadata:
            self.assertEqual(len(item_dict.keys()), 1)
            key = item_dict.keys()[0]
            if key == "OriginalFileInfo":
                self.assertEqual(item_dict["OriginalFileInfo"]["baseFilename"], "states")
                self.assertEqual(item_dict["OriginalFileInfo"]["fileCount"], 7)
                self.assertEqual(item_dict["OriginalFileInfo"]["fileType"], "ZSHP")
            elif key == "field_info_array":
                self.assertEqual(len(item_dict["field_info_array"]), 5)
            elif key == "geometryinformation":
                self.assertEqual(item_dict["geometryinformation"]["featureCount"], 51)
                self.assertEqual(item_dict["geometryinformation"]["geometryType"],
                                 "MULTIPOLYGON")
            elif key == "originalcoverage":
                self.assertEqual(item_dict["originalcoverage"]['datum'],
                                 'North_American_Datum_1983')
                self.assertEqual(item_dict["originalcoverage"]['eastlimit'], -66.96927125875777)
                self.assertEqual(item_dict["originalcoverage"]['northlimit'], 71.40623539396698)
                self.assertEqual(item_dict["originalcoverage"]['southlimit'], 18.92178634508703)
                self.assertEqual(item_dict["originalcoverage"]['westlimit'], -178.21759836236586)
                self.assertEqual(item_dict["originalcoverage"]['unit'], 'Degree')
                self.assertEqual(item_dict["originalcoverage"]['projection_name'],
                                 'GCS_North_American_1983')

        self.resGeoFeature = hydroshare.create_resource(
            resource_type=resource_type,
            owner=self.user,
            title=res_title,
            files=res_upload_files,
            source_names=[fed_test_file_full_path],
            fed_res_path=fed_res_path[0] if len(fed_res_path) == 1 else '',
            move=False,
            metadata=metadata)

        # test metadata is deleted after content file is deleted in user zone space
        for res_f_obj in ResourceFile.objects.filter(object_id=self.resGeoFeature.id):
            try:
                hydroshare.delete_resource_file(self.resGeoFeature.short_id, res_f_obj.short_path,
                                                self.user)
            # deleting one file may delete other relevant files as well, so ObjectDoesNotExist
            # exception is expected
            except ObjectDoesNotExist:
                continue
        self.assertEqual(ResourceFile.objects.filter(object_id=self.resGeoFeature.id).count(), 0)
        self.assertEqual(self.resGeoFeature.metadata.geometryinformation.all().count(), 0)
        self.assertEqual(self.resGeoFeature.metadata.fieldinformation.all().count(), 0)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.all().count(), 0)

        # test metadata extraction with a valid file being added coming from user zone space
        res_add_files = []
        fed_test_add_file_full_path = '/{zone}/home/{username}/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, username=self.user.username,
            fname=self.valid_file_name2)
        hydroshare.utils.resource_file_add_pre_process(
            resource=self.resGeoFeature,
            files=res_add_files, user=self.user, source_names=[fed_test_add_file_full_path])
        hydroshare.utils.resource_file_add_process(resource=self.resGeoFeature,
                                                   files=res_add_files,
                                                   user=self.user,
                                                   source_names=[fed_test_add_file_full_path])

        self.assertNotEqual(self.resGeoFeature.metadata.originalfileinfo.all().first(), None)
        self.assertEqual(self.resGeoFeature.metadata.originalfileinfo.all().first().baseFilename,
                         "gis.osm_adminareas_v06")
        self.assertEqual(self.resGeoFeature.metadata.originalfileinfo.all().first().fileCount, 5)
        self.assertEqual(self.resGeoFeature.metadata.originalfileinfo.all().first().
                         fileType, "ZSHP")
        self.assertEqual(self.resGeoFeature.metadata.fieldinformation.all().count(), 7)
        self.assertEqual(self.resGeoFeature.metadata.geometryinformation.all().
                         first().featureCount, 87)
        self.assertEqual(self.resGeoFeature.metadata.geometryinformation.all().
                         first().geometryType, "POLYGON")
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.all().first().datum,
                         'WGS_1984')
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.
                            all().first().eastlimit - 3.4520493) < self.allowance)
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.
                            all().first().northlimit - 45.0466382) < self.allowance)
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.
                            all().first().southlimit - 42.5732416) < self.allowance)
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.
                            all().first().westlimit - (-0.3263017)) < self.allowance)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.all().first().unit, 'Degree')
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.all().
                         first().projection_name, 'GCS_WGS_1984')
        self.assertEqual(CoreMetaData.objects.all().count(), 1)
        # delete resource
        hydroshare.delete_resource(self.resGeoFeature.short_id)
        self.assertEqual(CoreMetaData.objects.all().count(), 0)
