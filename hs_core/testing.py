"""Test cases and utilities for hs_core module. See also ./tests folder."""

from dateutil import parser
import tempfile
import os

from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import TestCase, RequestFactory

from hs_core.models import ResourceFile
from hs_core.hydroshare import add_resource_files
from hs_core.views.utils import create_folder, move_or_rename_file_or_folder, zip_folder, \
    unzip_file, remove_folder
from hs_core.views.utils import run_ssh_command
from theme.models import UserProfile
from django_irods.icommands import SessionException
from django_irods.storage import IrodsStorage


class MockIRODSTestCaseMixin(object):
    """Mix in to allow for mock iRODS testing."""

    def setUp(self):
        """Set up iRODS patchers for testing of data bags, etc."""
        super(MockIRODSTestCaseMixin, self).setUp()
        # only mock up testing iRODS operations when local iRODS container is not used
        if settings.IRODS_HOST != 'data.local.org':
            from mock import patch
            self.irods_patchers = (
                patch("hs_core.hydroshare.hs_bagit.delete_files_and_bag"),
                patch("hs_core.hydroshare.hs_bagit.create_bag"),
                patch("hs_core.hydroshare.hs_bagit.create_bag_files"),
                patch("hs_core.tasks.create_bag_by_irods"),
                patch("hs_core.hydroshare.utils.copy_resource_files_and_AVUs"),
            )
            for patcher in self.irods_patchers:
                patcher.start()

    def tearDown(self):
        """Stop iRODS patchers."""
        if settings.IRODS_HOST != 'data.local.org':
            for patcher in self.irods_patchers:
                patcher.stop()
        super(MockIRODSTestCaseMixin, self).tearDown()


