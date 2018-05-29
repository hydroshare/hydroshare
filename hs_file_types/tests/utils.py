import os

from dateutil import parser

from django.core.files.uploadedfile import UploadedFile

from hs_core.hydroshare.utils import get_resource_file_name_and_extension, add_file_to_resource
from hs_core.hydroshare import create_resource
from hs_file_types.models import GeoRasterLogicalFile, GeoRasterFileMetaData, GenericLogicalFile, \
    NetCDFLogicalFile, GeoFeatureLogicalFile, GeoFeatureFileMetaData, RefTimeseriesLogicalFile, \
    TimeSeriesLogicalFile, TimeSeriesFileMetaData


class CompositeResourceTestMixin(object):

    def add_file_to_resource(self, file_to_add, upload_folder=None):
        file_to_upload = UploadedFile(file=open(file_to_add, 'rb'),
                                      name=os.path.basename(file_to_add))

        new_res_file = add_file_to_resource(
            self.composite_resource, file_to_upload, folder=upload_folder, check_target_folder=True
        )
        return new_res_file

    def create_composite_resource(self, file_to_upload=[], auto_aggregate=False, folder=None):
        if isinstance(file_to_upload, str):
            file_to_upload = [file_to_upload]
        files = []
        full_paths = {}
        for file_name in file_to_upload:
            file_obj = open(file_name, 'r')
            if folder:
                full_paths[file_obj] = os.path.join(folder, file_name)
            uploaded_file = UploadedFile(file=file_obj, name=os.path.basename(file_obj.name))
            files.append(uploaded_file)
        self.composite_resource = create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title=self.res_title,
            files=files,
            auto_aggregate=auto_aggregate,
            full_paths=full_paths
        )


def assert_raster_file_type_metadata(self, aggr_folder_path):
    # test the resource now has 2 files (vrt file added as part of metadata extraction)
    self.assertEqual(self.composite_resource.files.all().count(), 2)

    # check that the 2 resource files are now associated with GeoRasterLogicalFile
    for res_file in self.composite_resource.files.all():
        self.assertEqual(res_file.logical_file_type_name, "GeoRasterLogicalFile")
        self.assertEqual(res_file.has_logical_file, True)
        self.assertTrue(isinstance(res_file.logical_file, GeoRasterLogicalFile))

    # check that the 2 files are in the aggr_folder_path
    for res_file in self.composite_resource.files.all():
        self.assertEqual(res_file.file_folder, aggr_folder_path)

    # check that there is no GenericLogicalFile object
    self.assertEqual(GenericLogicalFile.objects.count(), 0)
    # check that there is one GeoRasterLogicalFile object
    self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)

    res_file = self.composite_resource.files.first()
    expected_dataset_name = os.path.basename(res_file.file_folder)
    logical_file = res_file.logical_file
    self.assertEqual(logical_file.dataset_name, expected_dataset_name)
    self.assertEqual(logical_file.has_metadata, True)
    # check that the logicalfile is associated with 2 files
    self.assertEqual(logical_file.files.all().count(), 2)
    self.assertEqual(set(self.composite_resource.files.all()),
                     set(logical_file.files.all()))

    # test that size property of the logical file is equal to sun of size of all files
    # that are part of the logical file
    self.assertEqual(logical_file.size, sum([f.size for f in logical_file.files.all()]))

    # test that there should be 1 object of type GeoRasterFileMetaData
    self.assertEqual(GeoRasterFileMetaData.objects.count(), 1)

    # test that the metadata associated with logical file id of type GeoRasterFileMetaData
    self.assertTrue(isinstance(logical_file.metadata, GeoRasterFileMetaData))

    # there should be 2 format elements associated with resource
    self.assertEqual(self.composite_resource.metadata.formats.all().count(), 2)
    self.assertEqual(
        self.composite_resource.metadata.formats.all().filter(value='application/vrt').count(),
        1)
    self.assertEqual(self.composite_resource.metadata.formats.all().filter(
        value='image/tiff').count(), 1)

    # test extracted metadata for the file type

    # geo raster file type should have all the metadata elements
    self.assertEqual(logical_file.metadata.has_all_required_elements(), True)

    # there should be 1 coverage element - box type
    self.assertNotEqual(logical_file.metadata.spatial_coverage, None)
    self.assertEqual(logical_file.metadata.spatial_coverage.type, 'box')

    box_coverage = logical_file.metadata.spatial_coverage
    self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
    self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
    self.assertEqual(box_coverage.value['northlimit'], 42.0500269597691)
    self.assertEqual(box_coverage.value['eastlimit'], -111.57773718106195)
    self.assertEqual(box_coverage.value['southlimit'], 41.98722286029891)
    self.assertEqual(box_coverage.value['westlimit'], -111.69756293084055)

    # testing extended metadata element: original coverage
    ori_coverage = logical_file.metadata.originalCoverage
    self.assertNotEqual(ori_coverage, None)
    self.assertEqual(ori_coverage.value['northlimit'], 4655492.446916306)
    self.assertEqual(ori_coverage.value['eastlimit'], 452144.01909127034)
    self.assertEqual(ori_coverage.value['southlimit'], 4648592.446916306)
    self.assertEqual(ori_coverage.value['westlimit'], 442274.01909127034)
    self.assertEqual(ori_coverage.value['units'], 'meter')
    self.assertEqual(ori_coverage.value['projection'],
                     'NAD83 / UTM zone 12N')

    # testing extended metadata element: cell information
    cell_info = logical_file.metadata.cellInformation
    self.assertEqual(cell_info.rows, 230)
    self.assertEqual(cell_info.columns, 329)
    self.assertEqual(cell_info.cellSizeXValue, 30.0)
    self.assertEqual(cell_info.cellSizeYValue, 30.0)
    self.assertEqual(cell_info.cellDataType, 'Float32')

    # testing extended metadata element: band information
    self.assertEqual(logical_file.metadata.bandInformations.count(), 1)
    band_info = logical_file.metadata.bandInformations.first()
    self.assertEqual(band_info.noDataValue, '-3.40282346639e+38')
    self.assertEqual(band_info.maximumValue, '2880.00708008')
    self.assertEqual(band_info.minimumValue, '1870.63659668')


