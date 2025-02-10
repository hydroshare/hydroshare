"""Test cases and utilities for hs_core module. See also ./tests folder."""

from dateutil import parser
import tempfile
import os

from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.files.uploadedfile import UploadedFile
from django.test import TestCase, RequestFactory

from hs_core.hydroshare import add_file_to_resource, add_resource_files
from hs_core.views.utils import create_folder, move_or_rename_file_or_folder, zip_folder, \
    unzip_file, remove_folder
from hs_core.tasks import FileOverrideException


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

        store = istorage.listdir(res_path)
        self.assertEqual(store[0].count('sub_test_dir'), 1, msg='duplicate folder: sub_test_dir occurred more '
                                                                'than once')

        # rename the third file in file_name_list
        move_or_rename_file_or_folder(user, res.short_id,
                                      'data/contents/' + file_name_list[2],
                                      'data/contents/new_' + file_name_list[2])

        # move the first two files in file_name_list to the new folder that we will be zipping
        move_or_rename_file_or_folder(user, res.short_id,
                                      'data/contents/' + file_name_list[0],
                                      'data/contents/sub_test_dir/' + file_name_list[0])
        move_or_rename_file_or_folder(user, res.short_id,
                                      'data/contents/' + file_name_list[1],
                                      'data/contents/sub_test_dir/' + file_name_list[1])

        updated_res_file_names = []
        for rf in res.files.all():
            updated_res_file_names.append(rf.short_path)

        self.assertIn('new_' + file_name_list[2], updated_res_file_names,
                      msg="resource does not contain the updated file new_" + file_name_list[2])
        self.assertNotIn(file_name_list[2], updated_res_file_names,
                         msg='resource still contains the old file ' + file_name_list[2] + ' after renaming')
        self.assertIn('sub_test_dir/' + file_name_list[0], updated_res_file_names,
                      msg='resource does not contain ' + file_name_list[0] + ' moved to a folder')
        self.assertNotIn(file_name_list[0], updated_res_file_names,
                         msg='resource still contains the old ' + file_name_list[0] + 'after moving to a folder')
        self.assertIn('sub_test_dir/' + file_name_list[1], updated_res_file_names,
                      msg='resource does not contain ' + file_name_list[1] + 'moved to a new folder')
        self.assertNotIn(file_name_list[1], updated_res_file_names,
                         msg='resource still contains the old ' + file_name_list[1] + ' after moving to a folder')

        # zip the folder 'sub_test_dir'
        output_zip_fname, size = \
            zip_folder(user, res.short_id, 'data/contents/sub_test_dir', 'sub_test_dir.zip', True)

        self.assertGreater(size, 0, msg='zipped file has a size of 0')
        # Now resource should contain only two files: new_file3.txt and sub_test_dir.zip
        # since the folder is zipped into sub_test_dir.zip with the folder deleted
        self.assertEqual(res.files.all().count(), 2, msg="resource file count didn't match-")

        # >> testing folder name collision upon unzip
        # unzip should fail due to previous unzip collision
        with self.assertRaises(FileOverrideException):
            unzip_file(user, res.short_id, 'data/contents/sub_test_dir.zip', bool_remove_original=False)

        # remove the conflicting folder (sub_test_dir) to test that unzip should work after that
        remove_folder(user, res.short_id, 'data/contents/sub_test_dir')
        # unzip should work now
        unzip_file(user, res.short_id, 'data/contents/sub_test_dir.zip', bool_remove_original=False)

        remove_folder(user, res.short_id, 'data/contents/sub_test_dir')
        for rf in res.files.all():
            rf.delete()

        # >> test filename collision upon unzip
        # add the file 'test.txt'
        res_file_txt = _add_file_to_resource(resource=res, file_to_add=self.test_data_file_path)
        # add 'test.zip' file which contains one file 'test.txt'
        _add_file_to_resource(resource=res, file_to_add=self.test_data_zip_file_path)
        self.assertEqual(res.files.all().count(), 2)

        # unzipping of the above added zip file should fail due to filename (text.txt) collision
        with self.assertRaises(FileOverrideException):
            unzip_file(user, res.short_id, f'data/contents/{self.test_data_zip_file_name}', bool_remove_original=False)

        # delete the conflicting file (test.txt) - then unzip should work
        res_file_txt.delete()
        unzip_file(user, res.short_id, f'data/contents/{self.test_data_zip_file_name}', bool_remove_original=False)

        # the resource should have 2 files (test.zip and test.txt)
        self.assertEqual(res.files.all().count(), 2)
        # test unzip with original zip file being removed
        for rf in res.files.all():
            if rf.short_path == self.test_data_file_name:
                rf.delete()
                break
        # resource should have 1 file (test.zip)
        self.assertEqual(res.files.all().count(), 1)
        unzip_file(user, res.short_id, f'data/contents/{self.test_data_zip_file_name}', bool_remove_original=True)
        # resource should have 1 file (test.txt)
        self.assertEqual(res.files.all().count(), 1)
        res_file_txt = res.files.all().first()
        self.assertEqual(res_file_txt.short_path, self.test_data_file_name)
        zip_storage_file_path = os.path.join(res.file_path, self.test_data_zip_file_name)
        self.assertFalse(istorage.exists(zip_storage_file_path))

        # remove all files in sub_test_dir created by unzip, and then create an empty sub_test_dir
        for rf in res.files.all():
            rf.delete()

        # add 2 files to the root folder
        add_resource_files(res.short_id, self.test_file_1, self.test_file_3)
        # resource should have 2 files
        self.assertEqual(res.files.all().count(), 2)
        # check that the files were added to the root folder
        for rf in res.files.all():
            self.assertEqual(rf.file_folder, "")

        # TODO: use ResourceFile.rename, which doesn't require data/contents prefix
        # >> test moving files to a different directory
        # move the 2 files to the new directory - 'sub_test_dir'
        move_or_rename_file_or_folder(user, res.short_id,
                                      'data/contents/' + file_name_list[0],
                                      'data/contents/sub_test_dir/' + file_name_list[0])
        move_or_rename_file_or_folder(user, res.short_id,
                                      'data/contents/' + file_name_list[2],
                                      'data/contents/sub_test_dir/' + file_name_list[2])
        # resource should have 2 files
        self.assertEqual(res.files.all().count(), 2)
        # check the files got moved to a different directory
        for rf in res.files.all():
            self.assertEqual(rf.file_folder, "sub_test_dir")

        # >> test renaming files
        # rename one of the files
        move_or_rename_file_or_folder(user, res.short_id,
                                      'data/contents/sub_test_dir/' + file_name_list[0],
                                      'data/contents/sub_test_dir/new_' + file_name_list[0])
        file_renamed = False
        for rf in res.files.all():
            if rf.short_path == f"sub_test_dir/new_{file_name_list[0]}":
                file_renamed = True
                break
        self.assertTrue(file_renamed)
        file_storage_path_old = os.path.join(res.file_path, 'sub_test_dir', file_name_list[0])
        file_storage_path_new = os.path.join(res.file_path, 'sub_test_dir', f"new_{file_name_list[0]}")
        self.assertFalse(istorage.exists(file_storage_path_old))
        self.assertTrue(istorage.exists(file_storage_path_new))

        # >> test renaming a folder
        move_or_rename_file_or_folder(user, res.short_id,
                                      'data/contents/sub_test_dir',
                                      'data/contents/sub_dir')

        dir_storage_path_old = os.path.join(res.file_path, "sub_test_dir")
        dir_storage_path_new = os.path.join(res.file_path, "sub_dir")
        self.assertFalse(istorage.exists(dir_storage_path_old))
        self.assertTrue(istorage.exists(dir_storage_path_new))

        for rf in res.files.all():
            self.assertEqual(rf.file_folder, "sub_dir")

        remove_folder(user, res.short_id, 'data/contents/sub_dir')
        dir_storage_path_deleted = os.path.join(res.file_path, "sub_dir")
        self.assertFalse(istorage.exists(dir_storage_path_deleted))

        # resource should have no files after the folder containing the folder is deleted
        self.assertEqual(res.files.all().count(), 0)

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

        # testing additional metadata element: original coverage
        ori_coverage = self.resRaster.metadata.originalCoverage
        self.assertNotEqual(ori_coverage, None)
        self.assertEqual(float(ori_coverage.value['northlimit']), 4662392.446916306)
        self.assertEqual(float(ori_coverage.value['eastlimit']), 461954.01909127034)
        self.assertEqual(float(ori_coverage.value['southlimit']), 4612592.446916306)
        self.assertEqual(float(ori_coverage.value['westlimit']), 432404.01909127034)
        self.assertEqual(ori_coverage.value['units'], 'meter')
        self.assertEqual(ori_coverage.value['projection'], "NAD83 / UTM zone 12N")
        self.assertEqual(ori_coverage.value['datum'], "North_American_Datum_1983")
        projection_string = 'PROJCS["NAD83 / UTM zone 12N",GEOGCS["NAD83",' \
                            'DATUM["North_American_Datum_1983",' \
                            'SPHEROID["GRS 1980",6378137,298.257222101,' \
                            'AUTHORITY["EPSG","7019"]],' \
                            'TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","6269"]],' \
                            'PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],' \
                            'UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],' \
                            'AUTHORITY["EPSG","4269"]],PROJECTION["Transverse_Mercator"],' \
                            'PARAMETER["latitude_of_origin",0],' \
                            'PARAMETER["central_meridian",-111],' \
                            'PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],' \
                            'PARAMETER["false_northing",0],' \
                            'UNIT["metre",1,AUTHORITY["EPSG","9001"]],' \
                            'AXIS["Easting",EAST],AXIS["Northing",' \
                            'NORTH],AUTHORITY["EPSG","26912"]]'
        self.assertEqual(ori_coverage.value['projection_string'], projection_string)

        # testing additional metadata element: cell information
        cell_info = self.resRaster.metadata.cellInformation
        self.assertEqual(cell_info.rows, 1660)
        self.assertEqual(cell_info.columns, 985)
        self.assertEqual(cell_info.cellSizeXValue, 30.0)
        self.assertEqual(cell_info.cellSizeYValue, 30.0)
        self.assertEqual(cell_info.cellDataType, 'Float32')

        # testing additional metadata element: band information
        self.assertEqual(self.resRaster.metadata.bandInformations.count(), 1)
        band_info = self.resRaster.metadata.bandInformations.first()
        self.assertEqual(band_info.noDataValue, '-3.4028234663852886e+38')
        self.assertEqual(band_info.maximumValue, '3031.443115234375')
        self.assertEqual(band_info.minimumValue, '1358.3345947265625')

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

        # there should be one relation element of type 'source'
        self.assertEqual(self.resNetcdf.metadata.relations.filter(type='source').count(), 1)

        # there should be one license element:
        self.assertNotEqual(self.resNetcdf.metadata.rights.statement, 1)

        # there should be one relation element
        self.assertEqual(self.resNetcdf.metadata.relations.all().filter(type='references').count(), 1)

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
        self.assertEqual(float(box_coverage.value['northlimit']), 41.86712640899591)
        self.assertEqual(float(box_coverage.value['eastlimit']), -111.50594036845686)
        self.assertEqual(float(box_coverage.value['southlimit']), 41.8639080745171)
        self.assertEqual(float(box_coverage.value['westlimit']), -111.51138807956221)

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

        # testing additional metadata element: original coverage
        ori_coverage = self.resNetcdf.metadata.ori_coverage.all().first()
        self.assertNotEqual(ori_coverage, None)
        self.assertEqual(ori_coverage.projection_string_type, 'Proj4 String')
        proj_text = '+proj=tmerc +y_0=0.0 +x_0=500000.0 +k_0=0.9996 +lat_0=0.0 +lon_0=-111.0'
        self.assertEqual(ori_coverage.projection_string_text, proj_text)
        self.assertEqual(float(ori_coverage.value['northlimit']), 4.63515e+06)
        self.assertEqual(float(ori_coverage.value['eastlimit']), 458010.0)
        self.assertEqual(float(ori_coverage.value['southlimit']), 4.63479e+06)
        self.assertEqual(float(ori_coverage.value['westlimit']), 457560.0)
        self.assertEqual(ori_coverage.value['units'], 'Meter')
        self.assertEqual(ori_coverage.value['projection'], 'transverse_mercator')

        # testing additional metadata element: variables
        self.assertEqual(self.resNetcdf.metadata.variables.all().count(), 5)

        # test time variable
        var_time = self.resNetcdf.metadata.variables.all().filter(name='time').first()
        self.assertNotEqual(var_time, None)
        self.assertEqual(var_time.unit, 'hours since 2009-10-1 0:0:00 UTC')
        self.assertEqual(var_time.type, 'Float')
        self.assertEqual(var_time.shape, 'time')
        self.assertEqual(var_time.descriptive_name, 'time')

        # test x variable
        var_x = self.resNetcdf.metadata.variables.all().filter(name='x').first()
        self.assertNotEqual(var_x, None)
        self.assertEqual(var_x.unit, 'Meter')
        self.assertEqual(var_x.type, 'Float')
        self.assertEqual(var_x.shape, 'x')
        self.assertEqual(var_x.descriptive_name, 'x coordinate of projection')

        # test y variable
        var_y = self.resNetcdf.metadata.variables.all().filter(name='y').first()
        self.assertNotEqual(var_y, None)
        self.assertEqual(var_y.unit, 'Meter')
        self.assertEqual(var_y.type, 'Float')
        self.assertEqual(var_y.shape, 'y')
        self.assertEqual(var_y.descriptive_name, 'y coordinate of projection')

        # test SWE variable
        var_swe = self.resNetcdf.metadata.variables.all().filter(name='SWE').first()
        self.assertNotEqual(var_swe, None)
        self.assertEqual(var_swe.unit, 'm')
        self.assertEqual(var_swe.type, 'Float')
        self.assertEqual(var_swe.shape, 'y,x,time')
        self.assertEqual(var_swe.descriptive_name, 'Snow water equivalent')
        self.assertEqual(var_swe.method, 'model simulation of UEB model')
        self.assertEqual(var_swe.missing_value, '-9999')

        # test grid mapping variable
        var_grid = self.resNetcdf.metadata.variables.all().\
            filter(name='transverse_mercator').first()
        self.assertNotEqual(var_grid, None)
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

        # testing additional metadata elements

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


def _add_file_to_resource(resource, file_to_add, upload_folder=''):
    file_to_upload = UploadedFile(file=open(file_to_add, 'rb'),
                                  name=os.path.basename(file_to_add))

    new_res_file = add_file_to_resource(resource, file_to_upload, folder=upload_folder, check_target_folder=True)
    return new_res_file


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
        middleware = SessionMiddleware(request)
        middleware.process_request(request)
        request.session.save()