class TestCaseCommonUtilities(object):
    """Enable common utilities for iRODS testing."""
    def assert_federated_irods_available(self):
        """assert federated iRODS is available before proceeding with federation-related tests."""
        self.assertTrue(settings.REMOTE_USE_IRODS and
                        settings.HS_USER_ZONE_HOST == 'users.local.org' and
                        settings.IRODS_HOST == 'data.local.org',
                        "irods docker containers are not set up properly for federation testing")
        self.irods_fed_storage = IrodsStorage('federated')
        self.irods_storage = IrodsStorage()

    def create_irods_user_in_user_zone(self):
        """Create corresponding irods account in user zone."""
        try:
            exec_cmd = "{0} {1} {2}".format(settings.LINUX_ADMIN_USER_CREATE_USER_IN_USER_ZONE_CMD,
                                            self.user.username, self.user.username)
            output = run_ssh_command(host=settings.HS_USER_ZONE_HOST,
                                     uname=settings.LINUX_ADMIN_USER_FOR_HS_USER_ZONE,
                                     pwd=settings.LINUX_ADMIN_USER_PWD_FOR_HS_USER_ZONE,
                                     exec_cmd=exec_cmd)
            if output:
                if 'ERROR:' in output.upper():
                    # irods account failed to create
                    self.assertRaises(SessionException(-1, output, output))

            user_profile = UserProfile.objects.filter(user=self.user).first()
            user_profile.create_irods_user_account = True
            user_profile.save()
        except Exception as ex:
            self.assertRaises(SessionException(-1, ex.message, ex.message))

    def delete_irods_user_in_user_zone(self):
        """Delete irods test user in user zone."""
        try:
            exec_cmd = "{0} {1}".format(settings.LINUX_ADMIN_USER_DELETE_USER_IN_USER_ZONE_CMD,
                                        self.user.username)
            output = run_ssh_command(host=settings.HS_USER_ZONE_HOST,
                                     uname=settings.LINUX_ADMIN_USER_FOR_HS_USER_ZONE,
                                     pwd=settings.LINUX_ADMIN_USER_PWD_FOR_HS_USER_ZONE,
                                     exec_cmd=exec_cmd)
            if output:
                if 'ERROR:' in output.upper():
                    # there is an error from icommand run, report the error
                    self.assertRaises(SessionException(-1, output, output))

            user_profile = UserProfile.objects.filter(user=self.user).first()
            user_profile.create_irods_user_account = False
            user_profile.save()
        except Exception as ex:
            # there is an error from icommand run, report the error
            self.assertRaises(SessionException(-1, ex.message, ex.message))

    def save_files_to_user_zone(self, file_name_to_target_name_dict):
        """Save a list of files to iRODS user zone.

        :param file_name_to_target_name_dict: a dictionary in the form of {ori_file, target_file}
        where ori_file is the file to be save to, and the target_file is the full path file name
        in iRODS user zone to save ori_file to
        :return:
        """
        for file_name, target_name in file_name_to_target_name_dict.iteritems():
            self.irods_fed_storage.saveFile(file_name, target_name)

    def check_file_exist(self, irods_path):
        """Check whether the input irods_path exist in iRODS.

        :param irods_path: the iRODS path to check whether it exists or not
        :return: True if exist, False otherwise.
        """
        return self.irods_storage.exists(irods_path)

    def delete_directory(self, irods_path):
        """delete the input irods_path.
        :param irods_path: the iRODS path to be deleted
        :return:
        """
        self.irods_fed_storage.delete(irods_path)

    def verify_user_quota_usage_avu_in_user_zone(self, attname, qsize):
        '''
        Have to use LINUX_ADMIN_USER_FOR_HS_USER_ZONE with rodsadmin role to get user type AVU
        in user zone and verify its quota usage is set correctly
        :param attname: quota usage attribute name set on iRODS proxy user in user zone
        :param qsize: quota size (type string) to be verified to equal to the value set for attname.
        '''
        istorage = IrodsStorage()
        istorage.set_user_session(username=settings.LINUX_ADMIN_USER_FOR_HS_USER_ZONE,
                                  password=settings.LINUX_ADMIN_USER_PWD_FOR_HS_USER_ZONE,
                                  host=settings.HS_USER_ZONE_HOST,
                                  port=settings.IRODS_PORT,
                                  zone=settings.HS_USER_IRODS_ZONE,
                                  sess_id='user_proxy_session')

        uz_bagit_path = os.path.join('/', settings.HS_USER_IRODS_ZONE, 'home',
                                     settings.HS_IRODS_PROXY_USER_IN_USER_ZONE,
                                     settings.IRODS_BAGIT_PATH)
        get_qsize = istorage.getAVU(uz_bagit_path, attname)
        self.assertEqual(qsize, get_qsize)

    def resource_file_oprs(self):
        """Test common iRODS file operations.

        This is a common test utility function to be called by both regular folder operation
        testing and federated zone folder operation testing.
        Make sure the calling TestCase object has the following attributes defined before calling
        this method:
        self.res: resource that has been created that contains files listed in file_name_list
        self.user: owner of the resource
        self.file_name_list: a list of three file names that have been added to the res object
        self.test_file_1 needs to be present for the calling object for doing regular folder
        operations without involving federated zone so that the same opened file can be re-added
        to the resource for testing the case where zipping cannot overwrite existing file
        """
        user = self.user
        res = self.res
        file_name_list = self.file_name_list
        # create a folder, if folder is created successfully, no exception is raised, otherwise,
        # an iRODS exception will be raised which will be caught by the test runner and mark as
        # a test failure
        create_folder(res.short_id, 'data/contents/sub_test_dir')
        istorage = res.get_irods_storage()
        res_path = res.file_path
        store = istorage.listdir(res_path)
        self.assertIn('sub_test_dir', store[0], msg='resource does not contain created sub-folder')

        # rename the third file in file_name_list
        move_or_rename_file_or_folder(user, res.short_id,
                                      'data/contents/' + file_name_list[2],
                                      'data/contents/new_' + file_name_list[2])
        # move the first two files in file_name_list to the new folder
        move_or_rename_file_or_folder(user, res.short_id,
                                      'data/contents/' + file_name_list[0],
                                      'data/contents/sub_test_dir/' + file_name_list[0])
        move_or_rename_file_or_folder(user, res.short_id,
                                      'data/contents/' + file_name_list[1],
                                      'data/contents/sub_test_dir/' + file_name_list[1])
        updated_res_file_names = []
        for rf in ResourceFile.objects.filter(object_id=res.id):
            updated_res_file_names.append(rf.short_path)

        self.assertIn('new_' + file_name_list[2], updated_res_file_names,
                      msg="resource does not contain the updated file new_" + file_name_list[2])
        self.assertNotIn(file_name_list[2], updated_res_file_names,
                         msg='resource still contains the old file ' + file_name_list[2] +
                             ' after renaming')
        self.assertIn('sub_test_dir/' + file_name_list[0], updated_res_file_names,
                      msg='resource does not contain ' + file_name_list[0] + ' moved to a folder')
        self.assertNotIn(file_name_list[0], updated_res_file_names,
                         msg='resource still contains the old ' + file_name_list[0] +
                             'after moving to a folder')
        self.assertIn('sub_test_dir/' + file_name_list[1], updated_res_file_names,
                      msg='resource does not contain ' + file_name_list[1] +
                          'moved to a new folder')
        self.assertNotIn(file_name_list[1], updated_res_file_names,
                         msg='resource still contains the old ' + file_name_list[1] +
                             ' after moving to a folder')

        # zip the folder
        output_zip_fname, size = \
            zip_folder(user, res.short_id, 'data/contents/sub_test_dir',
                       'sub_test_dir.zip', True)
        self.assertGreater(size, 0, msg='zipped file has a size of 0')
        # Now resource should contain only two files: new_file3.txt and sub_test_dir.zip
        # since the folder is zipped into sub_test_dir.zip with the folder deleted
        self.assertEqual(res.files.all().count(), 2,
                         msg="resource file count didn't match-")

        # test unzip does not allow override of existing files
        # add an existing file in the zip to the resource
        if res.resource_federation_path:
            fed_test_file1_full_path = '/{zone}/home/{uname}/{fname}'.format(
                zone=settings.HS_USER_IRODS_ZONE, uname=user.username, fname=file_name_list[0])
            # TODO: why isn't this a method of resource?
            # TODO: Why do we repeat the resource_federation_path?
            add_resource_files(res.short_id, source_names=[fed_test_file1_full_path],
                               move=False)

        else:
            # TODO: Why isn't this a method of resource?
            add_resource_files(res.short_id, self.test_file_1)

        # TODO: use ResourceFile.create_folder, which doesn't require data/contents prefix
        create_folder(res.short_id, 'data/contents/sub_test_dir')

        # TODO: use ResourceFile.rename, which doesn't require data/contents prefix
        move_or_rename_file_or_folder(user, res.short_id,
                                      'data/contents/' + file_name_list[0],
                                      'data/contents/sub_test_dir/' + file_name_list[0])
        # Now resource should contain three files: file3_new.txt, sub_test_dir.zip, and file1.txt
        self.assertEqual(res.files.all().count(), 3, msg="resource file count didn't match")
        unzip_file(user, res.short_id, 'data/contents/sub_test_dir.zip', False)

        # Resource should still contain 5 files: file3_new.txt (2), sub_test_dir.zip,
        # and file1.txt (2)
        file_cnt = res.files.all().count()
        self.assertEqual(file_cnt, 5, msg="resource file count didn't match - " +
                                          str(file_cnt) + " != 5")

        # remove all files except the zippped file
        remove_folder(user, res.short_id, 'data/contents/sub_test_dir')
        remove_folder(user, res.short_id, 'data/contents/sub_test_dir-1')

        # Now resource should contain two files: file3_new.txt sub_test_dir.zip
        file_cnt = res.files.all().count()
        self.assertEqual(file_cnt, 2, msg="resource file count didn't match - " +
                                          str(file_cnt) + " != 2")
        unzip_file(user, res.short_id, 'data/contents/sub_test_dir.zip', True)
        # Now resource should contain three files: file1.txt, file2.txt, and file3_new.txt
        self.assertEqual(res.files.all().count(), 3, msg="resource file count didn't match")
        updated_res_file_names = []
        for rf in ResourceFile.objects.filter(object_id=res.id):
            updated_res_file_names.append(rf.short_path)
        self.assertNotIn('sub_test_dir.zip', updated_res_file_names,
                         msg="resource still contains the zip file after unzipping")
        self.assertIn('sub_test_dir/sub_test_dir/' + file_name_list[0], updated_res_file_names,
                      msg='resource does not contain unzipped file ' + file_name_list[0])
        self.assertIn('sub_test_dir/sub_test_dir/' + file_name_list[1], updated_res_file_names,
                      msg='resource does not contain unzipped file ' + file_name_list[1])
        self.assertIn('new_' + file_name_list[2], updated_res_file_names,
                      msg='resource does not contain unzipped file new_' + file_name_list[2])

        # rename a folder
        move_or_rename_file_or_folder(user, res.short_id,
                                      'data/contents/sub_test_dir/sub_test_dir',
                                      'data/contents/sub_dir')
        updated_res_file_names = []
        for rf in ResourceFile.objects.filter(object_id=res.id):
            updated_res_file_names.append(rf.short_path)

        self.assertNotIn('sub_test_dir/sub_test_dir/' + file_name_list[0], updated_res_file_names,
                         msg='resource still contains ' + file_name_list[0] +
                             ' in the old folder after renaming')
        self.assertIn('sub_dir/' + file_name_list[0], updated_res_file_names,
                      msg='resource does not contain ' + file_name_list[0] +
                          ' in the new folder after renaming')
        self.assertNotIn('sub_test_dir/sub_test_dir/' + file_name_list[1], updated_res_file_names,
                         msg='resource still contains ' + file_name_list[1] +
                             ' in the old folder after renaming')
        self.assertIn('sub_dir/' + file_name_list[1], updated_res_file_names,
                      msg='resource does not contain ' + file_name_list[1] +
                          ' in the new folder after renaming')

        # remove a folder
        # TODO: utilize ResourceFile.remove_folder instead. Takes a short path.
        remove_folder(user, res.short_id, 'data/contents/sub_dir')
        # Now resource only contains one file
        self.assertEqual(res.files.all().count(), 1, msg="resource file count didn't match")
        updated_res_file_names = []
        for rf in ResourceFile.objects.filter(object_id=res.id):
            updated_res_file_names.append(rf.short_path)

        self.assertEqual(len(updated_res_file_names), 1)
        self.assertEqual(updated_res_file_names[0], 'new_' + file_name_list[2])

    def raster_metadata_extraction(self):
        """Test raster metadata extraction.

        This is a common test utility function to be called by both regular raster metadata
        extraction testing and federated zone raster metadata extraction testing.
        Make sure the calling TestCase object has self.resRaster attribute defined before calling
        this method which is the raster resource that has been created containing valid raster
        files.
        """
        # there should be 2 content files
        self.assertEqual(self.resRaster.files.all().count(), 2)

        # test core metadata after metadata extraction
        extracted_title = "My Test Raster Resource"
        self.assertEqual(self.resRaster.metadata.title.value, extracted_title)

        # there should be 1 creator
        self.assertEqual(self.resRaster.metadata.creators.all().count(), 1)

        # there should be 1 coverage element - box type
        self.assertEqual(self.resRaster.metadata.coverages.all().count(), 1)
        self.assertEqual(self.resRaster.metadata.coverages.all().filter(type='box').count(), 1)

        box_coverage = self.resRaster.metadata.coverages.all().filter(type='box').first()
        self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(float(box_coverage.value['northlimit']), 42.11270614966863)
        self.assertEqual(float(box_coverage.value['eastlimit']), -111.45699925047542)
        self.assertEqual(float(box_coverage.value['southlimit']), 41.66222054591102)
        self.assertEqual(float(box_coverage.value['westlimit']), -111.81761887121905)

        # there should be 2 format elements
        self.assertEqual(self.resRaster.metadata.formats.all().count(), 2)
        self.assertEqual(self.resRaster.metadata.formats.all().filter(
            value='application/vrt').count(), 1)
        self.assertEqual(self.resRaster.metadata.formats.all().filter(
            value='image/tiff').count(), 1)

        # testing extended metadata element: original coverage
        ori_coverage = self.resRaster.metadata.originalCoverage
        self.assertNotEquals(ori_coverage, None)
        self.assertEqual(float(ori_coverage.value['northlimit']), 4662392.446916306)
        self.assertEqual(float(ori_coverage.value['eastlimit']), 461954.01909127034)
        self.assertEqual(float(ori_coverage.value['southlimit']), 4612592.446916306)
        self.assertEqual(float(ori_coverage.value['westlimit']), 432404.01909127034)
        self.assertEqual(ori_coverage.value['units'], 'meter')
        self.assertEqual(ori_coverage.value['projection'], "NAD83 / UTM zone 12N")
        self.assertEqual(ori_coverage.value['datum'], "North_American_Datum_1983")
        projection_string = u'PROJCS["NAD83 / UTM zone 12N",GEOGCS["NAD83",' \
                            u'DATUM["North_American_Datum_1983",' \
                            u'SPHEROID["GRS 1980",6378137,298.257222101,' \
                            u'AUTHORITY["EPSG","7019"]],' \
                            u'TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","6269"]],' \
                            u'PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],' \
                            u'UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],' \
                            u'AUTHORITY["EPSG","4269"]],PROJECTION["Transverse_Mercator"],' \
                            u'PARAMETER["latitude_of_origin",0],' \
                            u'PARAMETER["central_meridian",-111],' \
                            u'PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],' \
                            u'PARAMETER["false_northing",0],' \
                            u'UNIT["metre",1,AUTHORITY["EPSG","9001"]],' \
                            u'AXIS["Easting",EAST],AXIS["Northing",' \
                            u'NORTH],AUTHORITY["EPSG","26912"]]'
        self.assertEqual(ori_coverage.value['projection_string'], projection_string)

        # testing extended metadata element: cell information
        cell_info = self.resRaster.metadata.cellInformation
        self.assertEqual(cell_info.rows, 1660)
        self.assertEqual(cell_info.columns, 985)
        self.assertEqual(cell_info.cellSizeXValue, 30.0)
        self.assertEqual(cell_info.cellSizeYValue, 30.0)
        self.assertEqual(cell_info.cellDataType, 'Float32')

        # testing extended metadata element: band information
        self.assertEqual(self.resRaster.metadata.bandInformations.count(), 1)
        band_info = self.resRaster.metadata.bandInformations.first()
        self.assertEqual(band_info.noDataValue, '-3.40282346639e+38')
        self.assertEqual(band_info.maximumValue, '3031.44311523')
        self.assertEqual(band_info.minimumValue, '1358.33459473')

    def netcdf_metadata_extraction(self, expected_creators_count=1):
        """Test NetCDF metadata extraction.

        This is a common test utility function to be called by both regular netcdf metadata
        extraction testing and federated zone netCDF metadata extraction testing.
        Make sure the calling TestCase object has self.resNetcdf attribute defined before calling
        this method which is the netCDF resource that has been created containing valid netCDF
        files.
        """
        # there should 2 content file
        self.assertEqual(self.resNetcdf.files.all().count(), 2)

        # test core metadata after metadata extraction
        extracted_title = "Snow water equivalent estimation at TWDEF site from " \
                          "Oct 2009 to June 2010"
        self.assertEqual(self.resNetcdf.metadata.title.value, extracted_title)

        # there should be an abstract element
        self.assertNotEqual(self.resNetcdf.metadata.description, None)
        extracted_abstract = "This netCDF data is the simulation output from Utah Energy " \
                             "Balance (UEB) model.It includes the simulation result " \
                             "of snow water equivalent during the period " \
                             "Oct. 2009 to June 2010 for TWDEF site in Utah."
        self.assertEqual(self.resNetcdf.metadata.description.abstract, extracted_abstract)

        # there should be one source element
        self.assertEqual(self.resNetcdf.metadata.sources.all().count(), 1)

        # there should be one license element:
        self.assertNotEquals(self.resNetcdf.metadata.rights.statement, 1)

        # there should be one relation element
        self.assertEqual(self.resNetcdf.metadata.relations.all().filter(type='cites').count(), 1)

        # there should be creators equal to expected_creators_count
        self.assertEqual(self.resNetcdf.metadata.creators.all().count(), expected_creators_count)

        # there should be one contributor
        self.assertEqual(self.resNetcdf.metadata.contributors.all().count(), 1)

        # there should be 2 coverage element - box type and period type
        self.assertEqual(self.resNetcdf.metadata.coverages.all().count(), 2)
        self.assertEqual(self.resNetcdf.metadata.coverages.all().filter(type='box').count(), 1)
        self.assertEqual(self.resNetcdf.metadata.coverages.all().filter(type='period').count(), 1)

        box_coverage = self.resNetcdf.metadata.coverages.all().filter(type='box').first()
        self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(float(box_coverage.value['northlimit']), 41.867126409)
        self.assertEqual(float(box_coverage.value['eastlimit']), -111.505940368)
        self.assertEqual(float(box_coverage.value['southlimit']), 41.8639080745)
        self.assertEqual(float(box_coverage.value['westlimit']), -111.51138808)

        temporal_coverage = self.resNetcdf.metadata.coverages.all().filter(type='period').first()
        self.assertEqual(parser.parse(temporal_coverage.value['start']).date(),
                         parser.parse('10/01/2009').date())
        self.assertEqual(parser.parse(temporal_coverage.value['end']).date(),
                         parser.parse('05/30/2010').date())

        # there should be 2 format elements
        self.assertEqual(self.resNetcdf.metadata.formats.all().count(), 2)
        self.assertEqual(self.resNetcdf.metadata.formats.all().
                         filter(value='text/plain').count(), 1)
        self.assertEqual(self.resNetcdf.metadata.formats.all().
                         filter(value='application/x-netcdf').count(), 1)

        # there should be one subject element
        self.assertEqual(self.resNetcdf.metadata.subjects.all().count(), 1)
        subj_element = self.resNetcdf.metadata.subjects.all().first()
        self.assertEqual(subj_element.value, 'Snow water equivalent')

        # testing extended metadata element: original coverage
        ori_coverage = self.resNetcdf.metadata.ori_coverage.all().first()
        self.assertNotEquals(ori_coverage, None)
        self.assertEqual(ori_coverage.projection_string_type, 'Proj4 String')
        proj_text = u'+proj=tmerc +y_0=0.0 +k_0=0.9996 +x_0=500000.0 +lat_0=0.0 +lon_0=-111.0'
        self.assertEqual(ori_coverage.projection_string_text, proj_text)
        self.assertEqual(float(ori_coverage.value['northlimit']), 4.63515e+06)
        self.assertEqual(float(ori_coverage.value['eastlimit']), 458010.0)
        self.assertEqual(float(ori_coverage.value['southlimit']), 4.63479e+06)
        self.assertEqual(float(ori_coverage.value['westlimit']), 457560.0)
        self.assertEqual(ori_coverage.value['units'], 'Meter')
        self.assertEqual(ori_coverage.value['projection'], 'transverse_mercator')

        # testing extended metadata element: variables
        self.assertEqual(self.resNetcdf.metadata.variables.all().count(), 5)

        # test time variable
        var_time = self.resNetcdf.metadata.variables.all().filter(name='time').first()
        self.assertNotEquals(var_time, None)
        self.assertEqual(var_time.unit, 'hours since 2009-10-1 0:0:00 UTC')
        self.assertEqual(var_time.type, 'Float')
        self.assertEqual(var_time.shape, 'time')
        self.assertEqual(var_time.descriptive_name, 'time')

        # test x variable
        var_x = self.resNetcdf.metadata.variables.all().filter(name='x').first()
        self.assertNotEquals(var_x, None)
        self.assertEqual(var_x.unit, 'Meter')
        self.assertEqual(var_x.type, 'Float')
        self.assertEqual(var_x.shape, 'x')
        self.assertEqual(var_x.descriptive_name, 'x coordinate of projection')

        # test y variable
        var_y = self.resNetcdf.metadata.variables.all().filter(name='y').first()
        self.assertNotEquals(var_y, None)
        self.assertEqual(var_y.unit, 'Meter')
        self.assertEqual(var_y.type, 'Float')
        self.assertEqual(var_y.shape, 'y')
        self.assertEqual(var_y.descriptive_name, 'y coordinate of projection')

        # test SWE variable
        var_swe = self.resNetcdf.metadata.variables.all().filter(name='SWE').first()
        self.assertNotEquals(var_swe, None)
        self.assertEqual(var_swe.unit, 'm')
        self.assertEqual(var_swe.type, 'Float')
        self.assertEqual(var_swe.shape, 'y,x,time')
        self.assertEqual(var_swe.descriptive_name, 'Snow water equivalent')
        self.assertEqual(var_swe.method, 'model simulation of UEB model')
        self.assertEqual(var_swe.missing_value, '-9999')

        # test grid mapping variable
        var_grid = self.resNetcdf.metadata.variables.all().\
            filter(name='transverse_mercator').first()
        self.assertNotEquals(var_grid, None)
        self.assertEqual(var_grid.unit, 'Unknown')
        self.assertEqual(var_grid.type, 'Unknown')
        self.assertEqual(var_grid.shape, 'Not defined')

    def timeseries_metadata_extraction(self):
        """Test timeseries metadata extraction.

        This is a common test utility function to be called by both regular timeseries metadata
        extraction testing and federated zone timeseries metadata extraction testing.
        Make sure the calling TestCase object has self.resTimeSeries attribute defined before
        calling this method which is the timeseries resource that has been created containing
        valid timeseries file.
        """
        # there should one content file
        self.assertEqual(self.resTimeSeries.files.all().count(), 1)

        # there should be one contributor element
        self.assertEqual(self.resTimeSeries.metadata.contributors.all().count(), 1)

        # test core metadata after metadata extraction
        extracted_title = "Water temperature data from the Little Bear River, UT"
        self.assertEqual(self.resTimeSeries.metadata.title.value, extracted_title)

        # there should be an abstract element
        self.assertNotEqual(self.resTimeSeries.metadata.description, None)
        extracted_abstract = "This dataset contains time series of observations of water " \
                             "temperature in the Little Bear River, UT. Data were recorded every " \
                             "30 minutes. The values were recorded using a HydroLab MS5 " \
                             "multi-parameter water quality sonde connected to a Campbell " \
                             "Scientific datalogger."

        self.assertEqual(self.resTimeSeries.metadata.description.abstract.strip(),
                         extracted_abstract)

        # there should be 2 coverage element -  box type and period type
        self.assertEqual(self.resTimeSeries.metadata.coverages.all().count(), 2)
        self.assertEqual(self.resTimeSeries.metadata.coverages.all().filter(type='box').count(), 1)
        self.assertEqual(self.resTimeSeries.metadata.coverages.all().filter(
            type='period').count(), 1)

        box_coverage = self.resTimeSeries.metadata.coverages.all().filter(type='box').first()
        self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(float(box_coverage.value['northlimit']), 41.718473)
        self.assertEqual(float(box_coverage.value['eastlimit']), -111.799324)
        self.assertEqual(float(box_coverage.value['southlimit']), 41.495409)
        self.assertEqual(float(box_coverage.value['westlimit']), -111.946402)

        temporal_coverage = self.resTimeSeries.metadata.coverages.all().filter(
            type='period').first()
        self.assertEqual(parser.parse(temporal_coverage.value['start']).date(),
                         parser.parse('01/01/2008').date())
        self.assertEqual(parser.parse(temporal_coverage.value['end']).date(),
                         parser.parse('01/30/2008').date())

        # there should be one format element
        self.assertEqual(self.resTimeSeries.metadata.formats.all().count(), 1)
        format_element = self.resTimeSeries.metadata.formats.all().first()
        self.assertEqual(format_element.value, 'application/sqlite')

        # there should be one subject element
        self.assertEqual(self.resTimeSeries.metadata.subjects.all().count(), 1)
        subj_element = self.resTimeSeries.metadata.subjects.all().first()
        self.assertEqual(subj_element.value, 'Temperature')

        # there should be a total of 7 timeseries
        self.assertEqual(self.resTimeSeries.metadata.time_series_results.all().count(), 7)

        # testing extended metadata elements

        # test 'site' - there should be 7 sites
        self.assertEqual(self.resTimeSeries.metadata.sites.all().count(), 7)
        # each site be associated with one series id
        for site in self.resTimeSeries.metadata.sites.all():
            self.assertEqual(len(site.series_ids), 1)

        # test the data for a specific site
        site = self.resTimeSeries.metadata.sites.filter(site_code='USU-LBR-Paradise').first()
        self.assertNotEqual(site, None)
        site_name = 'Little Bear River at McMurdy Hollow near Paradise, Utah'
        self.assertEqual(site.site_name, site_name)
        self.assertEqual(site.elevation_m, 1445)
        self.assertEqual(site.elevation_datum, 'NGVD29')
        self.assertEqual(site.site_type, 'Stream')

        # test 'variable' - there should be 1 variable element
        self.assertEqual(self.resTimeSeries.metadata.variables.all().count(), 1)
        variable = self.resTimeSeries.metadata.variables.all().first()
        # there should be 7 series ids associated with this one variable
        self.assertEqual(len(variable.series_ids), 7)
        # test the data for a variable
        self.assertEqual(variable.variable_code, 'USU36')
        self.assertEqual(variable.variable_name, 'Temperature')
        self.assertEqual(variable.variable_type, 'Water Quality')
        self.assertEqual(variable.no_data_value, -9999)
        self.assertEqual(variable.variable_definition, None)
        self.assertEqual(variable.speciation, 'Not Applicable')

        # test 'method' - there should be 1 method element
        self.assertEqual(self.resTimeSeries.metadata.methods.all().count(), 1)
        method = self.resTimeSeries.metadata.methods.all().first()
        # there should be 7 series ids associated with this one method element
        self.assertEqual(len(method.series_ids), 7)
        self.assertEqual(method.method_code, '28')
        method_name = 'Quality Control Level 1 Data Series created from raw QC Level 0 data ' \
                      'using ODM Tools.'
        self.assertEqual(method.method_name, method_name)
        self.assertEqual(method.method_type, 'Instrument deployment')
        method_des = 'Quality Control Level 1 Data Series created from raw QC Level 0 data ' \
                     'using ODM Tools.'
        self.assertEqual(method.method_description, method_des)
        self.assertEqual(method.method_link, None)

        # test 'processing_level' - there should be 1 processing_level element
        self.assertEqual(self.resTimeSeries.metadata.processing_levels.all().count(), 1)
        proc_level = self.resTimeSeries.metadata.processing_levels.all().first()
        # there should be 7 series ids associated with this one element
        self.assertEqual(len(proc_level.series_ids), 7)
        self.assertEqual(proc_level.processing_level_code, '1')
        self.assertEqual(proc_level.definition, 'Quality controlled data')
        explanation = 'Quality controlled data that have passed quality assurance procedures ' \
                      'such as routine estimation of timing and sensor calibration or visual ' \
                      'inspection and removal of obvious errors. An example is USGS published ' \
                      'streamflow records following parsing through USGS quality control ' \
                      'procedures.'
        self.assertEqual(proc_level.explanation, explanation)

        # test 'timeseries_result' - there should be 7 timeseries_result element
        self.assertEqual(self.resTimeSeries.metadata.time_series_results.all().count(), 7)
        ts_result = self.resTimeSeries.metadata.time_series_results.filter(
            series_ids__contains=['182d8fa3-1ebc-11e6-ad49-f45c8999816f']).first()
        self.assertNotEqual(ts_result, None)
        # there should be only 1 series id associated with this element
        self.assertEqual(len(ts_result.series_ids), 1)
        self.assertEqual(ts_result.units_type, 'Temperature')
        self.assertEqual(ts_result.units_name, 'degree celsius')
        self.assertEqual(ts_result.units_abbreviation, 'degC')
        self.assertEqual(ts_result.status, 'Unknown')
        self.assertEqual(ts_result.sample_medium, 'Surface Water')
        self.assertEqual(ts_result.value_count, 1441)
        self.assertEqual(ts_result.aggregation_statistics, 'Average')

        # test for CV lookup tables
        # there should be 23 CV_VariableType records
        self.assertEqual(self.resTimeSeries.metadata.cv_variable_types.all().count(), 23)
        # there should be 805 CV_VariableName records
        self.assertEqual(self.resTimeSeries.metadata.cv_variable_names.all().count(), 805)
        # there should be 145 CV_Speciation records
        self.assertEqual(self.resTimeSeries.metadata.cv_speciations.all().count(), 145)
        # there should be 51 CV_SiteType records
        self.assertEqual(self.resTimeSeries.metadata.cv_site_types.all().count(), 51)
        # there should be 5 CV_ElevationDatum records
        self.assertEqual(self.resTimeSeries.metadata.cv_elevation_datums.all().count(), 5)
        # there should be 25 CV_MethodType records
        self.assertEqual(self.resTimeSeries.metadata.cv_method_types.all().count(), 25)
        # there should be 179 CV_UnitsType records
        self.assertEqual(self.resTimeSeries.metadata.cv_units_types.all().count(), 179)
        # there should be 4 CV_Status records
        self.assertEqual(self.resTimeSeries.metadata.cv_statuses.all().count(), 4)
        # there should be 17 CV_Medium records
        self.assertEqual(self.resTimeSeries.metadata.cv_mediums.all().count(), 18)
        # there should be 17 CV_aggregationStatistics records
        self.assertEqual(self.resTimeSeries.metadata.cv_aggregation_statistics.all().count(), 17)
        # there should not be any UTCOffset element
        self.assertEqual(self.resTimeSeries.metadata.utc_offset, None)


class ViewTestCase(TestCase):
    """Test basic view functionality."""

    def setUp(self):
        """Create request factory and set temp_dir for testing."""
        self.factory = RequestFactory()
        self.temp_dir = tempfile.mkdtemp()
        super(ViewTestCase, self).setUp()

    @staticmethod
    def set_request_message_attributes(request):
        """Set session and _messages attributies on request."""
        # the following 3 lines are for preventing error in unit test due to the view being
        # tested uses messaging middleware
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

    @staticmethod
    def add_session_to_request(request):
        """Use SessionMiddleware to add a session to the request."""
        """Annotate a request object with a session"""
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