def assert_netcdf_file_type_metadata(self, title, aggr_folder):
    # check that there is one NetCDFLogicalFile object
    self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
    # check that there is no GenericLogicalFile object
    self.assertEqual(GenericLogicalFile.objects.count(), 0)

    # There should be now 2 files
    self.assertEqual(self.composite_resource.files.count(), 2)
    # check that we put the 2 files in a new folder *aggr_folder*
    for res_file in self.composite_resource.files.all():
        expected_file_path = "{0}/{1}/{2}".format(self.composite_resource.file_path, aggr_folder,
                                                  res_file.file_name)
        self.assertEqual(res_file.full_path, expected_file_path)
        self.assertEqual(res_file.file_folder, aggr_folder)

    res_file = self.composite_resource.files.first()
    logical_file = res_file.logical_file

    # logical file should be associated with 2 files
    self.assertEqual(logical_file.files.all().count(), 2)
    file_extensions = set([f.extension for f in logical_file.files.all()])
    self.assertIn('.nc', file_extensions)
    self.assertIn('.txt', file_extensions)

    # test extracted netcdf file type metadata
    # there should 2 content file
    self.assertEqual(self.composite_resource.files.all().count(), 2)

    # test core metadata after metadata extraction
    # title = "Test NetCDF File Type Metadata"
    self.assertEqual(self.composite_resource.metadata.title.value, title)

    # there should be an abstract element
    self.assertNotEqual(self.composite_resource.metadata.description, None)
    extracted_abstract = "This netCDF data is the simulation output from Utah Energy " \
                         "Balance (UEB) model.It includes the simulation result " \
                         "of snow water equivalent during the period " \
                         "Oct. 2009 to June 2010 for TWDEF site in Utah."
    self.assertEqual(self.composite_resource.metadata.description.abstract, extracted_abstract)

    # there should be no source element
    self.assertEqual(self.composite_resource.metadata.sources.all().count(), 0)

    # there should be one license element:
    self.assertNotEquals(self.composite_resource.metadata.rights.statement, 1)

    # there should be no relation element
    self.assertEqual(self.composite_resource.metadata.relations.all().count(), 0)

    # there should be 2 creator
    self.assertEqual(self.composite_resource.metadata.creators.all().count(), 2)

    # there should be one contributor
    self.assertEqual(self.composite_resource.metadata.contributors.all().count(), 1)

    # there should be 2 coverage element - box type and period type
    self.assertEqual(self.composite_resource.metadata.coverages.all().count(), 2)
    self.assertEqual(self.composite_resource.metadata.coverages.all().filter(type='box').
                     count(), 1)
    self.assertEqual(self.composite_resource.metadata.coverages.all().filter(type='period').
                     count(), 1)

    box_coverage = self.composite_resource.metadata.coverages.all().filter(type='box').first()
    self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
    self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
    self.assertEqual(box_coverage.value['northlimit'], 41.867126409)
    self.assertEqual(box_coverage.value['eastlimit'], -111.505940368)
    self.assertEqual(box_coverage.value['southlimit'], 41.8639080745)
    self.assertEqual(box_coverage.value['westlimit'], -111.51138808)

    temporal_coverage = self.composite_resource.metadata.coverages.all().filter(
        type='period').first()
    self.assertEqual(parser.parse(temporal_coverage.value['start']).date(),
                     parser.parse('10/01/2009').date())
    self.assertEqual(parser.parse(temporal_coverage.value['end']).date(),
                     parser.parse('05/30/2010').date())

    # there should be 2 format elements
    self.assertEqual(self.composite_resource.metadata.formats.all().count(), 2)
    self.assertEqual(self.composite_resource.metadata.formats.all().
                     filter(value='text/plain').count(), 1)
    self.assertEqual(self.composite_resource.metadata.formats.all().
                     filter(value='application/x-netcdf').count(), 1)

    # test file type metadata
    res_file = self.composite_resource.files.first()
    logical_file = res_file.logical_file
    # there should be one keyword element
    self.assertEqual(len(logical_file.metadata.keywords), 1)
    self.assertIn('Snow water equivalent', logical_file.metadata.keywords)

    # test dataset_name attribute of the logical file which shoould have the extracted value
    dataset_title = "Snow water equivalent estimation at TWDEF site from Oct 2009 to June 2010"
    self.assertEqual(logical_file.dataset_name, dataset_title)

    # testing extended metadata element: original coverage
    ori_coverage = logical_file.metadata.originalCoverage
    self.assertNotEquals(ori_coverage, None)
    self.assertEqual(ori_coverage.projection_string_type, 'Proj4 String')
    proj_text = u'+proj=tmerc +y_0=0.0 +k_0=0.9996 +x_0=500000.0 +lat_0=0.0 +lon_0=-111.0'
    self.assertEqual(ori_coverage.projection_string_text, proj_text)
    self.assertEqual(ori_coverage.value['northlimit'], '4.63515e+06')
    self.assertEqual(ori_coverage.value['eastlimit'], '458010.0')
    self.assertEqual(ori_coverage.value['southlimit'], '4.63479e+06')
    self.assertEqual(ori_coverage.value['westlimit'], '457560.0')
    self.assertEqual(ori_coverage.value['units'], 'Meter')
    self.assertEqual(ori_coverage.value['projection'], 'transverse_mercator')

    # testing extended metadata element: variables
    self.assertEqual(logical_file.metadata.variables.all().count(), 5)

    # test time variable
    var_time = logical_file.metadata.variables.all().filter(name='time').first()
    self.assertNotEquals(var_time, None)
    self.assertEqual(var_time.unit, 'hours since 2009-10-1 0:0:00 UTC')
    self.assertEqual(var_time.type, 'Float')
    self.assertEqual(var_time.shape, 'time')
    self.assertEqual(var_time.descriptive_name, 'time')

    # test x variable
    var_x = logical_file.metadata.variables.all().filter(name='x').first()
    self.assertNotEquals(var_x, None)
    self.assertEqual(var_x.unit, 'Meter')
    self.assertEqual(var_x.type, 'Float')
    self.assertEqual(var_x.shape, 'x')
    self.assertEqual(var_x.descriptive_name, 'x coordinate of projection')

    # test y variable
    var_y = logical_file.metadata.variables.all().filter(name='y').first()
    self.assertNotEquals(var_y, None)
    self.assertEqual(var_y.unit, 'Meter')
    self.assertEqual(var_y.type, 'Float')
    self.assertEqual(var_y.shape, 'y')
    self.assertEqual(var_y.descriptive_name, 'y coordinate of projection')

    # test SWE variable
    var_swe = logical_file.metadata.variables.all().filter(name='SWE').first()
    self.assertNotEquals(var_swe, None)
    self.assertEqual(var_swe.unit, 'm')
    self.assertEqual(var_swe.type, 'Float')
    self.assertEqual(var_swe.shape, 'y,x,time')
    self.assertEqual(var_swe.descriptive_name, 'Snow water equivalent')
    self.assertEqual(var_swe.method, 'model simulation of UEB model')
    self.assertEqual(var_swe.missing_value, '-9999')

    # test grid mapping variable
    var_grid = logical_file.metadata.variables.all(). \
        filter(name='transverse_mercator').first()
    self.assertNotEquals(var_grid, None)
    self.assertEqual(var_grid.unit, 'Unknown')
    self.assertEqual(var_grid.type, 'Unknown')
    self.assertEqual(var_grid.shape, 'Not defined')


