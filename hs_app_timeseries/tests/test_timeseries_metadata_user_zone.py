from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.conf import settings

from hs_core import hydroshare
from hs_core.hydroshare import utils
from hs_core.models import CoreMetaData
from hs_core.testing import TestCaseCommonUtilities


class TestTimeSeriesMetaData(TestCaseCommonUtilities, TransactionTestCase):
    def setUp(self):
        super(TestTimeSeriesMetaData, self).setUp()
        if not super(TestTimeSeriesMetaData, self).is_federated_irods_available():
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

        super(TestTimeSeriesMetaData, self).create_irods_user_in_user_zone()

        self.odm2_sqlite_file_name = 'ODM2_Multi_Site_One_Variable.sqlite'
        self.odm2_sqlite_file = 'hs_app_timeseries/tests/{}'.format(self.odm2_sqlite_file_name)
        # transfer this file to user zone space for testing. Only need to test that file stored in
        # iRODS user zone space can be used to create a time series resource with metadata
        # automatically extracted. Other relevant tests are adding a file to an existing resource,
        # deleting a file in a resource from iRODS user zone, and deleting a resource stored in
        # iRODS user zone. Other detailed tests don't need to be retested for irods user zone space
        # scenario since as long as the file in iRODS user zone space can be read with metadata
        # extracted correctly, other functionalities are done with the same common functions
        # regardless of where the file comes from, either from local disk or from a federated
        # user zone

        irods_target_path = '/' + settings.HS_USER_IRODS_ZONE + '/home/' + self.user.username + '/'
        file_list_dict = {}
        file_list_dict[self.odm2_sqlite_file] = irods_target_path + self.odm2_sqlite_file_name
        super(TestTimeSeriesMetaData, self).save_files_to_user_zone(file_list_dict)

    def tearDown(self):
        super(TestTimeSeriesMetaData, self).tearDown()
        if not super(TestTimeSeriesMetaData, self).is_federated_irods_available():
            return
        super(TestTimeSeriesMetaData, self).delete_irods_user_in_user_zone()

    def test_metadata_in_user_zone(self):
        # only do federation testing when REMOTE_USE_IRODS is True and irods docker containers
        # are set up properly
        if not super(TestTimeSeriesMetaData, self).is_federated_irods_available():
            return

        # test metadata extraction with resource creation with file coming from user zone space
        fed_test_file_full_path = '/{zone}/home/{username}/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, username=self.user.username,
            fname=self.odm2_sqlite_file_name)
        self.resTimeSeries = hydroshare.create_resource(
            resource_type='TimeSeriesResource',
            owner=self.user,
            title='My Test TimeSeries Resource',
            source_names=[fed_test_file_full_path],
            fed_copy_or_move='copy'
        )
        utils.resource_post_create_actions(resource=self.resTimeSeries, user=self.user, metadata=[])

        super(TestTimeSeriesMetaData, self).timeseries_metadata_extraction()

        # test that metadata is NOT deleted (except format element) on content file deletion
        # there should be one content file at this point
        self.assertEqual(self.resTimeSeries.files.all().count(), 1)
        # there should be one format element
        self.assertEqual(self.resTimeSeries.metadata.formats.all().count(), 1)

        hydroshare.delete_resource_file(self.resTimeSeries.short_id, self.odm2_sqlite_file_name,
                                        self.user)
        # there should be no content file
        self.assertEqual(self.resTimeSeries.files.all().count(), 0)

        # test the core metadata at this point
        self.assertNotEqual(self.resTimeSeries.metadata.title, None)

        # there should be an abstract element
        self.assertNotEqual(self.resTimeSeries.metadata.description, None)

        # there should be one creator element
        self.assertEqual(self.resTimeSeries.metadata.creators.all().count(), 1)

        # there should be one contributor element
        self.assertEqual(self.resTimeSeries.metadata.contributors.all().count(), 1)

        # there should be 2 coverage element -  point type and period type
        self.assertEqual(self.resTimeSeries.metadata.coverages.all().count(), 2)
        self.assertEqual(self.resTimeSeries.metadata.coverages.all().filter(type='box').count(), 1)
        self.assertEqual(self.resTimeSeries.metadata.coverages.all().filter(
            type='period').count(), 1)
        # there should be no format element
        self.assertEqual(self.resTimeSeries.metadata.formats.all().count(), 0)
        # there should be one subject element
        self.assertEqual(self.resTimeSeries.metadata.subjects.all().count(), 1)

        # testing extended metadata elements
        self.assertNotEqual(self.resTimeSeries.metadata.sites.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.variables.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.methods.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.processing_levels.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.time_series_results.all().count(), 0)

        self.assertNotEqual(self.resTimeSeries.metadata.cv_variable_names.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.cv_variable_types.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.cv_speciations.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.cv_site_types.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.cv_elevation_datums.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.cv_method_types.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.cv_statuses.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.cv_mediums.all().count(), 0)
        self.assertNotEqual(self.resTimeSeries.metadata.cv_aggregation_statistics.all().count(), 0)

        # test metadata extraction with a valid ODM2 sqlite file being added coming from user zone
        # space
        res_add_files = []
        utils.resource_file_add_pre_process(resource=self.resTimeSeries, files=res_add_files,
                                            user=self.user, extract_metadata=False,
                                            source_names=[fed_test_file_full_path])

        utils.resource_file_add_process(resource=self.resTimeSeries, files=res_add_files,
                                        user=self.user,
                                        extract_metadata=True,
                                        source_names=[fed_test_file_full_path])

        super(TestTimeSeriesMetaData, self).timeseries_metadata_extraction()

        # test metadata deletion when deleting a resource in user zone space
        # all metadata should get deleted when the resource get deleted
        self.assertEqual(CoreMetaData.objects.all().count(), 1)
        # delete resource
        hydroshare.delete_resource(self.resTimeSeries.short_id)
        self.assertEqual(CoreMetaData.objects.all().count(), 0)
