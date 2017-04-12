from dateutil import parser

from hs_core.hydroshare.utils import get_resource_file_name_and_extension
from hs_file_types.models import GeoRasterLogicalFile, GeoRasterFileMetaData, GenericLogicalFile, \
    NetCDFLogicalFile, RefTimeseriesLogicalFile


def assert_raster_file_type_metadata(self):
    # test the resource now has 2 files (vrt file added as part of metadata extraction)
    self.assertEqual(self.composite_resource.files.all().count(), 2)

    # check that the 2 resource files are now associated with GeoRasterLogicalFile
    for res_file in self.composite_resource.files.all():
        self.assertEqual(res_file.logical_file_type_name, "GeoRasterLogicalFile")
        self.assertEqual(res_file.has_logical_file, True)
        self.assertTrue(isinstance(res_file.logical_file, GeoRasterLogicalFile))

    # check that we put the 2 files in a new folder (small_logan)
    for res_file in self.composite_resource.files.all():
        file_path, base_file_name, _ = get_resource_file_name_and_extension(res_file)
        expected_file_path = "{}/data/contents/small_logan/{}"
        expected_file_path = expected_file_path.format(self.composite_resource.root_path,
                                                       base_file_name)
        self.assertEqual(file_path, expected_file_path)

    # check that there is no GenericLogicalFile object
    self.assertEqual(GenericLogicalFile.objects.count(), 0)
    # check that there is one GeoRasterLogicalFile object
    self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)

    res_file = self.composite_resource.files.first()
    # check that the logicalfile is associated with 2 files
    logical_file = res_file.logical_file
    self.assertEqual(logical_file.dataset_name, 'small_logan')
    self.assertEqual(logical_file.has_metadata, True)
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


def assert_netcdf_file_type_metadata(self, title):
    # check that there is one NetCDFLogicalFile object
    self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
    # check that there is no GenericLogicalFile object
    self.assertEqual(GenericLogicalFile.objects.count(), 0)

    # There should be now 2 files
    self.assertEqual(self.composite_resource.files.count(), 2)
    # check that we put the 2 files in a new folder (netcdf_valid)
    for res_file in self.composite_resource.files.all():
        file_path, base_file_name = res_file.full_path, res_file.file_name
        expected_file_path = u"{}/data/contents/netcdf_valid/{}"
        expected_file_path = expected_file_path.format(self.composite_resource.root_path,
                                                       base_file_name)
        self.assertEqual(file_path, expected_file_path)

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
    self.assertEqual(len(logical_file.metadata.time_serieses), 2)

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