def assert_geofeature_file_type_metadata(self, expected_folder_name):
    # test files in the file type
    self.assertEqual(self.composite_resource.files.count(), 3)
    # check that there is no GenericLogicalFile object
    self.assertEqual(GenericLogicalFile.objects.count(), 0)
    # check that there is one GeoFeatureLogicalFile object
    self.assertEqual(GeoFeatureLogicalFile.objects.count(), 1)
    # check that there is one GeoFeatureFileMetaData object
    self.assertEqual(GeoFeatureFileMetaData.objects.count(), 1)

    logical_file = GeoFeatureLogicalFile.objects.first()
    self.assertEqual(logical_file.files.count(), 3)
    # check that the 3 resource files are now associated with GeoFeatureLogicalFile
    for res_file in self.composite_resource.files.all():
        self.assertEqual(res_file.logical_file_type_name, "GeoFeatureLogicalFile")
        self.assertEqual(res_file.has_logical_file, True)
        self.assertTrue(isinstance(res_file.logical_file, GeoFeatureLogicalFile))
    # check that we put the 3 files in a new folder
    for res_file in self.composite_resource.files.all():
        file_path, base_file_name, _ = get_resource_file_name_and_extension(res_file)
        expected_file_path = "{}/data/contents/{}/{}"
        res_file.file_folder = expected_folder_name
        expected_file_path = expected_file_path.format(self.composite_resource.root_path,
                                                       expected_folder_name, base_file_name)
        self.assertEqual(file_path, expected_file_path)
    # test extracted raster file type metadata
    # there should not be any resource level coverage
    self.assertEqual(self.composite_resource.metadata.coverages.count(), 0)
    self.assertNotEqual(logical_file.metadata.geometryinformation, None)
    self.assertEqual(logical_file.metadata.geometryinformation.featureCount, 51)
    self.assertEqual(logical_file.metadata.geometryinformation.geometryType,
                     "MULTIPOLYGON")

    self.assertNotEqual(logical_file.metadata.originalcoverage, None)
    self.assertEqual(logical_file.metadata.originalcoverage.datum,
                     'unknown')
    self.assertEqual(logical_file.metadata.originalcoverage.projection_name,
                     'unknown')
    self.assertGreater(len(logical_file.metadata.originalcoverage.projection_string), 0)
    self.assertEqual(logical_file.metadata.originalcoverage.unit, 'unknown')
    self.assertEqual(logical_file.metadata.originalcoverage.eastlimit, -66.9692712587578)
    self.assertEqual(logical_file.metadata.originalcoverage.northlimit, 71.406235393967)
    self.assertEqual(logical_file.metadata.originalcoverage.southlimit, 18.921786345087)
    self.assertEqual(logical_file.metadata.originalcoverage.westlimit, -178.217598362366)


