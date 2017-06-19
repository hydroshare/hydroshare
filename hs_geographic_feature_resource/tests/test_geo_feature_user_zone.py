from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.conf import settings

from hs_core import hydroshare
from hs_core.testing import TestCaseCommonUtilities


class TestGeoFeature(TestCaseCommonUtilities, TransactionTestCase):
    def setUp(self):
        super(TestGeoFeature, self).setUp()
        if not super(TestGeoFeature, self).is_federated_irods_available():
            return
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
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
        self.valid_file_name = 'states_required_files.zip'
        self.valid_file = 'hs_geographic_feature_resource/tests/{}'.format(self.valid_file_name)
        self.valid_file_name2 = 'gis.osm_adminareas_v06_all_files.zip'
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

        self.resGeoFeature = hydroshare.create_resource(
            resource_type=resource_type,
            owner=self.user,
            title=res_title,
            files=res_upload_files,
            source_names=[fed_test_file_full_path],
            fed_res_path='',
            move=False,
            metadata=[])

        # uploaded file validation and metadata extraction happens in post resource
        # creation handler
        hydroshare.utils.resource_post_create_actions(resource=self.resGeoFeature, user=self.user,
                                                      metadata=[])

        # check that the resource has 3 files
        self.assertEqual(self.resGeoFeature.files.count(), 3)

        # test extracted metadata

        # there should not be any resource level coverage
        self.assertEqual(self.resGeoFeature.metadata.coverages.count(), 0)
        self.assertNotEqual(self.resGeoFeature.metadata.geometryinformation, None)
        self.assertEqual(self.resGeoFeature.metadata.geometryinformation.featureCount, 51)
        self.assertEqual(self.resGeoFeature.metadata.geometryinformation.geometryType,
                         "MULTIPOLYGON")

        self.assertNotEqual(self.resGeoFeature.metadata.originalcoverage, None)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.datum,
                         'unknown')
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.projection_name,
                         'unknown')
        self.assertGreater(len(self.resGeoFeature.metadata.originalcoverage.projection_string), 0)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.unit, 'unknown')
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.eastlimit, -66.9692712587578)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.northlimit, 71.406235393967)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.southlimit, 18.921786345087)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.westlimit,
                         -178.217598362366)

        # test that all files get deleted and extracted metadata gets deleted when one of the
        # required files get deleted
        shp_res_file = [f for f in self.resGeoFeature.files.all() if f.extension == '.shp'][0]
        hydroshare.delete_resource_file(self.resGeoFeature.short_id, shp_res_file.id,
                                        self.user)
        # check that the resource has no files
        self.assertEqual(self.resGeoFeature.files.count(), 0)

        # test metadata extraction with a valid file being added coming from user zone space
        res_add_files = []
        fed_test_add_file_full_path = '/{zone}/home/{username}/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, username=self.user.username,
            fname=self.valid_file_name2)

        hydroshare.utils.resource_file_add_process(resource=self.resGeoFeature,
                                                   files=res_add_files,
                                                   user=self.user,
                                                   source_names=[fed_test_add_file_full_path])

        # check that the resource has 15 files
        self.assertEqual(self.resGeoFeature.files.count(), 15)

        # test extracted metadata
        self.assertEqual(self.resGeoFeature.metadata.fieldinformations.all().count(), 7)
        self.assertEqual(self.resGeoFeature.metadata.geometryinformation.featureCount, 87)
        self.assertEqual(self.resGeoFeature.metadata.geometryinformation.geometryType, "POLYGON")
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.datum, 'WGS_1984')
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.eastlimit -
                            3.4520493) < self.allowance)
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.northlimit -
                            45.0466382) < self.allowance)
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.southlimit -
                            42.5732416) < self.allowance)
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.westlimit -
                            (-0.3263017)) < self.allowance)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.unit, 'Degree')
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.projection_name,
                         'GCS_WGS_1984')

        self.resGeoFeature.delete()