def assert_ref_time_series_file_type_metadata(self):
    # check that there is one RefTimeseriesLogicalFile object
    self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 1)

    # test extracted metadata that updates resource level metadata

    # resource title should have been updated from the title value in json file
    res_title = "Sites, Variable"
    self.composite_resource.metadata.refresh_from_db()
    self.assertEqual(self.composite_resource.metadata.title.value, res_title)
    # resource abstract should have been updated from the abstract value in json file
    abstract = "Discharge, cubic feet per second,Blue-green algae (cyanobacteria), " \
               "phycocyanin data collected from 2016-04-06 to 2017-02-09 created on " \
               "Thu Apr 06 2017 09:15:56 GMT-0600 (Mountain Daylight Time) from the " \
               "following site(s): HOBBLE CREEK AT 1650 WEST AT SPRINGVILLE, UTAH, and " \
               "Provo River at Charleston Advanced Aquatic. Data created by " \
               "CUAHSI HydroClient: http://data.cuahsi.org/#."

    self.assertEqual(self.composite_resource.metadata.description.abstract, abstract)

    # test keywords - resource level keywords should have been updated with data from the json
    # file
    keywords = [kw.value for kw in self.composite_resource.metadata.subjects.all()]
    for kw in keywords:
        self.assertIn(kw, ["Time Series", "CUAHSI"])

    # test coverage metadata
    box_coverage = self.composite_resource.metadata.coverages.all().filter(type='box').first()
    self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
    self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
    self.assertEqual(box_coverage.value['northlimit'], 40.48498)
    self.assertEqual(box_coverage.value['eastlimit'], -111.46245)
    self.assertEqual(box_coverage.value['southlimit'], 40.1788719)
    self.assertEqual(box_coverage.value['westlimit'], -111.639338)

    temporal_coverage = self.composite_resource.metadata.coverages.all().filter(
        type='period').first()
    self.assertEqual(parser.parse(temporal_coverage.value['start']).date(),
                     parser.parse('04/06/2016').date())
    self.assertEqual(parser.parse(temporal_coverage.value['end']).date(),
                     parser.parse('02/09/2017').date())

    # test file level metadata
    res_file = self.composite_resource.files.first()
    logical_file = res_file.logical_file
    self.assertEqual(logical_file.dataset_name, res_title)
    for kw in logical_file.metadata.keywords:
        self.assertIn(kw, ["Time Series", "CUAHSI"])
    box_coverage = logical_file.metadata.coverages.all().filter(type='box').first()
    self.assertEqual(box_coverage.value['projection'], 'Unknown')
    self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
    self.assertEqual(box_coverage.value['northlimit'], 40.48498)
    self.assertEqual(box_coverage.value['eastlimit'], -111.46245)
    self.assertEqual(box_coverage.value['southlimit'], 40.1788719)
    self.assertEqual(box_coverage.value['westlimit'], -111.639338)
    temporal_coverage = logical_file.metadata.coverages.all().filter(
        type='period').first()
    self.assertEqual(parser.parse(temporal_coverage.value['start']).date(),
                     parser.parse('04/06/2016').date())
    self.assertEqual(parser.parse(temporal_coverage.value['end']).date(),
                     parser.parse('02/09/2017').date())

    # file level abstract
    self.assertEqual(logical_file.metadata.abstract, abstract)
    # there should be 2 time series
    self.assertEqual(len(logical_file.metadata.time_series_list), 2)

    # test site related metadata

    self.assertEqual(len(logical_file.metadata.sites), 2)
    site_names = [site.name for site in logical_file.metadata.sites]
    self.assertIn("HOBBLE CREEK AT 1650 WEST AT SPRINGVILLE, UTAH", site_names)
    self.assertIn("Provo River at Charleston Advanced Aquatic", site_names)
    site_codes = [site.code for site in logical_file.metadata.sites]
    self.assertIn("NWISDV:10153100", site_codes)
    self.assertIn("Provo River GAMUT:PR_CH_AA", site_codes)
    site_lats = [site.latitude for site in logical_file.metadata.sites]
    self.assertIn(40.178871899999997, site_lats)
    self.assertIn(40.48498, site_lats)
    site_lons = [site.longitude for site in logical_file.metadata.sites]
    self.assertIn(-111.639338, site_lons)
    self.assertIn(-111.46245, site_lons)

    # there should be 2 variables
    self.assertEqual(len(logical_file.metadata.variables), 2)
    var_names = [var.name for var in logical_file.metadata.variables]
    self.assertIn("Discharge, cubic feet per second", var_names)
    self.assertIn("Blue-green algae (cyanobacteria), phycocyanin", var_names)
    var_codes = [var.code for var in logical_file.metadata.variables]
    self.assertIn("NWISDV:00060/DataType=MEAN", var_codes)
    self.assertIn("iutah:BGA", var_codes)
    # there should be 2 web services
    self.assertEqual(len(logical_file.metadata.web_services), 2)
    web_urls = [web.url for web in logical_file.metadata.web_services]
    self.assertIn("http://hydroportal.cuahsi.org/nwisdv/cuahsi_1_1.asmx?WSDL", web_urls)
    self.assertIn("http://data.iutahepscor.org/ProvoRiverWOF/cuahsi_1_1.asmx?WSDL", web_urls)
    web_service_types = [web.service_type for web in logical_file.metadata.web_services]
    self.assertIn("SOAP", web_service_types)
    self.assertEqual(len(set(web_service_types)), 1)
    web_reference_types = [web.reference_type for web in logical_file.metadata.web_services]
    self.assertIn("WOF", web_reference_types)
    web_return_types = [web.return_type for web in logical_file.metadata.web_services]
    self.assertIn("WaterML 1.1", web_return_types)


def assert_time_series_file_type_metadata(self, expected_file_folder):
    """Test timeseries file type metadata extraction."""

    # check that there is one TimeSeriesLogicalFile object
    self.assertEqual(TimeSeriesLogicalFile.objects.count(), 1)

    # check that there is one TimeSeriesFileMetaData object
    self.assertEqual(TimeSeriesFileMetaData.objects.count(), 1)

    res_file = self.composite_resource.files.first()
    logical_file = res_file.logical_file
    self.assertTrue(isinstance(logical_file.metadata, TimeSeriesFileMetaData))

    # test extracted metadata that updates resource level metadata

    # there should one content file - sqlite file
    self.assertEqual(self.composite_resource.files.all().count(), 1)

    # there should be one contributor element
    self.assertEqual(self.composite_resource.metadata.contributors.all().count(), 1)

    # test core metadata after metadata extraction
    extracted_title = "Water temperature data from the Little Bear River, UT"
    self.assertEqual(self.composite_resource.metadata.title.value, extracted_title)

    # there should be an abstract element
    self.assertNotEqual(self.composite_resource.metadata.description, None)
    extracted_abstract = "This dataset contains time series of observations of water " \
                         "temperature in the Little Bear River, UT. Data were recorded every " \
                         "30 minutes. The values were recorded using a HydroLab MS5 " \
                         "multi-parameter water quality sonde connected to a Campbell " \
                         "Scientific datalogger."

    self.assertEqual(self.composite_resource.metadata.description.abstract.strip(),
                     extracted_abstract)

    # there should be 2 coverage element -  box type and period type
    self.assertEqual(self.composite_resource.metadata.coverages.all().count(), 2)
    self.assertEqual(self.composite_resource.metadata.coverages.all().filter(type='box').count(), 1)
    self.assertEqual(self.composite_resource.metadata.coverages.all().filter(
        type='period').count(), 1)

    box_coverage = self.composite_resource.metadata.coverages.all().filter(type='box').first()
    self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
    self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
    self.assertEqual(box_coverage.value['northlimit'], 41.718473)
    self.assertEqual(box_coverage.value['eastlimit'], -111.799324)
    self.assertEqual(box_coverage.value['southlimit'], 41.495409)
    self.assertEqual(box_coverage.value['westlimit'], -111.946402)

    temporal_coverage = self.composite_resource.metadata.coverages.all().filter(
        type='period').first()
    self.assertEqual(parser.parse(temporal_coverage.value['start']).date(),
                     parser.parse('01/01/2008').date())
    self.assertEqual(parser.parse(temporal_coverage.value['end']).date(),
                     parser.parse('01/31/2008').date())

    # there should be one format element
    self.assertEqual(self.composite_resource.metadata.formats.all().count(), 1)
    format_element = self.composite_resource.metadata.formats.all().first()
    self.assertEqual(format_element.value, 'application/sqlite')

    # there should be one subject element
    self.assertEqual(self.composite_resource.metadata.subjects.all().count(), 1)
    subj_element = self.composite_resource.metadata.subjects.all().first()
    self.assertEqual(subj_element.value, 'Temperature')

    # test that we put the sqlite file into a new directory
    res_file = self.composite_resource.files.first()
    self.assertEqual(res_file.file_folder, expected_file_folder)

    logical_file = res_file.logical_file

    # logical file should be associated with 1 file
    self.assertEqual(logical_file.files.all().count(), 1)
    res_file = logical_file.files.first()
    self.assertEqual('.sqlite', res_file.extension.lower())

    # test file level metadata extraction

    # there should be a total of 7 timeseries
    self.assertEqual(logical_file.metadata.time_series_results.all().count(), 7)

    # testing extended metadata elements

    # test title/dataset name
    self.assertEqual(logical_file.dataset_name, extracted_title)

    # test abstract
    self.assertEqual(logical_file.metadata.abstract, extracted_abstract)

    # there should be one keyword element
    self.assertEqual(len(logical_file.metadata.keywords), 1)
    self.assertIn('Temperature', logical_file.metadata.keywords)

    # test spatial coverage
    box_coverage = logical_file.metadata.spatial_coverage
    self.assertEqual(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
    self.assertEqual(box_coverage.value['units'], 'Decimal degrees')
    self.assertEqual(box_coverage.value['northlimit'], 41.718473)
    self.assertEqual(box_coverage.value['eastlimit'], -111.799324)
    self.assertEqual(box_coverage.value['southlimit'], 41.495409)
    self.assertEqual(box_coverage.value['westlimit'], -111.946402)

    # test temporal coverage
    temporal_coverage = logical_file.metadata.temporal_coverage
    self.assertEqual(parser.parse(temporal_coverage.value['start']).date(),
                     parser.parse('01/01/2008').date())
    self.assertEqual(parser.parse(temporal_coverage.value['end']).date(),
                     parser.parse('01/31/2008').date())

    # test 'site' - there should be 7 sites
    self.assertEqual(logical_file.metadata.sites.all().count(), 7)
    # each site be associated with one series id
    for site in logical_file.metadata.sites.all():
        self.assertEqual(len(site.series_ids), 1)

    # test the data for a specific site
    site = logical_file.metadata.sites.filter(site_code='USU-LBR-Paradise').first()
    self.assertNotEqual(site, None)
    site_name = 'Little Bear River at McMurdy Hollow near Paradise, Utah'
    self.assertEqual(site.site_name, site_name)
    self.assertEqual(site.elevation_m, 1445)
    self.assertEqual(site.elevation_datum, 'NGVD29')
    self.assertEqual(site.site_type, 'Stream')
    self.assertEqual(site.latitude, 41.575552)
    self.assertEqual(site.longitude, -111.855217)

    # test 'variable' - there should be 1 variable element
    self.assertEqual(logical_file.metadata.variables.all().count(), 1)
    variable = logical_file.metadata.variables.all().first()
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
    self.assertEqual(logical_file.metadata.methods.all().count(), 1)
    method = logical_file.metadata.methods.all().first()
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
    self.assertEqual(logical_file.metadata.processing_levels.all().count(), 1)
    proc_level = logical_file.metadata.processing_levels.all().first()
    # there should be 7 series ids associated with this one element
    self.assertEqual(len(proc_level.series_ids), 7)
    self.assertEqual(proc_level.processing_level_code, 1)
    self.assertEqual(proc_level.definition, 'Quality controlled data')
    explanation = 'Quality controlled data that have passed quality assurance procedures ' \
                  'such as routine estimation of timing and sensor calibration or visual ' \
                  'inspection and removal of obvious errors. An example is USGS published ' \
                  'streamflow records following parsing through USGS quality control ' \
                  'procedures.'
    self.assertEqual(proc_level.explanation, explanation)

    # test 'timeseries_result' - there should be 7 timeseries_result element
    self.assertEqual(logical_file.metadata.time_series_results.all().count(), 7)
    ts_result = logical_file.metadata.time_series_results.filter(
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
    self.assertEqual(logical_file.metadata.cv_variable_types.all().count(), 23)
    # there should be 805 CV_VariableName records
    self.assertEqual(logical_file.metadata.cv_variable_names.all().count(), 805)
    # there should be 145 CV_Speciation records
    self.assertEqual(logical_file.metadata.cv_speciations.all().count(), 145)
    # there should be 51 CV_SiteType records
    self.assertEqual(logical_file.metadata.cv_site_types.all().count(), 51)
    # there should be 5 CV_ElevationDatum records
    self.assertEqual(logical_file.metadata.cv_elevation_datums.all().count(), 5)
    # there should be 25 CV_MethodType records
    self.assertEqual(logical_file.metadata.cv_method_types.all().count(), 25)
    # there should be 179 CV_UnitsType records
    self.assertEqual(logical_file.metadata.cv_units_types.all().count(), 179)
    # there should be 4 CV_Status records
    self.assertEqual(logical_file.metadata.cv_statuses.all().count(), 4)
    # there should be 17 CV_Medium records
    self.assertEqual(logical_file.metadata.cv_mediums.all().count(), 18)
    # there should be 17 CV_aggregationStatistics records
    self.assertEqual(logical_file.metadata.cv_aggregation_statistics.all().count(), 17)
    # there should not be any UTCOffset element
    self.assertEqual(logical_file.metadata.utc_offset, None)
